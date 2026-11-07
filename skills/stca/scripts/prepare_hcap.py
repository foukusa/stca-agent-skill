#!/usr/bin/env python3
"""Prepare a calculation-only H-capped column while retaining original repeat units.

This is a skill adapter for a user-requested representation contract, not a
recovered author's preprocessing function. It neither changes nor fits STCA.
The output column must be selected explicitly for subsequent fingerprinting.
Final user-facing results should use the untouched original repeat-unit SMILES;
the capped molecule is not chemically reverse-converted back to connection points.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys

from stca_io import CSV_POLICY, read_csv_records
from stca_runtime import environment_receipt


POLICY = "terminal_single_bond_dummy_to_neutral_hydrogen_v1"


def hcap_smiles(smiles: str) -> tuple[str, int]:
    """Replace only supported terminal dummy atoms; preserve zero-dummy text."""
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles) if smiles.strip() else None
    if mol is None or not mol.GetNumAtoms() or not any(
        atom.GetAtomicNum() > 1 for atom in mol.GetAtoms()
    ):
        raise ValueError("Invalid, empty, or nonmaterial SMILES.")
    dummies = [atom for atom in mol.GetAtoms() if atom.GetAtomicNum() == 0]
    if not dummies:
        return smiles, 0

    # Validate every connection before making any change. Atom-map labels on
    # ordinary terminal [*:n] atoms are accepted; they are not hydrogen labels.
    for atom in dummies:
        index = atom.GetIdx()
        if atom.GetDegree() != 1:
            raise ValueError(f"Dummy atom {index} is not terminal (degree != 1).")
        bond = atom.GetBonds()[0]
        if bond.GetBondType() != Chem.BondType.SINGLE:
            raise ValueError(f"Dummy atom {index} is not joined by a single bond.")
        if atom.GetNeighbors()[0].GetAtomicNum() <= 1:
            raise ValueError(f"Dummy atom {index} is not attached to a heavy atom.")
        if (atom.GetFormalCharge() or atom.GetIsotope()
                or atom.GetNumRadicalElectrons() or atom.GetIsAromatic()):
            raise ValueError(f"Dummy atom {index} has unsupported charge/isotope/radical/aromatic attributes.")

    editable = Chem.RWMol(mol)
    for atom in dummies:
        hydrogen = Chem.Atom(1)
        hydrogen.SetNoImplicit(True)
        editable.ReplaceAtom(atom.GetIdx(), hydrogen, updateLabel=False, preserveProps=False)
    capped = editable.GetMol()
    Chem.SanitizeMol(capped)
    capped = Chem.RemoveHs(capped, implicitOnly=False, updateExplicitCount=False, sanitize=True)
    if any(atom.GetAtomicNum() == 0 for atom in capped.GetAtoms()):
        raise ValueError("Unexpected remaining dummy atom after H-capping.")
    return Chem.MolToSmiles(capped, canonical=True, isomericSmiles=True), len(dummies)


def prepare(args) -> dict:
    source, raw, header, records = read_csv_records(args.input)
    if not records:
        raise ValueError("CSV contains no data records.")
    if args.smiles_column not in header:
        raise ValueError(f"Missing SMILES column: {args.smiles_column!r}.")
    if not args.output_column.strip() or args.output_column in header:
        raise ValueError("Output column must be nonempty and must not replace an existing column.")
    if args.id_column is not None and args.id_column not in header:
        raise ValueError(f"Missing optional ID column: {args.id_column!r}.")

    output = Path(args.output).expanduser().resolve()
    manifest_path = Path(str(output) + ".manifest.json")
    if source in (output, manifest_path):
        raise ValueError("Output and manifest must not overwrite the input.")
    if output.exists() or manifest_path.exists():
        raise FileExistsError("Output or manifest already exists; choose a new output path.")

    prepared = []
    row_audit = []
    failures = []
    for position, record in enumerate(records):
        identity = {"row_position": position}
        if args.id_column is not None:
            identity["id"] = record[args.id_column]
        try:
            value, count = hcap_smiles(record[args.smiles_column])
        except (ValueError, RuntimeError) as exc:
            failures.append({**identity, "error": str(exc)})
            continue
        prepared.append({**record, args.output_column: value})
        row_audit.append({**identity, "connection_atoms_replaced": count,
                          "text_changed": value != record[args.smiles_column],
                          "status": "h_capped" if count else "unchanged_no_dummy"})
    if failures:
        # No output directory/file has been created: a bad row cannot disappear
        # from a seemingly successful prepared dataset.
        raise ValueError("H-capping rejected the entire batch; no output was written: "
                         + json.dumps({"failed_rows": len(failures),
                                       "first_failures": failures[:10]}, ensure_ascii=False))

    runtime = environment_receipt()
    from rdkit import rdBase

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=header + [args.output_column], lineterminator="\n")
    writer.writeheader()
    writer.writerows(prepared)
    payload = buffer.getvalue().encode("utf-8")
    digest = lambda value: hashlib.sha256(value).hexdigest()
    receipt = {
        "schema": "stca-hcap-preparation-v1",
        "operation": "explicit_hydrogen_capping_before_fingerprinting",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": POLICY,
        "policy_source": "user_requested_hydrogen_capping_contract",
        "implementation_origin": "skill_adapter_not_recovered_author_conversion_function",
        "historical_author_conversion_function_recovered": False,
        "csv_input_policy": CSV_POLICY,
        "input": {"path": str(source), "sha256": digest(raw), "columns": header},
        "output": {"path": str(output), "sha256": digest(payload),
                   "columns": header + [args.output_column]},
        "original_smiles_column": args.smiles_column,
        "processed_smiles_column": args.output_column,
        "final_presentation_smiles_column": args.smiles_column,
        "id_column": args.id_column,
        "input_count": len(records),
        "output_count": len(prepared),
        "h_capped_row_count": sum(row["connection_atoms_replaced"] > 0 for row in row_audit),
        "changed_row_count": sum(row["text_changed"] for row in row_audit),
        "unchanged_no_dummy_row_count": sum(row["connection_atoms_replaced"] == 0 for row in row_audit),
        "connection_atoms_replaced": sum(row["connection_atoms_replaced"] for row in row_audit),
        "processing_order": [
            "Read strict UTF-8 CSV; retain every original cell as text.",
            "Parse the original SMILES with RDKit; preserve the exact text when no dummy is present.",
            "Validate all dummy atoms as terminal, neutral, unlabelled-isotope, nonradical atoms with a single bond to a heavy atom.",
            "Replace each supported dummy atom, including an atom-mapped dummy, with neutral hydrogen; discard dummy atom-map labels.",
            "Sanitize; RemoveHs(implicitOnly=False, updateExplicitCount=False, sanitize=True).",
            "For changed rows, write canonical isomeric capped SMILES only into the new column.",
        ],
        "original_fields_preserved": True,
        "records_removed_or_deduplicated": 0,
        "input_file_modified": False,
        "reverse_hcap_conversion_attempted": False,
        "upstream_stca_algorithm_modified": False,
        "fingerprints_computed": False,
        "training_performed": False,
        "runtime": runtime,
        "rdkit_version": rdBase.rdkitVersion,
        "rows": row_audit,
        "interpretation": "Select the processed column explicitly for MACCS/STCA. Keep and present the original star-containing repeat-unit column after screening. Do not reconstruct connection points from the capped molecule; the original text is the authoritative structure record. Capped molecular identity does not establish polymer equivalence or physical-property success.",
    }
    manifest_payload = (json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for path, contents in ((output, payload), (manifest_path, manifest_payload)):
            with path.open("xb") as handle:
                created.append(path)
                handle.write(contents)
    except OSError:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return {"output": str(output), "manifest": str(manifest_path),
            "input_count": len(records), "changed_row_count": receipt["changed_row_count"],
            "unchanged_no_dummy_row_count": receipt["unchanged_no_dummy_row_count"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True, help="A new CSV path; its manifest is <output>.manifest.json.")
    parser.add_argument("--smiles-column", default="SMILES")
    parser.add_argument("--output-column", default="stca_calculation_smiles_hcap")
    parser.add_argument("--id-column", help="Optional existing ID column, copied verbatim into row receipts.")
    args = parser.parse_args(argv)
    try:
        result = prepare(args)
    except (OSError, ImportError, ValueError, RuntimeError) as exc:
        print(f"stca-hcap: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
