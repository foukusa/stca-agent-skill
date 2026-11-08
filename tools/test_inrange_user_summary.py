#!/usr/bin/env python3
"""Public delivery contract tests; no model fitting or uploaded data required."""
from __future__ import annotations

import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SKILL_DIR = Path(os.environ.get(
    "STCA_TEST_SKILL_DIR", str(Path(__file__).resolve().parents[1] / "skills" / "stca")))
MODULE_PATH = SKILL_DIR / "scripts" / "inrange_evaluation.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("inrange_user_summary_under_test", MODULE_PATH)
inrange = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inrange)


def fixture(*, primary="WRAcc", cutoff=1234.5):
    row = {
        "tier": .15, "deployment_cutoff_physical": cutoff,
        "primary": primary, "alternative": "STCA" if primary == "WRAcc" else "WRAcc",
        "recommendation_reason": "WRAcc_AS_exceeds_STCA_by_more_than_0.02"
        if primary == "WRAcc" else "STCA_retained_WRAcc_advantage_not_more_than_0.02",
        "cv_stca_status": "evaluated", "cv_wracc_status": "evaluated",
        "cv_stca_AS_mean": .5, "cv_stca_AS_sd": .03,
        "cv_wracc_AS_mean": .55, "cv_wracc_AS_sd": .02,
        "stca_rule": "K112=1", "wracc_rule": "K106=0 AND K112=1",
    }
    deployment = [
        {"method": "STCA", "tier": .15, "status": "rule_fitted",
         "selected_original_row_n": 3, "unknown_original_row_n": 1},
        {"method": "WRAcc", "tier": .15, "status": "rule_fitted",
         "selected_original_row_n": 5, "unknown_original_row_n": 1},
    ]
    return row, deployment


class UserSummaryContract(unittest.TestCase):
    def summary(self, row, deployment, *, direction="high", unit="Barrer"):
        return inrange.user_summary([row], deployment, target_name="test_property",
                                    direction=direction, unit=unit, original_input_rows=10)

    def test_storage_warning_keeps_the_comparison_table_intact(self):
        row, deployment = fixture()
        summary = self.summary(row, deployment)
        summary["storage_warnings"] = [{"method": "STCA", "operation": "save_rule_library",
                                        "error_type": "PermissionError", "error": "Denied test rule directory"}]
        lines = inrange.render_user_summary(summary).splitlines()
        header = next(i for i, line in enumerate(lines) if line.startswith("| 档位 |"))
        self.assertTrue(lines[header + 1].startswith("|---"))
        self.assertTrue(lines[header + 2].startswith("| Top 15% |"))
        warning = next(i for i, line in enumerate(lines) if line.startswith("存储提示"))
        self.assertLess(warning, header)

    def test_high_physical_units_and_distinct_method_deliveries(self):
        row, deployment = fixture()
        summary = self.summary(row, deployment)
        item = summary["tiers"][0]
        self.assertEqual((item["label"], item["operator"], item["physical_cutoff"], item["unit"]),
                         ("Top 15%", ">=", 1234.5, "Barrer"))
        self.assertEqual((item["recommended_method"], item["alternative_method"]), ("WRAcc", "STCA"))
        self.assertEqual(item["recommendation_reason"], row["recommendation_reason"])
        for method, selected, rejected in (("STCA", 3, 6), ("WRAcc", 5, 4)):
            result = item["methods"][method]
            self.assertEqual((result["selected_n"], result["not_selected_n"], result["unknown_n"]),
                             (selected, rejected, 1))
            self.assertEqual(result["cv_AS_mean"], row[f"cv_{method.lower()}_AS_mean"])
            self.assertEqual(result["cv_AS_sd"], row[f"cv_{method.lower()}_AS_sd"])
            self.assertEqual(result["results_with_failed_conditions"],
                             f"{method.lower()}/tier_0.15/screening/results.csv")
            self.assertEqual(result["selected_rows"], f"{method.lower()}/tier_0.15/selected.csv")
        text = inrange.render_user_summary(summary)
        self.assertIn(">= 1234.5 Barrer", text)
        self.assertIn("**STCA**：入选 3，未入选 6，未知 1", text)
        self.assertIn("**WRAcc**：入选 5，未入选 4，未知 1", text)
        self.assertIn("[全部原行及未满足的规则条件](stca/tier_0.15/screening/results.csv)", text)
        self.assertIn("[全部原行及未满足的规则条件](wracc/tier_0.15/screening/results.csv)", text)
        self.assertIn("主推：**WRAcc**；备选：STCA", text)

    def test_low_tail_preserves_original_units_and_operator(self):
        row, deployment = fixture(primary="STCA", cutoff=1.25)
        summary = self.summary(row, deployment, direction="low", unit="g/cm3")
        item = summary["tiers"][0]
        self.assertEqual((item["label"], item["operator"], item["physical_cutoff"], item["unit"]),
                         ("Bottom 15%", "<=", 1.25, "g/cm3"))
        text = inrange.render_user_summary(summary)
        self.assertIn("<= 1.25 g/cm3", text)
        self.assertIn("主推：**STCA**；备选：WRAcc", text)

    def test_no_rule_and_unavailable_scores_remain_unknown(self):
        row, deployment = fixture(cutoff=None)
        row.update(primary=None, alternative=None,
                   recommendation_reason="no_valid_full_data_rule_for_either_method")
        for method in ("stca", "wracc"):
            row[f"cv_{method}_status"] = "unavailable_no_usable_records"
            row[f"cv_{method}_AS_mean"] = math.nan
            row[f"cv_{method}_AS_sd"] = None
            row[f"{method}_rule"] = None
        for entry in deployment:
            entry.update(status="no_valid_rule", selected_original_row_n=0,
                         unknown_original_row_n=10)
        summary = self.summary(row, deployment)
        item = summary["tiers"][0]
        self.assertIsNone(item["physical_cutoff"])
        self.assertIsNone(item["recommended_method"])
        for result in item["methods"].values():
            self.assertEqual((result["selected_n"], result["not_selected_n"], result["unknown_n"]),
                             (0, 0, 10))
            self.assertIsNone(result["cv_AS_mean"])
            self.assertIsNone(result["cv_AS_sd"])
            self.assertEqual(result["status"], "no_valid_rule")
        # Strict JSON is required: unavailable evidence must not become NaN or zero.
        json.dumps(summary, allow_nan=False)
        text = inrange.render_user_summary(summary)
        self.assertIn("不可评价", text)
        self.assertIn("无有效规则，结果保持未知", text)
        self.assertNotIn("nan", text.lower())
        self.assertNotIn(">= 0 Barrer", text)

    def test_impossible_counts_are_rejected(self):
        for selected, unknown in ((-1, 0), (0, -1), (7, 4)):
            with self.subTest(selected=selected, unknown=unknown):
                row, deployment = fixture()
                deployment[0].update(selected_original_row_n=selected,
                                     unknown_original_row_n=unknown)
                with self.assertRaisesRegex(ValueError, "counts"):
                    self.summary(row, deployment)

    def test_method_choice_requires_advantage_strictly_above_margin(self):
        for score, expected in ((.49, "STCA"), (.51, "STCA"), (.52, "STCA"), (.520001, "WRAcc")):
            with self.subTest(wracc_AS=score):
                method, _ = inrange.choose_by_cv({"AS_mean": .5}, {"AS_mean": score})
                self.assertEqual(method, expected)
        for left, right in ((None, .7), (.5, None), (None, None)):
            method, reason = inrange.choose_by_cv({"AS_mean": left}, {"AS_mean": right})
            self.assertEqual(method, "STCA")
            self.assertEqual(reason, "STCA_default_comparison_unavailable")

    def test_cli_omitted_tiers_use_10_20_30_without_manual_transform_or_step(self):
        captured = []
        with patch.object(inrange, "run", side_effect=lambda args: captured.append(args) or 0):
            self.assertEqual(inrange.main(["--input", "unused.csv", "--target", "CO2",
                                           "--output-dir", "unused-out"]), 0)
        args = captured[0]
        self.assertEqual(inrange.parse_tiers(args.tiers), [.10, .20, .30])
        self.assertFalse(args.already_log)
        self.assertFalse(hasattr(args, "step"))
        self.assertEqual((args.folds, args.repeats), (5, 3))

    def test_cli_custom_percent_tiers_reach_run_unchanged(self):
        captured = []
        with patch.object(inrange, "run", side_effect=lambda args: captured.append(args) or 0):
            self.assertEqual(inrange.main(["--input", "unused.csv", "--target", "CO2",
                                           "--tiers", "15%", "25%", "--output-dir", "unused-out"]), 0)
        self.assertEqual(captured[0].tiers, ["15%", "25%"])
        self.assertEqual(inrange.parse_tiers(captured[0].tiers), [.15, .25])
        self.assertEqual(inrange.parse_tiers([".15,25%"]), [.15, .25])

    def test_invalid_or_duplicate_tiers_are_not_silently_accepted(self):
        for values in (["0%"], ["100%"], ["-1%"], ["nan"], ["15%", ".15"]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    inrange.parse_tiers(values)

    def test_explicit_holdout_entry_also_defaults_to_10_20_30(self):
        import auto_screen
        from custom_fit import parse_tiers
        captured = []
        with patch.object(auto_screen, "run", side_effect=lambda args: captured.append(args) or 0):
            self.assertEqual(auto_screen.main(["--input", "unused.csv", "--target", "CO2",
                "--unit", "Barrer", "--direction", "high", "--output-dir", "unused-out"]), 0)
        self.assertEqual(parse_tiers(captured[0].tiers), (.10, .20, .30))


if __name__ == "__main__":
    unittest.main(verbosity=2)
