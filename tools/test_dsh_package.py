"""Validate the npm tarball consumed by DSH Add plugin."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class DshPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='stca dsh npm pack ')
        result=subprocess.run(['npm','pack','--ignore-scripts','--json','--pack-destination',cls.temp.name],cwd=ROOT,capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        packed=json.loads(result.stdout)[0]
        cls.archive=Path(cls.temp.name)/packed['filename']
        with tarfile.open(cls.archive,'r:gz') as tar:
            members=tar.getmembers()
            if any(m.issym() or m.islnk() or Path(m.name).is_absolute() or '..' in Path(m.name).parts for m in members):
                raise AssertionError('Unsafe npm package member')
            cls.files={m.name[len('package/'):]:tar.extractfile(m).read() for m in members if m.isfile() and m.name.startswith('package/')}
        cls.manifest=json.loads(cls.files['package.json'])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_installable_bundle_entry_patch_and_version(self):
        p=self.manifest
        self.assertEqual(p['name'],'dsh-plugin-stca')
        self.assertEqual(p['version'],'0.1.0')
        self.assertIn(p['main'].removeprefix('./'),self.files)
        patch=p['dsh']['bundle']['patch'].removeprefix('./')
        self.assertIn(patch,self.files)
        self.assertIn(b'name: dsh-plugin-stca',self.files[patch])
        self.assertIn('dsh-plugin',p['keywords'])
        self.assertFalse(set(p.get('scripts',{})) & {'prepare','preinstall','install','postinstall'})

    def test_logo_and_localized_card_metadata(self):
        p=self.manifest
        self.assertEqual(self.files[p['icon'].removeprefix('./')],(ROOT/'assets/stca-logo.png').read_bytes())
        self.assertLess(len(self.files[p['icon'].removeprefix('./')]),256*1024)
        for lang in ['en','zh-cn']:
            meta=json.loads(self.files[f'dsh/locale/{lang}.json'])['meta']
            self.assertTrue(meta['title']);self.assertTrue(meta['description'])

    def test_all_frozen_rules_prompts_and_computational_scripts_preserved(self):
        prefix='skills/stca/'
        catalog=json.loads(self.files[prefix+'assets/rule_library/catalog.json'])
        self.assertEqual(len(catalog['entries']),149)
        self.assertEqual(sum(len(e['prompts']) for e in catalog['entries']),298)
        for e in catalog['entries']:
            for relative in [e['constraints'],*e['prompts'].values()]:
                name=prefix+'assets/rule_library/'+relative
                self.assertEqual(self.files[name],(ROOT/name).read_bytes())
        for name,data in self.files.items():
            if name.startswith(prefix+'scripts/') and name.endswith('.py'):
                self.assertEqual(data,(ROOT/name).read_bytes(),name)
        self.assertFalse(any('__pycache__' in n or n.endswith('.pyc') or '.DS_Store' in n for n in self.files))


if __name__=='__main__':
    unittest.main()
