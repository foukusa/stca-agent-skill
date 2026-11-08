#!/usr/bin/env python3
"""Evaluate frozen STCA, WRAcc and RF on exactly the same source/outer rows.

WRAcc and RF parameters reproduce the trial archive's three_mode_study/
mode2_base.py. This optional comparison utility is separate from the original STCA algorithm.
Target transformation is explicit, and all tier cutoffs come from model.json.
No outer target is used to train, choose configurations, or select rules.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import MACCSkeys
from sklearn.ensemble import RandomForestClassifier


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def literal_mask(x, literals):
    selected = np.ones(len(x), dtype=bool)
    for key, value in literals:
        selected &= x[:, key] == value
    return selected


def beam_wracc(x, y, depth=3, width=30, minsup=5):
    n = len(y)
    prevalence = y.mean()
    keys = [j for j in range(1, x.shape[1]) if x[:, j].min() != x[:, j].max()]
    literals = [(j, v) for j in keys for v in (1, 0)]

    def score(mask):
        count = mask.sum()
        return -1 if count < minsup else (count / n) * (y[mask].mean() - prevalence)

    beam = [((), np.ones(n, bool))]
    best = (-1, ())
    for _ in range(depth):
        candidates = {}
        for rule, mask in beam:
            used = {j for j, _ in rule}
            for literal in literals:
                if literal[0] in used:
                    continue
                next_rule = tuple(sorted(rule + (literal,)))
                if next_rule in candidates:
                    continue
                next_mask = mask & (x[:, literal[0]] == literal[1])
                value = score(next_mask)
                if value > 0:
                    candidates[next_rule] = (value, next_mask)
        top = sorted(candidates.items(), key=lambda item: -item[1][0])[:width]
        beam = [(rule, value[1]) for rule, value in top]
        if top and top[0][1][0] > best[0]:
            best = (top[0][1][0], top[0][0])
    return list(best[1])


def metric(y, predicted):
    y, predicted = np.asarray(y, bool), np.asarray(predicted, bool)
    tp = int((y & predicted).sum())
    fp = int((~y & predicted).sum())
    tn = int((~y & ~predicted).sum())
    fn = int((y & ~predicted).sum())
    denominator = math.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    mcc = (tp * tn - fp * fn) / denominator if denominator else None
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    prevalence = (tp + fn) / len(y)
    problems = []
    if not tp + fn:
        problems.append("no_target_positive")
    if not tn + fp:
        problems.append("no_target_negative")
    if not tp + fp:
        problems.append("zero_selection")
    if not tn + fn:
        problems.append("all_selected")
    return dict(n=len(y), positive_n=tp + fn, negative_n=tn + fp,
                selected_n=tp + fp, tp=tp, fp=fp, tn=tn, fn=fn, mcc=mcc,
                precision=p, recall=r, f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
                coverage=(tp + fp) / len(y), prevalence=prevalence,
                enrichment_factor=p / prevalence if p is not None and prevalence else None,
                metric_status="defined" if mcc is not None else "undefined",
                metric_reasons=problems,
                class_support_at_least_20=min(tp + fn, tn + fp) >= 20)


def frozen_rule(model, tier):
    item = model["tiers"][tier]
    name = item.get("selected_rule")
    if isinstance(name, dict):
        return name
    if name is None:
        return None
    for candidate in item.get("rules", []):
        rule = candidate.get("rule", candidate)
        if rule.get("name") == name:
            return rule
    raise ValueError(f"Selected rule {name!r} missing from tier {tier!r} family")


def run(args):
    out = Path(args.output_dir).resolve()
    if out.exists():
        raise FileExistsError(out)
    frame = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    model = json.loads(Path(args.model).read_text())
    required = [args.target_column, args.smiles_column, args.role_column]
    if any(name not in frame for name in required):
        raise ValueError(f"Missing columns: {[x for x in required if x not in frame]}")
    source = frame[args.role_column].isin(args.source_role).to_numpy()
    outer = frame[args.role_column].isin(args.outer_role).to_numpy()
    if not source.any() or not outer.any() or (source & outer).any():
        raise ValueError("Require nonempty, disjoint declared source and outer roles")
    unknown = ~(source | outer)
    if unknown.any():
        raise ValueError(f"Undeclared role values: {frame.loc[unknown, args.role_column].unique().tolist()}")
    if args.expected_source_count is not None and int(source.sum()) != args.expected_source_count:
        raise ValueError("Source count differs from supplied expected count")
    recorded_n = model.get("provenance", {}).get("n_source_records")
    if recorded_n is not None and int(source.sum()) != recorded_n:
        raise ValueError(f"Frozen model n_source_records={recorded_n}, input source={source.sum()}")
    target = pd.to_numeric(frame[args.target_column], errors="raise").to_numpy(float)
    if not np.isfinite(target).all():
        raise ValueError("Nonfinite targets in cleaned analysis input")
    if args.target_transform == "log10":
        if (target <= 0).any():
            raise ValueError("log10 requires positive target values")
        target = np.log10(target)
    mols = [Chem.MolFromSmiles(value) for value in frame[args.smiles_column]]
    if any(m is None for m in mols):
        raise ValueError("Invalid SMILES in cleaned analysis input")
    if any(any(atom.GetAtomicNum() == 0 for atom in mol.GetAtoms()) for mol in mols):
        raise ValueError("Use an already prepared H-cap calculation column, not wildcard structures")
    x = np.asarray([list(MACCSkeys.GenMACCSKeys(m)) for m in mols], dtype=np.int8)
    if x.shape != (len(frame), 167) or x[:, 0].any():
        raise ValueError("Unexpected MACCS167 contract")
    predictions = frame.copy()
    records = []
    direction = model["direction"]
    for tier, item in model["tiers"].items():
        cutoff = float(item["train_cutoff"])
        labels = target >= cutoff if direction == "high" else target <= cutoff
        predictions[f"tier_{tier}__label"] = labels
        train_labels = labels[source]
        if np.unique(train_labels).size < 2:
            raise ValueError(f"Tier {tier} lacks source class support")
        methods = {}
        rule = frozen_rule(model, tier)
        if rule is None:
            methods["STCA"] = (None, "no_frozen_rule", None)
        else:
            literals = list(zip(rule["keys"], rule["values"]))
            methods["STCA"] = (literal_mask(x[outer], literals), "frozen_rule", literals)
        try:
            literals = beam_wracc(x[source], train_labels)
            if literals:
                methods["WRAcc"] = (literal_mask(x[outer], literals), "fitted", literals)
            else:
                # Do not silently turn [] into an all-selected learned subgroup.
                methods["WRAcc"] = (None, "no_positive_wracc_subgroup", [])
        except Exception as exc:
            methods["WRAcc"] = (None, "fit_failed", f"{type(exc).__name__}: {exc}")
        try:
            rf = RandomForestClassifier(n_estimators=500, class_weight="balanced",
                                        min_samples_leaf=2, random_state=0,
                                        n_jobs=args.n_jobs).fit(x[source], train_labels)
            methods["RF"] = (rf.predict(x[outer]).astype(bool), "fitted", None)
        except Exception as exc:
            methods["RF"] = (None, "fit_failed", f"{type(exc).__name__}: {exc}")
        for method, (predicted, state, detail) in methods.items():
            row = dict(dataset=args.dataset, method=method, tier=float(tier), direction=direction,
                       cutoff_model_space=cutoff, cutoff_physical_space=10 ** cutoff
                       if (args.cutoff_inverse_transform or args.target_transform) == "log10" else cutoff,
                       target_transform=args.target_transform, status=state,
                       source_n=int(source.sum()), outer_n=int(outer.sum()), rule=detail)
            if predicted is not None:
                row.update(metric(labels[outer], predicted))
                predictions[f"tier_{tier}__{method}_selected"] = ""
                predictions.loc[outer, f"tier_{tier}__{method}_selected"] = predicted.astype(str)
            else:
                row.update(mcc=None, precision=None, recall=None, metric_status="not_run")
            records.append(row)
    out.mkdir(parents=True)
    predictions.to_csv(out / "outer_predictions.csv", index=False)
    pd.DataFrame(records).to_csv(out / "metrics.csv", index=False)
    summary = dict(schema="stca-same-rows-baselines-v1", dataset=args.dataset,
                   input_sha256=sha(args.input), model_sha256=sha(args.model),
                   benchmark_sha256=sha(__file__), n=len(frame), source_n=int(source.sum()),
                   outer_n=int(outer.sum()), source_role=args.source_role, outer_role=args.outer_role,
                   target_column=args.target_column, target_transform=args.target_transform,
                   smiles_column=args.smiles_column, model_target_name=model["target_name"],
                   model_target_unit=model["target_unit"], cutoff_origin="frozen_model_per_tier",
                   outer_configuration_selection_performed=False,
                   wracc=dict(depth=3, width=30, min_support=5),
                   random_forest=dict(n_estimators=500, class_weight="balanced", min_samples_leaf=2, random_state=0),
                   versions={p: importlib.metadata.version(p) for p in ["numpy", "pandas", "rdkit", "scikit-learn"]},
                   records=records)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output_dir": str(out), "records": len(records)}))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--target-column", required=True)
    ap.add_argument("--target-transform", required=True, choices=["none", "log10"],
                    help="Frozen source-decided transform; use none if target-column is already in model space")
    ap.add_argument("--cutoff-inverse-transform", choices=["none", "log10"],
                    help="Optional explicit reporting inverse, e.g. log10 when the input target is already log10")
    ap.add_argument("--smiles-column", default="stca_calculation_smiles_hcap")
    ap.add_argument("--role-column", default="split")
    ap.add_argument("--source-role", nargs="+", default=["source", "train", "interpolation"])
    ap.add_argument("--outer-role", nargs="+", default=["evaluation", "test", "extrapolation", "holdout"])
    ap.add_argument("--expected-source-count", type=int)
    ap.add_argument("--n-jobs", type=int, default=1)
    ap.add_argument("--output-dir", required=True)
    run(ap.parse_args())


if __name__ == "__main__":
    main()
