#!/usr/bin/env python3
"""Source-only numerical planning and non-destructive data readiness for STCA.

This adapter does not delete measurements, average replicates, learn structural
rules, or choose settings from evaluation labels. Heuristics are recorded as
custom-analysis settings, never described as original-paper defaults.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

from stca_io import read_csv_records

PROCESSING_PATTERN = re.compile(
    r"methanol[- ]treat|methanol treatment|\baged\b|\baging\b|\bageing\b|"
    r"heated at|anneal|cross[- ]?link|plasma[- ]polymer|irradiat|stretched|"
    r"oriented film|\bblend\b|\bcomposite\b|partition method", re.I)


def _vector(values, name="source"):
    try:
        y = np.asarray(list(values), dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name} target contains nonnumeric values; no rows were deleted.") from exc
    if y.ndim != 1 or not len(y):
        raise ValueError(f"{name} target must be a nonempty one-dimensional array.")
    if not np.isfinite(y).all():
        raise ValueError(f"{name} target contains nonfinite values; no rows were deleted.")
    return y


def apply_transform(values, transform="none"):
    y = _vector(values)
    if transform not in ("none", "log10"):
        raise ValueError("transform must be none or log10 after planning.")
    if transform == "log10":
        if not (y > 0).all():
            raise ValueError("log10 requires strictly positive targets; no clipping or deletion is allowed.")
        return np.log10(y)
    return y.copy()


def inverse_transform(value, transform="none"):
    if transform == "none":
        return float(value)
    if transform != "log10":
        raise ValueError("transform must be none or log10.")
    try:
        out = 10.0 ** float(value)
    except OverflowError:
        return None
    return out if math.isfinite(out) else None


def nice_floor(value):
    """Largest 1/2/5 x 10**n <= a positive finite value."""
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("scan scale must be finite and positive.")
    exponent = math.floor(math.log10(value))
    base = 10.0 ** exponent
    if base == 0:
        return value
    for multiple in (5.0, 2.0, 1.0):
        candidate = multiple * base
        if candidate <= value * (1 + 1e-12):
            return candidate
    return base / 2.0


def _nice_ceil(value):
    lower = nice_floor(value)
    if lower >= value * (1 - 1e-12):
        return lower
    exponent = math.floor(math.log10(lower))
    base = 10.0 ** exponent
    for multiple in (1.0, 2.0, 5.0, 10.0):
        candidate = multiple * base
        if candidate >= value * (1 - 1e-12):
            return candidate
    return value


def scan_plan(y_source_model, *, direction="high", min_subset_size=1,
              target_points=500, max_grid_points=20000):
    """Plan the exact upstream full-span value grid before its support filter.

    ``min_subset_size`` trims eligible subsets, not the initial grid range.
    Budget the full grid so upstream need not downsample before filtering.
    """
    y = _vector(y_source_model)
    if direction not in ("high", "low"):
        raise ValueError("direction must be high or low.")
    if isinstance(min_subset_size, bool) or int(min_subset_size) != min_subset_size:
        raise ValueError("min_subset_size must be an integer.")
    min_subset_size = int(min_subset_size)
    if not 1 <= min_subset_size <= len(y):
        raise ValueError("min_subset_size must be between 1 and n_source.")
    if target_points < 4 or max_grid_points < 4:
        raise ValueError("target_points >= 4 and max_grid_points >= 4 are required.")
    s = np.sort(y if direction == "high" else -y)
    n = len(s)
    _, counts = np.unique(s, return_counts=True)
    start, stop, full_stop = float(s[0]), float(s[-min_subset_size]), float(s[-1])
    span, full_span = stop - start, full_stop - start
    common = {
        "scan_mode": "value", "min_subset_size": min_subset_size,
        "settings_role": "source_only_custom_analysis", "direction": direction,
        "n_source": n, "target_grid_points": int(target_points),
        "max_grid_points": int(max_grid_points),
        "valid_range_scan_space": [start, stop],
        "full_range_scan_space": [start, full_stop],
        "grid_constructed_before_support_filter": True,
        "tie_share": float(counts[counts > 1].sum() / n),
        "largest_tie_share": float(counts.max() / n),
        "unique_target_values": int(len(counts)),
        "automatic_unique_or_quantile_switch": False,
    }
    def unavailable(status, **extra):
        return {**common, "status": status, "scan_step": None,
                "estimated_grid_points": None, "fit_numerically_available": False, **extra}
    if n < 4:
        return unavailable("fewer_than_four_source_records")
    if not math.isfinite(full_span) or not math.isfinite(span):
        return unavailable("nonfinite_range")
    if full_span <= 0 or span <= 0:
        return unavailable("constant_or_truncated_constant_target", estimated_grid_points=1)
    raw_step = span / min(int(target_points), int(max_grid_points) - 2)
    if raw_step <= 0 or not math.isfinite(raw_step):
        return unavailable("unrepresentable_step")
    resolution = max(abs(float(np.spacing(start))), abs(float(np.spacing(full_stop))))
    step = nice_floor(raw_step)
    step = max(step, _nice_ceil(resolution)) if resolution > 0 else step
    # The endpoint-alignment overhead is small, but use the upstream formula
    # below as the authority instead of assuming full_span / step is exact.
    step = max(step, _nice_ceil(full_span / max(1, int(max_grid_points) - 3)))
    def full_grid(st):
        if st <= 0 or not math.isfinite(st) or not math.isfinite(start / st) or not math.isfinite(full_stop / st):
            return None
        lo = math.floor(start / st) * st
        hi = math.ceil(full_stop / st) * st
        count_value = (hi + 0.5 * st - lo) / st
        if not math.isfinite(count_value):
            return None
        raw_n = int(math.floor(count_value)) + 1
        return lo, hi, raw_n
    grid = full_grid(step)
    if grid is None:
        return unavailable("unrepresentable_grid_alignment")
    for _ in range(8):
        if grid[2] <= max_grid_points:
            break
        step = _nice_ceil(step * max(1.01, grid[2] / max_grid_points))
        grid = full_grid(step)
        if grid is None:
            return unavailable("unrepresentable_grid_alignment")
    if grid[2] > max_grid_points:
        return unavailable("grid_budget_unreachable")
    eligible_values = s[s <= stop]
    max_bin_share = None
    refinements = 0
    for _ in range(5):
        bins = np.floor((eligible_values - start) / step)
        _, occupied = np.unique(bins, return_counts=True)
        max_bin_share = float(occupied.max() / n) if len(occupied) else 0.0
        proposed = nice_floor(step / 2.0) if step / 2.0 > 0 else step
        proposed_grid = full_grid(proposed)
        if (max_bin_share <= 0.01 or refinements >= 4 or proposed < resolution
                or proposed >= step or proposed_grid is None
                or proposed_grid[2] > max_grid_points):
            break
        step, grid = proposed, proposed_grid
        refinements += 1
    low, high, raw_n = grid
    thresholds = np.arange(low, high + 0.5 * step, step, dtype=float)
    if len(thresholds) > max_grid_points:
        return unavailable("actual_grid_exceeds_budget", estimated_grid_points=int(len(thresholds)))
    first = np.searchsorted(s, thresholds, side="left")
    subset_counts = n - first
    eligible = (first < n) & (subset_counts >= min_subset_size)
    eligible_n = int(eligible.sum())
    ok = eligible_n >= 4 and len(np.unique(thresholds[eligible])) >= 4
    return {**common, "status": "ready" if ok else "too_few_eligible_thresholds",
            "scan_step": float(step), "estimated_grid_points": int(raw_n),
            "actual_full_grid_points": int(len(thresholds)),
            "eligible_threshold_points": eligible_n,
            "required_eligible_threshold_points": 4,
            "grid_refinements": refinements,
            "source_max_bin_share": max_bin_share, "floating_point_resolution": resolution,
            "fit_numerically_available": ok,
            "scan_min": float(low), "scan_max": float(high),
            "upstream_grid_downsampling_required": False,
            "note": ("Budget covers the full upstream value grid before min-subset filtering. "
                     "Insufficient eligible thresholds are reported; scan mode is never changed silently.")}


def _physical_unit(unit, already_log):
    if already_log:
        match = re.fullmatch(r"\s*log10\s*\((.*)\)\s*", str(unit))
        return match.group(1).strip() if match else None
    return str(unit)


def audit_target(y_source, *, direction, tiers, unit, transform="auto", already_log=False,
                 y_eval=None, min_subset_size=1, target_points=500,
                 max_grid_points=20000, positive_support=20):
    y = _vector(y_source)
    if direction not in ("high", "low"):
        raise ValueError("direction must be high or low.")
    qs = [float(q) for q in tiers]
    if not qs or len(set(qs)) != len(qs) or any(not math.isfinite(q) or not 0 < q < 1 for q in qs):
        raise ValueError("tiers must be unique finite fractions strictly between 0 and 1.")
    if not str(unit).strip():
        raise ValueError("unit must be explicit.")
    if transform not in ("auto", "none", "log10"):
        raise ValueError("transform must be auto, none or log10.")
    if positive_support < 1:
        raise ValueError("positive_support must be positive.")
    if already_log and transform == "log10":
        raise ValueError("Already-log targets cannot be log10-transformed again.")
    source_span_decades = None
    if (y > 0).all():
        p1, p99 = np.quantile(y, [.01, .99])
        source_span_decades = float(np.log10(p99) - np.log10(p1))
    recommendation = ("log10" if not already_log and source_span_decades is not None
                      and source_span_decades >= 2 else "none")
    chosen = recommendation if transform == "auto" else transform
    if already_log:
        chosen = "none"
    ym = apply_transform(y, chosen)
    ev = _vector(y_eval, "evaluation") if y_eval is not None else None
    evm = apply_transform(ev, chosen) if ev is not None else None
    scan = scan_plan(ym, direction=direction, min_subset_size=min_subset_size,
                     target_points=target_points, max_grid_points=max_grid_points)
    model_unit = f"log10({unit})" if chosen == "log10" else str(unit)
    physical_unit = _physical_unit(unit, already_log)
    inverse_kind = "log10" if chosen == "log10" or already_log else "none"
    threshold_rows = []
    for q in qs:
        model_cut = float(np.quantile(ym, 1 - q if direction == "high" else q))
        source_positive = ym >= model_cut if direction == "high" else ym <= model_cut
        row = {"tier": q, "direction": direction,
               "tail": "top" if direction == "high" else "bottom",
               "cutoff_model": model_cut, "cutoff_model_unit": model_unit,
               "cutoff_input": inverse_transform(model_cut, chosen),
               "cutoff_input_unit": str(unit),
               "cutoff_physical": inverse_transform(model_cut, inverse_kind),
               "cutoff_physical_unit": physical_unit,
               "comparison": ">=" if direction == "high" else "<=",
               "n_source": len(ym), "source_positives": int(source_positive.sum()),
               "source_negatives": int((~source_positive).sum()),
               "boundary_tie_count_source": int((ym == model_cut).sum()),
               "support_threshold": int(positive_support),
               "support_threshold_is_diagnostic": True,
               "fit_or_screening_blocked_by_support": False}
        source_classes = bool(source_positive.any() and (~source_positive).any())
        source_positive_support = int(source_positive.sum()) >= positive_support
        source_negative_support = int((~source_positive).sum()) >= positive_support
        source_support = source_positive_support and source_negative_support
        if evm is not None:
            pos = evm >= model_cut if direction == "high" else evm <= model_cut
            evaluation_classes = bool(pos.any() and (~pos).any())
            row.update(n_evaluation=len(evm), evaluation_positives_fixed_train=int(pos.sum()),
                       evaluation_negatives_fixed_train=int((~pos).sum()),
                       boundary_tie_count_evaluation=int((evm == model_cut).sum()),
                       evaluation_has_both_classes=evaluation_classes,
                       evaluation_positive_support_sufficient=int(pos.sum()) >= positive_support,
                       evaluation_negative_support_sufficient=int((~pos).sum()) >= positive_support,
                       evaluation_support_sufficient=min(int(pos.sum()), int((~pos).sum())) >= positive_support)
        else:
            evaluation_classes = None
        row["source_has_both_classes"] = source_classes
        row["source_support_sufficient"] = source_support
        row["source_positive_support_sufficient"] = source_positive_support
        row["source_negative_support_sufficient"] = source_negative_support
        row["evidence_status"] = (
            "single_class_source" if not source_classes else
            "no_evaluation_labels" if evm is None else
            "single_class_evaluation" if not evaluation_classes else
            "limited_positive_support" if not (source_positive_support and row["evaluation_positive_support_sufficient"]) else
            "limited_negative_support" if not (source_negative_support and row["evaluation_negative_support_sufficient"]) else
            "support_check_passed")
        row["interpretation"] = (
            "Counts use the source-frozen numerical threshold. The declared positive/negative support heuristic limits inference, "
            "not rule fitting or candidate screening. Passing this check is not proof of model accuracy.")
        threshold_rows.append(row)
    return {
        "schema": "stca-data-readiness-v1", "target_unit": str(unit),
        "n_source": len(y), "direction": direction, "tiers": qs,
        "transform": chosen, "transform_request": transform,
        "transform_recommendation": recommendation,
        "already_log": bool(already_log),
        "transform_decision_role": "source_only",
        "transform_policy": "positive_source_robust_span_p99_p1_at_least_2_decades",
        "robust_span_decades": source_span_decades,
        "model_unit": model_unit, "physical_unit": physical_unit,
        "evaluation_labels_used_for_settings": False,
        "source_min": float(y.min()), "source_max": float(y.max()),
        "source_median": float(np.median(y)),
        "source_robust_sd": float(1.4826 * np.median(np.abs(y - np.median(y)))),
        "scan": scan, "scan_mode": scan["scan_mode"], "scan_step": scan["scan_step"],
        "min_subset_size": scan["min_subset_size"],
        "tier_readiness": threshold_rows,
        "cleaning_policy": "flag_only_no_deletion_no_aggregation",
    }


def _record_diagnostics(records, *, source_mask, target, smiles_column=None,
                        calculation_smiles_column=None, id_column=None,
                        metadata_columns=(), condition_columns=()):
    report = {"rows": len(records), "rows_deleted": 0, "rows_aggregated": 0,
              "processing_flags": [], "duplicate_groups": [], "source_target_outlier_rows": [],
              "identity_basis": "preserved_original_connection_point_smiles_and_condition_columns"}
    for i, record in enumerate(records):
        matches = {col: PROCESSING_PATTERN.findall(record[col]) for col in metadata_columns
                   if PROCESSING_PATTERN.search(record[col])}
        if matches:
            report["processing_flags"].append({"row_position": i, "matched_columns": matches,
                                                "action": "flag_only"})
    if id_column:
        ids = [r[id_column] for r in records]
        report["identifiers"] = {"column": id_column, "used_as_feature": False,
                                 "empty_rows": [i for i, v in enumerate(ids) if not v.strip()],
                                 "duplicate_values": [x for x, n in Counter(ids).items() if n > 1]}
    else:
        report["identifiers"] = {"column": None, "used_as_feature": False,
                                 "row_positions_preserved": True}
    if smiles_column:
        groups = defaultdict(list)
        for i, row in enumerate(records):
            # Original connection-point text remains authoritative. This layer
            # deliberately does not merge different originals sharing an H-cap.
            key = tuple([row[smiles_column]] + [row[c] for c in condition_columns])
            groups[key].append(i)
        for key, indices in groups.items():
            if len(indices) < 2:
                continue
            values = [float(records[i][target]) for i in indices]
            report["duplicate_groups"].append({"original_smiles": key[0],
                "conditions": dict(zip(condition_columns, key[1:])), "rows": indices,
                "distinct_values": len(set(values)), "range": [min(values), max(values)],
                "action": "flag_only", "roles_overlap": len({bool(source_mask[i]) for i in indices}) > 1})
        if calculation_smiles_column:
            hcaps = defaultdict(set)
            for r in records:
                hcaps[r[calculation_smiles_column]].add(r[smiles_column])
            report["hcap_collisions"] = [{"calculation_smiles": h, "originals": sorted(v),
                "action": "do_not_merge"} for h, v in hcaps.items() if len(v) > 1]
    ys = np.array([float(row[target]) for row, flag in zip(records, source_mask) if flag])
    centre = float(np.median(ys)); sd = float(1.4826 * np.median(np.abs(ys - centre)))
    if sd > 0:
        report["source_target_outlier_rows"] = [i for i, (r, flag) in enumerate(zip(records, source_mask))
            if flag and abs(float(r[target]) - centre) > 4 * sd]
    report["outlier_policy"] = "source_global_MAD_flag_only; no neighbour-based exclusion"
    report["condition_columns"] = list(condition_columns)
    return report


def build_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True); p.add_argument("--target", required=True)
    p.add_argument("--unit", required=True); p.add_argument("--direction", choices=("high", "low"), required=True)
    p.add_argument("--tiers", required=True, help="Comma-separated fractions, e.g. 0.30,0.20,0.10")
    p.add_argument("--role-column"); p.add_argument("--source-value", default="train")
    p.add_argument("--evaluation-value", default="test")
    p.add_argument("--transform", choices=("auto", "none", "log10"), default="auto")
    p.add_argument("--already-log", action="store_true")
    p.add_argument("--min-subset-size", type=int, default=1)
    p.add_argument("--target-points", type=int, default=500)
    p.add_argument("--max-grid-points", type=int, default=20000)
    p.add_argument("--positive-support", type=int, default=20)
    p.add_argument("--id-column"); p.add_argument("--smiles-column")
    p.add_argument("--calculation-smiles-column")
    p.add_argument("--metadata-columns", default="", help="Comma-separated free-text columns, flag only")
    p.add_argument("--condition-columns", default="", help="Comma-separated conditions kept in replicate identity")
    p.add_argument("--output", required=True)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        path, raw, header, records = read_csv_records(args.input)
        if not records:
            raise ValueError("CSV contains no records.")
        meta = [x.strip() for x in args.metadata_columns.split(",") if x.strip()]
        cond = [x.strip() for x in args.condition_columns.split(",") if x.strip()]
        required = [args.target] + meta + cond + [v for v in
            (args.role_column, args.id_column, args.smiles_column, args.calculation_smiles_column) if v]
        missing = set(required) - set(header)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        values = _vector([row[args.target] for row in records], "input")
        if args.role_column:
            if args.source_value == args.evaluation_value:
                raise ValueError("Source and evaluation role values must differ.")
            roles = [row[args.role_column] for row in records]
            unknown = set(roles) - {args.source_value, args.evaluation_value}
            if unknown:
                raise ValueError(f"Unmapped role values: {sorted(unknown)}; declare a two-role input explicitly.")
            source_mask = np.array([r == args.source_value for r in roles])
            eval_mask = ~source_mask
        else:
            source_mask = np.ones(len(records), dtype=bool)
            eval_mask = np.zeros(len(records), dtype=bool)
        report = audit_target(values[source_mask], direction=args.direction,
            tiers=[float(q.strip()) for q in args.tiers.split(",")], unit=args.unit,
            transform=args.transform, already_log=args.already_log,
            y_eval=values[eval_mask] if eval_mask.any() else None,
            min_subset_size=args.min_subset_size, target_points=args.target_points,
            max_grid_points=args.max_grid_points, positive_support=args.positive_support)
        report.update(target_column=args.target, input_sha256=hashlib.sha256(raw).hexdigest(),
                      role_column=args.role_column, source_value=args.source_value,
                      evaluation_value=args.evaluation_value,
                      diagnostics=_record_diagnostics(records, source_mask=source_mask,
                          target=args.target, smiles_column=args.smiles_column,
                          calculation_smiles_column=args.calculation_smiles_column,
                          id_column=args.id_column, metadata_columns=meta, condition_columns=cond))
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as h:
            json.dump(report, h, ensure_ascii=False, indent=2, allow_nan=False); h.write("\n")
        print(json.dumps({"output": str(output), "status": report["scan"]["status"],
                          "transform": report["transform"], "source_only_settings": True}))
        return 0
    except (ValueError, OSError, TypeError) as exc:
        print(f"stca-data-readiness: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
