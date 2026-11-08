"""Exercise real rule save/reload/import with denied destructive file operations."""
from contextlib import ExitStack, contextmanager
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import numpy as np

SKILL = Path(os.environ.get('STCA_TEST_SKILL_DIR', Path(__file__).resolve().parents[1] / 'skills/stca'))
sys.path.insert(0, str(SKILL / 'scripts'))
import user_rule_library as library
from frozen_literal_model import create_model_artifact, FrozenLiteralModel
from stca_tools import _constraint, _load_model


@contextmanager
def denied_rename_and_delete():
    def denied(*args, **kwargs):
        raise PermissionError('simulated host policy: rename/delete denied')
    with ExitStack() as stack:
        for target in ['os.rename', 'os.replace', 'os.unlink', 'os.remove', 'shutil.rmtree',
                       'pathlib.Path.rename', 'pathlib.Path.replace', 'pathlib.Path.unlink']:
            stack.enter_context(patch(target, side_effect=denied))
        yield


class RuleStoragePermissionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stca storage policy ')
        self.root = Path(self.temp.name)
        self.model_path = self.root / 'original-model.json'
        self.constraint_path = self.root / 'original-constraints.json'
        artifact = create_model_artifact(target_name='Density', target_unit='g/cm3', direction='high',
            feature_spec={'kind': 'rdkit_maccs167'}, learner='WRAcc',
            custom_data_contract={'property': 'Density', 'original_unit': 'g/cm3', 'model_unit': 'g/cm3',
                'transform': 'none', 'representation': 'hcap_maccs167', 'structure_kind': 'polymer_repeat_unit'},
            tiers={'0.3': {'train_cutoff': 1.2, 'selected_rule': 'test_rule', 'rules': [
                {'rule': {'keys': [42, 161], 'values': [1, 0], 'name': 'test_rule', 'family': 'WRAcc_test'}}]}})
        self.model_path.write_bytes(library.json_bytes(artifact))
        stca = SimpleNamespace(NoValidRuleError=ValueError)
        model, metadata = _load_model(stca, {'model': str(self.model_path), 'profile': None, 'protocol': None}, self.root)
        self.constraint_path.write_bytes(library.json_bytes(_constraint(stca, model, metadata, .3)))
        self.lib = self.root / 'my-rules'

    def tearDown(self):
        self.temp.cleanup()

    def save(self, root=None):
        return library.save_entry(root or self.lib, 'My Density WRAcc rules', self.model_path,
                                  [self.constraint_path], count=5, preferences='Prefer ethers.')

    def test_save_export_import_and_reload_without_rename_or_delete(self):
        original_bytes = self.model_path.read_bytes()
        with denied_rename_and_delete():
            saved = self.save()
            self.assertEqual(saved['status'], 'saved')
            first = saved['entry']
            shown = library.show_entry(self.lib, first['id'])
            self.assertEqual(shown['learner'], 'WRAcc')
            self.assertEqual(len(library.list_entries(self.lib)['entries']), 1)
            archive = self.root / 'portable.zip'
            exported = library.export_entry(self.lib, first['id'], archive)
            self.assertEqual(exported['status'], 'exported')
            imported = library.import_entry(self.lib, archive)
            self.assertEqual(imported['status'], 'saved')
            second = imported['entry']
            self.assertNotEqual(first['id'], second['id'])
            self.assertEqual(second['model']['artifact_sha256'], first['model']['artifact_sha256'])
            self.assertEqual(second['imported_from']['id'], first['id'])
            self.assertEqual(len(library.list_entries(self.lib)['entries']), 2)
            self.assertEqual(library.list_entries(self.lib)['invalid_entries'], [])
            matrix = np.zeros((3, 167), dtype=np.int8)
            matrix[0, 42] = 1
            matrix[1, [42, 161]] = 1
            for entry in [first, second]:
                restored = FrozenLiteralModel.load(entry['model_path'])
                self.assertEqual(restored.screen_fingerprints(matrix, tier=.3)['selected'].tolist(), [True, False, False])
                self.assertEqual(Path(entry['model_path']).read_bytes(), original_bytes)
                for rule in entry['usable_rules']:
                    for prompt_path in rule['prompt_paths'].values():
                        self.assertIn('K42=1 AND K161=0', Path(prompt_path).read_text())
        self.assertEqual(self.model_path.read_bytes(), original_bytes)

    def test_record_is_written_after_every_payload_and_verified_before_success(self):
        original_open = Path.open
        observed = []
        def observe(path, mode='r', *args, **kwargs):
            if mode == 'xb' and path.is_relative_to(self.lib):
                observed.append(path.name)
                if path.name == 'record.json':
                    self.assertTrue((path.parent / 'model.json').is_file())
                    self.assertTrue((path.parent / 'tiers/0.3/prompt.en.md').is_file())
                    self.assertTrue((path.parent / 'tiers/0.3/prompt.zh-CN.md').is_file())
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', observe):
            self.save()
        self.assertEqual(observed[-1], 'record.json')

    def test_payload_permission_denial_is_preserved_and_partial_entry_is_not_ready(self):
        original_open = Path.open
        def deny_prompt(path, mode='r', *args, **kwargs):
            if mode == 'xb' and path.name == 'prompt.zh-CN.md' and path.is_relative_to(self.lib):
                raise PermissionError('host denied this prompt write')
            return original_open(path, mode, *args, **kwargs)
        with denied_rename_and_delete(), patch.object(Path, 'open', deny_prompt):
            with self.assertRaisesRegex(PermissionError, 'host denied this prompt write'):
                self.save()
            inventory = library.list_entries(self.lib)
            self.assertEqual(inventory['entries'], [])
            self.assertEqual(len(inventory['invalid_entries']), 1)
            partial = next(self.lib.glob('rules-*'))
            self.assertTrue((partial / 'model.json').is_file())
            self.assertFalse((partial / 'record.json').exists())
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                library.show_entry(self.lib, partial.name)
        # A new independent save never overwrites or silently repairs the partial.
        before = {p.relative_to(partial): p.read_bytes() for p in partial.rglob('*') if p.is_file()}
        self.save()
        self.assertEqual({p.relative_to(partial): p.read_bytes() for p in partial.rglob('*') if p.is_file()}, before)
        self.assertEqual(len(library.list_entries(self.lib)['entries']), 1)

    def test_interrupted_commit_marker_is_not_a_ready_rule(self):
        original_open = Path.open
        def interrupt_record(path, mode='r', *args, **kwargs):
            if mode == 'xb' and path.name == 'record.json' and path.is_relative_to(self.lib):
                with original_open(path, mode, *args, **kwargs) as handle:
                    handle.write(b'{"schema":')
                raise PermissionError('commit marker interrupted')
            return original_open(path, mode, *args, **kwargs)
        with denied_rename_and_delete(), patch.object(Path, 'open', interrupt_record):
            with self.assertRaisesRegex(PermissionError, 'commit marker interrupted'):
                self.save()
            self.assertEqual(library.list_entries(self.lib)['entries'], [])
            self.assertEqual(len(library.list_entries(self.lib)['invalid_entries']), 1)

    def test_existing_rule_id_is_never_overwritten(self):
        first = self.save()['entry']
        existing = Path(first['directory'])
        before = {p.relative_to(existing): p.read_bytes() for p in existing.rglob('*') if p.is_file()}
        with patch.object(library.secrets, 'token_hex', return_value=first['id'][6:]):
            with self.assertRaises(FileExistsError):
                self.save()
        self.assertEqual({p.relative_to(existing): p.read_bytes() for p in existing.rglob('*') if p.is_file()}, before)

    def test_unexpected_disk_resource_is_not_accepted_as_complete(self):
        entry = self.save()['entry']
        (Path(entry['directory']) / 'unlisted.txt').write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'unexpected or missing'):
            library.show_entry(self.lib, entry['id'])
        self.assertEqual(library.list_entries(self.lib)['entries'], [])

    def test_tampered_or_unsafe_archive_is_rejected_before_any_library_write(self):
        entry = self.save()['entry']
        source = self.root / 'valid.zip'
        library.export_entry(self.lib, entry['id'], source)
        with zipfile.ZipFile(source) as archive:
            payload = {name: archive.read(name) for name in archive.namelist()}
        model_name = entry['id'] + '/model.json'
        payload[model_name] += b'\n'
        target = self.root / 'imported-rules'
        bad = self.root / 'tampered.zip'
        with zipfile.ZipFile(bad, 'w') as archive:
            for name, data in payload.items():
                archive.writestr(name, data)
        with denied_rename_and_delete():
            with self.assertRaisesRegex(ValueError, 'has changed'):
                library.import_entry(target, bad)
        self.assertFalse(target.exists())
        unsafe = self.root / 'unsafe.zip'
        with zipfile.ZipFile(unsafe, 'w') as archive:
            archive.writestr('../outside.json', b'{}')
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            library.import_entry(target, unsafe)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
