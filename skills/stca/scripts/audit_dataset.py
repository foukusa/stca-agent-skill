#!/usr/bin/env python3
"""Audit STCA CSV inputs and split identities without changing or dropping records."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys

from stca_runtime import environment_receipt, load_stca
from stca_io import read_csv_records as read_csv


EXAMPLE_LIMIT = 5


def finding(report, severity, code, message, **details):
    report["findings"].append({"severity": severity, "code": code, "message": message, **details})


def duplicate_summary(values):
    counts = Counter(x for x in values if x is not None and str(x).strip())
    repeated = {k: n for k, n in counts.items() if n > 1}
    return {
        "unique_values": len(counts),
        "repeated_groups": len(repeated),
        "records_in_repeated_groups": sum(repeated.values()),
        "additional_records": sum(n - 1 for n in repeated.values()),
        "examples": [{"identity": k, "count": n} for k, n in list(repeated.items())[:EXAMPLE_LIMIT]],
    }


def target_audit(report, rows, column):
    values, invalid, nonfinite = [], [], []
    for i, row in enumerate(rows):
        try:
            value = float(row[column])
        except (ValueError, TypeError):
            value = None
            invalid.append(i)
        if value is not None and not math.isfinite(value):
            value = None
            nonfinite.append(i)
        values.append(value)
    finite = [v for v in values if v is not None]
    report["targets"][column] = {
        "finite_count": len(finite),
        "nonnumeric_or_missing_count": len(invalid),
        "nonfinite_count": len(nonfinite),
        "distinct_finite_values": len(set(finite)),
        "min": min(finite) if finite else None,
        "max": max(finite) if finite else None,
        "unit": "not_inferred",
        "direction": "not_inferred",
    }
    if invalid or nonfinite:
        finding(report, "error", "invalid_target", f"Target {column!r} has missing, nonnumeric, or nonfinite values.",
                count=len(invalid) + len(nonfinite), record_positions=(invalid + nonfinite)[:EXAMPLE_LIMIT])
    if finite and len(set(finite)) == 1:
        finding(report, "warning", "constant_target", f"Target {column!r} is constant among finite records; it cannot support a new STCA scan.")
    return values


def binary_audit(report, rows, features):
    keys, invalid = [], []
    for i, row in enumerate(rows):
        try:
            values = tuple(float(row[name]) for name in features)
            valid = all(math.isfinite(x) and x in (0, 1) for x in values)
        except (ValueError, TypeError):
            values, valid = (), False
        if not valid:
            invalid.append(i)
            keys.append(None)
        else:
            # A complete, order-preserving descriptor identity, never a row number.
            keys.append("".join(str(int(x)) for x in values))
    report["representation"] = {"kind": "explicit_binary", "feature_names": features, "n_features": len(features),
                                "semantic_mapping": "user_defined_not_inferred", "valid_records": len(rows) - len(invalid)}
    if invalid:
        finding(report, "error", "nonbinary_features", "Feature cells must contain finite 0/1 values; nothing is binarized or imputed.",
                count=len(invalid), record_positions=invalid[:EXAMPLE_LIMIT])
    if "K0" in features:
        finding(report, "warning", "possible_maccs_dummy", "A column named K0 is present. If these are RDKit MACCS keys, K0 is a dummy and must not be mined as a real feature.")
        if features == [f"K{i}" for i in range(167)]:
            nonzero = [i for i, key in enumerate(keys) if key is not None and key[0] != "0"]
            if nonzero:
                finding(report, "error", "maccs_dummy_not_zero", "The declared K0..K166 layout has nonzero dummy K0 values.",
                        count=len(nonzero), record_positions=nonzero[:EXAMPLE_LIMIT])
    return keys


def smiles_audit(report, rows, column):
    from rdkit import Chem, rdBase
    from stca.chemistry import maccs_from_smiles

    smiles = [row[column] for row in rows]
    with rdBase.BlockLogs():
        matrix, audit = maccs_from_smiles(smiles, errors="report")
    valid = audit.input_valid.tolist()
    canonical = [s if ok else None for s, ok in zip(audit.canonical_smiles.tolist(), valid)]
    invalid = [i for i, ok in enumerate(valid) if not ok]
    report["representation"] = {
        "kind": "rdkit_maccs167", "n_features": int(matrix.shape[1]), "dummy_key": "K0", "real_keys": "K1..K166",
        "rdkit_version": rdBase.rdkitVersion, "valid_records": sum(valid), "invalid_records": len(invalid),
        "smiles_policy": "as_provided_no_capping_no_salt_or_tautomer_normalization",
        "identity_check": "canonical_SMILES_not_complete_polymer_equivalence",
    }
    if matrix.shape[1] != 167 or any(matrix[i, 0] != 0 for i, ok in enumerate(valid) if ok):
        finding(report, "error", "maccs_layout_mismatch", "Expected the original 167-position MACCS layout with zero dummy K0.")
    if invalid:
        finding(report, "error", "invalid_smiles", "Empty, unparsable, or nonmaterial SMILES remain invalid; they are not encoded as absent keys.",
                count=len(invalid), record_positions=invalid[:EXAMPLE_LIMIT])

    histogram, fragment_histogram, degree_histogram = Counter(), Counter(), Counter()
    representation_warnings = []
    fragment_records, degree_records, unusual_count_records = [], [], []
    unmarked_single_fragment = two_terminal_connections = 0
    with rdBase.BlockLogs():
        for i, ok in enumerate(valid):
            if not ok:
                continue
            mol = Chem.MolFromSmiles(smiles[i])
            connection_atoms = [a for a in mol.GetAtoms() if a.GetAtomicNum() == 0]
            histogram[str(len(connection_atoms))] += 1
            fragments = len(Chem.GetMolFrags(mol))
            degrees = [a.GetDegree() for a in connection_atoms]
            fragment_histogram[str(fragments)] += 1
            degree_histogram.update(str(degree) for degree in degrees)
            if not connection_atoms and fragments == 1:
                unmarked_single_fragment += 1
            if len(connection_atoms) == 2 and fragments == 1 and all(degree == 1 for degree in degrees):
                two_terminal_connections += 1
            if fragments != 1:
                fragment_records.append(i)
            if any(degree != 1 for degree in degrees):
                degree_records.append(i)
            if len(connection_atoms) not in (0, 2):
                unusual_count_records.append(i)
            if len(connection_atoms) not in (0, 2) or fragments != 1 or any(degree != 1 for degree in degrees):
                representation_warnings.append({"record_position": i, "connection_atoms": len(connection_atoms),
                                                "fragments": fragments, "connection_degrees": degrees})
    unmarked = histogram.get("0", 0)
    marked = sum(histogram.values()) - unmarked
    mixed_encoding = bool(unmarked and marked)
    report["polymer_scope"] = {
        "expected": "preserve the supplied SMILES and verify its encoding against the fitted source data",
        "connection_atom_definition": "wildcard atoms (atomic number 0); their presence does not prove polymer connection sites",
        "connection_count_histogram": dict(sorted(histogram.items(), key=lambda item: int(item[0]))),
        "fragment_count_histogram": dict(sorted(fragment_histogram.items(), key=lambda item: int(item[0]))),
        "connection_degree_histogram": dict(sorted(degree_histogram.items(), key=lambda item: int(item[0]))),
        "histogram_units": {"connection_count": "valid_records", "fragment_count": "valid_records", "connection_degree": "wildcard_atoms"},
        "unmarked_records": unmarked, "marked_records": marked,
        "unmarked_single_fragment_records": unmarked_single_fragment,
        "two_terminal_connection_atom_records": two_terminal_connections,
        "unusual_connection_count_records": len(unusual_count_records),
        "multiple_fragment_records": len(fragment_records),
        "nonterminal_connection_atom_records": len(degree_records),
        "mixed_connection_encoding": mixed_encoding,
        "scope_warning_records": len(representation_warnings), "examples": representation_warnings[:EXAMPLE_LIMIT],
        "unmarked_interpretation": "A single fragment without wildcard atoms is accepted as provided; it does not identify connection sites or establish a linear-homopolymer identity.",
        "marked_interpretation": "Two terminal wildcard atoms do not establish equivalence to a historical SMILES without wildcards; verify the representation policy against the fitted source data.",
        "structures_modified": 0,
        "is_complete_architecture_or_synthesis_validation": False,
    }
    if representation_warnings:
        finding(report, "warning", "repeat_unit_scope", "Some valid SMILES have a wildcard count other than 0 or 2, multiple fragments, or nonterminal wildcard atoms. Verify these encodings against the training representation; no wildcard atoms or other chemistry are changed.",
                count=len(representation_warnings))
    if mixed_encoding:
        finding(report, "warning", "mixed_connection_encoding", "This dataset mixes SMILES with and without wildcard atoms. Check that the representation policy matches the training data; these encodings are not automatically equivalent and are not normalized.",
                unmarked_records=unmarked, marked_records=marked)
    return canonical


def conflicting_targets(report, identities, targets, ids):
    groups = defaultdict(list)
    for i, identity in enumerate(identities):
        if identity is not None:
            groups[identity].append(i)
    conflicts = {}
    for target, values in targets.items():
        examples, group_count, record_count = [], 0, 0
        for identity, positions in groups.items():
            observed = sorted({values[i] for i in positions if values[i] is not None})
            if len(observed) > 1:
                group_count += 1
                record_count += len(positions)
                if len(examples) < EXAMPLE_LIMIT:
                    examples.append({"input_identity": identity, "record_positions": positions[:EXAMPLE_LIMIT],
                                     "ids": [ids[i] for i in positions[:EXAMPLE_LIMIT]], "finite_targets": observed[:8]})
        conflicts[target] = {"groups_with_multiple_finite_targets": group_count, "records_in_these_groups": record_count,
                             "examples": examples, "records_removed_or_averaged": 0}
        if group_count:
            finding(report, "warning", "same_input_different_targets", f"The same encoded input has multiple values of {target!r}; keep repeat-measurement and condition information rather than inventing a unique label.",
                    groups=group_count, records=record_count)
    report["target_variation_within_input"] = conflicts


def audit_one(label, path, args, features):
    report = {"role": label, "path": str(Path(path).expanduser().resolve()), "findings": [], "targets": {}}
    state = {"report": report, "ids": set(), "input_identities": set()}
    try:
        _, raw, header, rows = read_csv(path)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        finding(report, "error", "unreadable_csv", str(exc))
        return state
    report.update({"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw), "columns": header, "records": len(rows)})
    required = [*(features if features else [args.smiles_column]), *args.target]
    if args.id_column:
        required.insert(0, args.id_column)
    missing = sorted(set(required) - set(header))
    if missing:
        finding(report, "error", "missing_columns", "Required columns are missing.", columns=missing)
        return state
    if not rows:
        finding(report, "error", "empty_dataset", "CSV contains no data records.")
        return state
    if args.id_column:
        ids = [row[args.id_column] for row in rows]
        blank = [i for i, value in enumerate(ids) if not value.strip()]
        if blank:
            finding(report, "error", "empty_id", "Supplied row identifiers must be nonempty.", count=len(blank), record_positions=blank[:EXAMPLE_LIMIT])
        state["ids"] = {x for x in ids if x.strip()}
        state["supplied_ids"] = True
        report["id_audit"] = {
            "column": args.id_column,
            "source": "user_supplied_arbitrary_text_identifier",
            "strings_preserved": True,
            "used_as_model_feature": False,
            **duplicate_summary(ids),
        }
        if report["id_audit"]["repeated_groups"]:
            finding(report, "warning", "repeated_ids", "Identifiers repeat within this dataset. Preserve repeated observations; use a separate scientifically meaningful grouping column when constructing splits.",
                    groups=report["id_audit"]["repeated_groups"])
        padded = [i for i, value in enumerate(ids) if value != value.strip()]
        if padded:
            finding(report, "warning", "id_whitespace", "Identifiers contain leading or trailing whitespace; identity is currently checked as the exact supplied string.",
                    count=len(padded), record_positions=padded[:EXAMPLE_LIMIT])
    else:
        # Row identifiers are bookkeeping only. When no user column is supplied,
        # create deterministic labels for receipts without pretending they are
        # material IDs or using them to assert cross-dataset disjointness.
        ids = [f"{label}-row-{index + 1:06d}" for index in range(len(rows))]
        state["ids"] = set()
        state["supplied_ids"] = False
        report["id_audit"] = {
            "column": None,
            "source": "generated_from_row_position_for_receipts_only",
            "strings_preserved": True,
            "used_as_model_feature": False,
            "cross_dataset_id_overlap_checked": False,
            **duplicate_summary(ids),
        }

    targets = {column: target_audit(report, rows, column) for column in args.target}
    identities = binary_audit(report, rows, features) if features else smiles_audit(report, rows, args.smiles_column)
    state["input_identities"] = {x for x in identities if x is not None}
    report["input_identity_audit"] = duplicate_summary(identities)
    if report["input_identity_audit"]["repeated_groups"]:
        finding(report, "warning", "repeated_input_representation", "Some complete input representations repeat. This audit retains all observations.",
                groups=report["input_identity_audit"]["repeated_groups"])
    conflicting_targets(report, identities, targets, ids)
    return state


def make_report(args, features):
    load_stca(args.source)
    source_paths = [("input", args.input)]
    if args.selection_input:
        source_paths.append(("selection", args.selection_input))
    if args.test:
        source_paths.append(("test", args.test))
    states = {label: audit_one(label, path, args, features) for label, path in source_paths}
    report = {
        "schema_version": 1, "audit": "STCA_input_and_split_identity",
        "software": environment_receipt(args.source), "datasets": {k: v["report"] for k, v in states.items()},
        "between_datasets": [], "findings": [],
        "interpretation": {
            "record_positions": "zero_based_data_records_excluding_header",
            "records_removed_or_averaged": 0,
            "units_and_target_directions": "not_inferred",
            "binary_overlap": "identical_descriptors_do_not_prove_identical_materials",
            "smiles_validity": "not_synthesis_feasibility_or_property_validation",
            "scope": "input_audit_not_numerical_STCA_reproduction",
        },
    }
    for left, right in combinations(states, 2):
        id_overlap_checked = bool(states[left].get("supplied_ids") and states[right].get("supplied_ids"))
        id_overlap = sorted(states[left]["ids"] & states[right]["ids"]) if id_overlap_checked else []
        representation_overlap = sorted(states[left]["input_identities"] & states[right]["input_identities"])
        comparison = {"left": left, "right": right, "id_overlap_checked": id_overlap_checked,
                      "overlapping_ids": len(id_overlap),
                      "overlapping_input_representations": len(representation_overlap),
                      "id_examples": id_overlap[:EXAMPLE_LIMIT], "input_examples": representation_overlap[:EXAMPLE_LIMIT],
                      "representation_kind": "complete_binary_vector" if features else "canonical_SMILES"}
        report["between_datasets"].append(comparison)
        if id_overlap_checked and id_overlap:
            finding(report, "error", "cross_dataset_id_overlap", f"{left} and {right} share supplied record/group identities.", count=len(id_overlap))
        if representation_overlap:
            message = (f"{left} and {right} contain identical complete descriptor vectors; they are not representation-disjoint. This does not alone prove identical materials."
                       if features else f"{left} and {right} contain the same canonical structures, including any with different IDs; they are not structure-disjoint.")
            finding(report, "warning" if features else "error", "cross_dataset_input_overlap", message, count=len(representation_overlap))
        if not features:
            left_scope = states[left]["report"].get("polymer_scope", {})
            right_scope = states[right]["report"].get("polymer_scope", {})
            left_marking = (bool(left_scope.get("unmarked_records")), bool(left_scope.get("marked_records")))
            right_marking = (bool(right_scope.get("unmarked_records")), bool(right_scope.get("marked_records")))
            if any(left_marking) and any(right_marking) and left_marking != right_marking:
                finding(report, "warning", "cross_dataset_connection_encoding", f"{left} and {right} use different mixes of SMILES with and without wildcard atoms. Verify candidate/evaluation encoding against the training representation; no connection atoms are added or removed.")
    all_findings = report["findings"] + [f for dataset in report["datasets"].values() for f in dataset["findings"]]
    errors = sum(f["severity"] == "error" for f in all_findings)
    warnings = sum(f["severity"] == "warning" for f in all_findings)
    report.update({"status": "error" if errors else "warning" if warnings else "pass",
                   "error_findings": errors, "warning_findings": warnings})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Clean pinned STCA checkout; otherwise use the skill cache.")
    parser.add_argument("--input", required=True, help="Source or candidate CSV.")
    parser.add_argument("--selection-input", help="Separate CSV whose labels participate in rule selection, if applicable.")
    parser.add_argument("--test", help="Separate intended holdout CSV.")
    parser.add_argument(
        "--id-column",
        help=("Optional arbitrary row-identifier column (for example ID, SampleKey or RecordName). "
              "It is preserved as text and never used as a model feature. If omitted, deterministic "
              "row-position identifiers are generated for the audit receipt only."),
    )
    parser.add_argument("--smiles-column", default="SMILES")
    parser.add_argument("--features", help="Comma-separated explicit binary feature columns, replacing SMILES.")
    parser.add_argument("--target", action="append", default=[], help="Numeric target to audit in each CSV; repeat for multiple targets.")
    parser.add_argument("--output", required=True, help="New JSON report path; existing files are never overwritten.")
    args = parser.parse_args(argv)
    features = [name.strip() for name in args.features.split(",")] if args.features is not None else []
    if args.features is not None and (not all(features) or len(set(features)) != len(features)):
        parser.error("--features must contain distinct nonempty names.")
    if len(set(args.target)) != len(args.target):
        parser.error("Do not repeat a target column name.")
    forbidden = set(args.target)
    if args.id_column:
        forbidden.add(args.id_column)
    if set(features) & forbidden:
        parser.error("Features cannot contain the ID or target columns.")
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        print(f"stca-audit: Output exists: {output}", file=sys.stderr)
        return 2
    try:
        report = make_report(args, features)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
    except (OSError, RuntimeError, ImportError, ValueError) as exc:
        print(f"stca-audit: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "report": str(output),
                      "error_findings": report["error_findings"], "warning_findings": report["warning_findings"]}, ensure_ascii=False))
    return 1 if report["error_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
