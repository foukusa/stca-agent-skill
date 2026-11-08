#!/usr/bin/env python3
"""Prepare custom CSV data, compare in-range rules, deliver and save both methods.

Default evidence is protected-structure grouped 5-fold CV, repeated three times,
conditional on the full-data preparation and scan decisions. It is not an
unbiased estimate of the entire cleaning, scan-selection or deployment process.
The optional nested report selects the learner inside each outer training fold;
it retains that same preparation limitation. Full-data deployment rules and
cutoffs are exported separately from every training-fold cutoff.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from generation_prompt import infer_structure_kind, STRUCTURE_KINDS
from fingerprint_contract import audit_fit_fingerprints, verify_run_artifacts
from wracc_search import DEFAULT_CAPS, cap_name, normalize_wracc_limit, search_wracc

TIE = 0.02
METRICS = ("precision", "recall", "f1", "mcc", "AS")
EVIDENCE = "conditional_on_full_data_preparation_and_scan"
LIMITATION = ("Grouped CV conditions on cleaning, target transformation, influence quarantine and scan "
              "decisions already made using the full uploaded dataset. It estimates rules within the user's "
              "observed data range; it is not an unbiased validation of the entire adaptive pipeline and "
              "does not establish structural extrapolation or measured-property success for new candidates.")


def json_ready(value):
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, np.generic):
        return json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(json_ready(value), handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def parse_tiers(values):
    tiers = []
    for supplied in values:
        for token in str(supplied).split(","):
            token = token.strip()
            percent = token.endswith("%")
            number = float(token.rstrip("%"))
            if percent or number >= 1:
                number /= 100
            if not math.isfinite(number) or not 0 < number < 1:
                raise ValueError("Tiers must be distinct fractions or percentages strictly between 0 and 100%.")
            if number in tiers:
                raise ValueError("Duplicate tier.")
            tiers.append(number)
    if not tiers:
        raise ValueError("At least one tier is required.")
    return tiers


def column_list(values):
    return [item.strip() for value in values or [] for item in value.split(",") if item.strip()]


def available_column(columns, proposed):
    candidate, suffix = proposed, 2
    while candidate in columns:
        candidate = f"{proposed}_{suffix}"
        suffix += 1
    return candidate


def tier_key(tier):
    return format(float(tier), ".12g")


def cutoff(y, tier, direction):
    return float(np.quantile(y, 1 - tier if direction == "high" else tier))


def labels(y, threshold, direction):
    return y >= threshold if direction == "high" else y <= threshold


def physical_cutoff(value, transform):
    if value is None:
        return None
    try:
        return float(10.0 ** value) if transform == "log10" else float(value)
    except OverflowError:
        return None


def scores(truth, predicted):
    """Pooled OOF metrics; unavailable evidence stays null rather than fake zero."""
    truth = np.asarray(truth, dtype=bool)
    predicted = np.asarray(predicted, dtype=bool)
    base = {metric: None for metric in METRICS}
    if not len(truth) or not truth.any() or truth.all():
        return {**base, "status": "unavailable_target_has_one_class", "n": len(truth),
                "positive_n": int(truth.sum())}
    tp = int((truth & predicted).sum())
    fp = int((~truth & predicted).sum())
    fn = int((truth & ~predicted).sum())
    tn = int((~truth & ~predicted).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn)
    f1 = 2 * tp / (2 * tp + fp + fn)
    denominator = math.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    mcc = (tp * tn - fp * fn) / denominator if denominator else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "mcc": mcc,
            "AS": (mcc + precision + f1) / 3, "status": "evaluated",
            "n": len(truth), "positive_n": tp + fn, "negative_n": tn + fp,
            "selected_n": tp + fp, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "degenerate_prediction_metric_convention": "MCC=0 and precision=0 when their prediction denominator is zero"}


def rule_mask(matrix, rule):
    """A missing or empty rule is unknown, never the empty conjunction/all rows."""
    if not rule or not rule.get("keys"):
        return None
    result = np.ones(len(matrix), dtype=bool)
    for key, value in zip(rule["keys"], rule["values"]):
        result &= matrix[:, int(key)] == int(value)
    return result


def beam_wracc(matrix, truth, depth=3, width=30, min_support=5):
    """Compatibility wrapper; a supplied depth is honored without a hidden cap."""
    chosen = search_wracc(matrix, truth, caps=(depth,), width=width, min_support=min_support)["caps"][cap_name(depth)]
    return None if chosen is None else {"literals": chosen["literals"], "wracc": chosen["wracc"]}


def grouped_folds(groups, folds, seed):
    """Shuffle group identities and balance row counts without splitting groups."""
    unique, counts = np.unique(np.asarray(groups, dtype=str), return_counts=True)
    if len(unique) < folds:
        raise ValueError(f"insufficient_protected_groups:{len(unique)}<{folds}")
    generator = np.random.default_rng(seed)
    order = generator.permutation(len(unique))
    # Stable size sort retains random tie ordering.
    order = sorted(order, key=lambda i: -int(counts[i]))
    loads = np.zeros(folds, dtype=int)
    assignments = {}
    for index in order:
        fold = int(np.argmin(loads))
        assignments[unique[index]] = fold
        loads[fold] += int(counts[index])
    return np.asarray([assignments[str(group)] for group in groups], dtype=int)


class Learners:
    def __init__(self, matrix, target, groups, tiers, direction, scan, target_name, model_unit,
                 wracc_max_literals="auto", wracc_length_folds=3):
        self.matrix, self.target = matrix, target
        self.groups, self.tiers, self.direction = np.asarray(groups, dtype=str), tiers, direction
        self.scan, self.target_name, self.model_unit = scan, target_name, model_unit
        self.wracc_max_literals = normalize_wracc_limit(wracc_max_literals)
        self.wracc_length_folds = int(wracc_length_folds)
        if self.wracc_length_folds < 2:
            raise ValueError("WRAcc length selection requires at least two inner folds.")
        self.cache, self.length_cache = {}, {}

    def wracc_settings(self):
        return {"maximum_literals": self.wracc_max_literals, "beam_width": 30, "minimum_support": 5,
                "length_candidates": [cap_name(cap) for cap in DEFAULT_CAPS] if self.wracc_max_literals == "auto" else [],
                "inner_folds_requested": self.wracc_length_folds,
                "length_selection_scope": "inside_each_supplied_training_partition",
                "length_selection_score": "pooled_inner_OOF_(MCC+Precision+F1)/3",
                "tie_policy": "smaller_maximum_literals_then_unlimited",
                "unavailable_length_selection_fallback": "unlimited_with_explicit_unavailable_status",
                "unlimited_definition": "all_distinct_varying_MACCS_keys_or_positive_beam_exhaustion_no_plateau_stop"}

    def select_wracc_length(self, positions, tier):
        """Choose a depth using only the supplied training partition's groups/labels."""
        positions = np.asarray(positions, dtype=int)
        cache_key = (tuple(positions.tolist()), float(tier))
        if cache_key in self.length_cache:
            return self.length_cache[cache_key]
        setting = self.wracc_max_literals
        metadata = {"requested_maximum_literals": setting, "selected_max_literals": setting,
                    "selection_status": "user_specified", "training_positions": positions.tolist(),
                    "training_n": len(positions), "inner_folds_requested": self.wracc_length_folds,
                    "inner_folds_used": 0, "inner_folds": [], "candidates": [],
                    "criterion": "pooled_inner_OOF_(MCC+Precision+F1)/3",
                    "tie_policy": "smaller_maximum_literals_then_unlimited"}
        if setting != "auto":
            self.length_cache[cache_key] = metadata
            return metadata
        groups = self.groups[positions]
        folds = min(self.wracc_length_folds, len(np.unique(groups)))
        metadata.update(selected_max_literals="unlimited", selection_status="unavailable",
                        fallback="unlimited", fallback_reason="insufficient_protected_groups")
        if folds < 2 or len(positions) < 2:
            self.length_cache[cache_key] = metadata
            return metadata
        fold_ids = grouped_folds(groups, folds, 7319)
        metadata["inner_folds_used"] = folds
        predictions = {cap_name(cap): np.full(len(positions), -1, dtype=np.int8) for cap in DEFAULT_CAPS}
        truths = np.zeros(len(positions), dtype=bool)
        for fold in range(folds):
            local_train, local_test = np.flatnonzero(fold_ids != fold), np.flatnonzero(fold_ids == fold)
            train, test = positions[local_train], positions[local_test]
            overlap = set(self.groups[train]) & set(self.groups[test])
            if overlap:
                raise RuntimeError("Protected group leakage in WRAcc inner length-selection folds.")
            threshold = cutoff(self.target[train], tier, self.direction)
            train_truth = labels(self.target[train], threshold, self.direction)
            truths[local_test] = labels(self.target[test], threshold, self.direction)
            searched = search_wracc(self.matrix[train], train_truth, caps=DEFAULT_CAPS)
            candidates = {}
            for cap in DEFAULT_CAPS:
                name, learned = cap_name(cap), searched["caps"][cap_name(cap)]
                if learned is None:
                    candidates[name] = {"status": "no_valid_rule", "rule": None}
                    continue
                rule = {"keys": [j for j, _ in learned["literals"]],
                        "values": [v for _, v in learned["literals"]]}
                mask = rule_mask(self.matrix[test], rule)
                predictions[name][local_test] = mask.astype(np.int8)
                candidates[name] = {"status": "rule_fitted", "rule": rule,
                                    "training_wracc": learned["wracc"], "actual_literal_n": learned["length"]}
            metadata["inner_folds"].append({"fold": fold + 1, "train_positions": train.tolist(),
                "test_positions": test.tolist(), "training_cutoff_model": threshold,
                "training_n": len(train), "test_n": len(test), "protected_group_overlap_n": 0,
                "candidates": candidates, "search_last_depth": searched["last_depth"],
                "search_termination": searched["termination"]})
        eligible = []
        for cap in DEFAULT_CAPS:
            name = cap_name(cap)
            unknown = int((predictions[name] < 0).sum())
            metric = ({"status": "unavailable_missing_inner_rule", "AS": None,
                       "unknown_prediction_n": unknown} if unknown else scores(truths, predictions[name] == 1))
            item = {"max_literals": name if cap is None else cap, **metric}
            metadata["candidates"].append(item)
            if metric.get("AS") is not None and metric.get("status") == "evaluated":
                eligible.append((float(metric["AS"]), float("inf") if cap is None else cap, cap))
        if eligible:
            # Scores first; exact score ties prefer the simpler requested cap.
            _, _, selected = min(eligible, key=lambda item: (-item[0], item[1]))
            metadata.update(selected_max_literals="unlimited" if selected is None else selected,
                            selection_status="selected_by_training_only_grouped_inner_cv")
            metadata.pop("fallback", None)
            metadata.pop("fallback_reason", None)
        else:
            metadata["fallback_reason"] = "no_cap_has_complete_two_class_inner_OOF_evidence"
        self.length_cache[cache_key] = metadata
        return metadata

    def fit(self, positions):
        positions = np.asarray(positions, dtype=int)
        cache_key = tuple(positions.tolist())
        if cache_key in self.cache:
            return self.cache[cache_key]
        y, matrix = self.target[positions], self.matrix[positions]
        result = {method: {} for method in ("STCA", "WRAcc")}
        for tier in self.tiers:
            threshold = cutoff(y, tier, self.direction) if len(y) else None
            for method in result:
                result[method][tier] = {"rule": None, "status": "no_valid_rule", "train_cutoff": threshold,
                                        "source_metrics": {}}
        try:
            if not self.scan:
                raise ValueError("Preparation scan is numerically unavailable; no scan mode or step was invented.")
            from stca.training import STCA
            from stca.scan import ScanConfig
            from stca.chemistry import MACCS_NAMES, MACCS_SPEC
            trainer = STCA(direction=self.direction, tiers=tuple(self.tiers),
                           scan=ScanConfig(**self.scan), max_rank=10, family_size=8,
                           target_name=self.target_name, target_unit=self.model_unit)
            model = trainer.fit(pd.DataFrame(matrix, columns=MACCS_NAMES), y,
                                feature_names_=MACCS_NAMES, feature_spec=MACCS_SPEC,
                                groups=self.groups[positions])
            for tier in self.tiers:
                entry = model.artifact["tiers"][tier_key(tier)]
                chosen = next((item for item in entry["rules"]
                               if item["rule"]["name"] == entry.get("selected_rule")), None)
                if chosen and chosen["rule"].get("keys"):
                    result["STCA"][tier].update(rule=chosen["rule"], status="rule_fitted",
                                                 source_metrics=chosen.get("source_metrics", {}))
        except (ValueError, RuntimeError, KeyError, TypeError, ArithmeticError) as exc:
            for tier in self.tiers:
                result["STCA"][tier].update(status="fit_unavailable", error=f"{type(exc).__name__}: {exc}")
        for tier in self.tiers:
            if not len(y):
                continue
            truth = labels(y, result["WRAcc"][tier]["train_cutoff"], self.direction)
            selection = self.select_wracc_length(positions, tier)
            selected_cap = selection["selected_max_literals"]
            result["WRAcc"][tier]["length_selection"] = selection
            search = search_wracc(matrix, truth, caps=(selected_cap,))
            result["WRAcc"][tier]["search"] = {key: value for key, value in search.items() if key != "caps"}
            learned = search["caps"][cap_name(selected_cap)]
            if learned is not None:
                literal_pairs = learned["literals"]
                rule = {"keys": [j for j, _ in literal_pairs], "values": [v for _, v in literal_pairs],
                        "name": f"WRAcc_{tier_key(tier)}", "family": f"WRAcc_beam_max_{cap_name(selected_cap)}"}
                result["WRAcc"][tier].update(rule=rule, status="rule_fitted",
                    source_metrics={**scores(truth, rule_mask(matrix, rule)), "wracc": learned["wracc"]})
        self.cache[cache_key] = result
        return result


def empty_repeat(reason, n, unknown=None):
    return {**{metric: None for metric in METRICS}, "status": reason, "n": n,
            "unknown_prediction_n": n if unknown is None else unknown}


def aggregate_repeats(records, repeats):
    completed = [record for record in records if record.get("status") == "evaluated"]
    good = len(completed) == repeats and repeats > 0
    result = {"status": "evaluated" if good else "unavailable_incomplete_repeated_oof",
              "complete_repeat_count": len(completed), "requested_repeat_count": repeats,
              "aggregation": "pooled_OOF_metric_per_repeat_then_mean_and_sample_SD",
              "repeats": records}
    if records and not completed:
        result["status"] = records[0]["status"] if len({r["status"] for r in records}) == 1 else result["status"]
    for metric in METRICS:
        result[metric + "_mean"] = float(np.mean([r[metric] for r in records])) if good else None
        result[metric + "_sd"] = (float(np.std([r[metric] for r in records], ddof=1)) if repeats > 1 else None) if good else None
    return result


def choose_by_cv(stca_score, wracc_score):
    left, right = stca_score.get("AS_mean"), wracc_score.get("AS_mean")
    if left is None or right is None:
        return "STCA", "STCA_default_comparison_unavailable"
    if right > left + TIE:
        return "WRAcc", "WRAcc_AS_exceeds_STCA_by_more_than_0.02"
    return "STCA", "STCA_retained_WRAcc_advantage_not_more_than_0.02"


def evaluate(learners, *, folds=5, repeats=3, nested=False, with_rf=False,
             positions=None, seed_offset=0, minimum_positives=20):
    positions = np.arange(len(learners.target)) if positions is None else np.asarray(positions, dtype=int)
    methods = ["STCA", "WRAcc"] + (["nested_integrated"] if nested else []) + (["RF"] if with_rf else [])
    records = {method: {tier: [] for tier in learners.tiers} for method in methods}
    fold_rows, assignment_rows, oof_rows = [], [], []
    eligibility = {}
    for tier in learners.tiers:
        population = learners.target[positions]
        truth = labels(population, cutoff(population, tier, learners.direction), learners.direction) if len(population) else np.array([], dtype=bool)
        reasons = []
        if not len(population):
            reasons.append("unavailable_no_usable_records")
        elif not truth.any():
            reasons.append("unavailable_no_positive_examples")
        elif truth.all():
            reasons.append("unavailable_target_has_one_class")
        if len(np.unique(learners.groups[positions])) < folds:
            reasons.append("unavailable_insufficient_protected_groups")
        if len(population) < 5 or len(population) - math.ceil(len(population) / folds) < 4:
            reasons.append("unavailable_insufficient_training_records")
        if int(truth.sum()) < minimum_positives:
            reasons.append("unavailable_fewer_than_20_full_data_positives" if minimum_positives == 20 else "unavailable_insufficient_positives")
        eligibility[tier] = {"status": reasons[0] if reasons else "eligible", "unavailable_reasons": reasons,
                             "full_population_positive_n": int(truth.sum()),
                             "minimum_positive_n": minimum_positives, "population_n": len(population)}
    if all(entry["status"] != "eligible" for entry in eligibility.values()):
        for method in methods:
            for tier in learners.tiers:
                records[method][tier] = [empty_repeat(eligibility[tier]["status"], len(positions)) for _ in range(repeats)]
        return {"summary": {method: {tier: aggregate_repeats(records[method][tier], repeats) for tier in learners.tiers} for method in methods},
                "eligibility": eligibility, "folds": [], "assignments": [], "oof": []}
    for repeat in range(repeats):
        fold_ids = grouped_folds(learners.groups[positions], folds, seed_offset + repeat)
        predicted = {method: {tier: np.full(len(positions), -1, dtype=np.int8) for tier in learners.tiers} for method in methods}
        truths = {tier: np.zeros(len(positions), dtype=bool) for tier in learners.tiers}
        for local_index, position in enumerate(positions):
            assignment_rows.append({"repeat": repeat + 1, "model_row_position": int(position),
                                    "protected_group": learners.groups[position], "fold": int(fold_ids[local_index]) + 1})
        for fold in range(folds):
            local_test, local_train = np.flatnonzero(fold_ids == fold), np.flatnonzero(fold_ids != fold)
            train, test = positions[local_train], positions[local_test]
            overlap = set(learners.groups[train]) & set(learners.groups[test])
            if overlap:
                raise RuntimeError("Protected group leakage in CV assignments.")
            fitted = learners.fit(train)
            inner = None
            if nested:
                inner = evaluate(learners, folds=3, repeats=1, positions=train,
                                 seed_offset=10000 + (seed_offset + repeat) * folds + fold,
                                 minimum_positives=1)
            for tier in learners.tiers:
                if eligibility[tier]["status"] != "eligible":
                    continue
                threshold = cutoff(learners.target[train], tier, learners.direction)
                truths[tier][local_test] = labels(learners.target[test], threshold, learners.direction)
                for method in ("STCA", "WRAcc"):
                    entry = fitted[method][tier]
                    mask = rule_mask(learners.matrix[test], entry["rule"])
                    if mask is not None:
                        predicted[method][tier][local_test] = mask.astype(np.int8)
                    fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "tier": tier,
                        "method": method, "status": entry["status"], "error": entry.get("error"),
                        "training_n": len(train), "test_n": len(test),
                        "training_group_n": len(set(learners.groups[train])), "test_group_n": len(set(learners.groups[test])),
                        "protected_group_overlap_n": len(overlap), "training_fold_cutoff_model": threshold,
                        "test_positive_n_at_training_cutoff": int(truths[tier][local_test].sum()),
                        "rule": entry["rule"],
                        **({"WRAcc_length_selection": entry.get("length_selection"),
                            "WRAcc_search": entry.get("search")} if method == "WRAcc" else {})})
                if nested:
                    selected, reason = choose_by_cv(inner["summary"]["STCA"][tier], inner["summary"]["WRAcc"][tier])
                    predicted["nested_integrated"][tier][local_test] = predicted[selected][tier][local_test]
                    fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "tier": tier,
                        "method": "nested_integrated", "selected_method": selected, "selection_reason": reason,
                        "training_fold_cutoff_model": threshold,
                        "inner_STCA_AS": inner["summary"]["STCA"][tier]["AS_mean"],
                        "inner_WRAcc_AS": inner["summary"]["WRAcc"][tier]["AS_mean"],
                        "inner_evaluation_status": {m: inner["summary"][m][tier]["status"] for m in ("STCA", "WRAcc")},
                        "inner_folds": [item for item in inner["folds"] if item["tier"] == tier]})
                if with_rf:
                    try:
                        from sklearn.ensemble import RandomForestClassifier
                        rf = RandomForestClassifier(n_estimators=300, class_weight="balanced", min_samples_leaf=2,
                                                    random_state=seed_offset + repeat, n_jobs=1)
                        rf.fit(learners.matrix[train], labels(learners.target[train], threshold, learners.direction))
                        predicted["RF"][tier][local_test] = rf.predict(learners.matrix[test]).astype(np.int8)
                    except (ValueError, RuntimeError) as exc:
                        fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "tier": tier,
                                          "method": "RF", "status": "fit_unavailable", "error": str(exc)})
        for tier in learners.tiers:
            for method in methods:
                if eligibility[tier]["status"] != "eligible":
                    result = empty_repeat(eligibility[tier]["status"], len(positions))
                else:
                    unknown = int((predicted[method][tier] < 0).sum())
                    result = empty_repeat("unavailable_missing_rule_or_failed_fold", len(positions), unknown) if unknown else scores(truths[tier], predicted[method][tier] == 1)
                result["repeat"] = repeat + 1
                records[method][tier].append(result)
                if eligibility[tier]["status"] == "eligible":
                    for local_index, position in enumerate(positions):
                        prediction = int(predicted[method][tier][local_index])
                        oof_rows.append({"repeat": repeat + 1, "fold": int(fold_ids[local_index]) + 1,
                            "model_row_position": int(position), "tier": tier, "method": method,
                            "target_positive_at_training_fold_cutoff": bool(truths[tier][local_index]),
                            "selected": None if prediction < 0 else bool(prediction)})
    return {"summary": {method: {tier: aggregate_repeats(records[method][tier], repeats) for tier in learners.tiers} for method in methods},
            "eligibility": eligibility, "folds": fold_rows, "assignments": assignment_rows, "oof": oof_rows}


def rule_expression(rule):
    return " AND ".join(f"K{key}={value}" for key, value in zip(rule["keys"], rule["values"])) if rule else None


def user_summary(rows, deployment, *, target_name, direction, unit, original_input_rows, folds=5, repeats=3):
    """Join exact deployment counts to CV method choices without changing either."""
    operator = ">=" if direction == "high" else "<="
    by_method = {(entry["method"], float(entry["tier"])): entry for entry in deployment}
    tiers = []
    for row in rows:
        q = float(row["tier"])
        target = {"fraction": q, "percentage": q * 100,
                  "label": f"{'Top' if direction == 'high' else 'Bottom'} {q * 100:g}%",
                  "physical_cutoff": row["deployment_cutoff_physical"], "operator": operator, "unit": unit,
                  "cutoff_scope": "full_prepared_data_deployment",
                  "recommended_method": row["primary"], "alternative_method": row["alternative"],
                  "recommendation_reason": row["recommendation_reason"], "methods": {}}
        for method in ("STCA", "WRAcc"):
            item = by_method[(method, q)]
            selected, unknown = int(item["selected_original_row_n"]), int(item["unknown_original_row_n"])
            if min(selected, unknown) < 0 or selected + unknown > original_input_rows:
                raise ValueError("Screening summary counts do not match the original input rows.")
            prefix = f"{method.lower()}/tier_{tier_key(q)}"
            target["methods"][method] = {
                "status": item["status"], "cv_status": row[f"cv_{method.lower()}_status"],
                "cv_AS_mean": row[f"cv_{method.lower()}_AS_mean"],
                "cv_AS_sd": row[f"cv_{method.lower()}_AS_sd"],
                "selected_n": selected, "not_selected_n": original_input_rows - selected - unknown,
                "unknown_n": unknown, "original_input_n": original_input_rows,
                "rule": row[method.lower() + "_rule"],
                **({"WRAcc_length_selection": {key: value for key, value in (item.get("WRAcc_length_selection") or {}).items()
                        if key in {"requested_maximum_literals", "selected_max_literals", "selection_status",
                                   "inner_folds_used", "fallback", "fallback_reason"}},
                    "WRAcc_search": item.get("WRAcc_search"),
                    "WRAcc_length_selection_details": "wracc_length_selection.json"} if method == "WRAcc" else {}),
                "results_with_failed_conditions": prefix + "/screening/results.csv",
                "selected_rows": prefix + "/selected.csv", "constraints": prefix + "/constraints.json"}
        tiers.append(target)
    return json_ready({"schema": "stca-user-screening-summary-v1", "property": target_name,
                       "direction": direction, "unit": unit, "original_input_rows": original_input_rows,
                       "CV_folds": folds, "CV_repeats": repeats, "method_choice_margin": TIE,
                       "method_score": "(MCC + Precision + F1) / 3", "tiers": tiers,
                       "evaluation_scope": EVIDENCE, "next_action": "continue_conversation"})


def render_user_summary(summary):
    def number(value):
        return "不可评价" if value is None else format(float(value), ".10g")
    lines = [f"# {summary['property']}：规则与筛选结果", "",
             "每档分别交付 STCA 和 WRAcc。按分组交叉验证推荐方法：多次用部分结构分组学习、其余分组评价。沿用[作者 STCA 论文](https://doi.org/10.1038/s41524-026-02345-x)的平均筛选评分，即马修斯相关系数、精确率和 F1 分数的平均值（Average Score，AS=(MCC+Precision+F1)/3）；F1 综合精确率与召回率。",
             "WRAcc 的交叉验证平均筛选评分高于 STCA 超过 0.02 时主推 WRAcc，否则保留 STCA；无法比较时明确标注。", "",
             "| 档位 | 具体物理阈值 | STCA 入选 / 未知 | STCA 交叉验证平均评分 | WRAcc 入选 / 未知 | WRAcc 交叉验证平均评分 | 主推 |",
             "|---|---|---:|---:|---:|---:|---|"]
    if summary.get("fingerprint_contract", {}).get("status") == "verified":
        lines.insert(2, "计算约定：H-cap 核验通过；拟合指纹已逐位核对，见 [计算记录](fingerprint_contract.json)。")
    if summary.get("WRAcc_search"):
        setting = summary["WRAcc_search"]["maximum_literals"]
        lines.insert(3, "WRAcc 条件数：训练分区内自动比较 1、2、3、5、10 条与不限制条件数；评价折只用于评价。" if setting == "auto"
                     else f"WRAcc 条件数：按用户要求设置为 {setting}；不限制时搜索至所有可变键或候选耗尽。")
    for item in summary["tiers"]:
        left, right = item["methods"]["STCA"], item["methods"]["WRAcc"]
        threshold = f"{item['operator']} {number(item['physical_cutoff'])} {item['unit']}"
        lines.append(f"| {item['label']} | {threshold} | {left['selected_n']} / {left['unknown_n']} | {number(left['cv_AS_mean'])} | {right['selected_n']} / {right['unknown_n']} | {number(right['cv_AS_mean'])} | {item['recommended_method'] or '无有效规则'} |")
    reasons = {"WRAcc_AS_exceeds_STCA_by_more_than_0.02": "WRAcc 的交叉验证平均筛选评分高出 STCA 超过 0.02。",
               "STCA_retained_WRAcc_advantage_not_more_than_0.02": "WRAcc 的交叉验证平均筛选评分未高出 STCA 超过 0.02，保留 STCA。",
               "STCA_default_comparison_unavailable": "交叉验证比较证据不足，默认保留 STCA；不声称其得分更优。",
               "only_method_with_valid_full_data_rule_CV_superiority_not_established": "只有这一方法有可应用的全量规则，交叉验证优越性未确立。",
               "no_valid_full_data_rule_for_either_method": "两方法均无有效规则。"}
    for item in summary["tiers"]:
        lines += ["", f"## {item['label']}", "",
                  f"主推：**{item['recommended_method'] or '无有效规则'}**；备选：{item['alternative_method'] or '无'}。",
                  reasons.get(item["recommendation_reason"], item["recommendation_reason"]), ""]
        for method, result in item["methods"].items():
            lines += [f"- **{method}**：入选 {result['selected_n']}，未入选 {result['not_selected_n']}，未知 {result['unknown_n']}；交叉验证状态 {result['cv_status']}。",
                      f"  [全部原行及未满足的规则条件]({result['results_with_failed_conditions']}) · [入选表]({result['selected_rows']}) · [精确约束]({result['constraints']})。",
                      f"  规则：`{result['rule']}`。" if result['rule'] else "  无有效规则，结果保持未知。"]
            if method == "WRAcc" and result.get("WRAcc_length_selection"):
                choice = result["WRAcc_length_selection"]
                value = choice["selected_max_literals"]
                label = "不限制" if value == "unlimited" else str(value)
                status = {"user_specified": "用户指定", "selected_by_training_only_grouped_inner_cv": "训练分区内自动选择",
                          "unavailable": "内层评价不可用"}.get(choice["selection_status"], choice["selection_status"])
                lines.append(f"  搜索条件数上限：{label}；本条规则实际 {len(result['rule'].split(' AND ')) if result['rule'] else 0} 条；选择状态：{status}。")
                if choice.get("fallback_reason"):
                    lines.append("  内层评价证据不足，使用明确记录的不限制搜索回退；未声称已验证最优条件数。")
    lines += ["", "百分比对应准备后数据的目标尾部，表中阈值为最终部署模型的原始物理尺度边界；不是候选入选配额。",
              "交叉验证使用各训练折的阈值；最终原表回筛使用全量冻结阈值。二者不混同，评价范围见 run_manifest.json。",
              "完整中英文 prompt、模型和规则包按保存凭据交付。可接着要求用刚保存的规则筛选或生成；具体文件位置见保存记录。", ""]
    return "\n".join(lines)


def run(args):
    from stca_runtime import load_stca, environment_receipt
    stca = load_stca(args.source)
    from stca.chemistry import maccs_from_smiles, MACCS_SPEC
    from auto_data_layer import prepare_dataset
    from auto_screen import read_auto_frame
    from frozen_literal_model import create_model_artifact
    from stca_tools import export_rules, screen_candidates
    from user_rule_library import save_entry, export_entry

    tiers = parse_tiers(args.tiers)
    if args.folds < 2 or args.repeats < 1:
        raise ValueError("At least two folds and one repeat are required.")
    output = Path(args.output_dir).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"Output directory already exists: {output}; choose a new directory.")
    output.mkdir(parents=True)
    target_name = args.target_name or args.property or args.target
    requested_kind = getattr(args, "structure_kind", None)
    property_domain = {"molecule": "molecule", "polymer_repeat_unit": "polymer"}.get(requested_kind, "auto")
    prepared = prepare_dataset(args.input, smiles_column=args.smiles_column, target=args.target,
        property_name=args.property or target_name, output_dir=output / "preparation", unit=args.unit,
        already_log=args.already_log, direction=args.direction, tiers=tiers, id_column=args.id_column,
        condition_columns=column_list(args.condition_columns), text_columns=column_list(args.metadata_columns),
        skip_influence=args.skip_influence, source=args.source, property_domain=property_domain)
    data, audit = prepared["data"], prepared["audit"]
    observed_kind = infer_structure_kind(data["original_canon"].tolist())
    transform = audit.get("D3_transform", "none")
    if isinstance(transform, dict):
        transform = transform.get("transform", transform.get("name", "none"))
    transform = "log10" if transform == "log10" else "none"
    unit = audit.get("unit") or args.unit or "user_specified"
    model_unit = f"log10({unit})" if transform == "log10" else unit
    raw, format_audit = read_auto_frame(args.input)
    aliases = format_audit["column_alias_map"]
    def resolve(column):
        if column in raw:
            return column
        matches = [entry["normalized_header"] for entry in aliases if entry["original_header"] == column]
        if len(matches) == 1:
            return matches[0]
        return column.strip() if column and column.strip() in raw else column
    raw_path = output / "original_input.csv"
    raw.to_csv(raw_path, index=False)
    write_json(output / "input_format.json", format_audit)
    # The lower-level screener reserves stca_* output names. Archive aliases
    # exist only in its internal input; public results restore every raw name.
    screen_aliases, occupied = {}, set(raw.columns)
    for column in raw:
        if column.startswith("stca_"):
            alias = available_column(occupied, "archive_input_" + column)
            screen_aliases[column] = alias
            occupied.add(alias)
    screen_raw = raw.rename(columns=screen_aliases)
    screen_path = output / "screening_input.csv"
    screen_raw.to_csv(screen_path, index=False)
    write_json(output / "screening_input_aliases.json", {"internal_only": screen_aliases,
        "public_output_policy": "restore_all_original_input_columns_and_values_before_adding_derived_columns"})
    if len(data):
        matrix, _ = maccs_from_smiles(data["stca_calculation_smiles_hcap"].tolist())
        matrix = np.asarray(matrix, dtype=np.int8)
    else:
        matrix = np.empty((0, 167), dtype=np.int8)
    fingerprint_contract = audit_fit_fingerprints(data, matrix)
    write_json(output / "fingerprint_contract.json", fingerprint_contract)
    target = data["y_model"].to_numpy(dtype=float)
    groups = data["protected_group"].astype(str).to_numpy()
    scan_audit = audit.get("C1_scan", {})
    step = scan_audit.get("value_step", scan_audit.get("step", scan_audit.get("scan_step")))
    scan = None
    if isinstance(step, (float, int)) and math.isfinite(step) and step > 0:
        scan = {"mode": "value", "step": float(step), "min_subset_size": int(scan_audit.get("min_subset_size", 1)),
                "max_points": int(scan_audit.get("scan_plan", {}).get("max_grid_points", 20000))}
    wracc_limit = normalize_wracc_limit(getattr(args, "wracc_max_literals", "auto"))
    wracc_length_folds = int(getattr(args, "wracc_length_folds", 3))
    learners = Learners(matrix, target, groups, tiers, args.direction, scan, target_name, model_unit,
                        wracc_max_literals=wracc_limit, wracc_length_folds=wracc_length_folds)
    evaluation = evaluate(learners, folds=args.folds, repeats=args.repeats, nested=args.nested, with_rf=args.with_rf)
    for record in evaluation["folds"]:
        record["training_fold_cutoff_physical"] = physical_cutoff(record.get("training_fold_cutoff_model"), transform)
        record["unit"] = unit
    write_json(output / "cv_summary.json", {"schema": "stca-inrange-cv-v1", "evidence_status": EVIDENCE,
        "limitation": LIMITATION, "folds": args.folds, "repeats": args.repeats,
        "method_choice": "WRAcc only if AS exceeds STCA by more than 0.02; otherwise STCA",
        "WRAcc_search": learners.wracc_settings(),
        "fixed_preparation_scan": scan, "eligibility": evaluation["eligibility"], "methods": evaluation["summary"],
        "nested": {"requested": args.nested, "inner_folds": 3, "scope": "method_selection_inside_outer_training_fold",
                   "evidence_status": EVIDENCE, "entire_pipeline_unbiased": False},
        "RF": {"requested": args.with_rf, "role": "optional_nonrule_reference_not_a_guaranteed_ceiling"}})
    write_json(output / "cv_fold_rules_and_cutoffs.json", evaluation["folds"])
    pd.DataFrame(evaluation["assignments"]).to_csv(output / "cv_group_assignments.csv", index=False)
    pd.DataFrame(evaluation["oof"]).to_csv(output / "cv_oof_predictions.csv", index=False)
    full = learners.fit(np.arange(len(data)))
    deployment = []
    contract = {"property": target_name, "original_unit": unit, "model_unit": model_unit,
                "uploaded_unit": audit.get("input_unit", args.unit),
                "uploaded_target_already_logarithmic": bool(args.already_log),
                "unit_conversion": audit.get("unit_conversion"),
                "transform": transform, "representation": "hcap_maccs167",
                "structure_kind": requested_kind or observed_kind,
                "input_structure_kind": observed_kind,
                "structure_kind_basis": "user_specified" if requested_kind else "original_smiles_notation",
                "property_domain": audit.get("property_domain", property_domain),
                "original_smiles_column": resolve(args.smiles_column), "target_column": resolve(args.target),
                "all_original_rows_preserved_in_screening": True,
                "fit_scope": "full_prepared_data_deployment", "evaluation_evidence_status": EVIDENCE}
    methods_delivered, saved = {}, {}
    aggregate = raw.copy()
    for method in ("STCA", "WRAcc"):
        method_dir = output / method.lower()
        method_dir.mkdir()
        tier_entries = {}
        for tier in tiers:
            fitted = full[method][tier]
            rule = fitted["rule"]
            tier_entries[tier_key(tier)] = {"train_cutoff": fitted["train_cutoff"],
                "selected_rule": rule["name"] if rule else None,
                "rules": [{"rule": rule, "source_metrics": fitted["source_metrics"]}] if rule else []}
        artifact = create_model_artifact(target_name=target_name, target_unit=model_unit,
            direction=args.direction, feature_spec=MACCS_SPEC, tiers=tier_entries, learner=method,
            custom_data_contract=contract, provenance={"kind": "full_prepared_data_frozen_selected_literals",
                "fit_scope": "full_prepared_data_deployment", "learner": method,
                "source_input_sha256": format_audit["input_sha256"],
                "training_record_n": len(data), "protected_group_n": len(set(groups)),
                "scan": scan if method == "STCA" else None, "conditional_evaluation": EVIDENCE,
                "not_complete_STCA_discovery_archive": True,
                "WRAcc_search": learners.wracc_settings() if method == "WRAcc" else None,
                "WRAcc_tier_length_selection": {tier_key(tier): full[method][tier].get("length_selection")
                                                for tier in tiers} if method == "WRAcc" else None})
        model_path = method_dir / "model.json"
        write_json(model_path, artifact)
        constraints, delivered_tiers = [], []
        for tier in tiers:
            name = tier_key(tier)
            bundle = method_dir / f"tier_{name}"
            captured = io.StringIO()
            with redirect_stdout(captured):
                export_rules(argparse.Namespace(profile=None, model=str(model_path), protocol=None, tier=tier,
                    count=args.count, preferences=args.preferences, output_dir=str(bundle), source=args.source), stca)
                screen_candidates(argparse.Namespace(profile=None, model=str(model_path), protocol=None,
                    tier=tier, input=str(screen_path), id_column=None,
                    smiles_column=screen_aliases.get(resolve(args.smiles_column), resolve(args.smiles_column)),
                    hcap_output_column="stca_calculation_smiles_hcap", input_is_hcap=False,
                    label=f"{target_name} {method} {name} full-data rule", property=target_name,
                    direction=args.direction, source_property=None, transfer_role=None, allow_transfer=False,
                    output_dir=str(bundle / "screening"), source=args.source), stca)
            (bundle / "adapter_receipts.jsonl").write_text(captured.getvalue(), encoding="utf-8")
            results = pd.read_csv(bundle / "screening" / "results.csv", dtype=str, keep_default_na=False)
            if len(results) != len(raw) or any(column not in results or results[column].tolist() != screen_raw[column].tolist() for column in screen_raw):
                raise RuntimeError(f"Original row/field preservation failed for {method} tier {tier}.")
            selected = results["stca_joint__selected"].str.lower().eq("true")
            public_results, output_columns = raw.copy(), {}
            for column in results:
                if column in screen_raw:
                    continue
                public_name = available_column(public_results.columns, column)
                public_results[public_name] = results[column].to_numpy()
                output_columns[column] = public_name
            public_results.to_csv(bundle / "screening" / "results.csv", index=False)
            public_results.loc[selected].to_csv(bundle / "selected.csv", index=False)
            write_json(bundle / "screening" / "public_output_columns.json", output_columns)
            aggregate[available_column(aggregate.columns, f"inrange_{method.lower()}_{name}__selected")] = results["stca_joint__selected"].to_numpy()
            aggregate[available_column(aggregate.columns, f"inrange_{method.lower()}_{name}__status")] = results["stca_joint__status"].to_numpy()
            constraint = json.loads((bundle / "constraints.json").read_text(encoding="utf-8"))
            if constraint.get("rule") is not None:
                constraints.append(bundle / "constraints.json")
            fitted = full[method][tier]
            deployment.append({"method": method, "tier": tier, "status": fitted["status"],
                "fit_error": fitted.get("error"), "cutoff_scope": "full_prepared_data_deployment",
                "deployment_cutoff_model": fitted["train_cutoff"],
                "deployment_cutoff_physical": physical_cutoff(fitted["train_cutoff"], transform),
                "unit": unit, "model_unit": model_unit, "rule": fitted["rule"],
                "expression": rule_expression(fitted["rule"]), "source_insample_metrics": fitted["source_metrics"],
                **({"WRAcc_length_selection": fitted.get("length_selection"),
                    "WRAcc_search": fitted.get("search")} if method == "WRAcc" else {}),
                "original_input_row_n": len(raw), "selected_original_row_n": int(selected.sum()),
                "unknown_original_row_n": int(results["stca_joint__selected"].eq("").sum())})
            delivered_tiers.append({"tier": tier, "bundle": str(bundle), "status": constraint["status"],
                                    "complete_prompt_status": constraint.get("prompt_generation", {}).get("status")})
        methods_delivered[method] = {"model": str(model_path), "tiers": delivered_tiers}
        if constraints:
            receipt = save_entry(args.library_dir, f"{target_name} {args.direction} {method} in-range full-data rules",
                                 model_path, constraints, args.count, args.preferences)
            archive = output / f"saved_{method.lower()}_rules.zip"
            exported = export_entry(args.library_dir, receipt["entry"]["id"], archive)
            saved[method] = {"save": receipt, "export": exported}
        else:
            saved[method] = {"status": "not_saved_no_valid_rule", "reason": "No exact nonempty rule is available; no reusable rule or prompt was invented."}
    aggregate.to_csv(output / "all_rows_screening.csv", index=False)
    write_json(output / "deployment_rules_and_cutoffs.json", deployment)
    write_json(output / "saved_rule_receipts.json", saved)
    rows, recommendation = [], []
    for tier in tiers:
        comparison = evaluation["summary"]
        primary, reason = choose_by_cv(comparison["STCA"][tier], comparison["WRAcc"][tier])
        other = "WRAcc" if primary == "STCA" else "STCA"
        if full[primary][tier]["rule"] is None:
            if full[other][tier]["rule"] is not None:
                primary, other = other, primary
                reason = "only_method_with_valid_full_data_rule_CV_superiority_not_established"
            else:
                primary, other = None, None
                reason = "no_valid_full_data_rule_for_either_method"
        row = {"tier": tier, "label": f"{'top' if args.direction == 'high' else 'bottom'} {tier * 100:g}%",
               "primary": primary, "alternative": other, "recommendation_reason": reason,
               "comparison_evidence_status": EVIDENCE, "cv_eligibility": evaluation["eligibility"][tier]["status"],
               "deployment_cutoff_physical": physical_cutoff(full["STCA"][tier]["train_cutoff"], transform), "unit": unit}
        for method in comparison:
            row[f"cv_{method.lower()}_status"] = comparison[method][tier]["status"]
            for metric in METRICS:
                for statistic in ("mean", "sd"):
                    row[f"cv_{method.lower()}_{metric}_{statistic}"] = comparison[method][tier][f"{metric}_{statistic}"]
        for method in ("STCA", "WRAcc"):
            row[f"{method.lower()}_rule"] = rule_expression(full[method][tier]["rule"])
            row[f"{method.lower()}_status"] = full[method][tier]["status"]
            applied = next(item for item in deployment if item["method"] == method and item["tier"] == tier)
            row[f"{method.lower()}_selected_n"] = applied["selected_original_row_n"]
            row[f"{method.lower()}_unknown_n"] = applied["unknown_original_row_n"]
            row[f"{method.lower()}_not_selected_n"] = len(raw) - applied["selected_original_row_n"] - applied["unknown_original_row_n"]
        row["physical_operator"] = ">=" if args.direction == "high" else "<="
        rows.append(row)
        recommendation.append({"tier": tier, "primary": primary, "alternative": other, "reason": reason,
            "STCA": comparison["STCA"][tier], "WRAcc": comparison["WRAcc"][tier],
            "is_independent_whole_pipeline_validation": False, "is_structural_extrapolation_evidence": False})
    pd.DataFrame(rows).to_csv(output / "inrange_evaluation.csv", index=False)
    write_json(output / "recommendations.json", {"tie_margin": TIE, "evidence_status": EVIDENCE,
                                               "limitation": LIMITATION, "tiers": recommendation})
    generation_tiers = []
    for row in rows:
        tier = row["tier"]
        item = {"tier": tier, "primary": row["primary"], "alternative": row["alternative"],
                "recommendation_reason": row["recommendation_reason"], "methods": {}}
        for method in ("STCA", "WRAcc"):
            bundle = output / method.lower() / f"tier_{tier_key(tier)}"
            item["methods"][method] = {"learner": method, "exact_expression": row[method.lower() + "_rule"],
                "model": str(output / method.lower() / "model.json"),
                "constraints": json.loads((bundle / "constraints.json").read_text(encoding="utf-8")),
                "prompts": {language: str(bundle / f"prompt.{language}.md") if (bundle / f"prompt.{language}.md").exists() else None
                            for language in ("en", "zh-CN")},
                "CV": evaluation["summary"][method][tier]}
        generation_tiers.append(item)
    write_json(output / "rules_for_generation.json", {"schema": "stca-inrange-generation-delivery-v1",
        "property": target_name, "unit": unit, "direction": args.direction,
        "evidence_status": EVIDENCE, "measured_property_guarantee": False, "tiers": generation_tiers})
    summary = user_summary(rows, deployment, target_name=target_name, direction=args.direction, unit=unit,
                           original_input_rows=len(raw), folds=args.folds, repeats=args.repeats)
    write_json(output / "wracc_length_selection.json", {"settings": learners.wracc_settings(),
        "deployment": {tier_key(tier): full["WRAcc"][tier].get("length_selection") for tier in tiers},
        "evaluation": [{"repeat": item["repeat"], "fold": item["fold"], "tier": item["tier"],
                        "selection": item.get("WRAcc_length_selection")} for item in evaluation["folds"]
                       if item.get("method") == "WRAcc"]})
    summary["WRAcc_search"] = learners.wracc_settings()
    summary["fingerprint_contract"] = {"status": fingerprint_contract["status"],
        "path": "fingerprint_contract.json", "representation": fingerprint_contract["representation"]}
    write_json(output / "screening_summary.json", summary)
    (output / "recommendation.md").write_text(render_user_summary(summary), encoding="utf-8")
    manifest = {"schema": "stca-inrange-workflow-v1", "status": "completed", "next_action": "continue_conversation",
        "entrypoint": "inrange_evaluation.py",
        "entrypoint_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fingerprint_contract": {"path": "fingerprint_contract.json", "status": fingerprint_contract["status"],
            "sha256": hashlib.sha256((output / "fingerprint_contract.json").read_bytes()).hexdigest(),
            "representation": fingerprint_contract["representation"], "matrix_sha256": fingerprint_contract["matrix_sha256"]},
        "learner_implementations": {"STCA": "author_STCA_prefix_rule_selection",
            "WRAcc": "adapter_signed_literal_beam_WRAcc_training_only_length_selection",
            "WRAcc_search_sha256": hashlib.sha256((HERE / "wracc_search.py").read_bytes()).hexdigest()},
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "input": str(Path(args.input).resolve()),
        "input_sha256": format_audit["input_sha256"], "original_input_row_n": len(raw),
        "prepared_measurement_n": len(data), "protected_group_n": len(set(groups)),
        "prepared_data_sha256": hashlib.sha256((output / "preparation" / "cleaned.csv").read_bytes()).hexdigest(),
        "preparation_audit_sha256": hashlib.sha256((output / "preparation" / "audit.json").read_bytes()).hexdigest(),
        "learning_settings": {"target_column": resolve(args.target), "smiles_column": resolve(args.smiles_column),
            "transform": transform, "scan": scan, "folds": args.folds, "repeats": args.repeats,
            "nested_method_selection": args.nested, "direction": args.direction, "tiers": tiers,
            "WRAcc_search": learners.wracc_settings()},
        "fit_scope": "full_prepared_data_deployment", "evaluation_scope": "inrange_grouped_repeated_CV",
        "evidence_status": EVIDENCE, "limitation": LIMITATION, "tiers": tiers,
        "methods": methods_delivered, "saved_rules": saved, "runtime": environment_receipt(args.source)}
    write_json(output / "run_manifest.json", manifest)
    delivery_check = verify_run_artifacts(output)
    write_json(output / "delivery_verification.json", delivery_check)
    print(json.dumps({"status": "completed", "output_directory": str(output), "next_action": "continue_conversation",
                      "screening_summary": str(output / "screening_summary.json"),
                      "tiers": summary["tiers"]}, ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--target-name")
    parser.add_argument("--property")
    parser.add_argument("--unit")
    parser.add_argument("--direction", choices=("high", "low"), default="high")
    parser.add_argument("--tiers", nargs="+", default=[".10", ".20", ".30"])
    parser.add_argument("--smiles-column", default="SMILES")
    parser.add_argument("--structure-kind", choices=STRUCTURE_KINDS,
                        help="Structure context and generation notation; molecule disables bulk-polymer range heuristics.")
    parser.add_argument("--id-column")
    parser.add_argument("--metadata-columns", "--text-columns", nargs="*", default=[])
    parser.add_argument("--condition-columns", nargs="*", default=[])
    parser.add_argument("--already-log", action="store_true")
    parser.add_argument("--skip-influence", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--library-dir", default=str(Path.cwd() / "stca-rules"))
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--nested", action="store_true")
    parser.add_argument("--with-rf", action="store_true")
    parser.add_argument("--wracc-max-literals", default="auto", type=normalize_wracc_limit,
                        metavar="auto|unlimited|N",
                        help="WRAcc maximum conditions: training-only adaptive choice (default), unlimited, or positive integer.")
    parser.add_argument("--wracc-length-folds", type=int, default=3,
                        help="Grouped inner folds for WRAcc depth selection, inside each training partition (default: 3).")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--preferences", default="")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print(f"inrange-evaluation: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
