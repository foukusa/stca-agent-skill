import json
from pathlib import Path
import subprocess
import sys
import unittest


SKILL = Path(__file__).resolve().parents[1]/'skills'/'stca'
SCRIPT = SKILL/'scripts/task_menu.py'


class StarterTaskTests(unittest.TestCase):
    def call(self, *arguments):
        return subprocess.run([sys.executable, '-S', str(SCRIPT), *arguments],
                              capture_output=True, text=True)

    def test_menu_is_short_readable_and_has_three_choices(self):
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.strip().splitlines()), 5)
        self.assertNotIn('screen_existing', result.stdout)
        self.assertNotIn('Python', result.stdout)
        for title in ('上传自己的文件总结规则', '根据已有规则直接筛选', '根据已有规则直接生成'):
            self.assertIn('- '+title, result.stdout)
        for number in (1, 2, 3):
            self.assertNotIn(f'{number}. ', result.stdout)
        self.assertNotIn('我的规则', result.stdout)

    def test_number_and_task_name_resolve_the_same_bilingual_workflow(self):
        expected = json.loads((SKILL/'assets/starter_tasks.json').read_text())
        for task in expected['tasks']:
            for language in ('en', 'zh-CN'):
                by_number = self.call(str(task['number']), '--language', language)
                by_id = self.call('--task', task['id'], '--language', language)
                self.assertEqual(by_number.returncode, 0, by_number.stderr)
                self.assertEqual(by_id.returncode, 0, by_id.stderr)
                number_data, id_data = json.loads(by_number.stdout), json.loads(by_id.stdout)
                self.assertEqual(number_data, id_data)
                self.assertEqual(id_data['workflow'], task['workflow'])
                self.assertEqual(id_data['user_prompt'], task['user_prompt'][language])
                if task['number'] == 3:
                    self.assertEqual(id_data['default_count'], 20)

    def test_conversation_completion_and_scores_are_defined(self):
        result = self.call('1', '--language', 'en')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['on_complete'], 'continue_conversation')
        self.assertFalse(data['interaction_policy']['native_menu_or_saved_rule_tab_required'])
        self.assertIn('Matthews correlation coefficient', data['score_explanation'])
        self.assertIn('precision and F1', data['score_explanation'])

    def test_direct_generation_keeps_one_rule_and_marks_runtime_failures_unverified(self):
        result = self.call('3', '--rule', 'latest-pi-rho-stca-high-30', '--generation-mode', 'direct')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIsNone(data['rule_options'])
        self.assertEqual([r['id'] for r in data['selected_rules']], ['latest-pi-rho-stca-high-30'])
        self.assertEqual(data['next_action'], 'generate_with_current_llm_then_verify')
        self.assertTrue(data['generation_policy']['dependency_import_error_is_not_invalid_smiles'])
        self.assertEqual(data['generation_policy']['runtime_failure_status'], 'generated_unverified')
        self.assertLess(len(result.stdout), 25000)

    def test_invalid_or_conflicting_choices_are_not_silently_routed(self):
        for arguments in [('4',), ('missing',), ('1', '--task', '2')]:
            result = self.call(*arguments)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertNotIn('Traceback', result.stderr)

    def test_loading_and_selecting_needs_no_scientific_packages(self):
        code = '''import importlib.util,sys
spec=importlib.util.spec_from_file_location('task_menu',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert len(module.load_tasks()['tasks'])==3
assert not {'numpy','pandas','scipy','rdkit','sklearn'} & set(sys.modules)
'''
        result = subprocess.run([sys.executable, '-S', '-c', code, str(SCRIPT)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
