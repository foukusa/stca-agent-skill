#!/usr/bin/env python3
"""Reconcile completed Morgan delivery metadata without changing any model.

This also upgrades runs started before the final documentation-path polish.
It never fits a model, changes source/holdout membership or chooses a method.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/stca/scripts"))
from morgan_evaluation import prepared_source_distances, EVIDENCE
from inrange_evaluation import tier_key


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def finalize(output):
    output = Path(output).resolve()
    manifest = json.loads((output / "run_manifest.json").read_text())
    if manifest.get("entrypoint") != "morgan_evaluation.py":
        return {"output": str(output), "status": "skipped_not_morgan"}
    before = {method: hashlib.sha256((output / method.lower() / "model.json").read_bytes()).hexdigest() for method in ("STCA", "WRAcc")}
    recommendation = output / "recommendation.md"
    if recommendation.exists():
        text = recommendation.read_text().replace("主推在查看 holdout 前确定；源内交叉验证仅用于内部选择。", "主推由 source 内部 Morgan 距离验证确定；随机分组交叉验证仅作 source 内诊断。")
        recommendation.write_text(text, encoding="utf-8")
    source_manifest = json.loads((output / "source_fit/run_manifest.json").read_text())
    summary = json.loads((output / "screening_summary.json").read_text())
    membership = pd.read_csv(output / "split_membership.csv", dtype={"canonical_hcap": str, "role": str})
    distances = []
    for item in summary["tiers"]:
        distances.extend(prepared_source_distances(output, source_manifest, item["fraction"], membership))
    threshold = manifest["split"]["distance_threshold"]
    if any(record["nearest_actual_prepared_source_distance"] is not None and record["nearest_actual_prepared_source_distance"] + 1e-12 < threshold for record in distances):
        raise RuntimeError("Actual prepared-source distance fails the declared threshold; no metadata was finalized.")
    pd.DataFrame(distances).to_csv(output / "holdout_actual_training_distances.csv", index=False)
    generation = json.loads((output / "source_fit/rules_for_generation.json").read_text())
    generation.update(evidence_status=EVIDENCE, method_recommendation_scope="source_inner_strict_morgan_validation_before_outer_holdout")
    root_tiers = {float(item["fraction"]): item for item in summary["tiers"]}
    for item in generation["tiers"]:
        q = float(item["tier"])
        chosen = root_tiers[q]
        item.update(primary=chosen["recommended_method"], alternative=chosen["alternative_method"],
                    recommendation_reason=chosen["recommendation_reason"])
        for method, entry in item["methods"].items():
            base = output / method.lower() / f"tier_{tier_key(q)}"
            entry["model"] = str(output / method.lower() / "model.json")
            entry["prompts"] = {language: str(base / f"prompt.{language}.md") if (base / f"prompt.{language}.md").exists() else None for language in ("en", "zh-CN")}
            entry["holdout_metrics"] = chosen["methods"][method].get("holdout_metrics", chosen["methods"][method]["holdout"])
            if "CV" in entry:
                entry["source_internal_CV_diagnostic"] = entry.pop("CV")
    save(output / "rules_for_generation.json", generation)
    diagnostic = json.loads((output / "source_internal_selection.json").read_text())
    diagnostic.update(scope="source_only_conditional_grouped_CV_diagnostic", is_extrapolation_evidence=False,
                      used_for_main_method_recommendation=False)
    save(output / "source_internal_selection.json", diagnostic)
    for item in summary["tiers"]:
        for method, entry in item["methods"].items():
            entry["cv_scope"] = "source_only_internal_conditional_grouped_CV_diagnostic_not_method_selection"
    save(output / "screening_summary.json", summary)
    after = {method: hashlib.sha256((output / method.lower() / "model.json").read_bytes()).hexdigest() for method in ("STCA", "WRAcc")}
    if before != after:
        raise RuntimeError("Unexpected model change while reconciling metadata.")
    report = {"output": str(output), "status": "verified", "models_unchanged": True,
              "model_sha256": after, "actual_training_distance_rows": len(distances),
              "generation_recommendations_match_root_summary": True}
    save(output / "delivery_metadata_verification.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", default=[])
    parser.add_argument("--runs-dir")
    args = parser.parse_args()
    paths = [Path(value) for value in args.run]
    if args.runs_dir:
        paths.extend(path for path in Path(args.runs_dir).iterdir() if path.is_dir() and (path / "run_manifest.json").exists())
    reports = [finalize(path) for path in sorted(set(paths))]
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
