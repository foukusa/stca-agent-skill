import csv
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

SKILL = Path(__file__).resolve().parents[1] / 'skills' / 'stca'
sys.path.insert(0, str(SKILL/'scripts'))
import data_readiness as d

class ReadinessTests(unittest.TestCase):
    def test_evaluation_never_selects_settings(self):
        ys=np.geomspace(1e-3,1e5,200)
        a=d.audit_target(ys, direction='high',tiers=[.3,.2,.1],unit='Barrer',y_eval=[1,2,3,4])
        b=d.audit_target(ys, direction='high',tiers=[.3,.2,.1],unit='Barrer',y_eval=[1e10,1e11,1e12])
        self.assertEqual(a['transform'],'log10')
        self.assertEqual(a['scan'],b['scan'])
        self.assertFalse(a['evaluation_labels_used_for_settings'])
        self.assertEqual([x['cutoff_model'] for x in a['tier_readiness']], [x['cutoff_model'] for x in b['tier_readiness']])
    def test_low_cutoff_sign_and_inverse(self):
        ys=[1,10,100,1000,10000]
        a=d.audit_target(ys,direction='low',tiers=[.25],unit='Barrer',transform='log10',y_eval=[.1,10,1e6])
        r=a['tier_readiness'][0]
        self.assertEqual(r['comparison'],'<=')
        self.assertEqual(r['cutoff_model'],1)
        self.assertEqual(r['cutoff_physical'],10)
        self.assertEqual(r['source_positives'],2)
        self.assertEqual(r['evaluation_positives_fixed_train'],2)
        self.assertTrue(a['scan']['scan_max']<=0)
    def test_prelogged_unit_and_double_log_rejection(self):
        a=d.audit_target([0,1,2,3,4],direction='high',tiers=[.25],unit='log10(Barrer)',already_log=True)
        self.assertEqual(a['transform'],'none')
        self.assertEqual(a['tier_readiness'][0]['cutoff_physical'],1000)
        self.assertEqual(a['tier_readiness'][0]['cutoff_physical_unit'],'Barrer')
        with self.assertRaises(ValueError): d.audit_target([1,2,3],direction='high',tiers=[.2],unit='log10(Barrer)',already_log=True,transform='log10')
    def test_constant_and_ties(self):
        a=d.audit_target([5]*100,direction='high',tiers=[.3],unit='u')
        self.assertFalse(a['scan']['fit_numerically_available'])
        self.assertEqual(a['tier_readiness'][0]['evidence_status'],'single_class_source')
        self.assertFalse(a['tier_readiness'][0]['fit_or_screening_blocked_by_support'])
        a=d.audit_target([0]*80+[1]*20,direction='high',tiers=[.2],unit='u')
        self.assertFalse(a['scan']['automatic_unique_or_quantile_switch'])
    def test_heavy_tail_full_grid_budget_and_support(self):
        vals=np.r_[np.linspace(1,2,95),1e20,2e20,3e20,4e20,5e20]
        a=d.scan_plan(vals,min_subset_size=10,max_grid_points=200)
        self.assertEqual(a['full_range_scan_space'],[1,5e20])
        self.assertLess(a['valid_range_scan_space'][1],2)
        self.assertLessEqual(a['actual_full_grid_points'],200)
        self.assertFalse(a['upstream_grid_downsampling_required'])
        self.assertEqual(a['status'],'too_few_eligible_thresholds')
        self.assertLess(a['eligible_threshold_points'],4)
        self.assertFalse(a['fit_numerically_available'])

    def test_negative_support_reported(self):
        a=d.audit_target(range(100),direction='high',tiers=[.99],unit='u',y_eval=range(100))
        r=a['tier_readiness'][0]
        self.assertTrue(r['source_positive_support_sufficient'])
        self.assertFalse(r['source_negative_support_sufficient'])
        self.assertEqual(r['evidence_status'],'limited_negative_support')

    def test_floating_point_grid_resolution(self):
        a=d.scan_plan([1e16,1e16+2,1e16+4,1e16+6])
        self.assertGreaterEqual(a['scan_step'],2)
        a=d.scan_plan([0,1e-323,2e-323,3e-323])
        self.assertFalse(a['fit_numerically_available'])

    def test_small_support_and_single_class_eval_reported(self):
        a=d.audit_target(range(50),direction='high',tiers=[.1],unit='u',y_eval=[-4,-3])
        self.assertEqual(a['tier_readiness'][0]['evidence_status'],'single_class_evaluation')
        self.assertFalse(a['tier_readiness'][0]['fit_or_screening_blocked_by_support'])
    def test_bounded_grid_and_guard(self):
        a=d.scan_plan(np.r_[np.zeros(990),np.geomspace(1,1e18,10)],max_grid_points=200)
        self.assertLessEqual(a['estimated_grid_points'],200)
        self.assertEqual(a['scan_mode'],'value')
        for vals in ([],[1,float('nan')],[1,float('inf')]):
            with self.assertRaises(ValueError): d.audit_target(vals,direction='high',tiers=[.1],unit='u')
        with self.assertRaises(ValueError): d.scan_plan([1,2],min_subset_size=3)
    def test_cli_no_data_deletion_preserved_id_and_star(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); src=p/'input.csv'; out=p/'readiness.json'
            src.write_text('record,SMILES,hcap,value,role,text,temperature\n001,*CC*,CC,1,train,methanol treatment,25\nA-x,*C(*)C,CC,2,train,aged,25\nB9,*CC*,CC,3,test,plain,25\n')
            before=src.read_bytes()
            cmd=[sys.executable,str(SKILL/'scripts/data_readiness.py'),'--input',str(src),'--target','value','--unit','Barrer','--direction','high','--tiers','.3,.2','--role-column','role','--id-column','record','--smiles-column','SMILES','--calculation-smiles-column','hcap','--metadata-columns','text','--condition-columns','temperature','--output',str(out)]
            r=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            report=json.loads(out.read_text())
            self.assertEqual(src.read_bytes(),before)
            diag=report['diagnostics'];self.assertEqual(diag['rows_deleted'],0)
            self.assertEqual(len(diag['processing_flags']),2)
            self.assertEqual(diag['hcap_collisions'][0]['action'],'do_not_merge')
            self.assertEqual(set(diag['hcap_collisions'][0]['originals']),{'*CC*','*C(*)C'})
            self.assertTrue(diag['duplicate_groups'][0]['roles_overlap'])
            self.assertEqual(report['n_source'],2)

if __name__=='__main__': unittest.main()
