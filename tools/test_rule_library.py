"""Rule-library browsing, byte-preserving prompt and exact-MACCS tests."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1] / 'skills' / 'stca'
SCRIPT = SKILL/'scripts/rule_library.py'


class RuleLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stca-library-test-')
        self.root = Path(self.temp.name)
        self.lib = self.root/'library'
        entries = []
        for identifier, value in [('nitrogen',1),('no-nitrogen',0)]:
            directory = self.lib/'entries'/identifier
            directory.mkdir(parents=True)
            entry = {'id':identifier,'title':'N test','title_zh':'氮条件测试',
                     'property':'Test','property_zh':'测试','direction':'high','tier':.2,'unit':'1',
                     'constraints':f'entries/{identifier}/constraints.json',
                     'prompts':{'en':f'entries/{identifier}/prompt.en.md','zh-CN':f'entries/{identifier}/prompt.zh-CN.md'},
                     'provenance':{'kind':'custom','dataset':'synthetic-test','citation':None},'tags':['test']}
            entries.append(entry)
            constraint = {'schema':'stca-library-constraints-v1','property':'Test','direction':'high','tier':.2,
                          'target':{'unit':'1','physical_cutoff':1,'operator':'>='},
                          'representation':'hcap_maccs167','rule':{'name':identifier,'keys':[161],'values':[value]}}
            (directory/'constraints.json').write_text(json.dumps(constraint))
            (directory/'prompt.en.md').write_bytes(b'Propose 20 candidates.\r\nKeep all failed proposals.\r\n')
            (directory/'prompt.zh-CN.md').write_bytes('提出20个候选。\r\n保留所有失败项。\r\n'.encode())
        (self.lib/'catalog.json').write_text(json.dumps({'schema':'stca-rule-library-v1','version':'0.1.0','entries':entries}))

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, args, expected=0, no_site=False):
        cmd = [sys.executable, *(['-S'] if no_site else []), str(SCRIPT), '--library-dir',str(self.lib),*args]
        result = subprocess.run(cmd,capture_output=True)
        self.assertEqual(result.returncode, expected, result.stderr.decode())
        return result

    def test_browse_and_verbatim_prompts_without_site_packages(self):
        result = self.invoke(['list','--property','测试'],no_site=True)
        self.assertEqual(len(json.loads(result.stdout)['entries']),2)
        show = json.loads(self.invoke(['show','nitrogen'],no_site=True).stdout)
        self.assertEqual(show['constraints']['rule']['keys'],[161])
        expected = (self.lib/'entries/nitrogen/prompt.zh-CN.md').read_bytes()
        self.assertEqual(self.invoke(['prompt','nitrogen'],no_site=True).stdout, expected)
        path = self.root/'copy'/'prompt.md'
        self.invoke(['prompt','nitrogen','--language','en','--output',str(path)],no_site=True)
        self.assertEqual(path.read_bytes(),(self.lib/'entries/nitrogen/prompt.en.md').read_bytes())
        self.invoke(['prompt','nitrogen','--output',str(path)],expected=2,no_site=True)

    def test_exact_screen_keeps_originals_unknowns_and_failure_conditions(self):
        from rdkit import Chem
        from rdkit.Chem import MACCSkeys
        candidates = self.root/'candidates.csv'
        with (SKILL/'assets/public_smoke/candidates_10.csv').open() as handle:
            rows = list(csv.DictReader(handle))
        rows.append({'ID':'bad','SMILES':'not-smiles','design_label':'bad','generation_note':'unknown'})
        with candidates.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        output=self.root/'screen'
        self.invoke(['screen','nitrogen','--input',str(candidates),'--id-column','ID','--output-dir',str(output)])
        with (output/'results.csv').open() as handle: results=list(csv.DictReader(handle))
        with (output/'rows.csv').open() as handle: internal=list(csv.DictReader(handle))
        self.assertEqual([(r['ID'],r['SMILES']) for r in results],[(r['ID'],r['SMILES']) for r in rows])
        self.assertNotIn('stca_calculation_smiles_hcap',results[0])
        for shown,audited in zip(results[:-1],internal[:-1]):
            self.assertNotIn('*',audited['stca_calculation_smiles_hcap'])
            bits=MACCSkeys.GenMACCSKeys(Chem.MolFromSmiles(audited['stca_calculation_smiles_hcap']))
            passed=bool(bits[161])
            self.assertEqual(shown['stca_nitrogen__selected']=='True',passed)
            self.assertEqual(shown['stca_nitrogen__missing_required_present'],'' if passed else 'K161')
            self.assertEqual(json.loads(shown['stca_nitrogen__failed_conditions']),[] if passed else [{'key':161,'required':1,'observed':0}])
        self.assertEqual(results[-1]['stca_joint__status'],'unknown')
        self.assertEqual(len(results),11)
        contradictory=self.root/'contradictory'
        self.invoke(['screen','nitrogen','no-nitrogen','--input',str(candidates),'--output-dir',str(contradictory)])
        summary=json.loads((contradictory/'summary.json').read_text())
        self.assertEqual(summary['joint_selected_count'],0)
        self.assertEqual(summary['joint_unknown_count'],1)
        self.assertEqual(summary['literal_conflicts'],[161])

    def test_catalog_paths_cannot_escape_or_follow_external_symlink(self):
        catalog=json.loads((self.lib/'catalog.json').read_text())
        outside=self.root/'outside.md';outside.write_text('must not disclose')
        catalog['entries'][0]['prompts']['en']='../outside.md'
        (self.lib/'catalog.json').write_text(json.dumps(catalog))
        result=self.invoke(['prompt','nitrogen','--language','en'],expected=2,no_site=True)
        self.assertNotIn(b'must not disclose',result.stdout)
        (self.lib/'external.md').symlink_to(outside)
        catalog['entries'][0]['prompts']['en']='external.md'
        (self.lib/'catalog.json').write_text(json.dumps(catalog))
        self.invoke(['prompt','nitrogen','--language','en'],expected=2,no_site=True)


if __name__=='__main__':
    unittest.main(verbosity=2)
