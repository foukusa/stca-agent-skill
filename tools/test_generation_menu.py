"""Test the generation choice and confirmation gates without scientific packages."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(os.environ.get('STCA_TEST_SKILL_DIR',
                           str(Path(__file__).resolve().parents[1]/'skills'/'stca')))
SCRIPT = SKILL/'scripts/task_menu.py'
# Test the conversation gates with an immutable, available paper rule. The
# availability of a newly learned open-data rule is tested with its catalog.
RULE = 'paper-tg-high-30'


class GenerationMenuTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stca-generation-menu-')
        self.addCleanup(self.temp.cleanup)
        self.library = Path(self.temp.name)/'uncreated-user-rules'

    def call(self,*arguments):
        return subprocess.run([sys.executable,'-S',str(SCRIPT),
                               '--library-dir',str(self.library),*arguments],
                              capture_output=True,text=True)

    def selected(self,*arguments):
        result=self.call('3','--rule',RULE,*arguments)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(result.stdout)

    def test_rule_selection_and_generation_mode_are_independent_choices(self):
        data=self.selected()
        self.assertTrue(data['choice_required'])
        self.assertFalse(data['rule_choice_required'])
        self.assertTrue(data['generation_mode_required'])
        self.assertIsNone(data['generation_mode'])
        self.assertFalse(data['generation_gate']['generation_allowed'])
        self.assertEqual(data['next_action'],'choose_generation_mode_and_wait')
        self.assertEqual([x['id'] for x in data['generation_mode_options']],['preview','direct'])
        self.assertEqual([x['number'] for x in data['generation_mode_options']],[1,2])
        self.assertIsNone(data['session_helper']['prepare_command_template'])

    def test_numeric_task_alone_never_authorizes_direct_generation(self):
        result=self.call('3');self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertTrue(data['rule_choice_required'])
        self.assertTrue(data['generation_mode_required'])
        self.assertFalse(data['generation_gate']['generation_allowed'])
        self.assertEqual(data['next_action'],'choose_rule_and_wait')
        self.assertTrue(data['generation_policy']['numeric_task_choice_is_not_direct_authorization'])
        for mode in ['preview','direct']:
            result=self.call('3','--generation-mode',mode)
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads(result.stdout)
            self.assertTrue(data['rule_choice_required'])
            self.assertFalse(data['generation_mode_required'])
            self.assertFalse(data['generation_gate']['generation_allowed'])
            self.assertEqual(data['next_action'],'choose_rule_and_wait')

    def test_preview_stops_before_sampling_and_never_auto_confirms(self):
        data=self.selected('--generation-mode','preview')
        self.assertFalse(data['choice_required'])
        self.assertEqual(data['generation_mode'],'preview')
        gate=data['generation_gate']
        self.assertFalse(gate['generation_allowed'])
        self.assertTrue(gate['full_prompt_display_required'])
        self.assertTrue(gate['confirmation_required'])
        self.assertTrue(gate['revision_invalidates_confirmation'])
        self.assertEqual(gate['confirmation_source'],'observed_explicit_user_confirmation_of_current_prompt')
        self.assertEqual(data['next_action'],'prepare_complete_prompt_and_wait_for_confirmation')
        # Re-reading the menu does not mutate a session or turn review into approval.
        self.assertEqual(self.selected('--generation-mode','preview'),data)
        self.assertFalse(self.library.exists())

    def test_direct_mode_requires_current_llm_generation_and_exact_verification(self):
        data=self.selected('--generation-mode','direct')
        self.assertFalse(data['choice_required'])
        self.assertFalse(data['generation_mode_required'])
        self.assertFalse(data['generation_gate']['confirmation_required'])
        self.assertTrue(data['generation_gate']['generation_allowed'])
        self.assertEqual(data['generation_gate']['generator'],'current_llm')
        self.assertTrue(data['generation_gate']['exact_verification_required'])
        self.assertFalse(data['generation_gate']['prompt_file_alone_completes_generation'])
        self.assertEqual(data['next_action'],'generate_with_current_llm_then_verify')
        self.assertTrue(data['generation_policy']['reuse_explicit_natural_language_mode'])
        instructions=' '.join(data['agent_steps'])
        self.assertIn('actually generate',instructions)
        self.assertIn('verify every original proposal',instructions)
        self.assertIn('Do not ask again',instructions)

    def test_session_templates_use_exact_selected_constraints_and_review_safe_revision(self):
        data=self.selected('--generation-mode','preview')
        helper=data['session_helper']
        self.assertEqual(Path(helper['script']),SKILL/'scripts/generation_session.py')
        prepare=helper['prepare_command_template']
        self.assertEqual(prepare[prepare.index('--mode')+1],'preview')
        self.assertEqual(prepare[prepare.index('--count')+1],'20')
        for rule in data['selected_rules']:
            self.assertIn(rule['constraints_path'],prepare)
        self.assertEqual(prepare[prepare.index('--output-dir')+1],'<new-user-workspace-session-directory>')
        self.assertIn('<actual-observed-user-confirmation>',helper['confirm_command_template'])
        self.assertIn('<user-adjustments.md>',helper['revise_command_template'])
        self.assertNotIn('<edited-complete-prompt.md>',helper['revise_command_template'])
        self.assertIn('rerenders all frozen scientific conditions',helper['revision_note'])
        self.assertTrue(helper['user_workspace_only'])

    def test_menu_prepare_templates_reach_the_real_session_gate(self):
        for mode in ['preview','direct']:
            data=self.selected('--generation-mode',mode)
            command=data['session_helper']['prepare_command_template']
            output=Path(self.temp.name)/mode
            command=[sys.executable,'-S',*command[1:]]
            command[command.index('--output-dir')+1]=str(output)
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            session=json.loads(result.stdout)
            self.assertEqual(session['mode'],mode)
            self.assertEqual(session['generation_allowed'],mode=='direct')
            prompt=Path(session['prompt_path'])
            self.assertTrue(prompt.is_file())
            self.assertGreater(len(prompt.read_text(encoding='utf-8')),300)
            if mode=='preview':
                self.assertIsNone(session['approved_prompt_path'])
            else:
                approved=Path(session['approved_prompt_path'])
                self.assertEqual(approved.read_bytes(),prompt.read_bytes())
            self.assertFalse((output/'candidates.csv').exists())

    def test_generation_modes_are_bilingual_and_invalid_gates_fail_cleanly(self):
        for language,expected in [('zh-CN',['先看完整 prompt，确认后生成','直接生成并核验']),
                                  ('en',['Review the full prompt before generating','Generate and verify directly'])]:
            data=self.selected('--language',language)
            self.assertEqual([x['title'] for x in data['generation_mode_options']],expected)
            self.assertTrue(all(x['description'] for x in data['generation_mode_options']))
        for arguments in [('1','--generation-mode','direct'),('2','--generation-mode','preview'),
                          ('--generation-mode','direct'),('3','--generation-mode','unknown'),
                          ('3','--generation-mode','preview','--confirm')]:
            result=self.call(*arguments)
            self.assertEqual(result.returncode,2)
            self.assertEqual(result.stdout,'')
            self.assertNotIn('Traceback',result.stderr)

    def test_all_generation_gates_are_standard_library_only_and_read_only(self):
        code='''from pathlib import Path
import contextlib,importlib.util,io,sys
sys.path.insert(0,str(Path(sys.argv[1]).parent))
spec=importlib.util.spec_from_file_location('menu',sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for mode in [None,'preview','direct']:
 args=['3','--rule',sys.argv[2],'--library-dir',sys.argv[3]]
 if mode: args+=['--generation-mode',mode]
 with contextlib.redirect_stdout(io.StringIO()): assert m.main(args)==0
assert not {'numpy','pandas','scipy','rdkit','sklearn'} & set(sys.modules)
assert not Path(sys.argv[3]).exists()
'''
        result=subprocess.run([sys.executable,'-S','-c',code,str(SCRIPT),RULE,str(self.library)],
                              capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':
    unittest.main()
