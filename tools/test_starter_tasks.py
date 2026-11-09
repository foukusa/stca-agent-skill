import csv
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

    def test_default_learning_requires_real_distance_and_source_only_evidence(self):
        result = self.call('1', '--language', 'en')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['workflow'], 'learn_source_rules_with_strict_morgan_holdout')
        contract = data['execution_contract']
        self.assertEqual(contract['entrypoint'], 'morgan_evaluation.py')
        self.assertEqual(contract['representation'], 'hcap_maccs167')
        self.assertEqual(contract['verification_script'], 'fingerprint_contract.py')
        self.assertEqual(contract['verification_action'], '--run-dir')
        self.assertTrue({'run_manifest.json', 'source_fit/fingerprint_contract.json',
                         'split_membership.csv', 'split_audit.json',
                         'holdout_actual_training_distances.csv',
                         'morgan_holdout_evaluation.csv', 'source_inner_selection.json'}
                        <= set(contract['required_evidence']))
        self.assertEqual(data['method_policy']['recommendation_evidence'],
                         'source_internal_strict_morgan_validation; never_final_holdout')

    def test_direct_generation_keeps_one_rule_and_marks_runtime_failures_unverified(self):
        result = self.call('3', '--rule', 'paper-tg-high-30', '--generation-mode', 'direct')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIsNone(data['rule_options'])
        self.assertEqual([r['id'] for r in data['selected_rules']], ['paper-tg-high-30'])
        self.assertEqual(data['next_action'], 'generate_with_current_llm_then_verify')
        self.assertTrue(data['generation_policy']['dependency_import_error_is_not_invalid_smiles'])
        self.assertEqual(data['generation_policy']['runtime_failure_status'], 'generated_unverified')
        self.assertLess(len(result.stdout), 25000)

    def test_density_default_uses_primary_and_keeps_static_stca_generation_explicit(self):
        case = json.loads((SKILL/'assets/examples/radonpy_density_case.json').read_text())
        tasks = json.loads((SKILL/'assets/starter_tasks.json').read_text())
        catalog = json.loads((SKILL/'assets/rule_library/catalog.json').read_text())
        entries = {entry['id']: entry for entry in catalog['entries']}
        primary = case['existing_rule']
        alternative = case['alternative_method_rule']
        choices = [entry for entry in catalog['entries']
                   if entry.get('dataset') == 'PI_RHO' and entry.get('tier') == .3]
        self.assertEqual({entry['method'] for entry in choices}, {'STCA', 'WRAcc'})
        primaries = [entry for entry in choices if entry.get('is_primary')]
        self.assertEqual(len(primaries), 1)
        self.assertEqual(primary['id'], primaries[0]['id'])
        self.assertEqual(alternative['id'], primaries[0]['alternative_id'])
        evidence = json.loads((SKILL/'assets/rule_library/current_profile_evidence.json').read_text())
        self.assertEqual(evidence['contract'], 'strict_morgan_source_v1')
        self.assertFalse(evidence['holdout_used_for_method_choice'])
        evidence_rules = {row['id']: row for row in evidence['rules']}
        for example in (primary, alternative):
            entry = entries[example['id']]
            record = evidence_rules[example['id']]
            self.assertEqual(example['method'], entry['method'])
            self.assertEqual(example['expected_selected'], record['selected_n'])
            self.assertEqual(example['expected_unknown'], record['unknown_n'])
            self.assertEqual(example['expected_not_selected'],
                             record['input_n'] - record['selected_n'] - record['unknown_n'])
            self.assertEqual(example['physical_cutoff'], record['cutoff'])
            self.assertEqual(example['rule'], record['rule'])
            reference = entry['reference_evaluation']
            self.assertEqual(reference['evaluation_kind'], 'strict_morgan_distance_holdout')
            self.assertEqual(reference['fit_scope'], 'source_only_frozen_model')
            self.assertTrue(reference['every_holdout_meets_distance'])
            self.assertGreaterEqual(reference['minimum_holdout_nearest_source_distance'] + 1e-12,
                                    reference['distance_threshold'])
            self.assertEqual(reference['method_recommendation_scope'],
                             'source_inner_strict_morgan_validation_before_outer_holdout')
            self.assertTrue(entry['provenance']['original_repeat_unit_identity_preserved'])
            self.assertTrue(entry['provenance']['hcap_structure_not_used_to_merge_materials'])
        self.assertEqual(case['relearn']['entrypoint'], 'morgan_evaluation.py')
        self.assertEqual(case['relearn']['contract'], evidence['contract'])
        self.assertEqual(case['selection_policy']['default_screening_method'], 'catalog_primary')
        self.assertTrue(case['selection_policy']['honor_explicit_method'])
        density_case = next(item for item in tasks['example_cases'] if item['id'] == 'radonpy_density')
        self.assertEqual(density_case['preferred_builtin_rule'], primary['id'])
        result = self.call('2', '--rule', primary['id'])
        self.assertEqual(result.returncode, 0, result.stderr)
        selected = json.loads(result.stdout)['selected_rules']
        self.assertEqual([rule['id'] for rule in selected], [primary['id']])
        self.assertTrue(selected[0]['is_primary'])
        with (SKILL/'assets/examples/radonpy_generation_examples.csv').open(newline='') as stream:
            proposals = list(csv.DictReader(stream))
        self.assertEqual(len(proposals), 5)
        generation_rule = case['generation']['static_example_rule_id']
        self.assertEqual(entries[generation_rule]['method'], 'STCA')
        self.assertEqual({row['catalog_id'] for row in proposals}, {generation_rule})
        self.assertTrue(all('*' in row['SMILES'] for row in proposals))
        self.assertTrue(all('*' not in row['calculation_smiles_hcap'] for row in proposals))

    def test_featured_example_preserves_explicit_stca_and_true_catalog_recommendation(self):
        tasks = json.loads((SKILL/'assets/starter_tasks.json').read_text())
        self.assertEqual(tasks['featured_example_id'], 'adept_gap')
        self.assertEqual(tasks['example_cases'][0]['id'], 'adept_gap')
        water = next(item for item in tasks['example_cases'] if item['id'] == 'water_contact_angle')
        self.assertEqual(water['role'], 'supported_property_only')
        case = json.loads((SKILL/'assets/examples/adept_gap_case.json').read_text())
        catalog = json.loads((SKILL/'assets/rule_library/catalog.json').read_text())
        entries = {entry['id']: entry for entry in catalog['entries']}
        selected = case['existing_rule']
        self.assertEqual(selected['method'], 'STCA')
        self.assertEqual(selected['id'], 'current-ad-gap-stca-high-30')
        self.assertFalse(entries[selected['id']]['is_primary'])
        self.assertEqual(case['catalog_recommended_method'], 'WRAcc')
        self.assertEqual(case['input']['smiles_column'], 'SMILES')
        self.assertEqual(case['input']['target_column'], 'BANDGAP')
        self.assertEqual(case['source']['records'], 2916)
        self.assertEqual(selected['expected_selected'], 976)
        self.assertEqual(selected['physical_cutoff'], 11.914537535)
        with (SKILL/'assets/examples/adept_gap_generation_examples.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 5)
        self.assertTrue(all('*' in row['SMILES'] and '*' not in row['calculation_smiles_hcap'] for row in rows))
        self.assertEqual({row['catalog_id'] for row in rows}, {selected['id']})

    def test_current_catalog_metrics_belong_to_the_source_frozen_distance_models(self):
        root = SKILL/'assets/rule_library'
        catalog = json.loads((root/'catalog.json').read_text())
        evidence = json.loads((root/'current_profile_evidence.json').read_text())
        current = [entry for entry in catalog['entries'] if entry['id'].startswith('current-')]
        self.assertTrue(current)
        self.assertEqual(catalog['current_contract'], 'strict_morgan_source_v1')
        records = {row['id']: row for row in evidence['rules']}
        self.assertEqual({entry['id'] for entry in current}, set(records))
        self.assertFalse(evidence['holdout_used_for_method_choice'])
        for entry in current:
            with self.subTest(rule=entry['id']):
                record = records[entry['id']]
                payload = json.loads((root/entry['constraints']).read_text())
                provenance = entry['provenance']
                reference = entry['reference_evaluation']
                self.assertEqual(entry['experiment_id'], evidence['contract'])
                self.assertEqual(provenance['fit_scope'], 'source_only_frozen_model')
                self.assertEqual(provenance['cutoff_scope'], 'source_only')
                self.assertEqual(provenance['structural_role_fingerprint'],
                                 {'name': 'ECFP4', 'kind': 'Morgan', 'radius': 2, 'n_bits': 2048})
                self.assertEqual(provenance['rule_fingerprint'], 'Hcap_MACCS167')
                self.assertEqual(reference['evaluation_kind'], 'strict_morgan_distance_holdout')
                self.assertFalse(reference['buffer_used_for_learning'])
                self.assertEqual(reference['protected_group_overlap_n'], 0)
                self.assertEqual(reference['method_recommendation_scope'],
                                 'source_inner_strict_morgan_validation_before_outer_holdout')
                self.assertEqual(reference['physical_cutoff'], payload['target']['physical_cutoff'])
                self.assertEqual(reference['screened_input_selected_n'], record['selected_n'])
                self.assertEqual(reference['holdout_AS'], record['holdout_AS'])
                self.assertEqual(bool(payload.get('rule') and payload['rule'].get('keys')),
                                 entry['available'])

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
