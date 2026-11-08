#!/usr/bin/env python3
"""Representation regression tests: reject raw-star MACCS before fitting."""
import os
import hashlib
import json
import tempfile
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import MACCSkeys

SKILL = Path(os.environ.get('STCA_TEST_SKILL_DIR', str(Path(__file__).resolve().parents[1] / 'skills' / 'stca')))
sys.path.insert(0, str(SKILL / 'scripts'))
from fingerprint_contract import audit_fit_fingerprints, verify_run_artifacts
from prepare_hcap import hcap_smiles


def matrix(smiles):
    return np.asarray([list(MACCSkeys.GenMACCSKeys(Chem.MolFromSmiles(s))) for s in smiles], dtype=np.uint8)


def prepared(smiles):
    return pd.DataFrame({'original_canon': smiles,
        'stca_calculation_smiles_hcap': [hcap_smiles(s)[0] for s in smiles]})


class FingerprintContractTests(unittest.TestCase):
    def test_hcap_matrix_passes_and_input_is_unchanged(self):
        data = prepared(['*CCO*', '*CC(F)*'])
        before = data.copy(deep=True)
        receipt = audit_fit_fingerprints(data, matrix(data['stca_calculation_smiles_hcap']))
        pd.testing.assert_frame_equal(data, before)
        self.assertEqual(receipt['status'], 'verified')
        self.assertEqual(receipt['representation'], 'hcap_maccs167')
        self.assertEqual(receipt['prepared_record_n'], 2)
        self.assertEqual(receipt['feature_n'], 167)
        self.assertGreater(receipt['raw_star_vs_hcap_different_row_n'], 0)
        self.assertEqual(len(receipt['matrix_sha256']), 64)

    def test_raw_star_matrix_is_rejected(self):
        data = prepared(['*CCO*', '*CC(F)*'])
        with self.assertRaisesRegex(ValueError, 'independently recomputed H-cap MACCS'):
            audit_fit_fingerprints(data, matrix(data['original_canon']))

    def test_altered_calculation_copy_is_rejected(self):
        data = prepared(['*CCO*'])
        data.loc[0, 'stca_calculation_smiles_hcap'] = 'CC'
        with self.assertRaisesRegex(ValueError, 'differs from independent H-cap'):
            audit_fit_fingerprints(data, matrix(['CC']))

    def test_remaining_attachment_point_is_rejected(self):
        data = prepared(['*CCO*'])
        data.loc[0, 'stca_calculation_smiles_hcap'] = '*CCO'
        with self.assertRaisesRegex(ValueError, 'attachment atom remains'):
            audit_fit_fingerprints(data, matrix(['*CCO']))

    def test_different_original_repeat_units_are_not_merged(self):
        data = prepared(['*C(C*)CC', '*C(C)C(C)*'])
        self.assertNotEqual(data.loc[0, 'original_canon'], data.loc[1, 'original_canon'])
        self.assertEqual(data.loc[0, 'stca_calculation_smiles_hcap'], data.loc[1, 'stca_calculation_smiles_hcap'])
        receipt = audit_fit_fingerprints(data, matrix(data['stca_calculation_smiles_hcap']))
        self.assertEqual(len(data), 2)
        self.assertEqual(receipt['prepared_record_n'], 2)
        self.assertEqual(receipt['original_distinct_structure_n'], 2)
        self.assertEqual(receipt['hcap_distinct_structure_n'], 1)
        self.assertEqual(receipt['hcap_collision_group_n'], 1)

    def test_reordered_or_wrong_shape_matrix_fails(self):
        data = prepared(['*CCO*', '*CC(F)*'])
        bits = matrix(data['stca_calculation_smiles_hcap'])
        with self.assertRaisesRegex(ValueError, 'independently recomputed'):
            audit_fit_fingerprints(data, bits[::-1])
        with self.assertRaisesRegex(ValueError, 'one 167-bit row'):
            audit_fit_fingerprints(data, bits[:, :166])

    def run_fixture(self, directory):
        root = Path(directory)
        data = prepared(['*CCO*', '*CC(F)*'])
        receipt = audit_fit_fingerprints(data, matrix(data['stca_calculation_smiles_hcap']))
        (root / 'preparation').mkdir()
        data.to_csv(root / 'preparation' / 'cleaned.csv', index=False)
        payload = (json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode()
        (root / 'fingerprint_contract.json').write_bytes(payload)
        manifest = {'entrypoint': 'inrange_evaluation.py', 'prepared_measurement_n': len(data),
            'fingerprint_contract': {'path': 'fingerprint_contract.json', 'status': 'verified',
                'sha256': hashlib.sha256(payload).hexdigest(), 'matrix_sha256': receipt['matrix_sha256']}}
        (root / 'run_manifest.json').write_text(json.dumps(manifest))
        return root, data, manifest

    def test_stored_artifacts_are_verified_before_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _ = self.run_fixture(directory)
            result = verify_run_artifacts(root)
            self.assertEqual(result['status'], 'verified')
            self.assertEqual(result['prepared_record_n'], 2)
            self.assertIn('not_independent_CV_reproduction', result['scope'])

    def test_changed_prepared_original_is_rejected_before_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root, data, _ = self.run_fixture(directory)
            data.loc[0, 'original_canon'] = '*CCC*'
            data.to_csv(root / 'preparation' / 'cleaned.csv', index=False)
            with self.assertRaisesRegex(ValueError, 'differs from independent H-cap'):
                verify_run_artifacts(root)

    def test_changed_receipt_or_manifest_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, manifest = self.run_fixture(directory)
            manifest['fingerprint_contract']['matrix_sha256'] = '0' * 64
            (root / 'run_manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'manifest fit-matrix hash mismatch'):
                verify_run_artifacts(root)
            (root / 'fingerprint_contract.json').write_bytes((root / 'fingerprint_contract.json').read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'receipt hash mismatch'):
                verify_run_artifacts(root)

    def test_nonbinary_and_empty_inputs(self):
        data = prepared(['*CCO*'])
        bits = matrix(data['stca_calculation_smiles_hcap'])
        bits[0, 10] = 2
        with self.assertRaisesRegex(ValueError, 'must be binary'):
            audit_fit_fingerprints(data, bits)
        empty = prepared([])
        receipt = audit_fit_fingerprints(empty, np.empty((0, 167), dtype=np.uint8))
        self.assertEqual(receipt['prepared_record_n'], 0)
        self.assertEqual(receipt['status'], 'verified')


if __name__ == '__main__':
    unittest.main(verbosity=2)
