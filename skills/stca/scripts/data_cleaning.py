#!/usr/bin/env python3
"""Clean objectively unusable STCA records without label-dependent trimming.

Automatic exclusions are missing/nonfinite/nonnumeric targets, missing/invalid
structures, unsupported H-cap attachments, duplicate exports with the same
explicit stable record ID and the same complete original row, and user-declared
quality labels or inclusive target bounds. Original fields remain text. Extreme
but valid observations, treatment descriptions and H-cap collisions are retained.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

from prepare_hcap import hcap_smiles
from stca_io import read_csv_frame


def _column_name(columns, base):
    name = base
    suffix = 2
    while name in columns:
        name = f"{base}_{suffix}"
        suffix += 1
    return name


def _text(value):
    # CSV input is already text; this only makes the library API tolerate None.
    if value is None:
        return ""
    try:
        if value is not value:
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def clean_frame(frame, *, target=None, smiles_column="SMILES", id_column=None,
                quality_column=None, exclude_quality_values=(), target_min=None,
                target_max=None, role_column=None):
    """Return ``(cleaned, excluded, audit)`` without changing ``frame``.

    ``target=None`` supports unlabelled candidates. Bounds are inclusive, in the
    target's supplied units. Excluded quality values compare exact stripped text
    case-sensitively. Stable-ID export deduplication requires the entire original
    row to match, including its data role and measurement conditions.
    """
    import pandas as pd
    from rdkit import Chem, rdBase

    if not isinstance(frame, pd.DataFrame):
        raise ValueError("frame must be a pandas DataFrame.")
    if not len(frame.columns) or len(set(frame.columns)) != len(frame.columns):
        raise ValueError("Input must have distinct nonempty column names.")
    if any(not isinstance(c, str) or not c.strip() for c in frame.columns):
        raise ValueError("Input must have distinct nonempty text column names.")
    for label, value in (("target", target), ("smiles_column", smiles_column),
                         ("id_column", id_column), ("quality_column", quality_column),
                         ("role_column", role_column)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{label} must be null or a nonempty text column name.")
    required = [x for x in (target, smiles_column, id_column, quality_column, role_column) if x]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if not isinstance(smiles_column, str) or not smiles_column:
        raise ValueError("smiles_column is required.")
    if (target_min is not None or target_max is not None) and target is None:
        raise ValueError("Explicit target bounds require a target column.")
    if any(v is not None and not math.isfinite(float(v)) for v in (target_min, target_max)):
        raise ValueError("Target bounds must be finite.")
    if target_min is not None and target_max is not None and float(target_min) > float(target_max):
        raise ValueError("target_min must not exceed target_max.")
    quality_values = tuple(str(v).strip() for v in exclude_quality_values)
    if quality_values and not quality_column:
        raise ValueError("exclude_quality_values requires quality_column.")
    if isinstance(exclude_quality_values, str):
        raise ValueError("exclude_quality_values must be a sequence of complete labels, not one string.")

    columns = list(frame.columns)
    rename = {}
    occupied = set(columns)
    for col in columns:
        if col.startswith("stca_"):
            candidate = _column_name(occupied, "archive_" + col)
            rename[col] = candidate
            occupied.add(candidate)
    out = frame.copy(deep=True).rename(columns=rename).reset_index(drop=True)
    # Every original field keeps its content and column order. New mapping names
    # are collision-safe, so pre-existing user data are never overwritten.
    mapping_column = _column_name(set(out.columns), "archive_input_row_position")
    reason_column = _column_name(set(out.columns) | {mapping_column}, "cleaning_exclusion_reason")
    duplicate_column = _column_name(set(out.columns) | {mapping_column, reason_column}, "cleaning_duplicate_of_row")
    mapped = lambda name: rename.get(name, name) if name else None
    tcol, scol, icol, qcol, rcol = map(mapped, (target, smiles_column, id_column, quality_column, role_column))
    rows = out.to_dict("records")
    reasons = []
    duplicates = []
    export_seen = {}
    numeric_values = []
    valid_originals = []
    valid_caps = []
    # Validation failures are recorded, not replaced by zero fingerprints.
    with rdBase.BlockLogs():
        for i, row in enumerate(rows):
            why = []
            value = None
            if tcol:
                raw_target = _text(row[tcol]).strip()
                if not raw_target:
                    why.append("missing_target")
                else:
                    try:
                        value = float(raw_target)
                    except (ValueError, TypeError):
                        why.append("nonnumeric_target")
                    else:
                        if not math.isfinite(value):
                            why.append("nonfinite_target")
                        elif target_min is not None and value < float(target_min):
                            why.append("outside_declared_target_min")
                        elif target_max is not None and value > float(target_max):
                            why.append("outside_declared_target_max")
            numeric_values.append(value)
            raw_structure = _text(row[scol])
            canonical = cap_identity = None
            if not raw_structure.strip():
                why.append("missing_structure")
            else:
                try:
                    molecule = Chem.MolFromSmiles(raw_structure)
                    if molecule is None or molecule.GetNumAtoms() == 0:
                        why.append("invalid_structure")
                    else:
                        canonical = Chem.MolToSmiles(molecule, canonical=True)
                        try:
                            cap, _ = hcap_smiles(raw_structure)
                        except (ValueError, RuntimeError):
                            why.append("unsupported_hcap_structure")
                        else:
                            capped = Chem.MolFromSmiles(cap)
                            if capped is None or capped.GetNumAtoms() == 0:
                                why.append("invalid_hcap_structure")
                            else:
                                cap_identity = Chem.MolToSmiles(capped, canonical=True)
                except (ValueError, RuntimeError):
                    why.append("invalid_structure")
            valid_originals.append(canonical)
            valid_caps.append(cap_identity)
            if qcol and _text(row[qcol]).strip() in quality_values:
                why.append("explicit_quality_exclusion")
            duplicate_of = None
            if icol and _text(row[icol]).strip():
                # Exact values and every original column participate, not only
                # cap identity or target. Different roles/conditions stay apart.
                signature = tuple(_text(row[c]) for c in out.columns)
                if signature in export_seen:
                    duplicate_of = export_seen[signature]
                    why.append("duplicate_export_same_id_and_complete_row")
                else:
                    export_seen[signature] = i
            reasons.append(why)
            duplicates.append(duplicate_of)

    out[mapping_column] = range(len(out))
    keep = [not r for r in reasons]
    cleaned = out.loc[keep].copy().reset_index(drop=True)
    excluded = out.loc[[not k for k in keep]].copy().reset_index(drop=True)
    excluded_positions = [i for i, k in enumerate(keep) if not k]
    excluded[reason_column] = [";".join(reasons[i]) for i in excluded_positions]
    excluded[duplicate_column] = ["" if duplicates[i] is None else duplicates[i] for i in excluded_positions]
    reason_counts = Counter(reason for rr in reasons for reason in rr)
    cap_groups = {}
    for i, (orig, cap) in enumerate(zip(valid_originals, valid_caps)):
        if orig and cap:
            cap_groups.setdefault(cap, set()).add(orig)
    collisions = sum(len(v) > 1 for v in cap_groups.values())
    role_counts = None
    role_warnings = []
    if rcol:
        before = Counter(_text(r[rcol]) for r in rows)
        after = Counter(_text(rows[i][rcol]) for i, k in enumerate(keep) if k)
        role_counts = {"input": dict(before), "cleaned": dict(after)}
        empty_positions = [i for i, row in enumerate(rows) if not _text(row[rcol]).strip()]
        if empty_positions:
            role_warnings.append({"type": "missing_role_labels", "rows": empty_positions,
                                  "action": "retained_for_caller_to_resolve"})
    audit = {
        "schema": "stca-data-cleaning-v1", "integration_version": "0.1.0",
        "input_rows": len(frame), "cleaned_rows": len(cleaned), "excluded_rows": len(excluded),
        "original_columns": columns, "cleaned_columns": list(cleaned.columns),
        "reserved_column_renames": rename,
        "field_mapping": {"target": tcol, "smiles_column": scol, "id_column": icol,
                          "quality_column": qcol, "role_column": rcol},
        "row_position_column": mapping_column, "exclusion_reason_column": reason_column,
        "duplicate_reference_column": duplicate_column,
        "row_mapping": {"cleaned_original_positions": [i for i, k in enumerate(keep) if k],
                        "excluded_original_positions": excluded_positions},
        "reason_counts": dict(reason_counts),
        "exclusion_rules": {"target_required": target is not None,
            "target_min_inclusive": target_min, "target_max_inclusive": target_max,
            "quality_values_exact_case_sensitive": list(quality_values),
            "duplicate_export_rule": "same_explicit_nonempty_record_id_and_identical_complete_original_row",
            "duplicate_exports_removed_without_explicit_id": False},
        "processing_text_deletion": False, "extreme_value_deletion": False,
        "measurement_aggregation": "none", "hcap_identity_merge": False,
        "original_smiles_preserved_exactly": True,
        "hcap_collision_groups_flagged_not_merged": collisions,
        "roles_preserved": True, "role_counts": role_counts, "role_warnings": role_warnings,
        "source_evaluation_overlap_policy": "reported_by_later_fit_audit; never resolve by deleting one role",
        "evaluation_labels_used_to_choose_settings": False,
        "input_dataframe_modified": False,
    }
    return cleaned, excluded, audit


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True);p.add_argument("--output-dir", required=True)
    p.add_argument("--target");p.add_argument("--smiles-column", default="SMILES")
    p.add_argument("--id-column");p.add_argument("--role-column")
    p.add_argument("--quality-column")
    p.add_argument("--exclude-quality-value", action="append", default=[])
    p.add_argument("--target-min", type=float);p.add_argument("--target-max", type=float)
    a=p.parse_args(argv)
    try:
        source=Path(a.input).expanduser().resolve()
        frame=read_csv_frame(source)
        output=Path(a.output_dir).expanduser().resolve()
        if output.exists():
            raise FileExistsError("Output directory exists; choose a new output directory.")
        cleaned, excluded, audit=clean_frame(frame,target=a.target,
            smiles_column=a.smiles_column,id_column=a.id_column,role_column=a.role_column,
            quality_column=a.quality_column,exclude_quality_values=a.exclude_quality_value,
            target_min=a.target_min,target_max=a.target_max)
        audit.update(input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                     generated_at_utc=datetime.now(timezone.utc).isoformat())
        output.mkdir(parents=True)
        cleaned.to_csv(output/'cleaned.csv',index=False)
        excluded.to_csv(output/'excluded_rows.csv',index=False)
        with (output/'cleaning_audit.json').open('x',encoding='utf-8') as f:
            json.dump(audit,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        print(json.dumps({'status':'completed','output_directory':str(output),
            'input_rows':len(frame),'cleaned_rows':len(cleaned),'excluded_rows':len(excluded)}))
        return 0
    except (ValueError,RuntimeError,OSError,ImportError,TypeError) as exc:
        print(f'stca-cleaning: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
