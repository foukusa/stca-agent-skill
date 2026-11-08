#!/usr/bin/env python3
"""Prepare traceable full-data STCA analyses with the author's pinned learner.

``prepare_dataset`` returns data/audit/row_mapping/excluded_rows/tier_table and
optionally writes their CSV/JSON files. This is a full modelling-data preparation
policy: label-dependent D3/D4/D7 decisions precede subsequent CV. Such CV is
conditional on the prepared data, not an unbiased end-to-end validation. Use the
existing auto_screen workflow for explicit protected source/holdout analyses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REGISTRY = HERE.parent / "assets" / "property_registry.json"
OUTPUT_NAMES = ("cleaned.csv", "audit.json", "tier_table.csv", "row_mapping.csv", "excluded_rows.csv")
DERIVED = {"SMILES", "stca_calculation_smiles_hcap", "hcap_canon", "original_canon", "protected_group",
           "y_model", "y", "RecordKey", "n_measurements", "n_measurements_before_D4", "metadata",
           "flag_neighbour_inconsistent", "flag_implausible", "split", "nested", "ecfp4_cluster",
           "input_row_position", "prepared_record_key", "preparation_status", "preparation_reason",
           "used_for_aggregate", "representative_input_row_position"}


def _json_value(value):
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist())
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    return value


def _columns(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = value.split(",")
    return list(dict.fromkeys(str(c).strip() for c in value if str(c).strip()))


def _bibliographic_column(name):
    normalized = re.sub(r"[\s_-]+", "", str(name)).casefold()
    return normalized in {"reference", "references", "citation", "citations", "doi", "journal",
                          "bibliography", "publication", "参考文献", "文献来源", "期刊", "论文链接"}


def rsd(values):
    x = np.asarray(values, dtype=float)
    return 1.4826 * float(np.median(np.abs(x - np.median(x)))) if len(x) else 0.0


def nice_floor(value):
    from data_readiness import nice_floor as implementation
    return implementation(value)


def scan_step(y_src, min_sub):
    """Compatibility helper; unavailable small/constant data return None.

    The existing bounded planner checks the author's full initial grid, including
    tied targets; no unbounded histogram allocation or synthetic step is used.
    """
    from data_readiness import scan_plan
    y = np.asarray(y_src, dtype=float)
    if not len(y) or not 1 <= int(min_sub) <= len(y):
        return None, False
    plan = scan_plan(y, direction="high", min_subset_size=int(min_sub))
    return plan["scan_step"], bool(plan.get("step_hit_halving_cap", False))


def tsne_outer(fps, frac=0.2, seed=42):
    """Compatibility helper with explicit small-data failure, never a fallback."""
    from auto_screen import tsne_peripheral_split
    if frac != 0.2 or seed != 42:
        raise ValueError("The recorded automatic split uses frac=0.2 and seed=42.")
    _, outer, _, _ = tsne_peripheral_split(fps, np.arange(len(fps)), list(range(len(fps))), scope="preparation")
    mask = np.zeros(len(fps), dtype=bool)
    mask[outer] = True
    return mask


def stca_fit(X, y, groups, direction, min_sub, tiers, *, source=None,
             target_name="target", target_unit="model", provenance=None):
    """Configure the pinned STCA learner; leave its algorithm and selector intact."""
    from stca_runtime import load_stca
    load_stca(source)
    from stca.training import STCA
    from stca.scan import ScanConfig
    from stca.chemistry import MACCS_NAMES, MACCS_SPEC
    from data_readiness import scan_plan
    y = np.asarray(y, dtype=float)
    plan = scan_plan(y, direction=direction, min_subset_size=int(min_sub))
    if not plan["fit_numerically_available"]:
        raise ValueError(f"STCA fit unavailable: {plan['status']}")
    trainer = STCA(direction=direction, tiers=tuple(tiers),
                   scan=ScanConfig(mode="value", step=plan["scan_step"], min_subset_size=int(min_sub), max_points=20000),
                   max_rank=10, family_size=8, target_name=target_name, target_unit=target_unit,
                   selection="source_as", protocol_id="custom_source_f1_as_v1")
    return trainer.fit(X.reset_index(drop=True), y, feature_names_=MACCS_NAMES, feature_spec=MACCS_SPEC,
                       groups=np.asarray(groups), provenance=provenance)


def rule_sets(model, tiers):
    result = []
    for q in tiers:
        table = model.rules(tier=q)
        selected = table[table.selected == True] if "selected" in table else table.iloc[0:0]
        result.append(set(str(selected.expression.iloc[0]).split(" AND ")) if len(selected) else set())
    return result


def _rule_change(before, after):
    # Two absent rules carry no evidence of a changed literal set.
    values = [1 - len(a & b) / len(a | b) if a | b else 0.0 for a, b in zip(before, after)]
    return float(np.mean(values)) if values else None


def _property_config(name, unit, registry):
    def token(value):
        return re.sub(r"[\s_-]+", " ", str(value or "").casefold()).strip()
    query = token(name)
    matches = [key for key, value in registry["properties"].items()
               if query == token(key) or query in [token(a) for a in value.get("aliases", [])]]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous property alias {name!r}.")
    aliases = registry.get("unit_aliases", {})
    supplied = aliases.get(unit, unit) if unit is not None else None
    if query == "conductivity" and not matches:
        if supplied in ("S/cm", "S/m"):
            matches = ["electrical_conductivity"]
        elif supplied == "W/(m K)":
            matches = ["thermal_conductivity"]
    if matches:
        key = matches[0]
        profile = dict(registry["properties"][key])
        canonical_unit = profile["unit"]
        supplied = supplied or canonical_unit
        conversion = (1.0, 0.0) if supplied == canonical_unit else profile.get("from_units", {}).get(supplied)
        if conversion is None:
            raise ValueError(f"No registered conversion from {unit!r} to {canonical_unit!r} for {key}.")
        return key, profile, supplied, tuple(conversion), "registered"
    supplied = supplied or "unspecified"
    return str(name or "custom_property"), {"unit": supplied, "log_scale": False,
                                           "plausible_range": None}, supplied, (1.0, 0.0), "unregistered_custom"


def _features(data, source):
    from stca_runtime import load_stca
    load_stca(source)
    from stca.chemistry import maccs_from_smiles, MACCS_NAMES
    values, _ = maccs_from_smiles(data.stca_calculation_smiles_hcap.tolist())
    return pd.DataFrame(np.asarray(values), columns=MACCS_NAMES)


def _scan_settings(data, fps, direction, tiers, source):
    """Archive-style inner selection, explicitly conditional on prepared data."""
    from auto_screen import tsne_peripheral_split
    from data_readiness import scan_plan
    n = len(data)
    base = {"min_subset_size": 1, "value_step": None, "step_hit_halving_cap": False,
            "selection_status": "unavailable", "candidates": [],
            "settings_selected_before_cv": True, "settings_scope": "full_prepared_data_inner_roles",
            "inner_mcc_min_subset_1": None, "inner_mcc_min_subset_5pct": None}
    data["split"] = "unassigned"
    data["nested"] = "unassigned"
    if not n:
        return base, {}
    components = data.protected_group.tolist()
    reports = {}
    try:
        train, outer, _, reports["outer"] = tsne_peripheral_split(fps, np.arange(n), components, scope="optional_extrapolation")
        data.loc[train, "split"] = "train"
        data.loc[outer, "split"] = "test"
        data.loc[outer, "nested"] = "outer"
    except (ValueError, RuntimeError) as exc:
        train = np.arange(n)
        reports["outer"] = {"status": "unavailable", "reason": str(exc), "no_fallback_split": True}
    try:
        it, iv, _, reports["inner"] = tsne_peripheral_split(fps, train, components, scope="preparation_inner")
        data.loc[it, "nested"] = "pseudo_source"
        data.loc[iv, "nested"] = "pseudo_extrapolation"
        X = _features(data, source)
        y = data.y_model.to_numpy()
        groups = data.protected_group.to_numpy()
        minimum = max(10, math.ceil(0.5 * min(tiers) * len(it)))
        candidates = list(dict.fromkeys((1, minimum)))
        valid = {}
        for size in candidates:
            record = {"min_subset_size": size, "status": "unavailable", "mean_mcc": None, "tiers": []}
            try:
                model = stca_fit(X.iloc[it], y[it], groups[it], direction, size, tiers, source=source)
                metrics = {}
                for tier in tiers:
                    item = {"tier": tier, "status": "unavailable", "mcc": None}
                    try:
                        result = model.evaluate(X.iloc[iv].reset_index(drop=True), y[iv], tier=tier,
                                                groups=groups[iv], cutoff_mode="fixed_train")
                        positive = int(result["positive_n"])
                        selected = int(result["selected_n"])
                        if 0 < positive < len(iv) and 0 < selected < len(iv):
                            item.update(status="evaluated", mcc=float(result["mcc"]))
                            metrics[tier] = item["mcc"]
                        else:
                            item["reason"] = "undefined_MCC_single_truth_class_or_constant_prediction"
                    except (ValueError, RuntimeError) as exc:
                        item["reason"] = str(exc)
                    record["tiers"].append(item)
                record["status"] = "fitted"
                valid[size] = metrics
            except (ValueError, RuntimeError) as exc:
                record["reason"] = str(exc)
                valid[size] = {}
            base["candidates"].append(record)
        common = set.intersection(*(set(v) for v in valid.values())) if valid else set()
        base["common_defined_tiers"] = sorted(common)
        if common:
            means = {size: float(np.mean([v[q] for q in common])) for size, v in valid.items()}
            for record in base["candidates"]:
                record["mean_mcc"] = means[record["min_subset_size"]]
            base["inner_mcc_min_subset_1"] = means[1]
            base["inner_mcc_min_subset_5pct"] = means.get(minimum)
            base["selection_status"] = "inner_comparison"
            if len(candidates) == 2 and means[minimum] - means[1] >= 0.05:
                base["min_subset_size"] = max(10, math.ceil(0.5 * min(tiers) * len(data)))
                base["selected_policy"] = "half_strictest_tier_count"
            else:
                base["selected_policy"] = "minimum_1"
        else:
            base["reason"] = "No common defined inner MCC; preserve prespecified minimum=1, no synthetic zero score."
    except (ValueError, RuntimeError) as exc:
        reports["inner"] = {"status": "unavailable", "reason": str(exc), "no_fallback_split": True}
        base["reason"] = str(exc)
    size = int(base["min_subset_size"])
    try:
        plan = scan_plan(data.y_model.to_numpy(), direction=direction, min_subset_size=size)
    except ValueError as exc:
        plan = {"status": "unavailable", "scan_step": None, "fit_numerically_available": False, "reason": str(exc)}
    base.update(value_step=plan["scan_step"], scan_plan=plan,
                step_hit_halving_cap=bool(plan.get("step_hit_halving_cap", False)))
    return base, reports


def tier_table(ym, srcm, outer, cid, tiers, direction, transform, unit):
    """Separate full-data deployment cutoffs from optional role-based cutoffs."""
    ym = np.asarray(ym, dtype=float)
    s = ym if direction == "high" else -ym
    srcm, outer = np.asarray(srcm, bool), np.asarray(outer, bool)
    rows = []
    for q in tiers:
        cutoff = float(np.quantile(s, 1 - q)) if len(s) else None
        source_cut = float(np.quantile(s[srcm], 1 - q)) if srcm.any() else None
        sign = 1 if direction == "high" else -1
        def physical(value):
            if value is None:
                return None
            value = sign * value
            return float(10 ** value) if transform == "log10" else value
        pos = int((s >= cutoff).sum()) if cutoff is not None else 0
        source_positive = int((s[srcm] >= source_cut).sum()) if source_cut is not None else 0
        held = outer & (s >= source_cut) if source_cut is not None else np.zeros(len(s), bool)
        share = float(pd.Series(np.asarray(cid)[held]).value_counts().iloc[0] / held.sum()) if held.any() else None
        rows.append({"tier": q, "rule": f"{'top' if direction == 'high' else 'bottom'} {q*100:g}%",
                     "comparator": ">=" if direction == "high" else "<=", "unit": unit,
                     "cutoff_model_space": sign * cutoff if cutoff is not None else None,
                     "cutoff_physical": physical(cutoff), "positives": pos,
                     "inrange_cv_evaluable": bool(pos >= 20), "support_threshold_is_heuristic": True,
                     "deployment_cutoff_policy": "full_prepared_data_quantile",
                     "cv_threshold_policy": "training_fold_quantile_not_deployment_fixed_cutoff",
                     "source_cutoff_physical": physical(source_cut), "source_positives": source_positive,
                     "extrapolation_positives": int(held.sum()), "extrapolation_top_cluster_share": share,
                     "extrapolation_evaluable": bool(source_positive >= 20 and held.sum() >= 20),
                     "evaluation_scope": "conditional_on_full_data_preparation"})
    return rows


def prepare_dataset(input, *, smiles_column="SMILES", target, property_name=None, property=None, target_name=None,
                    output_dir=None, unit=None, already_log=False, direction="high", tiers=(0.30, 0.20, 0.10),
                    id_column=None, condition_columns=(), text_columns=(), skip_influence=False,
                    source=None, fingerprint_radius=2):
    """Return traceable prepared data plus audits; IDs never determine row joins.

    ``input`` is an original CSV path. ``condition_columns`` and ``text_columns``
    accept a sequence or comma-separated string. Empty text_columns scans no
    metadata. D4 combines equal canonical original units with equal explicit
    conditions, or equal other original metadata when no conditions are declared.
    H-cap collisions protect groups, never merge records.
    ``property`` is a compatibility alias for ``property_name``. Explicit held-out
    data should be handled by auto_screen instead of this full-data API.
    """
    from rdkit import Chem, DataStructs, rdBase
    from rdkit.Chem import rdFingerprintGenerator
    from rdkit.ML.Cluster import Butina
    from auto_screen import read_auto_frame, protected_components
    from prepare_hcap import hcap_smiles

    if direction not in ("high", "low"):
        raise ValueError("direction must be high or low.")
    tiers = tuple(float(q) for q in (tiers.split(",") if isinstance(tiers, str) else tiers))
    if not tiers or len(set(tiers)) != len(tiers) or any(not math.isfinite(q) or not 0 < q < 1 for q in tiers):
        raise ValueError("Specify distinct finite tier fractions strictly between zero and one.")
    if fingerprint_radius != 2:
        raise ValueError("This pipeline uses ECFP4 radius=2, bits=2048 for reproducible group diagnostics.")
    if property_name is not None and property is not None and property_name != property:
        raise ValueError("property_name and property disagree.")
    frame, format_audit = read_auto_frame(input)
    def resolve(name):
        if name is None or name in frame:
            return name
        name = name.strip()
        matches = [a["normalized_header"] for a in format_audit["column_alias_map"] if a["original_header"] == name]
        return matches[0] if len(matches) == 1 else name
    smiles_column, target, id_column = [resolve(c) for c in (smiles_column, target, id_column)]
    conditions = [resolve(c) for c in _columns(condition_columns)]
    textcols = [resolve(c) for c in _columns(text_columns)]
    required = {smiles_column, target, *conditions, *textcols}
    if id_column:
        required.add(id_column)
    if required - set(frame):
        raise ValueError(f"Missing columns: {sorted(required-set(frame))}")
    # Bibliography is provenance, not evidence about sample processing history.
    ignored_bibliography = [c for c in textcols if _bibliographic_column(c)]
    scanned_text = [c for c in textcols if c not in (id_column, smiles_column, target)
                    and c not in ignored_bibliography]
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    requested_property = property_name or property or target_name or target
    candidates = list(dict.fromkeys(c for c in (property_name, property, target_name, target) if c))
    key = profile = input_unit = conversion = registration = None
    for candidate in candidates:
        selected = _property_config(candidate, unit, registry)
        if selected[-1] == "registered":
            key, profile, input_unit, conversion, registration = selected
            break
    if registration is None:
        key, profile, input_unit, conversion, registration = _property_config(requested_property, unit, registry)
    canonical_unit = profile["unit"]
    occupied = set(frame)
    renames = {}
    for column in frame:
        if column in DERIVED or column.startswith("stca_"):
            candidate, suffix = "archive_" + column, 2
            while candidate in occupied:
                candidate = f"archive_{column}_{suffix}"
                suffix += 1
            occupied.add(candidate)
            renames[column] = candidate
    archival = frame.rename(columns=renames).copy()
    archived = lambda column: renames.get(column, column)
    audit = {"schema": "stca-auto-data-layer-v2", "property": key, "property_registration": registration,
             "unit": canonical_unit, "input_unit": input_unit, "input_rows": len(frame), "direction": direction,
             "input_format_audit": format_audit, "reserved_column_renames": renames,
             "input_field_mapping": {"smiles_column": archived(smiles_column), "target": archived(target),
                                     "id_column": archived(id_column) if id_column else None,
                                     "condition_columns": [archived(c) for c in conditions],
                                     "text_columns": [archived(c) for c in scanned_text]},
             "processing_metadata_audit": {"requested_columns": textcols,
                                           "scanned_columns": scanned_text,
                                           "ignored_bibliographic_columns": ignored_bibliography,
                                           "reason": "Bibliographic titles are not sample processing descriptions."},
             "row_identity": "zero_based_input_row_position_never_ID", "original_values_preserved_as_text": True,
             "original_smiles_preserved_exactly": True, "full_data_label_dependent_preparation": True,
             "evaluation_scope": "conditional_on_full_data_D3_D4_D7_preparation",
             "end_to_end_unbiased_cv_claim": False, "explicit_holdout_workflow": "auto_screen.py",
             "registry_schema": registry["schema"], "registry_sha256": hashlib.sha256(REGISTRY.read_bytes()).hexdigest(),
             "requested_property": requested_property, "measurement_semantics": profile.get("measurement_semantics"),
             "unit_status": "not_supplied_for_unregistered_property" if canonical_unit == "unspecified" else "declared_or_registered",
             "plausibility_bounds_are_heuristic": True, "already_log": bool(already_log),
             "unit_conversion": {"input_unit": input_unit, "physical_unit": canonical_unit,
                                 "multiplier": conversion[0], "offset": conversion[1],
                                 "order": "inverse_log10_if_requested_then_physical_unit_conversion_then_model_transform"}}
    raw = pd.to_numeric(frame[target], errors="coerce").to_numpy(dtype=float)
    with np.errstate(over="ignore", invalid="ignore"):
        physical = np.power(10.0, raw) if already_log else raw.copy()
        physical = physical * conversion[0] + conversion[1]
    reasons = [[] for _ in range(len(frame))]
    originals, caps, cap_ids = [], [], []
    with rdBase.BlockLogs():
        for i, smiles in enumerate(frame[smiles_column]):
            original = cap = cap_id = ""
            if not np.isfinite(physical[i]):
                reasons[i].append("nonfinite_or_nonnumeric_target_after_unit_conversion")
            elif profile["log_scale"] and physical[i] <= 0:
                reasons[i].append("nonpositive_for_registered_log_scale")
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None or mol.GetNumAtoms() == 0:
                    raise ValueError("invalid_original_structure")
                original = Chem.MolToSmiles(mol, canonical=True)
                cap, _ = hcap_smiles(smiles)
                cap_id = Chem.MolToSmiles(Chem.MolFromSmiles(cap), canonical=True)
            except (ValueError, RuntimeError):
                reasons[i].append("structure_or_attachment_point")
            originals.append(original)
            caps.append(cap)
            cap_ids.append(cap_id)
    if scanned_text:
        pattern = re.compile("|".join(registry["processing_keywords"]), re.I)
        texts = frame[scanned_text].agg(" | ".join, axis=1).tolist()
        for i, value in enumerate(texts):
            if pattern.search(value):
                reasons[i].append("processing_history_scope_exclusion")
    else:
        texts = [""] * len(frame)
    valid = np.asarray([not why for why in reasons], dtype=bool)
    yy = physical[valid]
    transform = "log10" if profile["log_scale"] else "none"
    if not profile["log_scale"] and len(yy) and (yy > 0).all():
        ratio = float(np.log10(np.quantile(yy, .99)) - np.log10(np.quantile(yy, .01)))
        if ratio >= 2:
            transform = "log10"
    model_y = np.full(len(frame), np.nan)
    model_y[valid] = np.log10(physical[valid]) if transform == "log10" else physical[valid]
    audit["D3_transform"] = transform
    audit["D3_transform_fit_scope"] = "full_valid_modelling_data"
    finite_raw = raw[np.isfinite(raw)]
    audit["input_target_diagnostics"] = {
        "finite_input_n": int(len(finite_raw)),
        "input_numeric_min": float(finite_raw.min()) if len(finite_raw) else None,
        "input_numeric_max": float(finite_raw.max()) if len(finite_raw) else None,
        "valid_physical_min_before_D4_D7": float(yy.min()) if len(yy) else None,
        "valid_physical_max_before_D4_D7": float(yy.max()) if len(yy) else None,
        "valid_physical_p01": float(np.quantile(yy, .01)) if len(yy) else None,
        "valid_physical_p99": float(np.quantile(yy, .99)) if len(yy) else None,
        "extremes_alone_are_not_exclusions": True,
    }
    audit["D2_text_columns"] = scanned_text
    audit["D2_configured_ID_column_excluded"] = id_column
    from collections import Counter
    audit["D1_D2_excluded"] = dict(Counter(r for why in reasons for r in why))
    mappings = archival.copy()
    mappings["input_row_position"] = np.arange(len(frame))
    mappings["prepared_record_key"] = ""
    mappings["preparation_status"] = ["excluded" if why else "pending" for why in reasons]
    mappings["preparation_reason"] = [";".join(why) for why in reasons]
    mappings["used_for_aggregate"] = False
    # D4: absent declared conditions, conservatively compare every other original
    # metadata cell. IDs and original SMILES spellings do not define conditions.
    aggregate_conditions = conditions or [c for c in frame if c not in (smiles_column, target, id_column)]
    # Original fields resembling generated/internal columns are still original
    # metadata. Their values are retained and compared instead of guessed away.
    buckets = {}
    for i in np.flatnonzero(valid):
        signature = (originals[i], *(frame.iloc[i][c] for c in aggregate_conditions))
        buckets.setdefault(signature, []).append(int(i))
    diffs = [float(np.ptp(model_y[positions])) for positions in buckets.values() if len(positions) > 1]
    floor = max(rsd(model_y[valid]) * 0.1, float(np.median(diffs)) if diffs else 0.0)
    records, dropped = [], 0
    for j, positions in enumerate(buckets.values()):
        identity = f"R{j:06d}"
        values = model_y[positions]
        keep = np.ones(len(positions), dtype=bool)
        if len(values) >= 3:
            keep = np.abs(values - np.median(values)) <= 3 * max(rsd(values), floor)
        retained = np.asarray(positions)[keep]
        if not len(retained):
            raise RuntimeError("D4 unexpectedly removed an entire replicate group.")
        first = int(retained[0])
        value = float(np.median(values[keep]))
        record = archival.iloc[first].to_dict()
        record.update(SMILES=frame.iloc[first][smiles_column], stca_calculation_smiles_hcap=caps[first],
                      hcap_canon=cap_ids[first], original_canon=originals[first], y_model=value,
                      y=float(10 ** value) if transform == "log10" else value, RecordKey=identity,
                      n_measurements=int(keep.sum()), n_measurements_before_D4=len(positions), metadata=texts[first],
                      representative_input_row_position=first)
        records.append(record)
        for position, kept in zip(positions, keep):
            mappings.loc[position, "prepared_record_key"] = identity
            mappings.loc[position, "preparation_status"] = "retained" if kept else "D4_excluded"
            mappings.loc[position, "preparation_reason"] = "" if kept else "replicate_outlier_same_original_and_conditions"
            mappings.loc[position, "used_for_aggregate"] = bool(kept)
            dropped += int(not kept)
    fixed_columns = ["SMILES", "stca_calculation_smiles_hcap", "hcap_canon", "original_canon", "y_model", "y",
                     "RecordKey", "n_measurements", "n_measurements_before_D4", "metadata", "representative_input_row_position"]
    data = pd.DataFrame(records, columns=list(archival.columns) + fixed_columns)
    data["protected_group"] = protected_components(data.original_canon.tolist(), data.hcap_canon.tolist())
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = [generator.GetFingerprint(Chem.MolFromSmiles(s)) for s in data.stca_calculation_smiles_hcap]
    n = len(data)
    ym = data.y_model.to_numpy(dtype=float)
    residual = np.full(n, np.nan)
    # Repeated measurement conditions of one structure do not count as independent neighbours.
    for i in range(n):
        sims = np.asarray(DataStructs.BulkTanimotoSimilarity(fps[i], fps))
        sims[data.protected_group.to_numpy() == data.protected_group.iloc[i]] = -1
        neighbours, seen = [], set()
        for j in np.argsort(-sims, kind="stable"):
            if sims[j] < 0.5 or len(neighbours) >= 5:
                break
            group = data.protected_group.iloc[j]
            if group not in seen:
                neighbours.append(j)
                seen.add(group)
        if len(neighbours) >= 2:
            residual[i] = ym[i] - np.median(ym[neighbours])
    observed = np.isfinite(residual)
    residual_scale = rsd(residual[observed]) if observed.sum() > 10 else None
    data["flag_neighbour_inconsistent"] = (observed & (np.abs(np.nan_to_num(residual)) > 4 * residual_scale)
                                            if residual_scale is not None and residual_scale > 0 else False)
    plausible = profile.get("plausible_range")
    data["flag_implausible"] = ((data.y < plausible[0]) | (data.y > plausible[1])) if plausible else False
    audit.update(D4_replicate_measurements_dropped=dropped, D4_replicate_scale_floor=floor,
                 D4_aggregation_identity="canonical_original_repeat_unit_and_exact_declared_conditions",
                 D4_condition_columns=aggregate_conditions, D4_explicit_condition_columns=conditions,
                 D4_condition_policy="explicit_columns" if conditions else "all_other_original_metadata_exact_match",
                 D4_hcap_aggregation=False,
                 D5_flagged=int(data.flag_neighbour_inconsistent.sum()), D5_residual_scale=residual_scale,
                 D6_flagged=int(data.flag_implausible.sum()), D6_plausible_range=plausible)
    quarantine, influence = [], {"enabled": not skip_influence, "scope": "full_prepared_modelling_data",
                                 "threshold": 0.3, "candidates": [], "status": "not_run"}
    if n and not skip_influence:
        signed = ym if direction == "high" else -ym
        eligible = np.flatnonzero((signed >= np.quantile(signed, 1 - min(tiers))) & data.flag_implausible.to_numpy())
        influence["status"] = "no_eligible_tail_records" if not len(eligible) else "evaluated"
        if len(eligible):
            try:
                X = _features(data, source)
                reference = rule_sets(stca_fit(X, ym, data.protected_group.to_numpy(), direction, 1, tiers, source=source), tiers)
                for position in eligible:
                    record = {"RecordKey": data.RecordKey.iloc[position], "prepared_position_before_D7": int(position),
                              "value": float(data.y.iloc[position]), "status": "unavailable", "rule_change": None}
                    keep = np.arange(n) != position
                    try:
                        changed = rule_sets(stca_fit(X.loc[keep], ym[keep], data.protected_group.to_numpy()[keep],
                                                     direction, 1, tiers, source=source), tiers)
                        difference = _rule_change(reference, changed)
                        record.update(status="evaluated", rule_change=difference)
                        if difference is not None and difference >= 0.3:
                            record["status"] = "quarantined"
                            quarantine.append(record.copy())
                    except (ValueError, RuntimeError) as exc:
                        record["reason"] = str(exc)
                    influence["candidates"].append(record)
            except (ValueError, RuntimeError) as exc:
                influence.update(status="unavailable", reason=str(exc))
    audit["D7_influence"] = influence
    audit["D7_quarantined"] = quarantine
    quarantined_keys = {r["RecordKey"] for r in quarantine}
    for identity in quarantined_keys:
        rows = mappings.prepared_record_key.eq(identity) & mappings.used_for_aggregate
        mappings.loc[rows, "preparation_status"] = "D7_quarantined"
        mappings.loc[rows, "preparation_reason"] = "implausible_tail_and_rule_literal_influence_at_least_0.3"
        mappings.loc[rows, "used_for_aggregate"] = False
    keep = ~data.RecordKey.isin(quarantined_keys).to_numpy()
    data = data.loc[keep].reset_index(drop=True)
    fps = [fp for fp, retained in zip(fps, keep) if retained]
    data["protected_group"] = protected_components(data.original_canon.tolist(), data.hcap_canon.tolist())
    settings, splits = _scan_settings(data, fps, direction, tiers, source)
    audit["C1_scan"], audit["split_audit"] = settings, splits
    # Butina's labels are descriptive diagnostics; the protected grouping above owns folds.
    distances = []
    for i in range(1, len(data)):
        distances.extend(1 - x for x in DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i]))
    clusters = np.zeros(len(data), dtype=int)
    if len(data):
        for group, members in enumerate(Butina.ClusterData(distances, len(data), 0.6, isDistData=True)):
            for position in members:
                clusters[position] = group
    data["ecfp4_cluster"] = clusters
    source_mask = data.split.eq("train").to_numpy()
    outer_mask = data.split.eq("test").to_numpy()
    tiers_table = tier_table(data.y_model.to_numpy(dtype=float), source_mask, outer_mask, clusters,
                             tiers, direction, transform, canonical_unit)
    evaluation_output = (Path(output_dir).expanduser().resolve() if output_dir is not None
                         else Path.cwd()) / "evaluation"
    evaluation_argv = [sys.executable, str(HERE / "agent_runtime.py"), "run", "--script",
                       "inrange_evaluation.py", "--", "--input", str(Path(input).expanduser().resolve()),
                       "--target", target, "--smiles-column", smiles_column, "--property", key,
                       "--direction", direction, "--tiers", *[str(q) for q in tiers],
                       "--output-dir", str(evaluation_output)]
    for flag, value in (("--target-name", target_name), ("--unit", unit), ("--id-column", id_column),
                        ("--source", source)):
        if value is not None:
            evaluation_argv.extend((flag, str(value)))
    for flag, values in (("--metadata-columns", scanned_text), ("--condition-columns", conditions)):
        if values:
            evaluation_argv.extend((flag, *values))
    if already_log:
        evaluation_argv.append("--already-log")
    if skip_influence:
        evaluation_argv.append("--skip-influence")
    audit.update(tiers=tiers_table, structures_after_cleaning=len(data), prepared_observations=len(data),
                 unique_original_structures=int(data.original_canon.nunique()),
                 legacy_structures_after_cleaning_counts_prepared_observations=True,
                 retained_input_measurements=int(mappings.used_for_aggregate.sum()),
                 excluded_input_measurements=int((~mappings.used_for_aggregate).sum()),
                 extrapolation_records=int(outer_mask.sum()), protected_groups=int(data.protected_group.nunique()),
                 fingerprint={"family": "Morgan", "radius": 2, "bits": 2048, "input": "calculation_only_hcap"},
                 group_protection="union_of_canonical_original_and_canonical_hcap_without_observation_merge",
                 hcap_collision_groups=int((data.groupby("hcap_canon").original_canon.nunique() > 1).sum()),
                 extreme_value_diagnostics={"physical_min": float(data.y.min()) if len(data) else None,
                                            "physical_max": float(data.y.max()) if len(data) else None,
                                            "D5_D6_are_flags_only": True},
                 status="prepared" if len(data) else "no_usable_observations",
                 recommended_evaluation_argv=evaluation_argv,
                 recommended_evaluation_command=shlex.join(evaluation_argv))
    excluded = mappings.loc[~mappings.used_for_aggregate].copy()
    tables = pd.DataFrame(tiers_table)
    paths = {}
    if output_dir is not None:
        output = Path(output_dir).expanduser().resolve()
        if any((output / name).exists() for name in OUTPUT_NAMES):
            raise FileExistsError("Preparation output files already exist; choose a new output directory.")
        output.mkdir(parents=True, exist_ok=True)
        data.to_csv(output / "cleaned.csv", index=False)
        mappings.to_csv(output / "row_mapping.csv", index=False)
        excluded.to_csv(output / "excluded_rows.csv", index=False)
        tables.to_csv(output / "tier_table.csv", index=False)
        with (output / "audit.json").open("x", encoding="utf-8") as handle:
            json.dump(_json_value(audit), handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        paths = {name: str(output / name) for name in OUTPUT_NAMES}
    return {"data": data, "audit": _json_value(audit), "row_mapping": mappings,
            "excluded_rows": excluded, "tier_table": tables, "paths": paths}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--smiles-column", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--property", dest="property_name", help="Registry key/alias; otherwise infer from target name")
    parser.add_argument("--target-name", help="Display/property alias fallback for the API")
    parser.add_argument("--unit", help="Physical unit of the input column, including when already logged")
    parser.add_argument("--already-log", action="store_true")
    parser.add_argument("--direction", choices=("high", "low"), default="high")
    parser.add_argument("--tiers", nargs="+", default=[0.30, 0.20, 0.10], help="Fractions, separated by spaces or commas")
    parser.add_argument("--id-column")
    parser.add_argument("--condition-columns", nargs="*", default=[])
    parser.add_argument("--text-columns", "--metadata-columns", nargs="*", default=[])
    parser.add_argument("--fingerprint-radius", type=int, default=2)
    parser.add_argument("--skip-influence", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    args.tiers = [float(q) for item in args.tiers for q in str(item).split(",")]
    try:
        result = prepare_dataset(**vars(args))
        print(json.dumps({"status": result["audit"]["status"], "output_directory": str(Path(args.output_dir).resolve()),
                          "prepared_observations": len(result["data"]),
                          "excluded_input_measurements": len(result["excluded_rows"]),
                          "evaluation_scope": result["audit"]["evaluation_scope"]}, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"stca-data-layer: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
