#!/usr/bin/env python3
"""Check explicit molecular scope without changing polymer preparation defaults.

Run with the ordinary STCA CPU dependencies:
    python tools/test_molecule_range_scope.py --skill-root /path/to/skills/stca

Four ordinary molecules stay below the t-SNE split minimum. These tests execute
the real structure preparation, registry conversions and range decisions; they
do not fit STCA rules or claim model performance.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import importlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.dont_write_bytecode = True
SKILL_ROOT = Path(os.environ.get(
    "STCA_SKILL_ROOT", str(Path(__file__).resolve().parents[1] / "skills" / "stca")
)).expanduser().resolve()


class MoleculeRangeScopeRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        cls.layer = importlib.import_module("auto_data_layer")
        if Path(cls.layer.__file__).resolve() != SKILL_ROOT / "scripts" / "auto_data_layer.py":
            raise RuntimeError("auto_data_layer was imported from a different skill root")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="stca-molecule-scope-")
        self.directory = Path(self.temporary.name)
        self.path = self.directory / "molecules.csv"
        self.smiles = ["CC", "CO", "CN", "CCO"]
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["SMILES", "target"])
            writer.writerows(zip(self.smiles, [300, 400, 500, 600]))

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self, **kwargs):
        return self.layer.prepare_dataset(
            self.path, target="target", property_name="density", unit="kg/m3", **kwargs)

    def test_explicit_molecule_keeps_conversion_and_skips_polymer_quarantine(self):
        # Influence remains enabled. No polymer-range flag may make a molecular
        # record eligible for D7 or invoke the learner to test that influence.
        with patch.object(self.layer, "stca_fit", side_effect=AssertionError("unexpected D7 fit")) as fit:
            result = self.prepare(property_domain="molecule")
        fit.assert_not_called()
        np.testing.assert_allclose(result["data"].y.to_numpy(), [.3, .4, .5, .6])
        self.assertEqual(result["data"].SMILES.tolist(), self.smiles)
        self.assertEqual(result["data"].flag_implausible.tolist(), [False] * 4)
        audit = result["audit"]
        self.assertEqual(audit["property"], "density")
        self.assertEqual(audit["property_registration"], "registered")
        self.assertEqual(audit["unit"], "g/cm3")
        self.assertEqual(audit["unit_conversion"]["multiplier"], .001)
        self.assertEqual(audit["D3_transform"], "none")
        self.assertEqual(audit["property_domain"], "molecule")
        self.assertEqual(audit["D6_registered_polymer_range"], [.7, 2.5])
        self.assertIsNone(audit["D6_plausible_range"])
        self.assertFalse(audit["D6_range_applied"])
        self.assertEqual(audit["D6_flagged"], 0)
        self.assertTrue(audit["D7_influence"]["enabled"])
        self.assertEqual(audit["D7_influence"]["candidates"], [])
        self.assertEqual(audit["D7_quarantined"], [])
        argv = audit["recommended_evaluation_argv"]
        self.assertEqual(argv[argv.index("--structure-kind") + 1], "molecule")

    def test_auto_does_not_infer_molecular_domain_from_absent_stars(self):
        implicit = self.prepare(skip_influence=True)
        explicit_auto = self.prepare(skip_influence=True, property_domain="auto")
        polymer = self.prepare(skip_influence=True, property_domain="polymer")
        for result in (implicit, explicit_auto, polymer):
            self.assertEqual(result["data"].flag_implausible.tolist(), [True] * 4)
            self.assertEqual(result["audit"]["D6_plausible_range"], [.7, 2.5])
            self.assertEqual(result["audit"]["D6_flagged"], 4)
            self.assertTrue(result["audit"]["D6_range_applied"])
            np.testing.assert_allclose(result["data"].y.to_numpy(), [.3, .4, .5, .6])
        self.assertEqual(implicit["audit"], explicit_auto["audit"])
        self.assertNotIn("--structure-kind", implicit["audit"]["recommended_evaluation_argv"])
        argv = polymer["audit"]["recommended_evaluation_argv"]
        self.assertEqual(argv[argv.index("--structure-kind") + 1], "polymer_repeat_unit")

    def test_custom_property_preserves_values_in_all_domains(self):
        for domain in ("auto", "molecule", "polymer"):
            result = self.layer.prepare_dataset(
                self.path, target="target", property_name="molecular_custom_property",
                unit="custom unit", property_domain=domain)
            audit = result["audit"]
            self.assertEqual(audit["property_registration"], "unregistered_custom")
            np.testing.assert_allclose(result["data"].y.to_numpy(), [300, 400, 500, 600])
            self.assertIsNone(audit["D6_registered_polymer_range"])
            self.assertEqual(audit["D6_flagged"], 0)
            self.assertEqual(audit["D7_quarantined"], [])

    def test_molecule_domain_does_not_bypass_unit_validation(self):
        with self.assertRaisesRegex(ValueError, "No registered conversion"):
            self.layer.prepare_dataset(
                self.path, target="target", property_name="density", unit="eV", property_domain="molecule")

    def test_unknown_domain_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "property_domain"):
            self.prepare(property_domain="guess_from_smiles")

    def test_cli_accepts_explicit_molecule_domain(self):
        captured = {}
        original = self.layer.prepare_dataset

        def capture(*args, **kwargs):
            captured.update(kwargs)
            return original(*args, **kwargs)

        with patch.object(self.layer, "prepare_dataset", side_effect=capture), contextlib.redirect_stdout(io.StringIO()):
            status = self.layer.main([
                "--input", str(self.path), "--smiles-column", "SMILES", "--target", "target",
                "--property", "density", "--unit", "kg/m3", "--property-domain", "molecule",
                "--output-dir", str(self.directory / "cli-output")])
        self.assertEqual(status, 0)
        self.assertEqual(captured["property_domain"], "molecule")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--skill-root", type=Path)
    options, remaining = parser.parse_known_args()
    if options.skill_root is not None:
        SKILL_ROOT = options.skill_root.expanduser().resolve()
    unittest.main(argv=[sys.argv[0], *remaining])
