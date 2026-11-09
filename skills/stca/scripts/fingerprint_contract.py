#!/usr/bin/env python3
"""Verify the calculation-only H-cap MACCS matrix before rule fitting.

This checks representation and row ordering only. It does not choose a model,
change cleaning, collapse structures, or certify a report produced elsewhere.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json

import numpy as np

from prepare_hcap import POLICY, hcap_smiles


def _strings_sha256(values):
    payload = json.dumps(list(values), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_fit_fingerprints(prepared, matrix):
    """Reject raw-star, altered-cap, reordered, or otherwise wrong MACCS bits.

    Each row is independently recapped from its original canonical repeat unit,
    and RDKit's direct MACCS generator verifies every bit of the supplied fit
    matrix. Rows are never grouped or dropped, including H-cap collisions.
    """
    from rdkit import Chem, rdBase
    from rdkit.Chem import MACCSkeys

    originals = prepared["original_canon"].astype(str).tolist()
    calculation = prepared["stca_calculation_smiles_hcap"].astype(str).tolist()
    supplied = np.asarray(matrix)
    if supplied.shape != (len(originals), 167):
        raise ValueError("H-cap fingerprint contract: matrix must have one 167-bit row per prepared record.")
    if not np.isin(supplied, (0, 1)).all():
        raise ValueError("H-cap fingerprint contract: MACCS entries must be binary.")

    expected_rows, raw_rows, canonical_caps, canonical_originals = [], [], [], []
    connection_atoms = 0
    for position, (original, recorded_cap) in enumerate(zip(originals, calculation)):
        expected_cap, count = hcap_smiles(original)
        original_mol = Chem.MolFromSmiles(original)
        recorded_mol = Chem.MolFromSmiles(recorded_cap)
        expected_mol = Chem.MolFromSmiles(expected_cap)
        if recorded_mol is None or expected_mol is None:
            raise ValueError(f"H-cap fingerprint contract: invalid calculation copy at prepared row {position}.")
        if any(atom.GetAtomicNum() == 0 for atom in recorded_mol.GetAtoms()):
            raise ValueError(f"H-cap fingerprint contract: attachment atom remains at prepared row {position}.")
        canonical_cap = Chem.MolToSmiles(recorded_mol, canonical=True, isomericSmiles=True)
        if canonical_cap != Chem.MolToSmiles(expected_mol, canonical=True, isomericSmiles=True):
            raise ValueError(f"H-cap fingerprint contract: calculation copy differs from independent H-cap at row {position}.")
        canonical_caps.append(canonical_cap)
        canonical_originals.append(Chem.MolToSmiles(original_mol, canonical=True, isomericSmiles=True))
        connection_atoms += count
        expected_rows.append(list(MACCSkeys.GenMACCSKeys(expected_mol)))
        raw_rows.append(list(MACCSkeys.GenMACCSKeys(original_mol)))

    expected = np.asarray(expected_rows, dtype=np.uint8).reshape(len(originals), 167)
    raw = np.asarray(raw_rows, dtype=np.uint8).reshape(len(originals), 167)
    if not np.array_equal(supplied, expected):
        mismatches = int(np.count_nonzero(supplied != expected))
        raise ValueError(f"H-cap fingerprint contract: fit matrix differs from independently recomputed H-cap MACCS ({mismatches} bits).")
    if len(expected) and np.any(expected[:, 0]):
        raise ValueError("H-cap fingerprint contract: RDKit MACCS dummy bit 0 must remain zero.")

    collisions = defaultdict(set)
    for original, capped in zip(canonical_originals, canonical_caps):
        collisions[capped].add(original)
    return {
        "schema": "stca-fit-fingerprint-contract-v1", "status": "verified",
        "representation": "hcap_maccs167", "hcap_policy": POLICY,
        "rdkit_version": rdBase.rdkitVersion,
        "prepared_record_n": len(originals), "feature_n": 167,
        "original_column": "original_canon", "calculation_column": "stca_calculation_smiles_hcap",
        "independent_verification": "rederive_Hcap_from_original_then_direct_RDKit_MACCS_all_bits",
        "original_canonical_sha256": _strings_sha256(canonical_originals),
        "calculation_canonical_sha256": _strings_sha256(canonical_caps),
        "matrix_sha256": hashlib.sha256(expected.tobytes(order="C")).hexdigest(),
        "matrix_hash_encoding": "ordered_rows_uint8_167_columns_C_order",
        "connection_atoms_replaced": connection_atoms,
        "raw_star_vs_hcap_different_row_n": int(np.count_nonzero(np.any(raw != expected, axis=1))),
        "original_distinct_structure_n": len(set(canonical_originals)),
        "hcap_distinct_structure_n": len(set(canonical_caps)),
        "hcap_collision_group_n": sum(len(v) > 1 for v in collisions.values()),
        "row_policy": "verified_in_original_prepared_order; no_grouping_or_dropping_in_this_check",
        "input_mutated": False,
    }


def _artifact_path(root, relative):
    """Resolve declared artifact paths without following archive symlinks."""
    from pathlib import Path

    if not isinstance(relative, str) or not relative:
        raise ValueError("Fingerprint delivery check: artifact paths must be nonempty relative paths.")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Fingerprint delivery check: artifact paths must remain inside the run directory.")
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("Fingerprint delivery check: artifact paths cannot contain symlinks.")
    resolved = current.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("Fingerprint delivery check: artifact paths must remain inside the run directory.")
    return resolved


def _verify_preparation(root, *, preparation_directory, fingerprint_contract_path,
                        reference, prepared_measurement_n, prepared_data_sha256=None,
                        preparation_audit_sha256=None):
    """Verify one tier's independently prepared rows and calculation receipt."""
    import pandas as pd
    from rdkit import Chem
    from rdkit.Chem import MACCSkeys

    if not isinstance(reference, dict) or reference.get("status") != "verified":
        raise ValueError("Fingerprint delivery check: a verified H-cap contract is required.")
    if reference.get("representation", "hcap_maccs167") != "hcap_maccs167":
        raise ValueError("Fingerprint delivery check: unsupported calculation representation.")
    prepared_path = _artifact_path(root, preparation_directory + "/cleaned.csv")
    audit_path = _artifact_path(root, preparation_directory + "/audit.json")
    receipt_path = _artifact_path(root, fingerprint_contract_path)
    payload = receipt_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != reference.get("sha256"):
        raise ValueError("Fingerprint delivery check: receipt hash mismatch.")
    stored = json.loads(payload)
    if prepared_data_sha256 is not None and hashlib.sha256(prepared_path.read_bytes()).hexdigest() != prepared_data_sha256:
        raise ValueError("Fingerprint delivery check: prepared dataset hash mismatch.")
    if preparation_audit_sha256 is not None and hashlib.sha256(audit_path.read_bytes()).hexdigest() != preparation_audit_sha256:
        raise ValueError("Fingerprint delivery check: preparation audit hash mismatch.")
    data = pd.read_csv(prepared_path,
                       dtype={"original_canon": str, "stca_calculation_smiles_hcap": str})
    capped = data["stca_calculation_smiles_hcap"].tolist()
    bits = []
    for position, value in enumerate(capped):
        mol = Chem.MolFromSmiles(value)
        if mol is None:
            raise ValueError(f"Fingerprint delivery check: invalid calculation copy at row {position}.")
        bits.append(list(MACCSkeys.GenMACCSKeys(mol)))
    actual = audit_fit_fingerprints(data, np.asarray(bits, dtype=np.uint8).reshape(len(data), 167))
    fields = ("schema", "status", "representation", "hcap_policy", "prepared_record_n", "feature_n",
              "original_canonical_sha256", "calculation_canonical_sha256", "matrix_sha256",
              "connection_atoms_replaced", "original_distinct_structure_n", "hcap_distinct_structure_n",
              "hcap_collision_group_n", "raw_star_vs_hcap_different_row_n")
    if any(actual.get(key) != stored.get(key) for key in fields):
        raise ValueError("Fingerprint delivery check: prepared structures or stored fingerprint receipt changed.")
    if actual["matrix_sha256"] != reference.get("matrix_sha256"):
        raise ValueError("Fingerprint delivery check: manifest fit-matrix hash mismatch.")
    if len(data) != prepared_measurement_n:
        raise ValueError("Fingerprint delivery check: prepared record count differs from the run manifest.")
    return {"schema": "stca-fit-fingerprint-delivery-check-v1", "status": "verified",
            "scope": "stored_representation_artifact_consistency; not_independent_CV_reproduction",
            "representation": actual["representation"], "prepared_record_n": len(data),
            "matrix_sha256": actual["matrix_sha256"], "fingerprint_contract": fingerprint_contract_path}


def verify_run_artifacts(run_directory):
    """Verify every tier's stored representation before result delivery.

    Legacy single-preparation runs keep their result schema. New independently
    prepared tiers each have their own dataset, audit, receipt and matrix hash;
    the root compatibility receipt alone cannot certify another tier.
    """
    from pathlib import Path

    root = Path(run_directory).expanduser().resolve()
    manifest = json.loads(_artifact_path(root, "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("entrypoint") != "inrange_evaluation.py":
        raise ValueError("Fingerprint delivery check: the declared learning entrypoint is missing or unsupported.")
    reference = manifest.get("fingerprint_contract", {})
    if reference.get("path") != "fingerprint_contract.json":
        raise ValueError("Fingerprint delivery check: a verified H-cap contract is required.")
    result = _verify_preparation(root, preparation_directory="preparation",
        fingerprint_contract_path="fingerprint_contract.json", reference=reference,
        prepared_measurement_n=manifest.get("prepared_measurement_n"),
        prepared_data_sha256=manifest.get("prepared_data_sha256"),
        preparation_audit_sha256=manifest.get("preparation_audit_sha256"))
    if "per_tier_preparation" not in manifest:
        return result
    records = manifest["per_tier_preparation"]
    if not isinstance(records, dict) or not records:
        raise ValueError("Fingerprint delivery check: per-tier preparation records must be a nonempty mapping.")
    requested = manifest.get("tiers")
    if not isinstance(requested, list) or set(records) != {format(float(q), ".12g") for q in requested}:
        raise ValueError("Fingerprint delivery check: per-tier preparation records must cover all requested tiers exactly.")
    required = {"preparation_directory", "fingerprint_contract_path", "prepared_measurement_n",
                "prepared_data_sha256", "preparation_audit_sha256", "fingerprint_contract"}
    tier_results = {}
    for tier, record in records.items():
        if not isinstance(record, dict) or not required.issubset(record):
            raise ValueError(f"Fingerprint delivery check: preparation evidence is incomplete for tier {tier}.")
        if any(not isinstance(record[key], str) or len(record[key]) != 64
               for key in ("prepared_data_sha256", "preparation_audit_sha256")):
            raise ValueError(f"Fingerprint delivery check: preparation hashes are missing for tier {tier}.")
        tier_results[tier] = _verify_preparation(root, **{key: record[key] for key in required
            if key != "fingerprint_contract"}, reference=record["fingerprint_contract"])
    result.update(tier_results=tier_results, all_tiers_verified=True)
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Verify stored H-cap fingerprint artifacts before delivering a learning run.")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_run_artifacts(args.run_dir)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
