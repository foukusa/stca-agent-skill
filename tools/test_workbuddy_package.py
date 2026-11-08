"""Integration checks for the actual shallow WorkBuddy upload artifact."""
import base64
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
from contextlib import redirect_stderr
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
import zlib

SKILL = Path(os.environ.get('STCA_TEST_SKILL_DIR',
                          Path(__file__).resolve().parents[1] / 'skills' / 'stca'))


class WorkBuddyPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='stca workbuddy package ')
        cls.root = Path(cls.temp.name)
        result = subprocess.run([sys.executable, str(SKILL/'scripts/build_platform_packages.py'),
                                 '--platform', 'workbuddy', '--output-dir', str(cls.root/'archives')],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        metadata=json.loads((SKILL/'assets/platforms/workbuddy.json').read_bytes())
        cls.version=metadata['package_version']
        cls.archive = cls.root/f'archives/stca-workbuddy-{cls.version}.zip' 
        cls.install = cls.root/'installed skill'
        with zipfile.ZipFile(cls.archive) as archive:
            cls.names = archive.namelist()
            if any(len(Path(n).parts) > 2 or '..' in Path(n).parts for n in cls.names):
                raise AssertionError('Upload artifact contains nested or unsafe resource paths')
            archive.extractall(cls.install)
        cls.script = cls.install/'scripts/workbuddy_runtime.py'
        cls.workspace = cls.root/'user workspace';cls.workspace.mkdir()
        outer = json.loads((cls.install/'assets/runtime_payload.json').read_bytes())
        cls.records = json.loads(zlib.decompress(base64.b64decode(outer['payload'])))['files']

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.env = dict(os.environ)
        self.env.pop('PYTHONPATH', None)
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'
        self.env['STCA_WORKBUDDY_CACHE_DIR'] = str(self.root/self._testMethodName)

    def invoke(self, *args, expected=0, script=None):
        result = subprocess.run([sys.executable, str(script or self.script), *args],
                                cwd=self.workspace, env=self.env, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stderr.decode())
        return result

    def prepare(self):
        return json.loads(self.invoke('prepare').stdout)

    def loader(self):
        spec = importlib.util.spec_from_file_location('workbuddy_loader_' + self._testMethodName, self.script)
        module = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, 'dont_write_bytecode', True):
            spec.loader.exec_module(module)
        return module

    def test_zip_root_and_maximum_two_path_components(self):
        self.assertIn('SKILL.md', self.names)
        self.assertIn('assets/stca-logo.png', self.names)
        self.assertIn('scripts/workbuddy_runtime.py', self.names)
        self.assertIn('scripts/agent_runtime.py', self.names)
        self.assertIn('scripts/launch_runtime.sh', self.names)
        self.assertIn('scripts/launch_runtime.ps1', self.names)
        self.assertTrue(all(len(Path(name).parts) <= 2 for name in self.names))
        entry=(self.install/'SKILL.md').read_text()
        self.assertIn('skill_instructions',entry)
        self.assertIn('runtime_skill_dir',entry)
        self.assertNotIn('](assets/rule_library/',entry)

    def test_upload_and_restored_release_versions_are_consistent(self):
        def declared_version(text):
            line=next(line for line in text.splitlines() if line.startswith('version:'))
            return line.split(':',1)[1].strip().strip("'\"")
        expected=self.version
        self.assertGreater(tuple(map(int,expected.split('.'))),(0,1,0))
        entry=(self.install/'SKILL.md').read_text()
        self.assertEqual(declared_version(entry.split('---',2)[1]),expected)
        self.assertIn(f'WorkBuddy package version **{expected}**',entry)
        outer=json.loads((self.install/'assets/runtime_payload.json').read_bytes())
        manifest=json.loads((self.install/'assets/platform-release.json').read_bytes())
        self.assertEqual(outer['version'],expected)
        self.assertEqual(manifest['package_version'],expected)
        runtime=Path(self.prepare()['runtime_skill_dir'])
        restored=(runtime/'SKILL.md').read_text()
        self.assertEqual(declared_version(restored.split('---',2)[1]),expected)
        self.assertIn(f'WorkBuddy 发布版本 **{expected}**',restored)
        self.assertNotIn('版本保持 **0.1.0**',restored)
        self.assertEqual(json.loads((runtime/'assets/platform-release.json').read_bytes())['package_version'],expected)
        self.assertEqual(declared_version((runtime/'CITATION.cff').read_text()),expected)
        self.assertIn(f'WorkBuddy 发布版本 **{expected}**',(runtime/'references/workbuddy.md').read_text())

    def test_release_version_mismatch_is_rejected_before_materialization(self):
        copied=self.root/'mismatched release skill';shutil.copytree(self.install,copied)
        path=copied/'assets/platform-release.json'
        value=json.loads(path.read_bytes());value['package_version']='99.0.0';path.write_text(json.dumps(value))
        result=self.invoke('prepare',expected=2,script=copied/'scripts/workbuddy_runtime.py')
        self.assertIn(b'payload version does not match',result.stderr)
        self.assertFalse(Path(self.env['STCA_WORKBUDDY_CACHE_DIR']).exists())

    def test_every_entry_resource_reference_is_bundled(self):
        entry=(self.install/'SKILL.md').read_text()
        references=set(re.findall(r'\b(?:scripts|assets|references)/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*',entry))
        self.assertIn('scripts/agent_runtime.py', references)
        self.assertTrue(references)
        self.assertFalse(references-set(self.names))
        manifest=json.loads((self.install/'assets/platform-release.json').read_bytes())
        self.assertEqual(manifest['core_scripts_location'],'verified_runtime_payload')
        for relative,digest in manifest['public_entrypoints_sha256'].items():
            self.assertEqual(hashlib.sha256((self.install/relative).read_bytes()).hexdigest(),digest)
        spec=importlib.util.spec_from_file_location('workbuddy_builder', SKILL/'scripts/build_platform_packages.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        with self.assertRaisesRegex(ValueError, 'scripts/missing_runtime.py'):
            builder.validate_workbuddy_entry_resources({'SKILL.md':b'Use `scripts/missing_runtime.py`.'})

    def test_visible_agent_entry_runs_complete_runtime_and_preserves_workdir(self):
        script=self.install/'scripts/agent_runtime.py'
        result=self.invoke('--help',script=script)
        self.assertIn(b'--python',result.stdout)
        self.assertIn(b'ensure',result.stdout)
        result=self.invoke('run','--script','task_menu.py','--','--language','en',script=script)
        for task in (b'Upload my data and learn rules', b'Screen directly with existing rules', b'Generate directly with existing rules'):
            self.assertIn(task,result.stdout)
        self.assertNotRegex(result.stdout, rb'(?m)^[123]\.')
        # The dispatcher is functional, while the actual implementation stays
        # in the verified payload and is not replaced with a placeholder.
        runtime=Path(self.prepare()['runtime_skill_dir'])
        self.assertNotEqual(script.read_bytes(),(runtime/'scripts/agent_runtime.py').read_bytes())
        self.assertFalse((self.install/'agent-runtime.json').exists())

    @unittest.skipIf(os.name=='nt', 'POSIX launcher is exercised on POSIX hosts')
    def test_visible_launcher_restores_with_explicit_bootstrap_interpreter(self):
        result=subprocess.run([shutil.which('sh') or '/bin/sh',str(self.install/'scripts/launch_runtime.sh'),
                               '--bootstrap-python',sys.executable,'--script',str(self.script),'prepare'],
                              cwd=self.workspace,env=self.env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('skill_instructions',json.loads(result.stdout))

    def test_cold_hot_cache_and_installation_unchanged(self):
        before={p.relative_to(self.install).as_posix():p.read_bytes() for p in self.install.rglob('*') if p.is_file()}
        first=self.prepare();second=self.prepare()
        self.assertFalse(first['cache_hit']);self.assertTrue(second['cache_hit'])
        self.assertEqual(first['runtime_skill_dir'],second['runtime_skill_dir'])
        self.assertNotIn(str(self.install),first['runtime_skill_dir'])
        after={p.relative_to(self.install).as_posix():p.read_bytes() for p in self.install.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_all_scripts_rules_and_prompts_survive_byte_for_byte(self):
        runtime=Path(self.prepare()['runtime_skill_dir'])
        for relative,record in self.records.items():
            data=(runtime/relative).read_bytes()
            self.assertEqual(data,base64.b64decode(record['data']))
            self.assertEqual(hashlib.sha256(data).hexdigest(),record['sha256'])
            original=SKILL/relative
            if relative not in {'SKILL.md','assets/platform-release.json','SHA256SUMS.txt'}:
                if relative in {'LICENSE','THIRD_PARTY_NOTICES.md','CITATION.cff'}:
                    original=SKILL/'assets/publication'/relative
                expected=original.read_bytes()
                if relative == 'CITATION.cff':
                    expected=re.sub(rb"(?m)^version:.*$", f"version: '{self.version}'".encode(), expected, count=1)
                elif relative == 'references/workbuddy.md':
                    expected=re.sub(r'版本 \*\*[0-9]+\.[0-9]+\.[0-9]+\*\*。',
                                    f'WorkBuddy 发布版本 **{self.version}**。', expected.decode(), count=1).encode()
                self.assertEqual(data,expected,relative)
        catalog=json.loads((runtime/'assets/rule_library/catalog.json').read_bytes())
        self.assertEqual(len(catalog['entries']),149)
        self.assertEqual(sum(len(e['prompts']) for e in catalog['entries']),298)

    def test_menu_and_verbatim_prompt_from_unpacked_artifact(self):
        runtime=Path(self.prepare()['runtime_skill_dir'])
        menu=self.invoke('run','--script','task_menu.py','--').stdout.decode()
        for task in ['上传自己的文件总结规则', '根据已有规则直接筛选', '根据已有规则直接生成']:
            self.assertIn(task,menu)
        self.assertNotRegex(menu, r'(?m)^[123]\.')
        catalog=json.loads((runtime/'assets/rule_library/catalog.json').read_bytes())
        entry=catalog['entries'][0]
        result=self.invoke('run','--script','rule_library.py','--','prompt',entry['id'],'--language','en')
        self.assertEqual(result.stdout,(runtime/'assets/rule_library'/entry['prompts']['en']).read_bytes())

    def test_payload_corruption_fails_before_cache_materialization(self):
        import shutil
        copied=self.root/'bad payload skill';shutil.copytree(self.install,copied)
        path=copied/'assets/runtime_payload.json'
        data=json.loads(path.read_bytes());data['payload_sha256']='0'*64;path.write_text(json.dumps(data))
        result=self.invoke('prepare',expected=2,script=copied/'scripts/workbuddy_runtime.py')
        self.assertIn(b'SHA-256 mismatch',result.stderr)
        self.assertFalse(Path(self.env['STCA_WORKBUDDY_CACHE_DIR']).exists())

    def test_modified_cache_is_not_executed(self):
        runtime=Path(self.prepare()['runtime_skill_dir'])
        script=runtime/'scripts/task_menu.py';script.write_bytes(script.read_bytes()+b'\n# tampered\n')
        result=self.invoke('run','--script','task_menu.py','--',expected=2)
        self.assertIn(b'changed',result.stderr)

    def test_restore_and_menu_require_no_rename_replace_or_delete(self):
        runtime = self.loader()
        denied = PermissionError('Simulated protected rename/delete operation')
        with mock.patch.dict(os.environ, self.env, clear=True), \
             mock.patch.object(Path, 'cwd', return_value=self.workspace), \
             mock.patch.object(Path, 'rename', side_effect=denied), \
             mock.patch.object(Path, 'replace', side_effect=denied), \
             mock.patch.object(Path, 'unlink', side_effect=denied), \
             mock.patch.object(os, 'rename', side_effect=denied), \
             mock.patch.object(os, 'replace', side_effect=denied), \
             mock.patch.object(os, 'unlink', side_effect=denied), \
             mock.patch.object(os, 'rmdir', side_effect=denied), \
             mock.patch.object(shutil, 'rmtree', side_effect=denied):
            first = runtime.prepare()
            second = runtime.prepare()
            self.assertFalse(first['cache_hit'])
            self.assertTrue(second['cache_hit'])
            self.assertEqual(first['runtime_skill_dir'], second['runtime_skill_dir'])
            self.assertTrue((Path(first['runtime_skill_dir']) / runtime.CACHE_MARKER).is_file())
            # The actual restored task-menu entry executes after verification.
            self.assertEqual(runtime.main(['run', '--script', 'task_menu.py', '--', '--language', 'en']), 0)

    def test_workspace_cache_default_and_backend_environment(self):
        runtime = self.loader()
        work = self.workspace / self._testMethodName
        work.mkdir()
        env = dict(self.env)
        env.pop('STCA_WORKBUDDY_CACHE_DIR', None)
        env.pop('STCA_CACHE_DIR', None)
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(Path, 'cwd', return_value=work):
            ready = runtime.prepare()
            self.assertTrue(Path(ready['runtime_skill_dir']).is_relative_to(work))
            expected = str(work / '.stca-runtime' / 'backend')
            self.assertEqual(ready['backend_cache_dir'], expected)
            with mock.patch.object(runtime.subprocess, 'run', return_value=mock.Mock(returncode=0)) as run:
                self.assertEqual(runtime.run_agent_runtime(['--help']), 0)
                forwarded = run.call_args.kwargs['env']
                self.assertEqual(forwarded['STCA_CACHE_DIR'], expected)
                self.assertEqual(forwarded['PYTHONDONTWRITEBYTECODE'], '1')
            with mock.patch.dict(os.environ, {'STCA_CACHE_DIR': str(work / 'explicit backend')}):
                self.assertEqual(runtime._runtime_environment()['STCA_CACHE_DIR'], str(work / 'explicit backend'))

    def test_incomplete_cache_is_not_executed_changed_or_cleaned(self):
        runtime = self.loader()
        expected, _ = runtime.load_payload()
        base = Path(self.env['STCA_WORKBUDDY_CACHE_DIR'])
        root = base / expected
        root.mkdir(parents=True)
        partial = root / 'SKILL.md'
        partial.write_text('partial interrupted output')
        errors = io.StringIO()
        with mock.patch.dict(os.environ, self.env, clear=True), \
             mock.patch.object(runtime.subprocess, 'run', side_effect=AssertionError('Must not execute incomplete cache')), \
             mock.patch.object(Path, 'unlink', side_effect=AssertionError('Must not delete incomplete cache')), \
             mock.patch.object(shutil, 'rmtree', side_effect=AssertionError('Must not clean incomplete cache')), \
             redirect_stderr(errors):
            self.assertEqual(runtime.main(['run', '--script', 'task_menu.py']), 2)
        self.assertIn('incomplete', errors.getvalue())
        self.assertEqual(partial.read_text(), 'partial interrupted output')
        self.assertFalse((root / runtime.CACHE_MARKER).exists())

    def test_file_creation_denial_retains_original_error_and_no_completion_marker(self):
        runtime = self.loader()
        expected, _ = runtime.load_payload()
        original_open = Path.open

        def deny_resource_write(path, mode='r', *args, **kwargs):
            if path.name == 'SKILL.md' and 'x' in mode:
                raise PermissionError(13, 'Simulated workspace write denial', str(path))
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.dict(os.environ, self.env, clear=True), \
             mock.patch.object(Path, 'open', new=deny_resource_write):
            with self.assertRaisesRegex(PermissionError, 'Simulated workspace write denial'):
                runtime.prepare()
        root = Path(self.env['STCA_WORKBUDDY_CACHE_DIR']) / expected
        self.assertTrue(root.is_dir())
        self.assertFalse((root / runtime.CACHE_MARKER).exists())

    def test_unexpected_bytecode_is_rejected_without_deleting_it(self):
        runtime = self.loader()
        with mock.patch.dict(os.environ, self.env, clear=True):
            root = Path(runtime.prepare()['runtime_skill_dir'])
            bytecode = root / 'scripts' / '__pycache__' / 'task_menu.cpython-310.pyc'
            bytecode.parent.mkdir()
            bytecode.write_bytes(b'Unverified bytecode')
            with mock.patch.object(Path, 'unlink', side_effect=AssertionError('Must not delete bytecode')):
                with self.assertRaisesRegex(RuntimeError, 'Unexpected cached runtime directory'):
                    runtime.prepare()
            self.assertEqual(bytecode.read_bytes(), b'Unverified bytecode')


if __name__ == '__main__':
    unittest.main()
