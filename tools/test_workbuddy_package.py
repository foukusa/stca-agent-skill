"""Integration checks for the actual shallow WorkBuddy upload artifact."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib

SKILL = Path(__file__).resolve().parents[1] / 'skills' / 'stca'


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
        cls.archive = cls.root/'archives/stca-workbuddy-0.1.0.zip'
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

    def test_zip_root_and_maximum_two_path_components(self):
        self.assertIn('SKILL.md', self.names)
        self.assertIn('assets/stca-logo.png', self.names)
        self.assertIn('scripts/workbuddy_runtime.py', self.names)
        self.assertTrue(all(len(Path(name).parts) <= 2 for name in self.names))
        entry=(self.install/'SKILL.md').read_text()
        self.assertIn('skill_instructions',entry)
        self.assertIn('runtime_skill_dir',entry)
        self.assertNotIn('](assets/rule_library/',entry)

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
                self.assertEqual(data,original.read_bytes(),relative)
        catalog=json.loads((runtime/'assets/rule_library/catalog.json').read_bytes())
        self.assertEqual(len(catalog['entries']),149)
        self.assertEqual(sum(len(e['prompts']) for e in catalog['entries']),298)

    def test_menu_and_verbatim_prompt_from_unpacked_artifact(self):
        runtime=Path(self.prepare()['runtime_skill_dir'])
        menu=self.invoke('run','--script','task_menu.py','--').stdout.decode()
        for number in [1,2,3]:
            self.assertIn(f'{number}.',menu)
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


if __name__ == '__main__':
    unittest.main()
