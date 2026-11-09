#!/usr/bin/env python3
"""Exercise preparation, screening and CV invariance to companion tiers."""
from __future__ import annotations

import concurrent.futures
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = Path(os.environ.get(
    "STCA_TEST_SKILL_DIR", str(Path(__file__).resolve().parents[1] / "skills" / "stca")))


class TierIndependence(unittest.TestCase):
    def test_single_batch_and_reordered_requests_have_identical_objective_results(self):
        try:
            import pandas as pd
            import rdkit  # noqa: F401
        except ImportError:
            self.skipTest("Numerical and chemistry dependencies are required for integration.")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "input.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["CandidateKey", "smiles", "density", "condition"])
                # Different connection graphs may share an H-cap, and each
                # repeated observation has an explicit distinct condition.
                for repeat in range(2):
                    for number in range(1, 21):
                        for branch in (False, True):
                            structure = f"*C({'C' * number})O*" if branch else f"*{'C' * number}O*"
                            value = .85 + ((number * 13 + repeat * 7 + branch * 17) % 100) / 100
                            if number == 1 and not branch and repeat == 0:
                                value = 4.5  # Exercise the tier-dependent influence diagnostic.
                            writer.writerow([f"id-{repeat}-{number}-{int(branch)}", structure,
                                             value, f"observation-{repeat}-{number}-{int(branch)}"])
            cases = {"single": [".3"], "batch": [".1", ".3"], "reordered": [".3", ".1"]}

            def run(item):
                name, tiers = item
                done = subprocess.run([sys.executable, str(SKILL_DIR / "scripts/inrange_evaluation.py"),
                    "--input", str(source), "--target", "density", "--property", "Density",
                    "--unit", "g/cm3", "--smiles-column", "smiles", "--id-column", "CandidateKey",
                    "--condition-columns", "condition", "--structure-kind", "polymer_repeat_unit",
                    "--tiers", *tiers, "--wracc-max-literals", "3", "--folds", "2", "--repeats", "1",
                    "--output-dir", str(root / name), "--library-dir", str(root / (name + "_rules"))],
                    capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stderr)

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                list(executor.map(run, cases.items()))
            expected = None
            for name in cases:
                output = root / name
                summary = json.loads((output / "screening_summary.json").read_text())
                tier = next(item for item in summary["tiers"] if item["fraction"] == .3)
                selected = {key: tier[key] for key in (
                    "physical_cutoff", "recommended_method", "recommendation_reason", "methods", "preparation")}
                if expected is None:
                    expected = selected
                self.assertEqual(selected, expected)
                receipt = json.loads((output / "delivery_verification.json").read_text())
                self.assertTrue(receipt["all_tiers_verified"])
                manifest = json.loads((output / "run_manifest.json").read_text())
                preparation = output / manifest["per_tier_preparation"]["0.3"]["preparation_directory"]
                initial_preparation = root / "single/preparation"
                actual_audit = json.loads((preparation / "audit.json").read_text())
                reference_audit = json.loads((initial_preparation / "audit.json").read_text())
                # Suggested follow-up commands naturally contain each output path.
                for audit in (actual_audit, reference_audit):
                    audit.pop("recommended_evaluation_argv", None)
                    audit.pop("recommended_evaluation_command", None)
                self.assertEqual(actual_audit, reference_audit)
                self.assertEqual(reference_audit["D7_influence"]["status"], "evaluated")
                self.assertTrue(reference_audit["D7_influence"]["candidates"])
                self.assertFalse(reference_audit["D4_hcap_aggregation"])
                for method in ("stca", "wracc"):
                    actual = pd.read_csv(output / method / "tier_0.3/screening/results.csv", dtype=str,
                                         keep_default_na=False)
                    reference = pd.read_csv(root / "single" / method / "tier_0.3/screening/results.csv",
                                            dtype=str, keep_default_na=False)
                    # Whole-model hashes differ because multi-tier artifacts
                    # carry additional objectives; outcomes and conditions do not.
                    columns = [column for column in reference if "model_sha256" not in column]
                    self.assertTrue(actual[columns].equals(reference[columns]))
                actual = pd.read_csv(output / "cv_oof_predictions.csv")
                actual = actual[actual.tier.eq(.3)].reset_index(drop=True)
                self.assertTrue(actual.equals(pd.read_csv(root / "single/cv_oof_predictions.csv")))


if __name__ == "__main__":
    unittest.main()
