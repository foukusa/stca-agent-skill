"""Publish only current and paper rules; removed IDs must never be aliased."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(os.environ.get("STCA_TEST_SKILL_DIR",
                           str(Path(__file__).resolve().parents[1] / "skills/stca")))
SCRIPT = SKILL / "scripts/task_menu.py"
ROOT = SKILL / "assets/rule_library"
REMOVED = ("latest-gas-co2-stca-high-10", "gas-co2-high-10",
           "adept-gap-high-10", "adept-gap-author-high-10",
           "gas-co2-high-15")
CURRENT = "current-gas-co2-stca-high-10"
UNAVAILABLE = "current-pi-dc-stca-high-20"


class RemovedRuleSelection(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.library = Path(self.folder.name) / "uncreated-rules"

    def call(self, *arguments):
        return subprocess.run([sys.executable, "-S", str(SCRIPT),
                               "--library-dir", str(self.library), *arguments],
                              capture_output=True, text=True)

    def test_catalog_and_files_contain_exactly_paper_and_current_results(self):
        catalog = json.loads((ROOT / "catalog.json").read_text())
        entries = catalog["entries"]
        ids = {entry["id"] for entry in entries}
        self.assertEqual(len(entries), 83)
        self.assertEqual(sum(name.startswith("paper-") for name in ids), 11)
        self.assertEqual(sum(name.startswith("current-") for name in ids), 72)
        self.assertTrue(all(name.startswith(("paper-", "current-")) for name in ids))
        self.assertTrue(all(entry.get("user_visible", True) for entry in entries))
        self.assertEqual(sum(entry.get("available", True) for entry in entries), 82)
        self.assertEqual({p.name for p in (ROOT / "entries").iterdir()}, ids)
        self.assertEqual(len([p for p in (ROOT / "entries").rglob("*") if p.is_file()]), 249)
        for removed in REMOVED:
            self.assertNotIn(removed, ids)
            self.assertFalse((ROOT / "entries" / removed).exists())

    def test_menu_lists_82_usable_rules_and_reports_the_unavailable_result(self):
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            spec = importlib.util.spec_from_file_location("current_menu_test", SCRIPT)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            menu = module.rule_options(self.library)
        finally:
            sys.path.remove(str(SCRIPT.parent))
        ids = {choice["id"] for group in menu["groups"]
               for prop in group["properties"] for choice in prop["choices"]}
        self.assertEqual(len(ids), 82)
        self.assertIn(CURRENT, ids)
        self.assertNotIn(UNAVAILABLE, ids)
        self.assertEqual(menu["retained_builtin_entries"], 83)
        self.assertEqual(menu["explicit_hidden_builtin_entries"], 0)
        self.assertEqual([e["id"] for e in menu["unavailable_entries"]], [UNAVAILABLE])

    def test_removed_ids_are_rejected_in_screening_and_generation_without_aliasing(self):
        for removed in REMOVED:
            for task in ("2", "3"):
                with self.subTest(rule=removed, task=task):
                    result = self.call(task, "--rule", removed)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(removed, result.stderr)
                    self.assertIn("unknown", result.stderr.lower())
                    self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.library.exists())

    def test_low_level_library_rejects_removed_id_and_preserves_current_identity(self):
        result = subprocess.run([sys.executable, "-S", str(SKILL / "scripts/rule_library.py"),
                                 "show", REMOVED[0]], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown library rule", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        result = self.call("3", "--rule", CURRENT, "--generation-mode", "direct")
        self.assertEqual(result.returncode, 0, result.stderr)
        selected = json.loads(result.stdout)["selected_rules"]
        self.assertEqual([entry["id"] for entry in selected], [CURRENT])
        self.assertEqual(Path(selected[0]["constraints_path"]),
                         ROOT / "entries" / CURRENT / "constraints.json")

    def test_current_no_rule_is_unavailable_without_falling_back_to_another_rule(self):
        result = self.call("3", "--rule", UNAVAILABLE, "--generation-mode", "direct")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn(UNAVAILABLE, result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
