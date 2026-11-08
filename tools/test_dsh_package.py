"""Validate the npm tarball consumed by DSH Add plugin."""
import hashlib
import json
import os
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

    def test_unpacked_gui_directory_registers_without_peer_module_resolution(self):
        # pnpm links local directories. Its node_modules is not an ancestor of
        # the unpacked plugin's real path, so the entry must use host services
        # without importing a provider package from that external directory.
        directory=Path(self.temp.name)/'GUI plugin outside profile'
        for relative,data in self.files.items():
            target=directory/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
        self.assertFalse(self.manifest.get('dependencies'))
        self.assertFalse(self.manifest.get('peerDependencies'))
        script=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const root=process.argv[1];
const plugin=await import(pathToFileURL(path.join(root,'dsh/index.js')).href);
let provider;
plugin.apply({skills:{registerProvider(factory){provider=factory({});}}});
assert.equal(provider.name,'stca');
const listed=await provider.list({});
assert.equal(listed.length,1);
assert.equal(listed[0].name,'stca');
assert.equal(listed[0].rank,600);
assert.equal(listed[0].resourceBase.path,path.join(root,'skills/stca'));
const loaded=await provider.get(listed[0],{});
assert.equal(loaded.provider,'stca');
assert(loaded.content.startsWith('# STCA'));
assert(!loaded.content.startsWith('---'));
assert(loaded.invocation.modelInvocable && loaded.invocation.userInvocable);
const catalog=JSON.parse(fs.readFileSync(path.join(loaded.resourceBase.path,'assets/rule_library/catalog.json'),'utf8'));
assert.equal(catalog.entries.length,149);
for(const entry of catalog.entries)for(const p of [entry.constraints,...Object.values(entry.prompts)])assert(fs.existsSync(path.join(loaded.resourceBase.path,'assets/rule_library',p)));
assert.equal(await provider.get({name:'other',provider:'other'},{}),undefined);
const cancel=new AbortController();cancel.abort();
await assert.rejects(provider.list({signal:cancel.signal}));
console.log(JSON.stringify({registered:true,external_dependencies:0,rules:catalog.entries.length}));
'''
        result=subprocess.run(['node','--input-type=module','-e',script,str(directory)],
                              cwd=self.temp.name,capture_output=True,text=True,
                              env={**os.environ,'NODE_PATH':''})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)['registered'])

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
