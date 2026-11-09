import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1] / 'skills' / 'stca'
SCRIPT = SKILL / 'scripts/generation_prompt.py'
spec = importlib.util.spec_from_file_location('generation_prompt', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def example():
    return {
        'schema': 'stca-library-constraints-v1',
        'catalog_id': 'example_CO2_high15',
        'property': 'CO2 permeability', 'direction': 'high', 'tier': 0.15,
        'target': {'physical_cutoff': 4100, 'unit': 'Barrer',
                   'model_cutoff': 3.6127838567197355,
                   'model_unit': 'log10(Barrer)', 'operator': '>='},
        'rule': {'keys': [149, 125], 'values': [0, 1]},
        'literals': [
            {'feature_index': 149, 'feature_name': 'K149', 'required_value': 0,
             'definition': {'smarts': '[C;H3,H4]', 'count_parameter': 1,
                            'bit_one_activation': 'unique_substructure_match_count > 1',
                            'rdkit_version': '2025.09.4'}},
            {'feature_index': 125, 'required_value': 1,
             'definition': {'status': 'rdkit_special_or_undefined_key'}},
        ],
        'metrics': {'MCC': 0.999, 'Precision': 0.99},
    }


class RenderPromptTest(unittest.TestCase):
    def test_both_languages_have_exact_targets_count_semantics_and_no_metrics(self):
        before = example()
        untouched = copy.deepcopy(before)
        for language in ('en', 'zh-CN'):
            text = module.render_prompt(before, language, 7, 'Exclude fluorine; allow aromatic ethers.')
            self.assertNotIn('{{', text)
            self.assertIn('7', text)
            self.assertIn('CO2 permeability', text)
            self.assertIn('Top 15%', text)
            self.assertIn('>= 4100 Barrer', text)
            self.assertIn('K149=0 AND K125=1', text)
            self.assertIn('unique_substructure_match_count > 1', text)
            self.assertIn('count_parameter=1', text)
            self.assertIn('generation_only', text)
            self.assertIn('Exclude fluorine;', text)
            self.assertNotIn('MCC', text)
            self.assertNotIn('0.999', text)
        self.assertEqual(before, untouched)

    def test_legacy_log_unit_inverts_once_and_preserves_low_operator(self):
        constraint = {
            'schema': 'stca-constraints-v1', 'status': 'frozen_representative',
            'tier_fraction': 0.2,
            'target': {'name': 'electrical conductivity', 'unit': 'log10(S/cm)',
                       'direction': 'low', 'reference_train_cutoff': -8,
                       'label_comparison': '<='},
            'rule': {'keys': [42], 'values': [0]},
        }
        text = module.render_prompt(constraint, 'en')
        self.assertIn('Bottom 20%', text)
        self.assertIn('<= 1e-08 S/cm', text)
        self.assertIn('<= -8 log10(S/cm)', text)

    def test_missing_physical_cutoff_never_uses_linear_model_value(self):
        constraint = example()
        constraint['target'] = {'model_cutoff': 1.5, 'model_unit': 'arbitrary_scale'}
        text = module.render_prompt(constraint, 'en')
        self.assertIn('physical cutoff not supplied', text)
        self.assertIn('model-space boundary: >= 1.5 arbitrary_scale', text)

    def test_explicit_physical_value_is_authoritative_not_double_inverted(self):
        text = module.render_prompt(example(), 'en')
        self.assertIn('>= 4100 Barrer', text)
        self.assertNotIn('physical boundary: >= 4100.', text)

    def test_and_intersection_conflict_refuses_before_generation(self):
        a, b = example(), example()
        b['property'] = 'oxygen permeability'
        b['rule'] = {'keys': [149], 'values': [1]}
        b['literals'] = []
        with self.assertRaisesRegex(ValueError, 'Contradictory.*K149'):
            module.render_prompt([a, b])
        b['rule']['values'] = [0]
        text = module.render_prompt([a, b], 'en')
        self.assertIn('Objective 2', text)
        self.assertIn('oxygen permeability', text)

    def test_metadata_placeholders_and_stale_expression_fail(self):
        for field, value in [('property', 'p')]:
            bad = example()
            bad[field] = value
            with self.assertRaisesRegex(ValueError, 'placeholder'):
                module.render_prompt(bad)
        bad = example()
        bad['target']['unit'] = 'u'
        with self.assertRaisesRegex(ValueError, 'placeholder'):
            module.render_prompt(bad)
        bad = example()
        bad['rule']['expression'] = 'K149=1 AND K125=1'
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            module.render_prompt(bad)

    def test_explicit_frozen_representation_cannot_be_changed(self):
        bad = example()
        bad['representation'] = 'as_provided_maccs167'
        with self.assertRaisesRegex(ValueError, 'frozen representation'):
            module.render_prompt(bad)
        bad.pop('representation')
        bad['model'] = {'custom_data_contract': {'representation': 'as_provided_maccs167'}}
        with self.assertRaisesRegex(ValueError, 'frozen representation'):
            module.render_prompt(bad)
        bad['model']['custom_data_contract']['representation'] = 'hcap_maccs167'
        bad['feature_spec'] = {'kind': 'rdkit_maccs167',
                               'smiles_policy': 'as_provided_no_capping_no_salt_or_tautomer_normalization'}
        self.assertIn('H-cap', module.render_prompt(bad))

    def test_conflicting_count_activation_metadata_is_rejected(self):
        bad = example()
        bad['literals'][0]['definition']['bit_one_activation'] = 'has_substructure_match'
        with self.assertRaisesRegex(ValueError, 'disagree.*K149'):
            module.render_prompt(bad)

    def test_bundled_frozen_rule_metadata_and_count_semantics(self):
        path = SKILL/'assets/rule_library/entries/current-gas-co2-stca-high-10/constraints.json'
        constraint = json.loads(path.read_text())
        text = module.render_prompt(constraint, 'en', 12)
        self.assertIn('CO2 permeability', text)
        self.assertIn('Barrer', text)
        self.assertIn(constraint['rule']['expression'], text)
        self.assertIn('unique_substructure_match_count > 1', text)
        invalid = copy.deepcopy(constraint)
        invalid['property'] = 'p'
        with self.assertRaisesRegex(ValueError, 'placeholder'):
            module.render_prompt(invalid)

    def test_cli_is_site_independent_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / 'constraints.json', root / 'prompt.md'
            source.write_text(json.dumps(example()))
            command = [sys.executable, '-S', str(SCRIPT), '--constraints', str(source),
                       '--language', 'en', '--count', '6', '--preferences', 'Use ethers.',
                       '--output', str(destination)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'prompt_rendered')
            self.assertIn('6 distinct polymer', destination.read_text())
            self.assertIn('Use ethers.', destination.read_text())
            original = destination.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(destination.read_bytes(), original)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
