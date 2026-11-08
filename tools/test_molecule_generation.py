"""Ordinary-SMILES generation format, session revisions and optional real fitting.

The integration fixture is synthetic software-test data, not a scientific case.
Set STCA_TEST_SOURCE to a clean author checkout and use a scientific runtime to
exercise actual STCA fitting, prompt export and exact candidate screening.
"""
import copy
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(os.environ.get("STCA_TEST_SKILL_DIR", Path(__file__).resolve().parents[1] / "skills/stca"))
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import generation_prompt as prompt
import generation_session as session


def example(kind=None):
    value = {"schema": "stca-library-constraints-v1", "catalog_id": "synthetic-score-high-50",
             "property": "synthetic molecular score", "direction": "high", "tier": .5,
             "target": {"physical_cutoff": 5, "unit": "score_units", "operator": ">="},
             "rule": {"keys": [161], "values": [1]}}
    if kind is not None:
        value["model"] = {"custom_data_contract": {"structure_kind": kind, "representation": "hcap_maccs167"}}
    return value


class MoleculeGenerationTest(unittest.TestCase):
    def test_saved_contract_infers_molecules_without_changing_rule(self):
        constraint = example("molecule")
        before = copy.deepcopy(constraint)
        for language in ("en", "zh-CN"):
            text = prompt.render_prompt(constraint, language, 3)
            self.assertIn("K161=1", text)
            self.assertIn("Top 50%", text)
            self.assertIn(">= 5 score_units", text)
            self.assertNotIn("exactly two", text)
            self.assertNotIn("恰好保留两个", text)
            self.assertIn("Do not add artificial `*`" if language == "en" else "不要人为添加 `*`", text)
        self.assertEqual(constraint, before)

    def test_legacy_default_and_explicit_polymer_keep_two_attachment_sites(self):
        for constraint in (example(), example("polymer_repeat_unit")):
            self.assertEqual(prompt.resolve_structure_kind(constraint), "polymer_repeat_unit")
            self.assertIn("exactly two terminal `*`", prompt.render_prompt(constraint, "en"))
        text = prompt.render_prompt(example(), "en", structure_kind="molecule")
        self.assertIn("# Generate molecules", text)
        self.assertNotIn("repeat unit", text)

    def test_mixed_or_conflicting_notation_requires_output_choice(self):
        for values in (example("mixed"), [example("molecule"), example("polymer_repeat_unit")]):
            with self.assertRaisesRegex(ValueError, "choose"):
                prompt.render_prompt(values, "en")
            self.assertIn("# Generate molecules", prompt.render_prompt(values, "en", structure_kind="molecule"))
        self.assertEqual(prompt.infer_structure_kind(["CCO", "c1ccccc1"]), "molecule")
        self.assertEqual(prompt.infer_structure_kind(["*CC*", "*CO*"]), "polymer_repeat_unit")
        self.assertEqual(prompt.infer_structure_kind(["CCO", "*CC*"]), "mixed")

    def test_session_kind_change_invalidates_approval_and_keeps_frozen_conditions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            constraint = root / "constraints.json"
            constraint.write_text(json.dumps(example("molecule")), encoding="utf-8")
            state = session.prepare_session([constraint], root / "generation", mode="direct", language="en")
            self.assertTrue(state["generation_allowed"])
            self.assertEqual(state["structure_kind"], "molecule")
            edited = session.revise_session(root / "generation", structure_kind="polymer_repeat_unit")
            self.assertFalse(edited["generation_allowed"])
            self.assertIsNone(edited["approved_prompt_path"])
            self.assertEqual(edited["structure_kind"], "polymer_repeat_unit")
            text = Path(edited["prompt_path"]).read_text(encoding="utf-8")
            self.assertIn("exactly two terminal `*`", text)
            self.assertIn("K161=1", text)
            self.assertEqual(state["constraints"], edited["constraints"])

    def test_old_session_missing_kind_still_loads_exact_approved_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            constraint = root / "constraints.json"
            constraint.write_text(json.dumps(example()), encoding="utf-8")
            state = session.prepare_session([constraint], root / "generation", mode="direct", language="en")
            saved = Path(state["session_path"])
            legacy = json.loads(saved.read_text(encoding="utf-8"))
            del legacy["structure_kind"]
            saved.write_text(json.dumps(legacy), encoding="utf-8")
            restored = session.session_status(saved, include_prompt=True)
            self.assertTrue(restored["generation_allowed"])
            self.assertEqual(restored["structure_kind"], "polymer_repeat_unit")
            self.assertIn("exactly two terminal `*`", restored["prompt"])

    def test_renderer_cli_explicit_molecule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            constraint = root / "constraints.json"
            constraint.write_text(json.dumps(example()), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPTS / "generation_prompt.py"),
                "--constraints", str(constraint), "--language", "en", "--structure-kind", "molecule",
                "--output", str(root / "prompt.md")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["structure_kind"], "molecule")


@unittest.skipUnless(os.environ.get("STCA_TEST_SOURCE"), "Set STCA_TEST_SOURCE for actual fit/export/screen integration.")
class ActualMoleculeFitTest(unittest.TestCase):
    def test_no_star_data_fit_export_and_exact_screen(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(os.environ.get("STCA_TEST_ARTIFACT_DIR", temporary.name))
        root.mkdir(parents=True, exist_ok=True)
        source = os.environ["STCA_TEST_SOURCE"]
        plain = ["C", "CC", "CCC", "CCCC", "CCCCC", "CCCCCC", "CCO", "CCCO", "CC(=O)O",
                 "CCOC", "CCCl", "CCBr", "c1ccccc1", "Cc1ccccc1", "Oc1ccccc1"]
        nitrogen = ["CN", "CCN", "CCCN", "CCCCN", "CCNCC", "CCNC", "CNC", "CC(C)N",
                    "NCCO", "NCCCO", "NCC(=O)O", "c1ccncc1", "Nc1ccccc1", "CC(=O)N", "NCCN"]
        holdout = ["NCCCCO", "CCCCCCl", "COCCN", "C1CCCCC1"]
        rows = [{"CandidateKey": f"synthetic-{i:03d}", "SMILES": smiles,
                 "synthetic_score": (10 if "N" in smiles or "n" in smiles else 0) + i / 100,
                 "role": "source" if i < 30 else "holdout"}
                for i, smiles in enumerate(plain + nitrogen + holdout)]
        input_path = root / "synthetic_molecules.csv"
        with input_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        env = dict(os.environ, STCA_CACHE_DIR=str(root / "runtime-cache"))
        commands = []
        def run(script, *arguments):
            command = [sys.executable, str(SCRIPTS / script), *map(str, arguments)]
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=180)
            commands.append({"script": script, "returncode": result.returncode, "stdout": result.stdout,
                             "stderr": result.stderr})
            (root / "integration_commands.json").write_text(json.dumps(commands, indent=2), encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr + "\n" + result.stdout)
        run("custom_fit.py", "--source", source, "--input", input_path, "--target", "synthetic_score",
            "--unit", "score_units", "--direction", "high", "--tiers", ".5", "--role-column", "role",
            "--id-column", "CandidateKey", "--positive-support", "2", "--max-rank", "4", "--family-size", "4",
            "--output-dir", root / "fit")
        run("stca_tools.py", "--source", source, "export-rules", "--model", root / "fit/model.json",
            "--tier", ".5", "--output-dir", root / "rule")
        constraint = json.loads((root / "rule/constraints.json").read_text(encoding="utf-8"))
        self.assertEqual(constraint["model"]["custom_data_contract"]["structure_kind"], "molecule")
        self.assertEqual(constraint["model"]["custom_data_contract"]["input_structure_kind"], "molecule")
        self.assertEqual(constraint["status"], "frozen_representative")
        self.assertIsInstance(constraint["target"]["physical_train_cutoff"], (int, float))
        self.assertIn("# Generate molecules", (root / "rule/prompt.en.md").read_text(encoding="utf-8"))
        run("stca_tools.py", "--source", source, "screen-candidates", "--model", root / "fit/model.json",
            "--tier", ".5", "--input", input_path, "--id-column", "CandidateKey", "--output-dir", root / "screen")
        with (root / "screen/results.csv").open(encoding="utf-8", newline="") as stream:
            screened = list(csv.DictReader(stream))
        self.assertEqual([row["SMILES"] for row in screened], [row["SMILES"] for row in rows])
        self.assertTrue(all(int(row["stca_hcap_connection_atoms_replaced"]) == 0 for row in screened))
        with (root / "fit/prepared_rows.csv").open(encoding="utf-8", newline="") as stream:
            prepared = list(csv.DictReader(stream))
        self.assertTrue(all(row["stca_calculation_smiles_hcap"] == row["SMILES"] for row in prepared))
        selected = sum(row["stca_joint__selected"].lower() == "true" for row in screened)
        self.assertGreater(selected, 0)
        self.assertLess(selected, len(rows))
        (root / "integration_summary.json").write_text(json.dumps({
            "fixture": "synthetic software-test labels, not scientific validation", "input_n": len(rows),
            "source_n": 30, "holdout_n": 4, "selected_n": selected, "structure_kind": "molecule",
            "cutoff": constraint["target"]["physical_train_cutoff"], "unit": "score_units",
            "rule": constraint["rule"]["expression"], "original_smiles_preserved": True,
            "hcap_was_noop": True, "complete_molecule_prompt_exported": True}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
