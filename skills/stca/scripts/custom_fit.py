#!/usr/bin/env python3
"""Fit/evaluate arbitrary-property STCA with source-owned preprocessing.

This adapter configures and calls the pinned author's STCA; it does not replace
the sliding correlation, signed rankings, prefix families or source_as selector.
Evaluation labels never choose the transform, step, family or representative.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from stca_io import read_csv_frame
from stca_runtime import load_stca, environment_receipt
from prepare_hcap import hcap_smiles
from generation_prompt import infer_structure_kind, STRUCTURE_KINDS


def write_json(path, data):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _physical_unit(unit, already_log):
    if already_log and unit.startswith("log10(") and unit.endswith(")"):
        return unit[6:-1]
    return None if already_log else unit


def parse_tiers(value):
    tiers = [float(t) for t in value.split(",")]
    if not tiers or len(set(tiers)) != len(tiers) or any(not 0 < t < 1 for t in tiers):
        raise ValueError("Specify distinct comma-separated tier fractions strictly between 0 and 1.")
    return tuple(tiers)


def prepare_rows(frame, args):
    """Preserve observations and original connection identities. Never merge caps."""
    import numpy as np
    import pandas as pd
    from rdkit import Chem
    required = {args.smiles_column, args.target}
    required.update(c for c in (args.group_column, args.id_column) if c)
    required.update(c.strip() for c in (args.condition_columns+","+args.metadata_columns).split(",") if c.strip())
    if required - set(frame):
        raise ValueError(f"Missing columns: {sorted(required-set(frame))}")
    if any(str(c).startswith("stca_") for c in frame):
        raise ValueError("Reserved stca_ output columns are present; supply the original input table.")
    out = frame.copy()
    out.insert(0, "stca_row_position", range(len(frame)))
    out["stca_record_id"] = (frame[args.id_column].astype(str) if args.id_column else
                            [f"row-{i+1:06d}" for i in range(len(frame))])
    y = pd.to_numeric(frame[args.target], errors="coerce").to_numpy(float)
    original, capped, cap_identity, errors = [], [], [], []
    for s, v in zip(frame[args.smiles_column], y):
        try:
            mol = Chem.MolFromSmiles(s)
            if mol is None:
                raise ValueError("invalid_original_smiles")
            orig = Chem.MolToSmiles(mol, canonical=True)
            cap, _ = hcap_smiles(s)
            c = Chem.MolFromSmiles(cap)
            if c is None:
                raise ValueError("invalid_hcap_smiles")
            if not np.isfinite(v):
                raise ValueError("missing_or_nonfinite_target")
            original.append(orig); capped.append(cap)
            cap_identity.append(Chem.MolToSmiles(c, canonical=True)); errors.append("")
        except (ValueError, RuntimeError) as exc:
            original.append(""); capped.append(""); cap_identity.append(""); errors.append(str(exc))
    out["stca_original_identity"] = original
    out["stca_calculation_smiles_hcap"] = capped
    out["stca_hcap_identity"] = cap_identity
    out["stca_input_error"] = errors
    out["stca_input_valid"] = [not e for e in errors]
    if args.invalid_policy == "error" and any(errors):
        raise ValueError(f"{sum(bool(e) for e in errors)} invalid structures/targets. Use --invalid-policy report to exclude explicitly and retain the exclusion table.")
    return out, y


def overlap_audit(rows, a, b, group_column=None):
    result = {}
    for name in ("stca_original_identity", "stca_hcap_identity", group_column):
        if name is None:
            continue
        result[name] = len(set(rows.loc[a, name]) & set(rows.loc[b, name]))
    return result


def fit_one(X, y, groups, mask, args, transform, min_subset, override_step=None):
    from stca.training import STCA
    from stca.scan import ScanConfig
    from stca.chemistry import MACCS_NAMES, MACCS_SPEC
    from data_readiness import scan_plan
    model_y = y[mask]
    plan = scan_plan(model_y, direction=args.direction, min_subset_size=min_subset,
                     target_points=args.target_points, max_grid_points=args.max_grid_points)
    step = override_step if override_step is not None else plan["scan_step"]
    if step is None or (override_step is None and not plan["fit_numerically_available"]):
        raise ValueError(f"Target cannot be scanned under the declared grid budget: {plan}")
    signed = model_y if args.direction == "high" else -model_y
    grid_n = int(math.ceil((float(signed.max())-float(signed.min()))/step))+3
    if grid_n > args.max_grid_points:
        raise ValueError(f"Explicit/effective scan step needs about {grid_n} grid points, exceeding --max-grid-points. Choose a coarser step explicitly.")
    model_unit = f"log10({args.unit})" if transform == "log10" else args.unit
    observed_kind = infer_structure_kind(groups[mask])
    requested_kind = getattr(args, "structure_kind", None)
    trainer = STCA(direction=args.direction, tiers=args.tiers,
                   scan=ScanConfig(mode="value", step=step, min_subset_size=min_subset,
                                   max_points=args.max_grid_points),
                   max_rank=args.max_rank, family_size=args.family_size,
                   target_name=args.target_name or args.target, target_unit=model_unit,
                   selection="source_as", protocol_id="custom_source_f1_as_v1")
    contract = {
        "property": args.target_name or args.target, "input_target_column": args.target,
        "original_unit": args.unit, "model_unit": model_unit,
        "transform": transform, "already_log": bool(args.already_log),
        "representation": "hcap_maccs167", "group_identity": "canonical_original_structure",
        "structure_kind": requested_kind or observed_kind,
        "input_structure_kind": observed_kind,
        "structure_kind_basis": "user_specified" if requested_kind else "original_smiles_notation",
        "input_smiles_column": args.smiles_column, "id_column": args.id_column,
        "ids_are_features": False, "source_owned_preprocessing": True,
        "analysis_kind": "custom_STCA_adaptive_adapter",
        "scan_policy": args.scan_policy, "min_subset_size": int(min_subset),
        "scan_step": float(step), "source_settings_only": True,
        "minimum_positive_support_heuristic": args.positive_support,
        "conditions_columns": args.condition_columns.split(",") if args.condition_columns else [],
        "observation_aggregation": "none", "outlier_deletion": "none",
        "input_sha256": sha(args.input),
        "data_kind": args.data_kind,
        "source_hcap_identity_hashes": sorted(set(hashlib.sha256(str(x).encode()).hexdigest()
                                                   for x in args._hcap_groups[mask])),
    }
    model = trainer.fit(X.loc[mask].reset_index(drop=True), model_y,
                        feature_names_=MACCS_NAMES, feature_spec=MACCS_SPEC,
                        groups=groups[mask], provenance={"custom_data_contract": contract})
    return model, trainer, plan


def tier_evaluation(model, X, y, groups, mask, args, transform):
    """Preserve real zero metrics, report errors and undefined metrics separately."""
    import numpy as np
    from stca.errors import NoValidRuleError
    from data_readiness import inverse_transform
    result = []
    for q in args.tiers:
        entry = model.artifact["tiers"][format(q, ".12g")]
        cut = entry["train_cutoff"]
        row = {"tier": q, "n": int(mask.sum()), "cutoff_model_space": cut,
               "cutoff_physical": inverse_transform(cut, "log10" if transform == "log10" or args.already_log else "none"),
               "physical_unit": _physical_unit(args.unit, args.already_log), "operator": ">=" if args.direction == "high" else "<=",
               "cutoff_mode": "fixed_train", "metrics": None}
        try:
            model.rule_for(q)
        except NoValidRuleError as exc:
            row.update(status="no_frozen_rule", reason=str(exc)); result.append(row); continue
        if not mask.any():
            row.update(status="not_evaluated", reason="No evaluation rows supplied.")
            result.append(row); continue
        try:
            metrics = model.evaluate(X.loc[mask].reset_index(drop=True), y[mask], tier=q,
                                     groups=groups[mask], cutoff_mode="fixed_train")
        except (ValueError, RuntimeError) as exc:
            row.update(status="evaluation_failed", error_type=type(exc).__name__, reason=str(exc))
            result.append(row); continue
        pos = int(metrics["positive_n"]); neg = int(metrics["n"]-pos)
        selected = int(metrics["selected_n"])
        no_truth_class = pos == 0 or neg == 0
        constant_prediction = selected == 0 or selected == int(metrics["n"])
        row["metric_status"] = ("undefined_single_truth_class" if no_truth_class else
                                "undefined_constant_prediction" if constant_prediction else "computed")
        row["evidence_status"] = ("no_target_positives" if pos == 0 else
                                  "no_target_negatives" if neg == 0 else
                                  "low_support_exploratory" if min(pos, neg) < args.positive_support else
                                  "support_threshold_met_not_external_validation_guarantee")
        row["selection_status"] = "zero_selection" if selected == 0 else "nonzero_selection"
        metrics["upstream_raw_mcc"] = metrics["mcc"]
        metrics["upstream_raw_average_score"] = metrics["average_score"]
        if no_truth_class or constant_prediction:
            metrics["mcc"] = None
            metrics["average_score"] = None
        if pos == 0:
            metrics["recall"] = None
            metrics["f1"] = None
            metrics["enrichment_factor"] = None
        if selected == 0:
            metrics["precision"] = None
            metrics["enrichment_factor"] = None
        row.update(status="evaluated", metrics=metrics)
        result.append(row)
    return result


def run(args):
    import numpy as np
    import pandas as pd
    load_stca(args.source)
    from stca.chemistry import maccs_from_smiles, MACCS_NAMES
    from data_readiness import audit_target, apply_transform, inverse_transform, _record_diagnostics
    output = Path(args.output_dir).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Output directory exists; use a new directory.")
    frame = read_csv_frame(args.input)
    if args.role_column not in frame:
        raise ValueError("Custom fits require explicit data roles. No random-ID or implicit t-SNE split is generated.")
    if args.source_value == args.evaluation_value:
        raise ValueError("Source and evaluation role values must differ.")
    roles = set(frame[args.role_column])
    if roles - {args.source_value, args.evaluation_value}:
        raise ValueError(f"Unrecognized data roles {roles}; declare exactly source/evaluation values or supply a selected table.")
    rows, y_raw = prepare_rows(frame, args)
    valid = rows.stca_input_valid.to_numpy(bool)
    source = (frame[args.role_column] == args.source_value).to_numpy() & valid
    evaluation = (frame[args.role_column] == args.evaluation_value).to_numpy() & valid
    if source.sum() < 4:
        raise ValueError("At least four valid source records are required.")
    if args.group_column and frame.loc[valid, args.group_column].str.strip().eq("").any():
        raise ValueError("Configured group column contains empty group labels.")
    overlap = overlap_audit(rows, source, evaluation, args.group_column)
    if overlap.get("stca_original_identity") or (args.group_column and overlap.get(args.group_column)):
        raise ValueError(f"Source/evaluation identity overlap: {overlap}. Keep related structures in one role.")
    # Use original structure identities for duplicate protection, never random record IDs.
    groups = rows.stca_original_identity.to_numpy()
    args._hcap_groups = rows.stca_hcap_identity.to_numpy()
    X, fp_audit = maccs_from_smiles(rows.stca_calculation_smiles_hcap.where(valid, "").tolist(), errors="report")
    X = pd.DataFrame(np.asarray(X), columns=MACCS_NAMES)
    output.mkdir(parents=True)
    rows.to_csv(output/"prepared_rows.csv", index=False)
    rows.loc[~valid].to_csv(output/"excluded_rows.csv", index=False)
    try:
        transform_mask = source
        inner_train = inner_val = None
        if args.scan_policy == "nested":
            if not args.inner_role_column or args.inner_role_column not in frame:
                raise ValueError("nested scan policy requires an explicit --inner-role-column within source rows.")
            inner_train = source & (frame[args.inner_role_column] == args.inner_train_value).to_numpy()
            inner_val = source & (frame[args.inner_role_column] == args.inner_validation_value).to_numpy()
            if (inner_train.sum() < 4 or not inner_val.any() or
                    not np.array_equal(inner_train | inner_val, source)):
                raise ValueError("Inner roles must partition all source rows with >=4 train and >=1 validation rows.")
            inner_overlap = overlap_audit(rows, inner_train, inner_val, args.group_column)
            if inner_overlap["stca_original_identity"] or (args.group_column and inner_overlap.get(args.group_column)):
                raise ValueError(f"Inner train/validation identity overlap: {inner_overlap}")
            transform_mask = inner_train
        report = audit_target(y_raw[transform_mask], direction=args.direction, tiers=args.tiers,
                              unit=args.unit, transform=args.transform, already_log=args.already_log,
                              min_subset_size=args.min_subset_size, target_points=args.target_points,
                              max_grid_points=args.max_grid_points, positive_support=args.positive_support)
        transform = report["transform"]
        y = np.full(len(frame), np.nan)
        y[valid] = apply_transform(y_raw[valid], transform)
        rows["stca_model_target"] = y
        rows.to_csv(output/"prepared_rows.csv", index=False)
        nested = {"policy": args.scan_policy, "evaluation_labels_used": False,
                  "transform_fit_role": "inner_train" if inner_train is not None else "source",
                  "candidates": [], "selection_margin": args.selection_margin}
        min_subset = args.min_subset_size
        if args.scan_policy == "nested":
            minimum = max(10, math.ceil(0.5*min(args.tiers)*inner_train.sum()))
            candidates = list(dict.fromkeys([1, minimum]))
            scores = {}
            for ms in candidates:
                record = {"min_subset_size": ms, "status": "not_fitted", "score": None}
                try:
                    model, _, _ = fit_one(X, y, groups, inner_train, args, transform, ms, args.scan_step)
                    ev = tier_evaluation(model, X, y, groups, inner_val, args, transform)
                    # No-rule is unavailable, never a synthetic MCC=0; compare common valid tiers only.
                    record.update(status="fitted", tier_evaluations=ev)
                    scores[ms] = {r["tier"]: r["metrics"]["mcc"] for r in ev
                                  if r["metrics"] is not None and r["metrics"]["mcc"] is not None}
                except (ValueError, RuntimeError) as exc:
                    record.update(status="fit_failed", error_type=type(exc).__name__, reason=str(exc))
                    scores[ms] = {}
                nested["candidates"].append(record)
            common = set.intersection(*(set(s) for s in scores.values())) if scores else set()
            nested["common_valid_tiers"] = sorted(common)
            nested["selected_fraction_policy"] = "min_subset_1_prespecified_default"
            min_subset = 1
            if common:
                means = {ms: float(np.mean([s[q] for q in common])) for ms, s in scores.items()}
                for r in nested["candidates"]: r["score"] = means[r["min_subset_size"]]
                if len(candidates) == 2 and means[minimum]-means[1] >= args.selection_margin:
                    min_subset = max(10, math.ceil(0.5*min(args.tiers)*source.sum()))
                    nested["selected_fraction_policy"] = "half_strictest_tier_count"
            else:
                nested["fallback_reason"] = "No common defined MCC tiers; preserve predeclared minimum=1, no evaluation-driven fallback."
            selected_inner = minimum if nested["selected_fraction_policy"] == "half_strictest_tier_count" else 1
            nested["selected_inner_min_subset_size"] = selected_inner
            nested["selected_candidate"] = next(
                (r for r in nested["candidates"] if r["min_subset_size"] == selected_inner), None)
        model, trainer, scan = fit_one(X, y, groups, source, args, transform, min_subset, args.scan_step)
        model.save(output/"model.json")
        trainer.export_diagnostics(output/"diagnostics")
        readiness = audit_target(y_raw[source], direction=args.direction, tiers=args.tiers,
                                 unit=args.unit, transform=transform, already_log=args.already_log,
                                 y_eval=y_raw[evaluation] if evaluation.any() else None,
                                 min_subset_size=min_subset, target_points=args.target_points,
                                 max_grid_points=args.max_grid_points, positive_support=args.positive_support)
        readiness["identity_overlap"] = overlap
        readiness["diagnostics"] = _record_diagnostics(
            frame.loc[valid].to_dict("records"), source_mask=source[valid], target=args.target,
            smiles_column=args.smiles_column, id_column=args.id_column,
            metadata_columns=[c.strip() for c in args.metadata_columns.split(",") if c.strip()],
            condition_columns=[c.strip() for c in args.condition_columns.split(",") if c.strip()])
        cap_groups = rows.loc[valid].groupby("stca_hcap_identity")["stca_original_identity"].nunique()
        readiness["hcap_collision_group_count"] = int((cap_groups > 1).sum())
        readiness["hcap_collisions_never_aggregated"] = True
        readiness["hcap_collisions_block_independence_claim"] = bool(overlap.get("stca_hcap_identity"))
        readiness["group_identity_kind"] = "canonical_original_structure"
        write_json(output/"source_audit.json", readiness)
        write_json(output/"source_settings.json", {"preprocessing_fit_report": report, "scan": scan,
                   "actual_scan_step": model.artifact["training_config"]["scan"]["step"],
                   "min_subset_size": min_subset, "selection": nested,
                   "evaluation_labels_used_for_settings": False,
                   "heuristic_status": "trial_informed_custom_adapter_not_published_STCA_default"})
        evaluations = tier_evaluation(model, X, y, groups, evaluation, args, transform)
        if overlap.get("stca_hcap_identity"):
            for r in evaluations:
                r["representation_overlap"] = True
                r["independence_claim"] = "not_verified_due_to_Hcap_collision; no automatic merge or deletion"
        write_json(output/"evaluation_metrics.json", {"schema": "stca-custom-evaluation-v1", "tiers": evaluations,
                   "evaluation_labels_used_for_fit": False,
                   "support_threshold_is_heuristic": True})
        table = []
        for q in args.tiers:
            cutoff = model.artifact["tiers"][format(q, ".12g")]["train_cutoff"]
            table.append({"property": args.target_name or args.target, "tier": q,
                          "direction": args.direction, "cutoff_model_space": cutoff,
                          "cutoff_physical": inverse_transform(cutoff, "log10" if transform == "log10" or args.already_log else "none"),
                          "physical_unit": _physical_unit(args.unit, args.already_log), "model_unit": model.artifact["target_unit"],
                          "transform": transform,
                          "source_positives": int(((y[source] >= cutoff) if args.direction == "high" else (y[source] <= cutoff)).sum()),
                          "evaluation_positives": int(((y[evaluation] >= cutoff) if args.direction == "high" else (y[evaluation] <= cutoff)).sum())})
        pd.DataFrame(table).to_csv(output/"tier_cutoffs.csv", index=False)
        evaluation_failed = any(r["status"] == "evaluation_failed" for r in evaluations)
        run_status = "partial_failure" if evaluation_failed else "completed"
        write_json(output/"run_manifest.json", {"status": run_status, "schema": "stca-custom-fit-v1",
                   "integration_version": "0.1.0", "input_sha256": sha(args.input),
                   "model_sha256": sha(output/"model.json"), "environment": environment_receipt(args.source),
                   "analysis_kind": "custom_fit_not_paper_reproduction", "source_n": int(source.sum()),
                   "evaluation_n": int(evaluation.sum()), "excluded_n": int((~valid).sum()),
                   "evaluation_labels_used_for_fit": False, "target": args.target_name or args.target,
                   "unit": args.unit, "transform": transform, "conditions_columns": args.condition_columns,
                   "support_threshold_is_a_reporting_heuristic": True})
        print(json.dumps({"output_directory": str(output), "model": str(output/"model.json"),
                          "status": run_status,
                          "source_n": int(source.sum()), "evaluation_n": int(evaluation.sum()),
                          "transform": transform, "min_subset_size": min_subset}))
        return 2 if evaluation_failed else 0
    except Exception as exc:
        # Record the exact failure, then propagate; never convert to a zero score.
        write_json(output/"failure.json", {"status": "failed", "error_type": type(exc).__name__,
                   "reason": str(exc), "metrics": None})
        raise


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", help="Clean pinned author source checkout")
    for name in ("input", "target", "unit", "direction", "tiers", "role-column", "output-dir"):
        p.add_argument("--"+name, required=True)
    p.add_argument("--target-name")
    p.add_argument("--smiles-column", default="SMILES")
    p.add_argument("--structure-kind", choices=STRUCTURE_KINDS,
                   help="Generation output notation; otherwise infer it from valid source SMILES.")
    p.add_argument("--id-column")
    p.add_argument("--group-column")
    p.add_argument("--source-value", default="source")
    p.add_argument("--evaluation-value", default="holdout")
    p.add_argument("--inner-role-column")
    p.add_argument("--inner-train-value", default="train")
    p.add_argument("--inner-validation-value", default="validation")
    p.add_argument("--scan-policy", choices=("fixed", "nested"), default="fixed")
    p.add_argument("--transform", choices=("auto", "none", "log10"), default="none")
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
    p.add_argument("--invalid-policy", choices=("error", "report"), default="error")
    a = p.parse_args(argv)
    try:
        a.tiers = parse_tiers(a.tiers)
        if a.direction not in ("high", "low"):
            raise ValueError("direction must be high or low")
        if a.scan_step is not None and (not math.isfinite(a.scan_step) or a.scan_step <= 0):
            raise ValueError("scan-step must be positive and finite")
        if not (1 <= a.min_subset_size and a.positive_support >= 1 and a.selection_margin >= 0):
            raise ValueError("Invalid support or selection settings")
        return run(a)
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"stca-custom: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
