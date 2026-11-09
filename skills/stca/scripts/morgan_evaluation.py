#!/usr/bin/env python3
"""Learn source-only polymer rules and evaluate a strict Morgan-distance holdout.

Raw structures define roles before any target-driven preparation. All learned
cleaning, transforms, scan settings, rule choices and method recommendations use
source data only. Frozen source models screen every original row; only valid
labeled holdout rows form the independent distance-extrapolation evaluation.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from auto_screen import read_auto_frame, protected_components
from inrange_evaluation import (parse_tiers, tier_key, write_json, scores,
                                available_column, column_list, json_ready)
from morgan_split import split_distance_holdout

EVIDENCE = "independent_strict_ecfp4_tanimoto_distance_holdout"


def resolve_column(column, frame, audit):
    if column is None or column in frame:
        return column
    if column.strip() in frame:
        return column.strip()
    matches = [entry["normalized_header"] for entry in audit["column_alias_map"] if entry["original_header"] == column]
    return matches[0] if len(matches) == 1 else column


def structural_split(frame, smiles_column, *, group_column=None, threshold=.5, fraction=.2, min_source=10):
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator
    from prepare_hcap import hcap_smiles
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    valid, original, capped, fingerprints, excluded = [], [], [], [], []
    for position, smiles in enumerate(frame[smiles_column].tolist()):
        try:
            cap, _ = hcap_smiles(smiles)
            molecule = Chem.MolFromSmiles(smiles)
            calculation = Chem.MolFromSmiles(cap)
            original.append(Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True))
            capped.append(Chem.MolToSmiles(calculation, canonical=True, isomericSmiles=True))
            fingerprints.append(generator.GetFingerprint(calculation))
            valid.append(position)
        except (ValueError, RuntimeError, TypeError) as exc:
            excluded.append({"input_row_position": position, "role": "excluded_structure", "reason": str(exc)})
    explicit = frame.iloc[valid][group_column].astype(str).tolist() if group_column else None
    if explicit is not None and any(not value.strip() for value in explicit):
        raise ValueError("Explicit group column has blank values; supply valid grouping values.")
    groups = protected_components(original, capped, explicit)
    result = split_distance_holdout(fingerprints, groups, threshold=threshold, holdout_fraction=fraction,
                                   min_source=min_source, identities=original)
    membership = pd.DataFrame({"input_row_position": valid, "canonical_original": original,
                               "canonical_hcap": capped, "protected_group": groups, "role": result["roles"]})
    membership["nearest_source_distance"] = np.nan
    membership.loc[result["holdout"], "nearest_source_distance"] = result["holdout_nearest_source_distance"]
    if excluded:
        membership = pd.concat([membership, pd.DataFrame(excluded)], ignore_index=True).sort_values("input_row_position").reset_index(drop=True)
    result["membership"] = membership
    result["valid_input_positions"] = np.asarray(valid, dtype=int)
    result["audit"]["excluded_structure_n"] = len(excluded)
    result["audit"]["original_input_n"] = len(frame)
    return result


def heldout_targets(frame, contract, target_column):
    """Apply only the SOURCE-frozen unit conversion to untouched holdout labels."""
    values = pd.to_numeric(frame[target_column], errors="coerce").to_numpy(dtype=float)
    conversion = contract.get("unit_conversion") or {}
    if isinstance(conversion, dict):
        multiplier = conversion.get("factor", conversion.get("scale", conversion.get("multiplier", 1.0)))
        offset = conversion.get("offset", 0.0)
    elif isinstance(conversion, (list, tuple)) and len(conversion) == 2:
        multiplier, offset = conversion
    else:
        multiplier, offset = 1.0, 0.0
    if contract.get("uploaded_target_already_logarithmic"):
        with np.errstate(over="ignore", invalid="ignore"):
            values = np.power(10.0, values)
    values = values * float(multiplier) + float(offset)
    return values


def prepared_source_distances(output, source_manifest, q, membership):
    """Recheck every heldout row against the actual tier's retained fit rows."""
    from rdkit import Chem, DataStructs
    from rdkit.Chem import rdFingerprintGenerator
    info = source_manifest["per_tier_preparation"][tier_key(q)]
    preparation = output / "source_fit" / info["preparation_directory"] / "cleaned.csv"
    prepared = pd.read_csv(preparation, dtype=str, keep_default_na=False)
    capped = prepared["stca_calculation_smiles_hcap"].tolist()
    allowed = set(membership.loc[membership.role == "source", "canonical_hcap"])
    if any(value not in allowed for value in capped):
        raise RuntimeError("Prepared fit structure is not a member of the protected source partition.")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    training = [generator.GetFingerprint(Chem.MolFromSmiles(value)) for value in capped]
    records = []
    for _, row in membership.loc[membership.role == "holdout"].iterrows():
        fingerprint = generator.GetFingerprint(Chem.MolFromSmiles(row.canonical_hcap))
        distance = 1 - max(DataStructs.BulkTanimotoSimilarity(fingerprint, training)) if training else None
        records.append({"input_row_position": int(row.input_row_position), "tier": q,
                        "nearest_actual_prepared_source_distance": distance})
    return records


def run(args):
    from stca_runtime import load_stca
    from stca_tools import export_rules, screen_candidates
    import inrange_evaluation
    stca = load_stca(args.source)
    output = Path(args.output_dir).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"Output directory already exists: {output}")
    output.mkdir(parents=True)
    raw, input_audit = read_auto_frame(args.input)
    smiles = resolve_column(args.smiles_column, raw, input_audit)
    target = resolve_column(args.target, raw, input_audit)
    group = resolve_column(args.group_column, raw, input_audit)
    for column in (smiles, target, group):
        if column is not None and column not in raw:
            raise ValueError(f"Missing input column: {column!r}")
    raw.to_csv(output / "original_input.csv", index=False)
    write_json(output / "input_format.json", input_audit)
    split = structural_split(raw, smiles, group_column=group, threshold=args.distance_threshold,
                             fraction=args.holdout_fraction, min_source=args.min_source)
    membership, split_audit = split["membership"], split["audit"]
    membership.to_csv(output / "split_membership.csv", index=False)
    write_json(output / "split_audit.json", split_audit)
    roles = membership.set_index("input_row_position")["role"].reindex(range(len(raw))).to_numpy()
    for role in ("source", "holdout", "buffer", "excluded_structure"):
        raw.loc[roles == role].to_csv(output / f"{role}_input.csv", index=False)
    if split_audit["status"] != "available":
        write_json(output / "failure.json", {"status": "unavailable", "reason": split_audit["status"],
            "source_n": split_audit["source_n"], "holdout_n": split_audit["holdout_n"],
            "buffer_n": split_audit["buffer_n"], "metrics": None, "no_fallback_split": True})
        return 2
    inner_selection = {"scope": "source_only_strict_morgan_validation", "holdout_labels_used": False,
                       "distance_threshold": args.distance_threshold, "status": "not_requested_internal_leaf", "tiers": {}}
    if not getattr(args, "_internal_no_nested", False):
        inner_args = copy.copy(args)
        inner_args.input = str(output / "source_input.csv")
        inner_args.output_dir = str(output / "source_inner_morgan")
        inner_args.library_dir = str(output / "source_inner_morgan_rules")
        inner_args._internal_no_nested = True
        inner_args.smiles_column, inner_args.target = smiles, target
        inner_args.group_column = group
        try:
            with (output / "source_inner_morgan.log").open("x", encoding="utf-8") as log, redirect_stdout(log):
                inner_code = run(inner_args)
            inner_metrics_path = output / "source_inner_morgan" / "holdout_metrics.json"
            if inner_code or not inner_metrics_path.exists():
                inner_selection.update(status="unavailable_strict_source_inner_split_or_fit", default_method="STCA")
            else:
                inner_metrics = json.loads(inner_metrics_path.read_text())
                for q in parse_tiers(args.tiers):
                    comparison = {record["method"]: record for record in inner_metrics["results"] if float(record["tier"]) == q}
                    a, b = comparison["STCA"].get("AS"), comparison["WRAcc"].get("AS")
                    if a is not None and b is not None:
                        chosen = "WRAcc" if b > a + .02 else "STCA"
                        reason = "WRAcc_source_inner_Morgan_average_score_exceeds_STCA_by_more_than_0.02" if chosen == "WRAcc" else "STCA_retained_source_inner_Morgan_WRAcc_advantage_not_more_than_0.02"
                        state = "selected_by_source_inner_strict_morgan_validation"
                    else:
                        chosen, reason, state = "STCA", "strict_source_inner_comparison_unavailable_declared_STCA_default", "unavailable_comparison_declared_default"
                    inner_selection["tiers"][tier_key(q)] = {"recommended_method": chosen, "reason": reason, "status": state,
                        "STCA": comparison["STCA"], "WRAcc": comparison["WRAcc"]}
                inner_selection.update(status="computed", metrics="source_inner_morgan/holdout_metrics.json")
        except PermissionError:
            # A platform denial is an execution failure, not evidence that a
            # scientific comparison is unavailable. Preserve partial outputs.
            raise
        except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
            inner_selection.update(status="unavailable_strict_source_inner_split_or_fit", default_method="STCA", reason=f"{type(exc).__name__}: {exc}")
    write_json(output / "source_inner_selection.json", inner_selection)
    train_args = copy.copy(args)
    train_args.input = str(output / "source_input.csv")
    train_args.output_dir = str(output / "source_fit")
    train_args.smiles_column, train_args.target = smiles, target
    train_args.id_column = resolve_column(args.id_column, raw, input_audit)
    # Only the split source reaches any target-dependent preparation. The source
    # runner's internal CV is explicitly a tuning/comparison aid, not outer evidence.
    with (output / "source_learning.log").open("x", encoding="utf-8") as log, redirect_stdout(log):
        code = inrange_evaluation.run(train_args)
    if code:
        raise RuntimeError(f"Source-only learner returned {code}; see source_learning.log")
    source_fit = output / "source_fit"
    source_summary = json.loads((source_fit / "screening_summary.json").read_text())
    source_manifest = json.loads((source_fit / "run_manifest.json").read_text())
    # Keep separate source evidence rather than presenting it as outer scores.
    write_json(output / "source_internal_selection.json", {
        "scope": "source_only_conditional_grouped_CV_diagnostic", "is_extrapolation_evidence": False,
        "holdout_labels_used": False, "used_for_main_method_recommendation": False,
        "source_summary": "source_fit/screening_summary.json", "tiers": source_summary["tiers"]})
    tiers = parse_tiers(args.tiers)
    actual_distances = []
    for q in tiers:
        actual_distances.extend(prepared_source_distances(output, source_manifest, q, membership))
    if any(record["nearest_actual_prepared_source_distance"] is not None and
           record["nearest_actual_prepared_source_distance"] + 1e-12 < args.distance_threshold for record in actual_distances):
        raise RuntimeError("Actual prepared training data violate the declared Morgan distance holdout.")
    pd.DataFrame(actual_distances).to_csv(output / "holdout_actual_training_distances.csv", index=False)
    source_tiers = {float(item["fraction"]): item for item in source_summary["tiers"]}
    for q, item in source_tiers.items():
        chosen = inner_selection["tiers"].get(tier_key(q), {}).get("recommended_method", "STCA")
        reason = inner_selection["tiers"].get(tier_key(q), {}).get("reason", "strict_source_inner_comparison_unavailable_declared_STCA_default")
        other = "WRAcc" if chosen == "STCA" else "STCA"
        if not item["methods"][chosen].get("rule"):
            if item["methods"][other].get("rule"):
                chosen, other = other, chosen
                reason = "only_method_with_valid_source_rule_no_comparative_superiority_claim"
            else:
                chosen, other, reason = None, None, "no_valid_source_rule"
        item.update(recommended_method=chosen, alternative_method=other, recommendation_reason=reason)
    screen_aliases, occupied = {}, set(raw.columns)
    for column in raw:
        if column.startswith("stca_"):
            alias = available_column(occupied, "archive_input_" + column)
            screen_aliases[column] = alias
            occupied.add(alias)
    screen_raw = raw.rename(columns=screen_aliases)
    screen_path = output / "screening_input.csv"
    screen_raw.to_csv(screen_path, index=False)
    all_rows = raw.copy()
    role_column = available_column(all_rows.columns, "stca_morgan_role")
    all_rows[role_column] = roles
    delivered, metrics_rows = [], []
    for method in ("STCA", "WRAcc"):
        method_dir = output / method.lower()
        method_dir.mkdir()
        model_path = method_dir / "model.json"
        shutil.copy2(source_fit / method.lower() / "model.json", model_path)
        artifact = json.loads(model_path.read_text())
        contract = artifact.get("custom_data_contract", artifact.get("metadata", {}).get("custom_data_contract", {}))
        if not contract:
            # Author-compatible models store the contract inside provenance.
            contract = artifact.get("provenance", {}).get("custom_data_contract", {})
        if not contract:
            # Existing adapter contract uses a top-level custom-data object.
            contract = artifact.get("custom_data", {})
        target_values = heldout_targets(raw, contract, target)
        for q in tiers:
            name = tier_key(q)
            bundle = method_dir / f"tier_{name}"
            with (output / "screening.log").open("a", encoding="utf-8") as log, redirect_stdout(log):
                export_rules(argparse.Namespace(profile=None, model=str(model_path), protocol=None, tier=q,
                    count=args.count, preferences=args.preferences, output_dir=str(bundle), source=args.source), stca)
                screen_candidates(argparse.Namespace(profile=None, model=str(model_path), protocol=None, tier=q,
                    input=str(screen_path), id_column=None, smiles_column=screen_aliases.get(smiles, smiles),
                    hcap_output_column="stca_calculation_smiles_hcap", input_is_hcap=False,
                    label=f"{args.target_name or target} {method} Morgan source-frozen rule", property=args.target_name or target,
                    direction=args.direction, source_property=None, transfer_role=None, allow_transfer=False,
                    output_dir=str(bundle / "screening"), source=args.source), stca)
            screened = pd.read_csv(bundle / "screening" / "results.csv", dtype=str, keep_default_na=False)
            if len(screened) != len(raw) or any(screened[column].tolist() != screen_raw[column].tolist() for column in screen_raw):
                raise RuntimeError("Original input rows or values changed during screening.")
            results = raw.copy()
            for column in screened:
                if column not in screen_raw:
                    results[available_column(results.columns, column)] = screened[column].to_numpy()
            results[available_column(results.columns, "stca_morgan_role")] = roles
            selected = screened["stca_joint__selected"].str.lower().eq("true").to_numpy()
            known = screened["stca_joint__selected"].str.lower().isin(("true", "false")).to_numpy()
            results.to_csv(bundle / "screening" / "results.csv", index=False)
            results.loc[selected].to_csv(bundle / "selected.csv", index=False)
            held_mask = roles == "holdout"
            results.loc[held_mask].to_csv(bundle / "holdout_results.csv", index=False)
            cutoff_value = source_tiers[q]["physical_cutoff"]
            valid_target = np.isfinite(target_values)
            # Source-frozen conversion/transform only; no holdout aggregation,
            # influence filtering, plausibility learning or threshold refitting.
            evaluated = held_mask & valid_target & known
            unknown = int((held_mask & valid_target & ~known).sum())
            truth = target_values >= cutoff_value if args.direction == "high" else target_values <= cutoff_value
            metric = scores(truth[evaluated], selected[evaluated]) if not unknown else {
                "status": "unavailable_missing_rule", **{key: None for key in ("precision", "recall", "f1", "mcc", "AS")}}
            record = {"method": method, "tier": q, "physical_cutoff": cutoff_value,
                "operator": ">=" if args.direction == "high" else "<=", "unit": source_summary["unit"],
                "evaluation_scope": EVIDENCE, "distance_threshold": args.distance_threshold,
                "source_n_before_target_preparation": int((roles == "source").sum()),
                "source_prepared_n": source_tiers[q]["preparation"]["prepared_measurement_n"],
                "holdout_original_n": int(held_mask.sum()), "holdout_valid_target_n": int((held_mask & valid_target).sum()),
                "holdout_evaluated_n": int(evaluated.sum()), "holdout_unknown_prediction_n": unknown,
                "holdout_missing_or_nonfinite_target_n": int((held_mask & ~valid_target).sum()),
                "original_input_n": len(raw), "original_selected_n": int(selected.sum()),
                "original_unknown_n": int((~known).sum()), "rule": source_tiers[q]["methods"][method]["rule"],
                "recommended_method": source_tiers[q]["recommended_method"],
                "recommendation_scope": "source_inner_strict_morgan_validation_before_outer_holdout", **metric}
            metrics_rows.append(record)
            method_item = {**source_tiers[q]["methods"][method],
                "selected_n": int(selected.sum()), "not_selected_n": int((known & ~selected).sum()),
                "unknown_n": int((~known).sum()), "original_input_n": len(raw),
                "holdout": record, "holdout_metrics": record, "cv_scope": "source_only_internal_conditional_grouped_CV_diagnostic_not_method_selection",
                "results_with_failed_conditions": f"{method.lower()}/tier_{name}/screening/results.csv",
                "selected_rows": f"{method.lower()}/tier_{name}/selected.csv",
                "constraints": f"{method.lower()}/tier_{name}/constraints.json"}
            delivered.append((q, method, method_item))
            all_rows[available_column(all_rows.columns, f"morgan_{method.lower()}_{name}__selected")] = screened["stca_joint__selected"].to_numpy()
            all_rows[available_column(all_rows.columns, f"morgan_{method.lower()}_{name}__status")] = screened["stca_joint__status"].to_numpy()
    all_rows.to_csv(output / "all_rows_screening.csv", index=False)
    pd.DataFrame(metrics_rows).to_csv(output / "morgan_holdout_evaluation.csv", index=False)
    summary = {"schema": "stca-morgan-screening-summary-v1", "property": source_summary["property"],
        "unit": source_summary["unit"], "direction": args.direction, "original_input_rows": len(raw),
        "evaluation_scope": EVIDENCE, "split": split_audit,
        "method_score": "(MCC + Precision + F1) / 3", "method_recommendation_scope": "source_inner_strict_morgan_validation_before_outer_holdout",
        "holdout_used_for_method_or_tier_selection": False, "model_fit_scope": "source_only_prepared_data",
        "source_internal_evidence": "source_internal_selection.json", "source_inner_selection": "source_inner_selection.json",
        "source_run_dir": "source_fit", "source_inner_run_dir": "source_inner_morgan", "tiers": [],
        "status": source_summary["status"], "storage_warnings": source_summary.get("storage_warnings", []),
        "all_available_rule_sets_saved_and_exported": source_summary.get("all_available_rule_sets_saved_and_exported"),
        "next_action": "continue_conversation"}
    for q in tiers:
        item = copy.deepcopy(source_tiers[q])
        item["cutoff_scope"] = "source_only_frozen_physical_cutoff"
        item["methods"] = {method: record for tier, method, record in delivered if tier == q}
        summary["tiers"].append(item)
    write_json(output / "screening_summary.json", summary)
    write_json(output / "holdout_metrics.json", {"schema": "stca-morgan-holdout-metrics-v1", "split": split_audit, "results": metrics_rows})
    write_json(output / "run_manifest.json", {"schema": "stca-morgan-workflow-v1", "entrypoint": "morgan_evaluation.py",
        "status": summary["status"], "evaluation_scope": EVIDENCE, "input": str(Path(args.input).resolve()),
        "input_sha256": input_audit["input_sha256"], "original_input_row_n": len(raw), "split": split_audit,
        "learning_input": "source_input.csv", "learning_input_sha256": hashlib.sha256((output / "source_input.csv").read_bytes()).hexdigest(),
        "source_learning_manifest": "source_fit/run_manifest.json", "methods": {method: {"model": f"{method.lower()}/model.json"} for method in ("STCA", "WRAcc")},
        "source_run_dir": "source_fit", "source_inner_run_dir": "source_inner_morgan", "source_inner_selection": "source_inner_selection.json",
        "learning_settings": {"target_column": target, "smiles_column": smiles,
            "direction": args.direction, "tiers": tiers, "distance_threshold": args.distance_threshold,
            "holdout_fraction": args.holdout_fraction},
        "all_target_dependent_preparation_fit_scope": "source_only", "model_fit_scope": "source_only_prepared_data",
        "holdout_labels_used_for_fit_or_selection": False, "buffer_used_for_fit_or_selection": False,
        "original_star_smiles_preserved": True, "source_internal_CV_is_extrapolation_evidence": False,
        "source_internal_CV_conditioning": source_manifest["evidence_status"], "tiers": tiers})
    for file in ("saved_rule_receipts.json", "saved_stca_rules.zip", "saved_wracc_rules.zip"):
        if (source_fit / file).exists():
            shutil.copy2(source_fit / file, output / file)
    generation = json.loads((source_fit / "rules_for_generation.json").read_text())
    generation.update(evidence_status=EVIDENCE,
                      method_recommendation_scope="source_inner_strict_morgan_validation_before_outer_holdout")
    for item in generation["tiers"]:
        chosen = source_tiers[float(item["tier"])]
        item.update(primary=chosen["recommended_method"], alternative=chosen["alternative_method"],
                    recommendation_reason=chosen["recommendation_reason"])
        for method, entry in item["methods"].items():
            base = output / method.lower() / f"tier_{tier_key(item['tier'])}"
            entry["model"] = str(output / method.lower() / "model.json")
            entry["prompts"] = {language: str(base / f"prompt.{language}.md") if (base / f"prompt.{language}.md").exists() else None for language in ("en", "zh-CN")}
            entry["holdout_metrics"] = next(record for record in metrics_rows if record["method"] == method and record["tier"] == float(item["tier"]))
            if "CV" in entry:
                entry["source_internal_CV_diagnostic"] = entry.pop("CV")
    write_json(output / "rules_for_generation.json", generation)
    lines = [f"# {summary['property']}：Morgan 距离外推与筛选", "",
        f"ECFP4（Morgan radius=2，2048 位）最近邻 Tanimoto 距离 ≥ {args.distance_threshold:g}；source {split_audit['source_n']} 条，独立 holdout {split_audit['holdout_n']} 条，缓冲区 {split_audit['buffer_n']} 条。",
        "所有数据变换、自动步长、支持量和规则学习仅使用 source。主推由 source 内另一层严格 Morgan 距离验证确定，之后才评价外层 holdout；源内随机分组交叉验证只保留为诊断。", "",
        "| 档位 | 冻结物理阈值 | 方法 | 外推精确率 | 外推召回率 | 外推 F1 | 外推 MCC | 全表入选 |", "|---|---|---|---:|---:|---:|---:|---:|"]
    number = lambda v: "不可评价" if v is None else f"{v:.4f}"
    for record in metrics_rows:
        lines.append(f"| {'Top' if args.direction == 'high' else 'Bottom'} {record['tier']*100:g}% | {record['operator']} {record['physical_cutoff']:.10g} {record['unit']} | {record['method']} | {number(record.get('precision'))} | {number(record.get('recall'))} | {number(record.get('f1'))} | {number(record.get('mcc'))} | {record['original_selected_n']} |")
    lines.extend(["", "缓冲区保留并回筛，但不用于学习或外推评分。缺少性质的 holdout 行保留筛选结果，无法计入有标签评价。", "原始带星号重复单元 SMILES 保留在全部结果与入选表；H-cap 只用于计算。", ""])
    (output / "recommendation.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": summary["status"], "output_directory": str(output), "evaluation_scope": EVIDENCE,
                      "split": split_audit, "screening_summary": str(output / "screening_summary.json")}, ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "target", "output-dir"):
        parser.add_argument("--" + name, required=True)
    for name in ("target-name", "property", "unit", "id-column", "group-column", "source", "structure-kind"):
        parser.add_argument("--" + name)
    parser.add_argument("--smiles-column", default="SMILES")
    parser.add_argument("--direction", choices=("high", "low"), default="high")
    parser.add_argument("--tiers", nargs="+", default=[".10", ".20", ".30"])
    parser.add_argument("--metadata-columns", "--text-columns", nargs="*", default=[])
    parser.add_argument("--condition-columns", nargs="*", default=[])
    parser.add_argument("--already-log", action="store_true")
    parser.add_argument("--skip-influence", action="store_true")
    parser.add_argument("--library-dir", default=str(Path.cwd() / "stca-rules"))
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--nested", action="store_true")
    parser.add_argument("--with-rf", action="store_true")
    parser.add_argument("--wracc-max-literals", default="auto")
    parser.add_argument("--wracc-length-folds", type=int, default=3)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--preferences", default="")
    parser.add_argument("--distance-threshold", type=float, default=.5)
    parser.add_argument("--holdout-fraction", type=float, default=.2)
    parser.add_argument("--min-source", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print(f"morgan-evaluation: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
