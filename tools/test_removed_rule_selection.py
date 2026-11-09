"""Publish only current and paper rules; removed IDs must never be aliased."""
from __future__ import annotations

import importlib.util
from contextlib import redirect_stdout, redirect_stderr
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILL = Path(os.environ.get("STCA_TEST_SKILL_DIR",
                           str(Path(__file__).resolve().parents[1] / "skills/stca")))
SCRIPT = SKILL / "scripts/task_menu.py"
ROOT = SKILL / "assets/rule_library"
REMOVED = ("latest-gas-co2-stca-high-10", "gas-co2-high-10",
           "adept-gap-high-10", "adept-gap-author-high-10",
           "gas-co2-high-15")
EXPECTED_CURRENT = 13 * 3 * 2
EXPECTED_TOTAL = EXPECTED_CURRENT + 11


def load_menu_module():
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        spec = importlib.util.spec_from_file_location("current_menu_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # rule_options deliberately imports these standard-library-only modules
        # lazily; resolve them while this isolated skill path is in scope.
        __import__('rule_library')
        __import__('user_rule_library')
        return module
    finally:
        sys.path.remove(str(SCRIPT.parent))


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
        self.assertEqual(len(entries), EXPECTED_TOTAL)
        self.assertEqual(sum(name.startswith("paper-") for name in ids), 11)
        self.assertEqual(sum(name.startswith("current-") for name in ids), EXPECTED_CURRENT)
        self.assertTrue(all(name.startswith(("paper-", "current-")) for name in ids))
        self.assertTrue(all(entry.get("user_visible", True) for entry in entries))
        current = [entry for entry in entries if entry['id'].startswith('current-')]
        available = sum(entry.get('available', False) for entry in current)
        self.assertEqual(available, catalog['counts']['current_available_rules'])
        self.assertEqual(EXPECTED_CURRENT - available, catalog['counts']['current_unavailable_results'])
        water = [entry for entry in current if entry['dataset'] == 'OPENPOLY_WCA']
        self.assertEqual({(entry['method'], entry['tier']) for entry in water},
                         {(method, tier) for method in ('STCA', 'WRAcc') for tier in (.1, .2, .3)})
        self.assertEqual({p.name for p in (ROOT / "entries").iterdir()}, ids)
        expected_files = {ROOT / relative for entry in entries
                          for relative in [entry['constraints'], *entry['prompts'].values()]}
        self.assertEqual({path for path in (ROOT / 'entries').rglob('*') if path.is_file()}, expected_files)
        for removed in REMOVED:
            self.assertNotIn(removed, ids)
            self.assertFalse((ROOT / "entries" / removed).exists())

    def test_menu_lists_every_usable_rule_and_reports_actual_unavailable_results(self):
        module = load_menu_module()
        menu = module.rule_options(self.library)
        catalog = json.loads((ROOT / 'catalog.json').read_text())
        usable = {entry['id'] for entry in catalog['entries'] if entry.get('available', True)}
        unavailable = {entry['id'] for entry in catalog['entries'] if not entry.get('available', True)}
        ids = {choice['id'] for group in menu['groups']
               for prop in group['properties'] for choice in prop['choices']}
        self.assertEqual(ids, usable)
        self.assertEqual(menu['retained_builtin_entries'], EXPECTED_TOTAL)
        self.assertEqual(menu['explicit_hidden_builtin_entries'], 0)
        self.assertEqual({entry['id'] for entry in menu['unavailable_entries']}, unavailable)

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
        catalog = json.loads((ROOT / 'catalog.json').read_text())
        current = next(entry['id'] for entry in catalog['entries']
                       if entry['id'].startswith('current-') and entry.get('available'))
        result = self.call("3", "--rule", current, "--generation-mode", "direct")
        self.assertEqual(result.returncode, 0, result.stderr)
        selected = json.loads(result.stdout)["selected_rules"]
        self.assertEqual([entry["id"] for entry in selected], [current])
        self.assertEqual(Path(selected[0]["constraints_path"]),
                         ROOT / "entries" / current / "constraints.json")

    def test_no_rule_and_empty_conditions_are_unavailable_without_fallback(self):
        module = load_menu_module()
        catalog = json.loads((ROOT / 'catalog.json').read_text())
        original = next(entry for entry in catalog['entries'] if entry['id'].startswith('paper-'))
        constraint = json.loads((ROOT / original['constraints']).read_text())
        for invalid_rule in (None, {'keys': [], 'values': [], 'expression': ''}):
            with self.subTest(rule=invalid_rule):
                fixture = Path(self.folder.name) / ('no-rule' if invalid_rule is None else 'empty-rule')
                fixture.mkdir()
                entries = []
                for method in ('STCA', 'WRAcc'):
                    identifier = f'current-pi-test-{method.lower()}-high-30'
                    entry = copy.deepcopy(original)
                    entry.update(id=identifier, dataset='PI_TEST', method=method,
                                 provenance={'kind': 'test_source_frozen_rule'},
                                 available=method == 'WRAcc', is_primary=method == 'WRAcc',
                                 constraints=f'entries/{identifier}/constraints.json',
                                 prompts={lang: f'entries/{identifier}/prompt.{lang}.md'
                                          for lang in ('en', 'zh-CN')})
                    payload = copy.deepcopy(constraint)
                    payload['rule'] = invalid_rule if method == 'STCA' else constraint['rule']
                    path = fixture / entry['constraints']
                    path.parent.mkdir(parents=True)
                    path.write_text(json.dumps(payload))
                    for relative in entry['prompts'].values():
                        (fixture / relative).write_text('Frozen prompt fixture')
                    entries.append(entry)
                (fixture / 'catalog.json').write_text(json.dumps({**catalog, 'entries': entries}))
                options = module.rule_options(self.library, catalog_root=fixture)
                absent = entries[0]['id']
                self.assertEqual([item['id'] for item in options['unavailable_entries']], [absent])
                available = [item for group in options['groups'] for prop in group['properties']
                             for item in prop['choices']]
                self.assertEqual([item['id'] for item in available], [entries[1]['id']])
                with self.assertRaisesRegex(ValueError, 'unavailable'):
                    module.resolve_rules(options, [absent])
                original_options = module.rule_options
                def fixture_options(*args, **kwargs):
                    return original_options(*args, catalog_root=fixture, **kwargs)
                for task in ('2', '3'):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    arguments = [task, '--rule', absent, '--library-dir', str(self.library)]
                    if task == '3':
                        arguments += ['--generation-mode', 'direct']
                    with patch.object(module, 'rule_options', side_effect=fixture_options), \
                            redirect_stdout(stdout), redirect_stderr(stderr):
                        self.assertEqual(module.main(arguments), 2)
                    self.assertEqual(stdout.getvalue(), '')
                    self.assertIn('unavailable', stderr.getvalue())
                    self.assertIn(absent, stderr.getvalue())
        self.assertFalse(self.library.exists())


if __name__ == "__main__":
    unittest.main()
