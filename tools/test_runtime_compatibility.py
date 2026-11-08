import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]/'skills'/'stca'
sys.path.insert(0, str(SKILL/'scripts'))
import agent_runtime as runtime
import runtime_compat as compat


class CompatibleRuntimeTests(unittest.TestCase):
    def package_version(self, name):
        return {'numpy':'1.24.4','pandas':'2.0.3','scipy':'1.10.1',
                'rdkit':'2023.9.1','scikit-learn':'1.5.2','threadpoolctl':'3.1.0'}[name]

    def fake_interpreter(self, command, **kwargs):
        version = [3,10] if command[0] == 'python310' else [3,12]
        return subprocess.CompletedProcess(command, 0, json.dumps({'version':version,'implementation':'CPython'}), '')

    def test_setup_uses_first_310_without_demanding_312(self):
        with patch.object(runtime,'candidates',return_value=['python310','python312']), patch.object(runtime.subprocess,'run',side_effect=self.fake_interpreter):
            self.assertEqual(runtime.setup_interpreter('fit'), 'python310')
            self.assertEqual(runtime.setup_interpreter('chem'), 'python310')
            self.assertEqual(runtime.setup_interpreter('fit',dependency_mode='locked'), 'python312')

    def test_existing_310_reused_without_preparation(self):
        with patch.object(runtime,'existing_source',return_value='source'), patch.object(runtime,'candidates',return_value=['python310']), patch.object(runtime,'probe',return_value={'ready':True,'python':'python310','python_version':'3.10.22'}), patch.object(runtime,'save',side_effect=lambda x:x), patch.object(runtime,'setup_interpreter',side_effect=AssertionError('must not prepare')):
            actual=runtime.ensure('fit',allow_install=False)
        self.assertEqual(actual['python'],'python310')
        self.assertFalse(actual['installed_now'])

    def test_discovery_checks_common_and_minimum_interpreter_names(self):
        names=[]
        def which(name):
            names.append(name)
            return '/bin/python310' if name=='python3.10' else None
        with patch.object(runtime,'receipt',return_value={}),patch.object(runtime.shutil,'which',side_effect=which):
            actual=runtime.candidates()
        self.assertIn('python3',names)
        self.assertIn('python',names)
        self.assertIn('/bin/python310',actual)

    def test_chem_prepares_minimum_range_and_no_author_source(self):
        calls=[]
        def run(command,**kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command,0,'','')
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime.shutil,'which',return_value=None),patch.object(runtime.subprocess,'run',side_effect=run),patch.object(runtime,'probe',return_value={'ready':True,'python':'prepared'}):
            result=runtime.prepare_chem('python310',Path(directory)/'env')
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0][1:3],['-m','venv'])
        self.assertIn('rdkit>=2023.9',calls[1])
        self.assertNotIn('rdkit==2025.9.4',calls[1])
        self.assertIsNone(result['source'])

    def test_old_supported_versions_pass_compatible_policy(self):
        with patch.object(compat.sys,'version_info',(3,10,22)),patch.object(compat.importlib,'import_module'),patch.object(compat.importlib.metadata,'version',side_effect=self.package_version),patch.object(compat,'_check_maccs',return_value={'molecules':24}),patch.object(compat,'_check_fit_apis',return_value={'tsne_max_iter_api':True}):
            result=compat.probe_current('fit')
        self.assertTrue(result['ready'],result)
        self.assertEqual(result['dependency_mode'],'compatible')
        self.assertEqual(result['packages']['rdkit'],'2023.9.1')

    def test_unsupported_package_fails_with_explicit_reason(self):
        def version(name):
            return '2022.9.5' if name=='rdkit' else self.package_version(name)
        with patch.object(compat.importlib,'import_module'),patch.object(compat.importlib.metadata,'version',side_effect=version):
            result=compat.probe_current('chem')
        self.assertFalse(result['ready'])
        self.assertIn('rdkit>=2023.9_required',result['errors'][0])

    def test_functional_panel_mismatch_does_not_silently_pass(self):
        with patch.object(compat.importlib,'import_module'),patch.object(compat.importlib.metadata,'version',side_effect=self.package_version),patch.object(compat,'_check_maccs',side_effect=ValueError('MACCS167_panel_mismatch')):
            result=compat.probe_current('chem')
        self.assertFalse(result['ready'])
        self.assertIn('MACCS167_panel_mismatch',result['errors'][0])

    def test_explicit_archival_lock_is_separate(self):
        with patch.object(compat.sys,'version_info',(3,10,22)),patch.object(compat.importlib,'import_module'),patch.object(compat.importlib.metadata,'version',side_effect=self.package_version):
            result=compat.probe_current('chem',locked=True)
        self.assertFalse(result['ready'])
        self.assertIn('explicit_archival_lock_requires_Python_3.12',result['errors'])
        self.assertTrue(any('archival_lock:rdkit==2025.9.4' in x for x in result['errors']))

    def test_stdlib_prompt_never_checks_scientific_packages(self):
        with patch.object(runtime,'ensure',side_effect=AssertionError('must bypass')),patch.object(runtime.subprocess,'run',return_value=subprocess.CompletedProcess([],0)):
            for script in ('generation_prompt.py','generation_session.py'):
                self.assertEqual(runtime.main(['run','--script',script,'--','--help']),0)

    def test_probe_returns_failed_readiness_details(self):
        value={'ready':False,'errors':['functional_check: failed']}
        with patch.object(runtime.subprocess,'run',return_value=subprocess.CompletedProcess([],2,json.dumps(value),'')):
            self.assertEqual(runtime.probe('python310','fit'),value)

    def test_uv_seeds_chem_environment_when_available(self):
        calls=[]
        def run(command,**kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command,0,'','')
        with tempfile.TemporaryDirectory() as directory,patch.object(runtime.shutil,'which',return_value='/bin/uv'),patch.object(runtime.subprocess,'run',side_effect=run),patch.object(runtime,'probe',return_value={'ready':True,'python':'prepared'}):
            runtime.prepare_chem('python310',Path(directory)/'env')
        self.assertEqual(calls[0][:5],['/bin/uv','venv','--python','python310','--seed'])
        self.assertIn('rdkit>=2023.9',calls[1])

    def test_ready_environment_only_prepares_missing_author_source(self):
        with patch.object(runtime,'existing_source',return_value=None),patch.object(runtime,'candidates',return_value=['python310']),patch.object(runtime,'probe',return_value={'ready':True,'python':'python310'}),patch.object(runtime,'prepare_source',return_value='new-source') as prepare,patch.object(runtime,'save',side_effect=lambda x:x),patch.object(runtime,'setup_interpreter',side_effect=AssertionError('must reuse')):
            result=runtime.ensure('fit')
        prepare.assert_called_once_with()
        self.assertEqual(result['source'],'new-source')
        self.assertEqual(result['python'],'python310')
        self.assertTrue(result['source_prepared_now'])
        self.assertFalse(result['installed_now'])

    def test_no_install_does_not_clone_source(self):
        with patch.object(runtime,'existing_source',return_value=None),patch.object(runtime,'candidates',return_value=['python310']),patch.object(runtime,'probe',return_value={'ready':True,'python':'python310'}),patch.object(runtime,'prepare_source',side_effect=AssertionError('must not clone')):
            with self.assertRaisesRegex(RuntimeError,'preparation is disabled'):
                runtime.ensure('fit',allow_install=False)

    def test_source_only_preparation_is_pinned(self):
        calls=[]
        def run(command,**kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command,0,'','')
        with tempfile.TemporaryDirectory() as directory,patch.object(runtime,'cache_root',return_value=Path(directory)),patch.object(runtime.shutil,'which',return_value='/bin/git'),patch.object(runtime.subprocess,'run',side_effect=run),patch.object(runtime,'verify_source',side_effect=lambda x:x):
            result=runtime.prepare_source()
        self.assertIn('source-',result)
        self.assertEqual(calls[0][:3],['git','clone','--no-checkout'])
        self.assertEqual(calls[1][-2:],['--detach',runtime.UPSTREAM_COMMIT])

    def test_uv_python_preparation_stays_in_user_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);python=root/'python310';python.write_text('fixture')
            calls=[]
            def run(command,**kwargs):
                calls.append((command,kwargs))
                return subprocess.CompletedProcess(command,0,str(python)+'\n' if command[2]=='find' else '','')
            with patch.object(runtime,'cache_root',return_value=root),patch.object(runtime.shutil,'which',return_value='/bin/uv'),patch.object(runtime.subprocess,'run',side_effect=run):
                found=runtime.acquire_interpreter()
            self.assertEqual(found,str(python))
            self.assertEqual(calls[0][0],['/bin/uv','python','install','3.10'])
            self.assertEqual(calls[1][0],['/bin/uv','python','find','3.10'])
            self.assertEqual(calls[0][1]['env']['UV_PYTHON_INSTALL_DIR'],str(root/'python'))

    def test_cleaning_and_hcap_take_runtime_with_required_dependencies(self):
        for script in ['data_cleaning.py','prepare_hcap.py','audit_dataset.py']:
            with patch.object(runtime,'ensure',return_value={'python':'python310','source':'pinned'}) as ensure,patch.object(runtime.subprocess,'run',return_value=subprocess.CompletedProcess([],0)):
                self.assertEqual(runtime.main(['run','--script',script,'--','--help']),0)
            self.assertEqual(ensure.call_args.args[0],'fit')


if __name__=='__main__':
    unittest.main()
