#!/usr/bin/env python3
"""Evaluate a frozen custom STCA model on same-property labeled data, no refit.

Reads the transform/units/representation contract saved by custom_fit.py.
Cross-source evaluation retains the numerical source cutoff by default.
Dataset-relative labeling is a separate explicitly requested ranking task.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from stca_runtime import load_stca, environment_receipt
from stca_io import read_csv_frame
from custom_fit import prepare_rows, write_json, sha, _physical_unit, parse_tiers


def run(args):
    import numpy as np
    import pandas as pd
    stca = load_stca(args.source)
    from stca.chemistry import MACCS_NAMES, maccs_from_smiles
    from stca.errors import NoValidRuleError
    from data_readiness import apply_transform, inverse_transform
    model = stca.ScreeningModel.load(args.model)
    contract = model.provenance.get("caller_metadata", {}).get("custom_data_contract")
    if not contract:
        raise ValueError("Model lacks custom_data_contract; use the original upstream evaluator with an explicit representation contract.")
    if args.property != model.artifact["target_name"]:
        raise ValueError("Evaluation property differs from the frozen target; cross-property claims are not same-property transfer.")
    if args.unit != contract["original_unit"]:
        raise ValueError("Evaluation unit differs from the saved input unit. Convert units explicitly in a separate table first.")
    if contract["representation"] != "hcap_maccs167":
        raise ValueError("Unsupported saved representation.")
    out = Path(args.output_dir).expanduser().resolve()
    if out.exists():
        raise FileExistsError("Output directory exists; use a new directory.")
    args.group_column = None
    args.condition_columns = args.metadata_columns = ""
    rows, raw_y = prepare_rows(read_csv_frame(args.input), args)
    valid = rows.stca_input_valid.to_numpy(bool)
    if not valid.any():
        raise ValueError("No valid labeled evaluation rows.")
    X, _ = maccs_from_smiles(rows.stca_calculation_smiles_hcap.where(valid, "").tolist(), errors="report")
    X = pd.DataFrame(np.asarray(X), columns=MACCS_NAMES)
    y = apply_transform(raw_y[valid], contract["transform"])
    groups = rows.loc[valid, "stca_original_identity"].to_numpy()
    hcap_hashes = {hashlib.sha256(str(x).encode()).hexdigest() for x in rows.loc[valid, "stca_hcap_identity"]}
    training_caps = set(contract.get("source_hcap_identity_hashes", []))
    cap_overlap = len(hcap_hashes & training_caps) if training_caps else None
    out.mkdir(parents=True)
    results = rows.copy()
    reports = []
    tiers = model.tiers if args.tiers is None else parse_tiers(args.tiers)
    for q in tiers:
        row = {"tier": q, "metrics": None}
        row["hcap_identity_overlap_count"] = cap_overlap
        row["independence_claim"] = ("not_verified_Hcap_overlap" if cap_overlap else
                                     "Hcap_identity_audit_unavailable" if cap_overlap is None else
                                     "original_and_Hcap_identity_audited_not_proof_of_all_condition_independence")
        try:
            rule = model.rule_for(q)
            m = model.evaluate(X.loc[valid], y, tier=q, groups=groups,
                               cutoff_mode=args.cutoff_mode)
            cut = m["cutoff"]
            inverse = "log10" if contract["transform"] == "log10" or contract["already_log"] else "none"
            pos = int(m["positive_n"]); neg = int(m["n"]-pos)
            row.update(status="evaluated", physical_cutoff=inverse_transform(cut, inverse),
                       physical_unit=_physical_unit(contract["original_unit"], contract["already_log"]),
                       model_space_cutoff=cut, cutoff_mode=args.cutoff_mode,
                       target_definition=("frozen_source_numerical_boundary" if args.cutoff_mode == "fixed_train"
                                          else "evaluation_relative_percentile_not_same_physical_target"),
                       evidence_status=("no_target_positives" if pos == 0 else "no_target_negatives" if neg == 0
                                        else "low_support_exploratory" if min(pos,neg) < args.positive_support
                                        else "support_threshold_met_not_guaranteed_accuracy"))
            m["upstream_raw_mcc"] = m["mcc"]
            m["upstream_raw_average_score"] = m["average_score"]
            constant_prediction = m["selected_n"] == 0 or m["selected_n"] == m["n"]
            if pos == 0 or neg == 0 or constant_prediction:
                m["mcc"] = None
                m["average_score"] = None
                row["metric_status"] = ("undefined_single_truth_class" if pos == 0 or neg == 0 else
                                        "undefined_constant_prediction")
                if pos == 0:
                    for k in ["recall", "f1", "enrichment_factor"]: m[k] = None
            else:
                row["metric_status"] = "computed"
            if m["selected_n"] == 0:
                m["precision"] = None
                m["enrichment_factor"] = None
            row["metrics"] = m
            selected = pd.Series(pd.NA, index=results.index, dtype="boolean")
            selected.loc[valid] = rule.apply(X.loc[valid].to_numpy())
            results[f"stca_tier_{q:g}_selected"] = selected
        except NoValidRuleError as exc:
            row.update(status="no_frozen_rule", reason=str(exc))
        except (ValueError, RuntimeError) as exc:
            row.update(status="evaluation_failed", error_type=type(exc).__name__, reason=str(exc))
        reports.append(row)
    results.to_csv(out/"rows.csv", index=False)
    presentation = results.drop(columns=["stca_calculation_smiles_hcap", "stca_hcap_identity"], errors="ignore")
    presentation.to_csv(out/"results.csv", index=False)
    write_json(out/"evaluation_metrics.json", {"schema":"stca-frozen-custom-evaluation-v1", "property":args.property,
        "unit":args.unit, "cutoff_mode":args.cutoff_mode, "model_sha256":sha(args.model),
        "input_sha256":sha(args.input), "transform":contract["transform"], "refitted":False,
        "overlap_policy":"upstream stored original-identity hashes reject overlapping observations; never silently delete overlaps",
        "support_threshold":args.positive_support, "threshold_is_heuristic":True,
        "tiers":reports, "environment":environment_receipt(args.source)})
    print(json.dumps({"output_directory":str(out), "evaluated_tiers":len(reports), "refitted":False}))
    return 2 if any(r["status"] == "evaluation_failed" for r in reports) else 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source")
    for name in ("input","model","target","property","unit","output-dir"):p.add_argument("--"+name,required=True)
    p.add_argument("--smiles-column", default="SMILES")
    p.add_argument("--id-column")
    p.add_argument("--tiers")
    p.add_argument("--cutoff-mode",choices=("fixed_train","dataset_relative"),default="fixed_train")
    p.add_argument("--positive-support",type=int,default=20)
    p.add_argument("--invalid-policy",choices=("error","report"),default="error")
    a=p.parse_args(argv)
    try:
        if a.positive_support < 1:
            raise ValueError("positive-support must be at least 1")
        return run(a)
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"stca-evaluate-custom: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
