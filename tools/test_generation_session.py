"""Generation review gates, prompt revisions and exact-constraint integrity."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(os.environ.get("STCA_TEST_SKILL_DIR", Path(__file__).resolve().parents[1] / "skills/stca"))
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("generation_session_under_test", SCRIPTS / "generation_session.py")
session = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session)


def example():
    return {"schema": "stca-library-constraints-v1", "catalog_id": "density-low-20",
            "property": "density", "direction": "low", "tier": 0.2,
            "target": {"physical_cutoff": 1.1, "unit": "g/cm3", "operator": "<="},
            "rule": {"keys": [141, 164], "values": [0, 1]}}


class GenerationSessionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.constraint = self.root / "constraints.json"
        self.constraint.write_text(json.dumps(example()), encoding="utf-8")
        self.output = self.root / "generation"

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self, mode="preview", **kwargs):
        return session.prepare_session([self.constraint], self.output, mode=mode, **kwargs)

    def test_review_stages_complete_prompt_without_authorizing_generation(self):
        result = self.prepare(count=7, preferences="使用芳香醚。")
        self.assertFalse(result["generation_allowed"])
        self.assertFalse(result["generation_performed"])
        self.assertIsNone(result["approved_prompt_path"])
        self.assertEqual(result["next_action"], "show_full_prompt_and_wait_for_user_confirmation")
        prompt = Path(result["prompt_path"]).read_text(encoding="utf-8")
        for text in ("K141=0 AND K164=1", "density", "Bottom 20%", "1.1 g/cm3", "使用芳香醚。", "H-cap"):
            self.assertIn(text, prompt)
        # Merely reading it again, even in a new process, cannot create approval.
        status = session.session_status(self.output, include_prompt=True)
        self.assertFalse(status["generation_allowed"])
        self.assertEqual(status["prompt"], prompt)

    def test_confirmation_approves_exact_current_prompt(self):
        initial = self.prepare()
        with self.assertRaisesRegex(ValueError, "confirmation"):
            session.confirm_session(self.output, confirmation_text=" ")
        approved = session.confirm_session(self.output, confirmation_text="确认，按这个生成。")
        self.assertTrue(approved["generation_allowed"])
        self.assertFalse(approved["generation_performed"])
        self.assertEqual(approved["next_action"], "invoke_current_llm_and_verify")
        self.assertEqual(Path(approved["approved_prompt_path"]).read_bytes(), Path(initial["prompt_path"]).read_bytes())
        self.assertEqual(approved["current_prompt_sha256"], approved["approved_prompt_sha256"])
        self.assertEqual(approved["authorization"]["text"], "确认，按这个生成。")

    def test_direct_mode_authorizes_current_llm_without_second_confirmation(self):
        result = self.prepare("direct", language="en", count=3)
        self.assertTrue(result["generation_allowed"])
        self.assertEqual(result["authorization"]["kind"], "direct_mode_requested")
        self.assertEqual(result["executor"], "current_ai_assistant")
        self.assertFalse(result["api_configuration_required"])
        self.assertFalse(result["generation_performed"])
        self.assertTrue(Path(result["approved_prompt_path"]).is_file())

    def test_revision_keeps_frozen_conditions_and_requires_new_confirmation(self):
        original = self.prepare("direct", count=3)
        draft = self.root / "my-adjustments.md"
        draft.write_text("优先线性结构，CSV 中加入设计理由。", encoding="utf-8")
        edited = session.revise_session(self.output, count=5, preferences="不用氟。", draft_file=draft)
        self.assertFalse(edited["generation_allowed"])
        self.assertIsNone(edited["approved_prompt_path"])
        self.assertEqual(edited["revision"], 2)
        self.assertNotEqual(original["current_prompt_sha256"], edited["current_prompt_sha256"])
        text = Path(edited["prompt_path"]).read_text(encoding="utf-8")
        for expected in ("K141=0 AND K164=1", "1.1 g/cm3", "不用氟。", "优先线性结构"):
            self.assertIn(expected, text)
        approved = session.confirm_session(self.output, confirmation_text="确认修改后的版本")
        self.assertEqual(approved["approved_revision"], 2)
        self.assertEqual(approved["approved_prompt_sha256"], edited["current_prompt_sha256"])
        self.assertTrue(Path(original["approved_prompt_path"]).is_file())

    def test_constraint_snapshot_is_authoritative_even_if_original_changes(self):
        initial = self.prepare()
        changed = example()
        changed["rule"]["values"] = [1, 0]
        self.constraint.write_text(json.dumps(changed), encoding="utf-8")
        stable = session.confirm_session(self.output, confirmation_text="确认")
        self.assertEqual(stable["constraints"], initial["constraints"])
        self.assertIn("K141=0 AND K164=1", Path(stable["approved_prompt_path"]).read_text(encoding="utf-8"))

    def test_changed_constraint_snapshot_refuses_confirmation(self):
        initial = self.prepare()
        snapshot = self.output / initial["constraints"][0]["snapshot_path"]
        snapshot.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            session.confirm_session(self.output, confirmation_text="确认")

    def test_changed_prompt_or_approved_prompt_refuses_generation_status(self):
        initial = self.prepare("direct")
        Path(initial["approved_prompt_path"]).write_text("Use K164=0 instead", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Approved prompt changed"):
            session.session_status(self.output)
        # Restore the approved copy, then tamper with the visible prompt.
        Path(initial["approved_prompt_path"]).write_bytes(Path(initial["prompt_path"]).read_bytes())
        Path(initial["prompt_path"]).write_text("Use K164=0 instead", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Prompt content changed"):
            session.session_status(self.output)

    def test_revisions_validate_before_writing_and_session_never_overwrites(self):
        initial = self.prepare()
        before = (self.output / "session.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "positive integer"):
            session.revise_session(self.output, count=0)
        self.assertEqual((self.output / "session.json").read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "Output directory exists"):
            self.prepare("direct")
        self.assertEqual((self.output / "session.json").read_bytes(), before)
        self.assertTrue(Path(initial["prompt_path"]).is_file())

    def test_conflicting_objectives_refuse_before_creating_session(self):
        second = self.root / "second.json"
        constraint = example()
        constraint["rule"]["values"] = [1, 1]
        second.write_text(json.dumps(constraint), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Contradictory"):
            session.prepare_session([self.constraint, second], self.output, mode="direct")
        self.assertFalse(self.output.exists())

    def test_stdlib_cli_preview_edit_confirm_has_no_generation_side_effect(self):
        script = str(SCRIPTS / "generation_session.py")
        command = [sys.executable, "-S", script]
        def run(arguments, expected=0):
            result = subprocess.run(command + arguments, capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            return json.loads(result.stdout) if expected == 0 else result
        initial = run(["prepare", "--constraints", str(self.constraint), "--mode", "preview",
                       "--output-dir", str(self.output), "--count", "2"])
        self.assertFalse(initial["generation_allowed"])
        edited = run(["revise", "--session", str(self.output), "--count", "4", "--preferences", "Use ethers."])
        self.assertFalse(edited["generation_allowed"])
        run(["confirm", "--session", str(self.output)], expected=2)
        approved = run(["confirm", "--session", str(self.output), "--confirmation-text", "Proceed with the revised prompt."])
        self.assertTrue(approved["generation_allowed"])
        self.assertFalse(approved["verification_performed"])
        current = run(["status", "--session", str(self.output), "--include-prompt"])
        self.assertIn("Use ethers.", current["prompt"])
        self.assertEqual(list(self.output.glob("*.csv")), [])


if __name__ == "__main__":
    unittest.main()
