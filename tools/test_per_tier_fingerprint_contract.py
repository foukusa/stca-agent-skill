#!/usr/bin/env python3
"""Ensure a valid first tier cannot hide a corrupt independent preparation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import MACCSkeys

SKILL = Path(os.environ.get('STCA_TEST_SKILL_DIR', str(Path(__file__).resolve().parents[1] / 'skills' / 'stca')))
sys.path.insert(0, str(SKILL / 'scripts'))
from fingerprint_contract import audit_fit_fingerprints, verify_run_artifacts
from prepare_hcap import hcap_smiles


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(root, directory, receipt_path, smiles):
    data = pd.DataFrame({'original_canon': smiles,
        'stca_calculation_smiles_hcap': [hcap_smiles(s)[0] for s in smiles]})
    bits = np.asarray([list(MACCSkeys.GenMACCSKeys(Chem.MolFromSmiles(s)))
        for s in data.stca_calculation_smiles_hcap], dtype=np.uint8)
    receipt = audit_fit_fingerprints(data, bits)
    target = root / directory
    target.mkdir(parents=True)
    data.to_csv(target / 'cleaned.csv', index=False)
    (target / 'audit.json').write_text('{}\n')
    payload = root / receipt_path
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text(json.dumps(receipt))
    return {'preparation_directory': directory, 'fingerprint_contract_path': receipt_path,
        'prepared_measurement_n': len(data), 'prepared_data_sha256': digest(target / 'cleaned.csv'),
        'preparation_audit_sha256': digest(target / 'audit.json'),
        'fingerprint_contract': {'sha256': digest(payload), 'status': 'verified',
            'representation': 'hcap_maccs167', 'matrix_sha256': receipt['matrix_sha256']}}


def fixture(root):
    first = record(root, 'preparation', 'fingerprint_contract.json', ['*CCO*'])
    second = record(root, 'tier_preparation/0.3', 'tier_preparation/0.3/fingerprint_contract.json',
                    ['*CC(F)*', '*CCC*'])
    manifest = {'entrypoint': 'inrange_evaluation.py', 'tiers': [.1, .3],
        'prepared_measurement_n': first['prepared_measurement_n'],
        'prepared_data_sha256': first['prepared_data_sha256'],
        'preparation_audit_sha256': first['preparation_audit_sha256'],
        'fingerprint_contract': {**first['fingerprint_contract'], 'path': 'fingerprint_contract.json'},
        'per_tier_preparation': {'0.1': first, '0.3': second}}
    (root / 'run_manifest.json').write_text(json.dumps(manifest))
    return manifest


class PerTierFingerprintContractTests(unittest.TestCase):
    def test_different_tier_datasets_are_each_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = verify_run_artifacts(root)
            self.assertTrue(result['all_tiers_verified'])
            self.assertEqual(result['tier_results']['0.1']['prepared_record_n'], 1)
            self.assertEqual(result['tier_results']['0.3']['prepared_record_n'], 2)
            self.assertNotEqual(result['tier_results']['0.1']['matrix_sha256'],
                                result['tier_results']['0.3']['matrix_sha256'])

    def test_secondary_preparation_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            path = root / 'tier_preparation/0.3/cleaned.csv'
            data = pd.read_csv(path)
            data.loc[0, 'original_canon'] = '*CCO*'
            data.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'prepared dataset hash mismatch'):
                verify_run_artifacts(root)

    def test_secondary_receipt_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            path = root / 'tier_preparation/0.3/fingerprint_contract.json'
            path.write_bytes(path.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'receipt hash mismatch'):
                verify_run_artifacts(root)

    def test_missing_tier_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = fixture(root)
            del manifest['per_tier_preparation']['0.3']
            (root / 'run_manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'cover all requested tiers'):
                verify_run_artifacts(root)

    def test_path_escape_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            manifest = fixture(root)
            item = manifest['per_tier_preparation']['0.3']
            item['preparation_directory'] = '../escape'
            (root / 'run_manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'inside the run directory'):
                verify_run_artifacts(root)
            (root / 'linked').symlink_to(outside, target_is_directory=True)
            item['preparation_directory'] = 'linked'
            (root / 'run_manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'cannot contain symlinks'):
                verify_run_artifacts(root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
