from pathlib import Path
import json
import pandas as pd
import sys
import tempfile
import unittest
import subprocess
S=Path(__file__).resolve().parents[1]/'skills'/'stca'/'scripts'
sys.path.insert(0,str(S))
from data_cleaning import clean_frame

class CleaningTests(unittest.TestCase):
 def test_invalid_records_and_exact_id_export(self):
  d=pd.DataFrame([{'key':'001','SMILES':'*CC*','y':'1','role':'source','notes':'aged methanol treatment'},
   {'key':'001','SMILES':'*CC*','y':'1','role':'source','notes':'aged methanol treatment'},
   {'key':'001','SMILES':'*CC*','y':'2','role':'source','notes':'different measurement'},
   {'key':'b','SMILES':'*CO*','y':'100000000','role':'holdout','notes':'extreme but valid'},
   {'key':'c','SMILES':'not_smiles','y':'3','role':'source','notes':''},
   {'key':'d','SMILES':'*CC*','y':'nan','role':'holdout','notes':''},
   {'key':'e','SMILES':'*CC*','y':'','role':'source','notes':''},
   {'key':'f','SMILES':'*CC*','y':'word','role':'holdout','notes':''},
   {'key':'g','SMILES':'C*C','y':'5','role':'source','notes':''}])
  before=d.copy(deep=True)
  c,e,a=clean_frame(d,target='y',id_column='key',role_column='role')
  pd.testing.assert_frame_equal(d,before)
  self.assertEqual(c['key'].tolist(),['001','001','b'])
  self.assertEqual(a['cleaned_rows'],3);self.assertEqual(a['excluded_rows'],6)
  self.assertEqual(a['reason_counts']['duplicate_export_same_id_and_complete_row'],1)
  self.assertEqual(a['row_mapping']['cleaned_original_positions'],[0,2,3])
  self.assertFalse(a['extreme_value_deletion']);self.assertFalse(a['processing_text_deletion'])
 def test_no_id_no_export_dedup_and_hcap_collision(self):
  d=pd.DataFrame({'SMILES':['*CC*','*CC*','*C(*)C'],'y':['1','1','2']})
  c,e,a=clean_frame(d,target='y')
  self.assertEqual(len(c),3);self.assertEqual(len(e),0)
  self.assertEqual(a['hcap_collision_groups_flagged_not_merged'],1)
 def test_explicit_bounds_quality_roles(self):
  d=pd.DataFrame({'id':['a','b','c','d','e'],'SMILES':['*CC*']*5,'v':['0','1','2','3','4'],
   'quality':['ok','ok','bad','ok','ok'],'role':['source','source','holdout','holdout','']})
  c,e,a=clean_frame(d,target='v',id_column='id',role_column='role',quality_column='quality',
   exclude_quality_values=['bad'],target_min=1,target_max=3)
  self.assertEqual(c['id'].tolist(),['b','d'])
  self.assertEqual(a['reason_counts'],{'outside_declared_target_min':1,'explicit_quality_exclusion':1,'outside_declared_target_max':1})
  self.assertEqual(a['role_warnings'][0]['rows'],[4])
 def test_reserved_names_collision_preserves_all_fields(self):
  d=pd.DataFrame({'SMILES':['*CC*'],'y':['2'],'stca_keep':['X'],
    'archive_stca_keep':['Y'],'archive_input_row_position':['user_value']})
  c,e,a=clean_frame(d,target='y')
  self.assertEqual(a['reserved_column_renames']['stca_keep'],'archive_stca_keep_2')
  self.assertEqual(c['archive_stca_keep'].iloc[0],'Y')
  self.assertEqual(c['archive_stca_keep_2'].iloc[0],'X')
  self.assertEqual(c['archive_input_row_position'].iloc[0],'user_value')
  self.assertEqual(a['row_position_column'],'archive_input_row_position_2')
 def test_unlabelled_candidate_and_invalid_configuration(self):
  d=pd.DataFrame({'SMILES':['*CC*','']})
  c,e,a=clean_frame(d);self.assertEqual(len(c),1)
  with self.assertRaises(ValueError):clean_frame(d,target_min=0)
  with self.assertRaises(ValueError):clean_frame(d,target='missing')
 def test_cli_and_failure_no_success(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);inp=p/'data.csv';out=p/'cleaned'
   inp.write_text('K,SMILES,y\n001,*CC*,3\nx,invalid,nan\n')
   before=inp.read_bytes()
   cmd=[sys.executable,str(S/'data_cleaning.py'),'--input',str(inp),'--target','y',
    '--id-column','K','--output-dir',str(out)]
   r=subprocess.run(cmd,capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(inp.read_bytes(),before)
   c=pd.read_csv(out/'cleaned.csv',dtype=str);self.assertEqual(c['K'].iloc[0],'001')
   self.assertEqual(json.loads((out/'cleaning_audit.json').read_text())['excluded_rows'],1)
   r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,2)

if __name__=='__main__':unittest.main()
