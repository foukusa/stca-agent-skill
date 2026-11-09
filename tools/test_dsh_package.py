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
assert.equal(catalog.entries.length,Number(process.argv[2]));
assert.equal(new Set(catalog.entries.map(entry=>entry.id)).size,catalog.entries.length);
for(const entry of catalog.entries)for(const p of [entry.constraints,...Object.values(entry.prompts)])assert(fs.existsSync(path.join(loaded.resourceBase.path,'assets/rule_library',p)));
assert.equal(await provider.get({name:'other',provider:'other'},{}),undefined);
const cancel=new AbortController();cancel.abort();
await assert.rejects(provider.list({signal:cancel.signal}));
console.log(JSON.stringify({registered:true,external_dependencies:0,rules:catalog.entries.length}));
'''
        expected_catalog=json.loads((ROOT/'skills/stca/assets/rule_library/catalog.json').read_bytes())
        result=subprocess.run(['node','--input-type=module','-e',script,str(directory),str(len(expected_catalog['entries']))],
                              cwd=self.temp.name,capture_output=True,text=True,
                              env={**os.environ,'NODE_PATH':''})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)['registered'])

    def test_all_frozen_rules_prompts_and_computational_scripts_preserved(self):
        prefix='skills/stca/'
        catalog=json.loads(self.files[prefix+'assets/rule_library/catalog.json'])
        self.assertEqual(self.files[prefix+'assets/rule_library/catalog.json'],
                         (ROOT/prefix/'assets/rule_library/catalog.json').read_bytes())
        entries=catalog['entries']
        self.assertEqual(len({entry['id'] for entry in entries}),len(entries))
        self.assertEqual(catalog['counts']['retained'],len(entries))
        paper=[entry for entry in entries if entry['id'].startswith('paper-')]
        previous=[entry for entry in entries if entry['id'].startswith('latest-')]
        current=[entry for entry in entries if entry['id'].startswith('current-')]
        historical=[entry for entry in entries
                    if not entry['id'].startswith(('paper-','latest-','current-'))]
        self.assertEqual(len(paper),11)
        self.assertEqual(len(entries),83)
        self.assertEqual(len(previous),0)
        self.assertEqual(len(historical),0)
        self.assertEqual(len(current),72)
        self.assertEqual(sum(entry.get('available', True) for entry in current),71)
        visible=[entry for entry in entries if entry.get('user_visible',True)]
        self.assertEqual(len(visible),83)
        active=current
        self.assertTrue(all(entry.get('user_visible',True) for entry in active))
        self.assertEqual({entry['id'] for entry in entries},
                         {path.parent.name for path in (ROOT/'skills/stca/assets/rule_library/entries').glob('*/constraints.json')})
        pairs={}
        for entry in active:
            pairs.setdefault((entry['dataset'],entry['tier']),[]).append(entry)
        self.assertEqual(len(pairs),36)
        for pair in pairs.values():
            self.assertEqual({entry['learner'] for entry in pair},{'STCA','WRAcc'})
            self.assertEqual(sum(bool(entry['is_primary']) for entry in pair),1)
            self.assertTrue(all(entry['alternative_id'] in {other['id'] for other in pair}
                                and entry['alternative_id']!=entry['id'] for entry in pair))
        self.assertEqual(sum(len(entry['prompts']) for entry in entries),2*len(entries))
        for e in catalog['entries']:
            self.assertEqual(set(e['prompts']),{'en','zh-CN'})
            for relative in [e['constraints'],*e['prompts'].values()]:
                name=prefix+'assets/rule_library/'+relative
                self.assertEqual(self.files[name],(ROOT/name).read_bytes())
        # Every ordinary skill resource must survive npm's selection, including
        # scripts that are not directly referenced by the entry module.
        for source in (ROOT/'skills/stca').rglob('*'):
            if not source.is_file() or self.is_junk(source.relative_to(ROOT).as_posix()):
                continue
            name=source.relative_to(ROOT).as_posix()
            self.assertIn(name,self.files,name)
            self.assertEqual(self.files[name],source.read_bytes(),name)
        self.assertFalse(any(self.is_junk(name) for name in self.files))

    @staticmethod
    def is_junk(name):
        path=Path(name)
        return ('__pycache__' in path.parts or path.suffix in {'.pyc','.pyo'}
                or path.name in {'.DS_Store','Thumbs.db'})

    def test_pack_excludes_junk_inside_explicitly_included_directories(self):
        # npm's explicit `files` directories take precedence over root ignore
        # rules. Exercise the real npm selector with junk still on disk.
        with tempfile.TemporaryDirectory(prefix='stca npm exclusion fixture ') as temp:
            root=Path(temp)
            (root/'package.json').write_bytes((ROOT/'package.json').read_bytes())
            (root/'.npmignore').write_bytes((ROOT/'.npmignore').read_bytes())
            good=['skills/stca/SKILL.md','skills/stca/scripts/agent_runtime.py',
                  'skills/stca/assets/resource.json','dsh/index.js']
            junk=['skills/stca/scripts/__pycache__/agent_runtime.cpython-312.pyc',
                  'skills/stca/assets/author_source/stca/__pycache__/training.pyc',
                  'skills/stca/scripts/leftover.pyo','skills/stca/.DS_Store',
                  'skills/stca/assets/Thumbs.db','dsh/__pycache__/cache.bin']
            for name in good+junk:
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b'fixture')
            result=subprocess.run(['npm','pack','--ignore-scripts','--dry-run','--json'],
                                  cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            names={item['path'] for item in json.loads(result.stdout)[0]['files']}
            self.assertTrue(set(good)<=names)
            self.assertFalse(any(name in names for name in junk))
            self.assertTrue(all((root/name).is_file() for name in junk))


if __name__=='__main__':
    unittest.main()
