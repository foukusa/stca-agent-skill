"""User percentage defaults, exact physical cutoffs and dual-method delivery."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(os.environ.get("STCA_TEST_SKILL_DIR", Path(__file__).resolve().parents[1] / "skills/stca"))
SCRIPT = SKILL / "scripts/task_menu.py"


class PercentageMethodContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="stca-percentage-contract-")
        self.addCleanup(self.temporary.cleanup)
        self.library = Path(self.temporary.name) / "uncreated-rules"

    def call(self, *arguments):
        result = subprocess.run([sys.executable, "-S", str(SCRIPT), "--library-dir", str(self.library), *arguments],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_missing_percentages_use_defaults_without_becoming_a_question(self):
        result = self.call("1")
        self.assertEqual(result["default_tiers"], [0.1, 0.2, 0.3])
        policy = result["percentage_policy"]
        self.assertEqual(policy["default_when_omitted"], "use_default_tiers_without_a_followup_question_once_target_is_clear")
        self.assertTrue(policy["allow_user_defined_tiers"])
        self.assertTrue(policy["accept_nonstandard_tiers"])
        self.assertTrue(policy["never_replace_explicit_tiers_with_defaults"])
        self.assertFalse(result["choice_required"])
        self.assertFalse(any("tier" in value or "percentage" in value for value in result["ask_only_if_missing"]))
        self.assertFalse(self.library.exists())

    def test_two_methods_and_explicit_recommendation_are_required_deliverables(self):
        result = self.call("1")
        policy = result["method_policy"]
        self.assertEqual(policy["default_training_methods"], ["STCA", "WRAcc"])
        self.assertTrue(policy["deliver_both_methods_independently"])
        self.assertTrue(policy["recommendation_per_tier"])
        self.assertEqual(policy["wracc_advantage_required"], 0.02)
        self.assertEqual(policy["wracc_selection_comparison"], "strictly_greater_than")
        self.assertEqual(policy["otherwise_prefer"], "STCA")
        self.assertTrue(policy["accept_recommended_method_without_another_confirmation"])
        required = set(result["required_summary_columns"])
        self.assertTrue({"percentage", "physical_cutoff", "physical_comparison", "physical_unit",
                         "stca_selected", "wracc_selected", "stca_AS", "wracc_AS",
                         "recommended_method", "recommendation_reason"} <= required)

    def test_existing_default_tiers_never_choose_or_fabricate_a_rule(self):
        for task in ("2", "3"):
            result = self.call(task)
            self.assertTrue(result["rule_choice_required"])
            self.assertEqual(result["selected_rules"], [])
            policy = result["percentage_policy"]
            self.assertTrue(policy["require_exact_frozen_tier"])
            self.assertTrue(policy["never_nearest_neighbor_or_interpolate"])
            self.assertTrue(policy["do_not_choose_source_property_or_frozen_rule_from_tier_defaults"])
            self.assertEqual(policy["missing_frozen_tier"], "use_a_saved_exact_tier_or_offer_learning_from_labelled_data")
            self.assertTrue(result["method_policy"]["use_catalog_primary_when_recommendation_accepted"])
            self.assertTrue(result["method_policy"]["honor_explicit_method_choice"])
            self.assertEqual(result["next_action"], "choose_rule_and_wait")

    def test_screening_defaults_apply_after_target_choice_and_keep_method_results_separate(self):
        result = self.call("2")
        self.assertEqual(result["default_tiers"], [0.1, 0.2, 0.3])
        self.assertEqual(result["percentage_policy"]["when_omitted"],
                         "once_source_property_and_direction_are_clear_apply_all_available_default_tiers_without_asking_for_percentages")
        policy = result["method_policy"]
        self.assertEqual(policy["default_screening_methods"], ["STCA", "WRAcc"])
        self.assertTrue(policy["deliver_both_methods_independently_when_available"])
        self.assertTrue(policy["report_per_tier_primary_and_reason"])
        self.assertEqual(policy["explicit_single_method_choice"], "apply_only_the_named_method")
        self.assertIn("never_pass_alternative_methods_to_an_implicit_AND", policy["method_comparison_execution"])

    def test_generation_uses_selected_tier_without_implicit_multi_tier_expansion(self):
        result = self.call("3", "--rule", "current-gas-co2-stca-high-10", "--generation-mode", "preview")
        self.assertIsNone(result["default_tiers"])
        self.assertFalse(result["percentage_policy"]["implicit_default_tiers_for_generation"])
        self.assertTrue(result["percentage_policy"]["never_AND_same_property_different_tiers"])
        self.assertFalse(result["generation_policy"]["implicit_multi_tier_generation"])
        self.assertEqual(result["generation_policy"]["explicit_multi_tier_request"], "independent_sessions_per_tier")
        self.assertFalse(result["generation_gate"]["generation_allowed"])
        self.assertTrue(result["generation_gate"]["confirmation_required"])

    def test_selected_builtin_cutoff_matches_frozen_physical_target_and_unit(self):
        result = self.call("2", "--rule", "current-gas-co2-stca-high-10")
        choice = result["selected_rules"][0]
        constraint = json.loads(Path(choice["constraints_path"]).read_text(encoding="utf-8"))
        target = constraint["target"]
        self.assertEqual(choice["physical_cutoff"], target["physical_cutoff"])
        self.assertEqual(choice["physical_unit"], "Barrer")
        self.assertEqual(choice["physical_comparison"], ">=")
        self.assertEqual(choice["physical_cutoff_status"], "available")
        self.assertFalse(result["rule_choice_required"])
        self.assertFalse(result["choice_required"])
        self.assertEqual(result["next_action"], "execute_requested_task")

    def test_saved_target_uses_physical_not_logarithmic_cutoff(self):
        spec = importlib.util.spec_from_file_location("stca_menu_targets", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        constraint = {"schema": "stca-constraints-v1", "target": {
            "direction": "low", "physical_train_cutoff": 1000.0,
            "physical_unit": "Barrer", "model_space_cutoff": 3.0,
            "model_space_unit": "log10(Barrer)", "label_comparison": "<="}}
        result = module.physical_target(constraint)
        self.assertEqual(result["physical_cutoff"], 1000.0)
        self.assertEqual(result["physical_unit"], "Barrer")
        self.assertEqual(result["physical_comparison"], "<=")
        self.assertEqual(result["physical_cutoff_status"], "available")
        del constraint["target"]["physical_train_cutoff"]
        result = module.physical_target(constraint)
        self.assertIsNone(result["physical_cutoff"])
        self.assertEqual(result["physical_cutoff_status"], "not_provided")


if __name__ == "__main__":
    unittest.main()
