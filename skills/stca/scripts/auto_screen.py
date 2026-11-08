#!/usr/bin/env python3
"""Clean a property table, assign protected ECFP4 roles, fit and screen STCA.

This orchestration adapter calls the pinned author's implementation through
custom_fit. Its automatic decisions use source/inner data only. Generated
t-SNE memberships are a new custom split, not recovered paper memberships.
Original repeat-unit SMILES remain authoritative; MACCS always uses H-cap.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def read_auto_frame(path):
    """Repair export headers only; preserve text cells and reject broken CSV."""
    import pandas as pd

    source = Path(path).expanduser().resolve()
    raw = source.read_bytes()
    blank_count = 0
    original_header = None
    rows = []
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        for row in reader:
            # A blank physical record outside quotes has no fields. Blank lines
            # inside a quoted field remain part of that field and are preserved.
            if not row:
                blank_count += 1
                continue
            if original_header is None:
                original_header = list(row)
                continue
            if len(row) != len(original_header):
                raise ValueError(f"CSV record ending at physical line {reader.line_num} has {len(row)} fields; expected {len(original_header)}. No values were shifted or dropped.")
            rows.append(row)
    except (UnicodeError, csv.Error) as exc:
        raise ValueError(f"Cannot read strict UTF-8 CSV: {exc}") from exc
    if original_header is None:
        raise ValueError("CSV has no header.")
    if not rows:
        raise ValueError("CSV contains no data records.")
    # Preserve existing meaningful names when a generated alias needs a suffix.
    reserved = {name.strip() for name in original_header if name.strip()}
    header, aliases, used = [], [], set()
    for position, original in enumerate(original_header, 1):
        base = original.strip() or f"archive_unnamed_column_{position}"
        candidate, suffix = base, 2
        if not original.strip() and candidate in reserved:
            candidate = f"{base}_{suffix}"
            suffix += 1
        while candidate in used or (candidate != base and candidate in reserved):
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        header.append(candidate)
        aliases.append({"column_position_1based": position, "original_header": original,
                        "normalized_header": candidate, "changed": original != candidate})
    audit = {"schema": "stca-auto-input-format-v1", "input_path": str(source),
             "input_sha256": hashlib.sha256(raw).hexdigest(),
             "encoding": "utf-8-sig", "csv_strict": True,
             "original_header": original_header, "normalized_header": header,
             "column_alias_map": aliases, "data_records": len(rows),
             "blank_physical_record_count": blank_count,
             "blank_record_policy": "skip_only_zero_field_physical_records_outside_quotes",
             "column_count": len(header), "record_width_validated": True,
             "data_values_changed": False, "no_values_changed": True, "columns_removed": 0,
             "data_rows_removed": 0, "numeric_coercion_performed": False}
    return pd.DataFrame(rows, columns=header, dtype=str), audit


def resolve_input_columns(args, frame, format_audit):
    """Resolve named input columns after transparent header normalization."""
    aliases = format_audit["column_alias_map"]

    def resolve(value):
        if value is None or value in frame:
            return value
        if value.strip() in frame:
            return value.strip()
        matches = [r["normalized_header"] for r in aliases if r["original_header"] == value]
        return matches[0] if len(matches) == 1 else value

    for name in ("target", "smiles_column", "id_column", "group_column", "role_column",
                 "inner_role_column", "quality_column"):
        setattr(args, name, resolve(getattr(args, name)))
    for name in ("metadata_columns", "condition_columns"):
        setattr(args, name, ",".join(resolve(c.strip()) for c in getattr(args, name).split(",") if c.strip()))


def unique_column(frame, name):
    candidate, suffix = name, 2
    while candidate in frame:
        candidate = f"{name}_{suffix}"
        suffix += 1
    return candidate


def protected_components(original, capped, explicit_groups=None):
    """Union related observations without aggregating or deleting records."""
    parent = list(range(len(original)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a, b)] = min(a, b)

    for values in (original, capped, explicit_groups):
        if values is None:
            continue
        seen = {}
        for i, value in enumerate(values):
            if value in seen:
                union(i, seen[value])
            else:
                seen[value] = i
    return [find(i) for i in range(len(original))]


def tsne_peripheral_split(fingerprints, positions, components, *, scope):
    """Archive architecture: 2D ECFP4 t-SNE, centroid distance, outer 20%."""
    import numpy as np
    import sklearn
    from sklearn.manifold import TSNE
    from threadpoolctl import threadpool_limits
    from rdkit import DataStructs

    positions = np.asarray(positions, dtype=int)
    n = len(positions)
    if n < 5:
        raise ValueError(f"{scope} split unavailable: at least five valid records are required for >=4 training and >=1 validation/holdout records. Supply explicit roles or explicitly choose --scan-policy fixed for an unavailable inner split.")
    matrix = np.zeros((n, 2048), dtype=np.int8)
    for i, position in enumerate(positions):
        DataStructs.ConvertToNumpyArray(fingerprints[position], matrix[i])
    perplexity = min(30, max(5, n // 4), n - 1)
    with threadpool_limits(limits=1):
        embedding = TSNE(n_components=2, random_state=42, perplexity=perplexity,
                         init="pca", learning_rate="auto", metric="euclidean",
                         method="barnes_hut", angle=0.5, n_jobs=1, max_iter=1000,
                         early_exaggeration=12.0, n_iter_without_progress=300,
                         min_grad_norm=1e-7).fit_transform(matrix)
    if not np.isfinite(embedding).all():
        raise ValueError(f"{scope} t-SNE returned nonfinite coordinates; no alternative split was substituted.")
    distance = np.linalg.norm(embedding - embedding.mean(axis=0), axis=1)
    n_outer = int(0.2 * n)
    initial_outer = np.zeros(n, dtype=bool)
    initial_outer[np.argsort(distance, kind="stable")[-n_outer:]] = True
    outer_groups = {components[p] for p in positions[initial_outer]}
    outer = np.asarray([components[p] in outer_groups for p in positions], dtype=bool)
    if int((~outer).sum()) < 4 or not outer.any():
        raise ValueError(f"{scope} split unavailable after original/H-cap/group protection: train={int((~outer).sum())}, outer={int(outer.sum())}. No groups were split, merged into observations, or deleted. Supply explicit valid roles or explicitly choose --scan-policy fixed when only the inner split is unavailable.")
    report = {
        "scope": scope, "method": "ecfp4_hcap_tsne_centroid_outer_20pct",
        "fingerprint": {"family": "Morgan", "radius": 2, "diameter": 4,
                        "bits": 2048, "input": "calculation_only_hcap"},
        "tsne": {"n_components": 2, "random_state": 42, "perplexity": perplexity,
                 "init": "pca", "learning_rate": "auto", "metric": "euclidean",
                 "method": "barnes_hut", "angle": 0.5, "n_jobs": 1,
                 "max_iter": 1000, "early_exaggeration": 12.0,
                 "n_iter_without_progress": 300, "min_grad_norm": 1e-7,
                 "threadpool_limit": 1, "sklearn_version": sklearn.__version__},
        "n": n, "requested_outer_fraction": 0.2,
        "initial_outer_n": int(initial_outer.sum()), "protected_outer_n": int(outer.sum()),
        "protected_train_n": int((~outer).sum()),
        "records_moved_to_outer_for_protection": int((outer & ~initial_outer).sum()),
        "protection": ["canonical_original_repeat_unit", "canonical_hcap", "explicit_group_if_supplied"],
        "protection_policy": "outer_wins_no_record_aggregation_or_deletion",
        "target_values_used": False, "new_custom_memberships": True,
        "exact_paper_memberships_reproduced": False,
        "structural_extrapolation_guaranteed": False,
    }
    return positions[~outer], positions[outer], distance, report


def recommendations(settings):
    """Recommend tiers only from the selected candidate's inner validation."""
    selection = settings.get("selection", {})
    selected = selection.get("selected_candidate")
    result = {"scope": "selected_candidate_inner_validation", "eligible_tiers": [],
              "strictest_eligible_tier": None, "outer_labels_used": False,
              "performance_guarantee": False, "tiers": []}
    if not isinstance(selected, dict):
        result["status"] = "unavailable_without_selected_inner_candidate"
        result["reason"] = "Fixed/source-only fitting supplies no inner-validation tier recommendation; source resubstitution is not independent evidence."
        return result
    for record in selected.get("tier_evaluations", []):
        metrics = record.get("metrics") or {}
        n = metrics.get("n", record.get("n", 0))
        pos = metrics.get("positive_n")
        prevalence = float(pos) / n if n and pos is not None else None
        mcc, precision = metrics.get("mcc"), metrics.get("precision")
        selected_n = metrics.get("selected_n", 0)
        reasons = []
        if record.get("status") != "evaluated":
            reasons.append("no_successful_inner_evaluation")
        if record.get("metric_status") != "computed":
            reasons.append("undefined_or_unavailable_metrics")
        if not selected_n:
            reasons.append("zero_selection_coverage")
        if mcc is None or not math.isfinite(float(mcc)) or mcc <= 0:
            reasons.append("MCC_not_strictly_positive")
        if precision is None or prevalence is None or precision <= prevalence:
            reasons.append("precision_not_above_target_prevalence")
        tier = float(record["tier"])
        result["tiers"].append({"tier": tier, "eligible": not reasons,
                                "failed_conditions": reasons, "mcc": mcc,
                                "precision": precision, "prevalence": prevalence,
                                "selected_n": selected_n,
                                "evidence_status": record.get("evidence_status")})
        if not reasons:
            result["eligible_tiers"].append(tier)
    result["eligible_tiers"] = sorted(set(result["eligible_tiers"]))
    if result["eligible_tiers"]:
        result["strictest_eligible_tier"] = min(result["eligible_tiers"])
        result["status"] = "inner_validation_recommendation"
    else:
        result["status"] = "no_eligible_inner_validation_tier"
        result["reason"] = "All actual tier results remain available. No tier is invented and no outer result selects a tier."
    return result


def _forward(argv, flag, value):
    if value is not None:
        argv.extend([flag, str(value)])


def run(args):
    import numpy as np
    import pandas as pd
    from rdkit import Chem, rdBase
    from rdkit.Chem import rdFingerprintGenerator
    from prepare_hcap import hcap_smiles
    from data_cleaning import clean_frame
    import custom_fit

    output = Path(args.output_dir).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Output directory exists; choose a new directory.")
    frame, input_format = read_auto_frame(args.input)
    resolve_input_columns(args, frame, input_format)
    # An archival input-column rename must not rename the user's property.
    if args.target_name is None:
        args.target_name = args.target
    required = {args.smiles_column, args.target}
    required.update(c for c in (args.role_column, args.inner_role_column, args.id_column,
                                args.group_column, args.quality_column) if c)
    required.update(c.strip() for c in (args.metadata_columns + "," + args.condition_columns).split(",") if c.strip())
    if required - set(frame):
        raise ValueError(f"Missing columns: {sorted(required-set(frame))}")
    if args.source_value == args.evaluation_value or args.inner_train_value == args.inner_validation_value:
        raise ValueError("Training and evaluation role values must differ.")
    output.mkdir(parents=True)
    write_json(output / "input_format_audit.json", input_format)
    try:
        cleaned, excluded, cleaning = clean_frame(
            frame, target=args.target, smiles_column=args.smiles_column,
            id_column=args.id_column, quality_column=args.quality_column,
            exclude_quality_values=args.exclude_quality_value,
            target_min=args.target_min, target_max=args.target_max,
            role_column=args.role_column)
        cleaned = cleaned.reset_index(drop=True)
        cleaned.to_csv(output / "cleaned_input.csv", index=False)
        excluded.to_csv(output / "excluded_rows.csv", index=False)
        write_json(output / "cleaning_audit.json", cleaning)
        if len(cleaned) < 4:
            raise ValueError("Fewer than four usable records remain; consult excluded_rows.csv. No fit was attempted.")
        # The cleaner may rename reserved input columns; use its declared mapping.
        renamed = cleaning.get("reserved_column_renames", {})
        if isinstance(renamed, dict):
            for attr in ("target", "smiles_column", "id_column", "group_column", "role_column", "inner_role_column", "quality_column"):
                value = getattr(args, attr)
                if value in renamed:
                    setattr(args, attr, renamed[value])
            for attr in ("condition_columns", "metadata_columns"):
                value = getattr(args, attr)
                setattr(args, attr, ",".join(renamed.get(c.strip(), c.strip()) for c in value.split(",") if c.strip()))
        original, capped = [], []
        for smiles in cleaned[args.smiles_column]:
            original.append(Chem.MolToSmiles(Chem.MolFromSmiles(smiles), canonical=True))
            cap, _ = hcap_smiles(smiles)
            capped.append(Chem.MolToSmiles(Chem.MolFromSmiles(cap), canonical=True))
        explicit_groups = None
        if args.group_column:
            explicit_groups = cleaned[args.group_column].astype(str).tolist()
            if any(not g.strip() for g in explicit_groups):
                raise ValueError("Explicit grouping column contains empty values; no rows were silently removed for grouping.")
        components = protected_components(original, capped, explicit_groups)
        generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        fps = [generator.GetFingerprint(Chem.MolFromSmiles(cap)) for cap in capped]
        membership = pd.DataFrame({"cleaned_row_position": np.arange(len(cleaned)),
                                   "original_smiles": cleaned[args.smiles_column],
                                   "canonical_original": original, "canonical_hcap": capped,
                                   "protected_group": components})
        position_column = cleaning.get("row_position_column")
        if position_column in cleaned:
            membership["input_row_position"] = cleaned[position_column].to_numpy()
        split_reports = {}
        if args.role_column:
            roles = set(cleaned[args.role_column])
            if roles - {args.source_value, args.evaluation_value}:
                raise ValueError(f"Unrecognized explicit data roles: {sorted(roles)}")
            split_reports["outer"] = {"method": "user_supplied_roles_preserved", "role_column": args.role_column,
                                      "target_values_used": False}
        else:
            args.role_column = unique_column(cleaned, "auto_role")
            tr, te, distance, report = tsne_peripheral_split(fps, np.arange(len(cleaned)), components, scope="outer")
            cleaned[args.role_column] = args.source_value
            cleaned.loc[te, args.role_column] = args.evaluation_value
            membership["outer_centroid_distance"] = distance
            split_reports["outer"] = report
        source = np.flatnonzero((cleaned[args.role_column] == args.source_value).to_numpy())
        evaluation = np.flatnonzero((cleaned[args.role_column] == args.evaluation_value).to_numpy())
        if len(source) < 4:
            raise ValueError("At least four usable source records are required.")
        source_set, evaluation_set = set(source), set(evaluation)
        split_reports["outer"]["protected_group_overlap"] = len({components[i] for i in source_set} & {components[i] for i in evaluation_set})
        membership["role"] = cleaned[args.role_column].to_numpy()
        if args.scan_policy == "nested":
            if args.inner_role_column:
                split_reports["inner"] = {"method": "user_supplied_inner_roles_preserved",
                                          "role_column": args.inner_role_column, "outer_rows_used": False}
            else:
                args.inner_role_column = unique_column(cleaned, "auto_inner_role")
                itr, iva, distance, report = tsne_peripheral_split(fps, source, components, scope="inner_source_only")
                cleaned[args.inner_role_column] = ""
                cleaned.loc[itr, args.inner_role_column] = args.inner_train_value
                cleaned.loc[iva, args.inner_role_column] = args.inner_validation_value
                membership["inner_centroid_distance"] = np.nan
                membership.loc[source, "inner_centroid_distance"] = distance
                split_reports["inner"] = report
            membership["inner_role"] = cleaned[args.inner_role_column].to_numpy()
        else:
            split_reports["inner"] = {"method": "not_used_explicit_fixed_policy", "outer_labels_used": False}
        cleaned.to_csv(output / "workflow_input.csv", index=False)
        membership.to_csv(output / "split_membership.csv", index=False)
        write_json(output / "split_audit.json", split_reports)
        already_log = args.already_log or bool(re.fullmatch(r"\s*log10\s*\(.*\)\s*", args.unit))
        if already_log and args.transform == "log10":
            raise ValueError("Already-log input cannot be log10-transformed again.")
        fit_args = []
        for flag, value in (("--source", args.source), ("--input", output / "workflow_input.csv"),
                            ("--target", args.target), ("--target-name", args.target_name),
                            ("--unit", args.unit), ("--direction", args.direction), ("--tiers", args.tiers),
                            ("--role-column", args.role_column), ("--source-value", args.source_value),
                            ("--evaluation-value", args.evaluation_value), ("--smiles-column", args.smiles_column),
                            ("--id-column", args.id_column), ("--group-column", args.group_column),
                            ("--inner-role-column", args.inner_role_column if args.scan_policy == "nested" else None),
                            ("--inner-train-value", args.inner_train_value), ("--inner-validation-value", args.inner_validation_value),
                            ("--scan-policy", args.scan_policy), ("--transform", args.transform),
                            ("--scan-step", args.scan_step), ("--min-subset-size", args.min_subset_size),
                            ("--target-points", args.target_points), ("--max-grid-points", args.max_grid_points),
                            ("--positive-support", args.positive_support), ("--selection-margin", args.selection_margin),
                            ("--max-rank", args.max_rank), ("--family-size", args.family_size),
                            ("--condition-columns", args.condition_columns), ("--metadata-columns", args.metadata_columns),
                            ("--data-kind", args.data_kind), ("--invalid-policy", "error"),
                            ("--output-dir", output / "fit")):
            _forward(fit_args, flag, value)
        if already_log:
            fit_args.append("--already-log")
        write_json(output / "automation_plan.json", {
            "schema": "stca-auto-workflow-v1", "integration_version": "0.1.0",
            "input_sha256": hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
            "custom_fit_argv": fit_args, "MACCS_representation": "hcap_maccs167",
            "original_repeat_unit_retained": True, "outer_labels_used_for_settings": False,
            "target_transform_policy": args.transform, "already_log": already_log,
            "already_log_inferred_from_unit": already_log and not args.already_log,
            "already_log_inference_rule": "explicit_log10(unit)_notation_only",
            "automatic_chemical_representation_switch": False,
            "automatic_split_is_paper_exact_reproduction": False,
            "rdkit_version": rdBase.rdkitVersion})
        code = custom_fit.main(fit_args)
        model = output / "fit" / "model.json"
        if code and not model.exists():
            raise RuntimeError(f"custom_fit exited {code}; see fit/failure.json and the captured diagnostic.")
        settings_path = output / "fit" / "source_settings.json"
        settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
        recommendation = recommendations(settings)
        write_json(output / "tier_recommendations.json", recommendation)
        screen_result = {"status": "not_requested"}
        if args.candidates:
            import stca_tools
            tier = args.screen_tier if args.screen_tier is not None else recommendation["strictest_eligible_tier"]
            if tier is None:
                screen_result = {"status": "not_screened_no_recommended_tier",
                                 "reason": "No eligible inner-validation tier. All rules and evaluations remain available; supply --screen-tier explicitly to inspect a declared tier."}
            else:
                screen_args = []
                _forward(screen_args, "--source", args.source)
                screen_args.append("screen-candidates")
                for flag, value in (("--model", model), ("--tier", tier), ("--input", args.candidates),
                                    ("--id-column", args.candidate_id_column),
                                    ("--smiles-column", args.candidate_smiles_column),
                                    ("--output-dir", output / "screening")):
                    _forward(screen_args, flag, value)
                screen_code = stca_tools.main(screen_args)
                screen_result = {"status": "completed" if screen_code == 0 else "failed",
                                 "tier": tier, "tier_source": "user_explicit" if args.screen_tier is not None else "selected_inner_validation",
                                 "exit_code": screen_code, "output_directory": str(output / "screening")}
                if screen_code:
                    code = 2
        status = "partial_failure" if code else "completed"
        write_json(output / "run_manifest.json", {
            "schema": "stca-auto-workflow-v1", "integration_version": "0.1.0", "status": status,
            "cleaned_n": len(cleaned), "excluded_n": len(excluded),
            "source_n": len(source), "holdout_n": len(evaluation),
            "cleaning_audit": "cleaning_audit.json", "split_audit": "split_audit.json",
            "input_format_audit": "input_format_audit.json",
            "model": "fit/model.json", "tier_recommendations": "tier_recommendations.json",
            "screening": screen_result, "outer_labels_used_for_fit_or_tier_selection": False,
            "upstream_STCA_modified": False, "performance_guaranteed": False})
        print(json.dumps({"status": status, "output_directory": str(output), "model": str(model),
                          "recommended_tier": recommendation["strictest_eligible_tier"], "screening": screen_result}))
        return int(code)
    except Exception as exc:
        if "split_reports" in locals() and not (output / "split_audit.json").exists():
            split_reports["workflow_failure"] = {"status": "unavailable", "reason": str(exc),
                                                  "no_fallback_split": True}
            write_json(output / "split_audit.json", split_reports)
        if "membership" in locals() and not (output / "split_membership.csv").exists():
            membership.to_csv(output / "split_membership.csv", index=False)
        failure = output / "failure.json"
        if not failure.exists():
            write_json(failure, {"status": "failed", "error_type": type(exc).__name__, "reason": str(exc),
                                 "metrics": None, "no_fallback_split_or_fake_zero_score": True})
        raise


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "target", "unit", "direction", "tiers", "output-dir"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--source", help="Clean pinned author source checkout")
    p.add_argument("--target-name")
    p.add_argument("--smiles-column", default="SMILES")
    p.add_argument("--id-column")
    p.add_argument("--group-column")
    p.add_argument("--role-column", help="Preserve explicit source/holdout roles; omit for protected ECFP4 t-SNE roles")
    p.add_argument("--source-value", default="source")
    p.add_argument("--evaluation-value", default="holdout")
    p.add_argument("--inner-role-column")
    p.add_argument("--inner-train-value", default="train")
    p.add_argument("--inner-validation-value", default="validation")
    p.add_argument("--scan-policy", choices=("nested", "fixed"), default="nested")
    p.add_argument("--transform", choices=("auto", "none", "log10"), default="auto")
    p.add_argument("--already-log", action="store_true")
    p.add_argument("--scan-step", type=float)
    p.add_argument("--min-subset-size", type=int, default=1)
    p.add_argument("--target-points", type=int, default=500)
    p.add_argument("--max-grid-points", type=int, default=20000)
    p.add_argument("--positive-support", type=int, default=20)
    p.add_argument("--selection-margin", type=float, default=0.05)
    p.add_argument("--max-rank", type=int, default=10)
    p.add_argument("--family-size", type=int, default=8)
    p.add_argument("--condition-columns", default="")
    p.add_argument("--metadata-columns", default="")
    p.add_argument("--data-kind", choices=("experimental", "computed", "unspecified"), default="unspecified")
    p.add_argument("--quality-column")
    p.add_argument("--exclude-quality-value", action="append", default=[], help="Explicit unusable quality value; repeat for multiple values")
    p.add_argument("--target-min", type=float)
    p.add_argument("--target-max", type=float)
    p.add_argument("--candidates", help="Optional independent candidate table to screen after fitting")
    p.add_argument("--candidate-id-column")
    p.add_argument("--candidate-smiles-column", default="SMILES")
    p.add_argument("--screen-tier", type=float, help="Explicit fitted tier; otherwise use the strictest eligible inner-validation tier")
    args = p.parse_args(argv)
    try:
        from custom_fit import parse_tiers
        tiers = parse_tiers(args.tiers)
        if args.direction not in ("high", "low"):
            raise ValueError("direction must be high or low")
        if args.screen_tier is not None and args.screen_tier not in tiers:
            raise ValueError("screen-tier must equal one of the requested tier fractions")
        if args.scan_step is not None and (not math.isfinite(args.scan_step) or args.scan_step <= 0):
            raise ValueError("scan-step must be positive and finite")
        if args.target_points < 4 or args.max_grid_points < 4 or args.min_subset_size < 1:
            raise ValueError("target-points/max-grid-points must be >=4 and min-subset-size >=1")
        if args.max_rank < 1 or args.family_size < 1 or args.positive_support < 1 or args.selection_margin < 0:
            raise ValueError("Invalid rank, family, support or selection settings")
        if args.target_min is not None and args.target_max is not None and args.target_min > args.target_max:
            raise ValueError("target-min must not exceed target-max")
        if args.exclude_quality_value and not args.quality_column:
            raise ValueError("exclude-quality-value requires --quality-column")
        return run(args)
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"stca-auto: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
