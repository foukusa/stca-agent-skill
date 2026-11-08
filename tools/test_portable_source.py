"""Offline source provenance and create-only runtime cache regressions."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import marshal

SKILL = Path(os.environ.get('STCA_TEST_SKILL_DIR', Path(__file__).resolve().parents[1] / 'skills/stca'))
sys.path.insert(0, str(SKILL / 'scripts'))
import agent_runtime as runtime
import source_integrity as integrity
import stca_runtime


class PortableSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stca source regression ')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def copy_source(self):
        destination = self.root / 'author snapshot'
        shutil.copytree(SKILL / 'assets/author_source', destination)
        return destination

    def child(self, code, source=None):
        env = dict(os.environ, PYTHONPATH=str(SKILL / 'scripts'), PYTHONDONTWRITEBYTECODE='1',
                   STCA_CACHE_DIR=str(self.root / 'backend'))
        env.pop('STCA_SOURCE', None)
        if source is not None:
            env['STCA_SOURCE'] = str(source)
        return subprocess.run([sys.executable, '-B', '-c', code], env=env,
                              capture_output=True, text=True, timeout=60)

    def test_default_bundle_identity_and_unchanged_author_files(self):
        manifest = integrity.trusted_manifest()
        self.assertEqual(manifest['commit'], stca_runtime.UPSTREAM_COMMIT)
        self.assertEqual(len(manifest['files']), 37)
        self.assertIn('LICENSE', manifest['files'])
        self.assertIn('NOTICE', manifest['files'])
        self.assertIn('src/stca/assets/tg_high_paper_refit.json', manifest['files'])
        with patch.dict(os.environ, {}, clear=False), patch.object(stca_runtime.subprocess, 'run', side_effect=AssertionError('Git must not run')):
            os.environ.pop('STCA_SOURCE', None)
            self.assertEqual(stca_runtime.verify_source(), integrity.bundled_source_root().resolve())

    def test_changed_author_code_is_rejected(self):
        source = self.copy_source()
        path = source / 'src/stca/training.py'
        path.write_bytes(path.read_bytes() + b'\n# altered\n')
        with self.assertRaisesRegex(RuntimeError, 'checksum mismatch: src/stca/training.py'):
            integrity.verify_snapshot(source, strict_root=True)

    def test_changed_frozen_author_resource_is_rejected(self):
        source = self.copy_source()
        path = source / 'src/stca/assets/tg_high_paper_refit.json'
        path.write_bytes(b'{}')
        with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
            integrity.verify_snapshot(source, strict_root=True)

    def test_extra_importable_module_is_rejected(self):
        source = self.copy_source()
        (source / 'src/stca/shadow.py').write_text('raise RuntimeError("untrusted")')
        with self.assertRaisesRegex(RuntimeError, 'inventory mismatch'):
            integrity.verify_snapshot(source, strict_root=True)

    def test_missing_license_is_rejected(self):
        source = self.copy_source()
        (source / 'LICENSE').unlink()
        with self.assertRaisesRegex(RuntimeError, 'inventory mismatch'):
            integrity.verify_snapshot(source, strict_root=True)

    def test_symlinked_source_file_is_rejected(self):
        source = self.copy_source()
        path = source / 'src/stca/metrics.py'
        target = self.root / 'metrics.py'
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            integrity.verify_snapshot(source, strict_root=True)

    def test_replacing_manifest_cannot_redefine_trust(self):
        source = self.copy_source()
        path = source / integrity.MANIFEST_NAME
        manifest = json.loads(path.read_text())
        manifest['files']['src/stca/training.py'] = '0' * 64
        path.write_text(json.dumps(manifest))
        with patch.object(integrity, 'bundled_source_root', return_value=source):
            with self.assertRaisesRegex(RuntimeError, 'manifest failed verification'):
                integrity.verify_snapshot(source, strict_root=True)

    def test_invalid_explicit_source_never_falls_back_or_clones(self):
        source = self.copy_source()
        (source / 'src/stca/scan.py').write_text('changed')
        with patch.object(runtime, 'prepare_source', side_effect=AssertionError('must not clone')):
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                runtime.existing_source(str(source))
        with patch.dict(os.environ, {'STCA_SOURCE': str(self.root / 'missing')}):
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                runtime.existing_source()

    def test_default_fit_runtime_works_with_git_and_rename_delete_denied(self):
        result = self.child('''
import json, os, subprocess, sys
from pathlib import Path
def guard(event,args):
    if event in {'os.rename','os.remove','os.rmdir'}:
        raise PermissionError('injected restricted host: '+event)
sys.addaudithook(guard)
original=subprocess.run
def run(command,*args,**kwargs):
    if isinstance(command,(list,tuple)) and Path(str(command[0])).name == 'git':
        raise PermissionError('Git is not available in this host')
    return original(command,*args,**kwargs)
subprocess.run=run
import agent_runtime,stca_runtime
value=agent_runtime.ensure('fit',python=sys.executable,allow_install=False)
stca=stca_runtime.load_stca()
assert stca.load_pretrained('tg-high',protocol='paper')
receipt=stca_runtime.environment_receipt()
assert receipt['source_integrity']['requires_git'] is False
assert not (Path(value['source'])/'.git').exists()
assert not list(Path(value['source']).rglob('__pycache__'))
print(json.dumps({'ready':value['ready'],'source_kind':receipt['source_integrity']['kind']}))
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['source_kind'], 'bundled_author_snapshot')

    def test_poisoned_external_bytecode_is_never_executed(self):
        source = self.copy_source()
        original = source / 'src/stca/__init__.py'
        cache = original.parent / '__pycache__'
        cache.mkdir()
        code = compile('raise RuntimeError("poisoned bytecode executed")', str(original), 'exec')
        payload = (importlib.util.MAGIC_NUMBER + struct.pack('<I', 0)
                   + struct.pack('<II', int(original.stat().st_mtime), original.stat().st_size)
                   + marshal.dumps(code))
        (cache / ('__init__.' + sys.implementation.cache_tag + '.pyc')).write_bytes(payload)
        result = self.child('''
import json,sys
from pathlib import Path
def guard(event,args):
    if event=='open' and '/stca/__pycache__/' in str(args[0]):
        raise AssertionError('author bytecode cache must not be read')
sys.addaudithook(guard)
import stca_runtime
module=stca_runtime.load_stca()
assert module.STCA
print(json.dumps(stca_runtime.environment_receipt()['source_integrity']))
''', source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['kind'], 'checksum_verified_author_snapshot')

    def test_runtime_receipts_survive_without_rename_or_deletion(self):
        destination = self.root / 'runtime.json'
        with patch.object(runtime, 'RECEIPT', destination), \
             patch('os.rename', side_effect=PermissionError('denied rename')), \
             patch('os.replace', side_effect=PermissionError('denied replace')), \
             patch('os.unlink', side_effect=PermissionError('denied unlink')):
            runtime.save({'python': 'first', 'ready': True})
            initial = destination.read_bytes()
            runtime.save({'python': 'second', 'ready': True})
            self.assertEqual(destination.read_bytes(), initial)
            self.assertEqual(runtime.receipt()['python'], 'second')
            # Coarse filesystem timestamps must not make the first record win
            # lexicographic ties over a subsequently completed immutable record.
            for path in self.root.glob('runtime*.json'):
                os.utime(path, ns=(1_000_000_000, 1_000_000_000))
            self.assertEqual(runtime.receipt()['python'], 'second')
            (self.root / 'runtime-999-partial.json').write_text('{')
            (self.root / 'runtime-999-invalid.json').write_text(json.dumps({
                'schema': 'stca-agent-runtime-receipt-v2', 'complete': True,
                'record': {'python': 'wrong'}, 'record_sha256': '0'*64}))
            self.assertEqual(runtime.receipt()['python'], 'second')

    def test_runtime_receipt_write_denial_has_exact_path_and_no_patch_retry(self):
        destination = self.root / 'blocked/runtime.json'
        original = Path.open
        def blocked(path, mode='r', *args, **kwargs):
            if 'x' in mode and path.parent == destination.parent:
                raise PermissionError('injected write denial')
            return original(path, mode, *args, **kwargs)
        with patch.object(runtime, 'RECEIPT', destination), patch.object(Path, 'open', blocked):
            with self.assertRaisesRegex(PermissionError, 'authorized writable task workspace') as error:
                runtime.save({'python': sys.executable})
        self.assertIn(str(destination.parent), str(error.exception))
        self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
