#!/usr/bin/env python3
"""Public regression checks for processing metadata and continuation arguments.

Run in a supported STCA CPU environment:
    python tools/test_auto_data_metadata.py
    python tools/test_auto_data_metadata.py --skill-root /path/to/skills/stca

Four valid repeat units keep preparation below the t-SNE split minimum. Influence
analysis is disabled. These checks do not fit rules or run cross-validation. The
continuation check uses the real inrange argparse entry point and replaces only
its run() function, so it validates parsing without repeating an evaluation.
"""
from __future__ import annotations

import argparse
import csv
import importlib
from pathlib import Path
import os
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SKILL_ROOT = Path(os.environ.get(
    "STCA_SKILL_ROOT", str(Path(__file__).resolve().parents[1] / "skills" / "stca")
)).expanduser().resolve()


class AutoDataMetadataRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        cls.layer = importlib.import_module("auto_data_layer")
        cls.inrange = importlib.import_module("inrange_evaluation")
        if Path(cls.layer.__file__).resolve() != SKILL_ROOT / "scripts" / "auto_data_layer.py":
            raise RuntimeError("auto_data_layer was imported from a different skill root")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="stca metadata regression ")
        self.directory = Path(self.temporary.name)
        self.rows = [
            {"SMILES": "*CC*", "target": "1", "sample code": "annealed",
             "Reference": 'Composites Part B: Engineering, "Polymer membranes"',
             "DOI": "10.0000/composite.example.1", "Journal": "Composites Science and Technology",
             "Details": "as prepared", "Temperature C": "25", "Protocol": "A"},
            {"SMILES": "*CO*", "target": "2", "sample code": "composite",
             "Reference": "Journal of Composites — original citation",
             "DOI": "10.0000/plasma-polymer.example.2", "Journal": "Composites Part A",
             "Details": "as prepared", "Temperature C": "30", "Protocol": "B"},
            {"SMILES": "*CN*", "target": "3", "sample code": "methanol-treated",
             "Reference": "Composites Part B; authors and title remain verbatim",
             "DOI": "10.0000/annealed.example.3", "Journal": "Composites Communications",
             "Details": "as prepared", "Temperature C": "35", "Protocol": "C"},
            {"SMILES": "*CCO*", "target": "4", "sample code": "aged",
             "Reference": "Composites, volume 1, pages 2–3",
             "DOI": "10.0000/cross-link.example.4", "Journal": "Composites Part B",
             "Details": "as prepared", "Temperature C": "40", "Protocol": "D"},
        ]

    def tearDown(self):
        self.temporary.cleanup()

    def write_input(self, name="input table.csv"):
        path = self.directory / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)
        return path

    def prepare(self, *, text_columns=(), **kwargs):
        path = self.write_input()
        result = self.layer.prepare_dataset(
            path, target="target", id_column="sample code", text_columns=text_columns,
            skip_influence=True, **kwargs)
        return path, result

    def assert_original_fields_preserved(self, result):
        # This checks all raw values, including excluded rows, rather than only
        # representatives in the cleaned modeling table.
        for column in self.rows[0]:
            archival_name = result["audit"]["reserved_column_renames"].get(column, column)
            self.assertEqual(result["row_mapping"][archival_name].tolist(),
                             [row[column] for row in self.rows], column)

    def test_bibliographic_composites_titles_are_not_processing_evidence(self):
        _, result = self.prepare(text_columns=["Reference", "DOI", "Journal", "Details"])
        self.assertEqual(len(result["data"]), 4)
        self.assertEqual(result["audit"]["D1_D2_excluded"], {})
        self.assertEqual(result["audit"]["D2_text_columns"], ["Details"])
        metadata = result["audit"]["processing_metadata_audit"]
        self.assertEqual(metadata["requested_columns"], ["Reference", "DOI", "Journal", "Details"])
        self.assertEqual(metadata["ignored_bibliographic_columns"], ["Reference", "DOI", "Journal"])
        self.assertEqual(metadata["scanned_columns"], ["Details"])
        self.assert_original_fields_preserved(result)
        for column in ("Reference", "DOI", "Journal"):
            self.assertEqual(result["data"][column].tolist(), [row[column] for row in self.rows])

    def test_actual_annealing_in_details_still_excludes_only_that_row(self):
        self.rows[1]["Details"] = "annealed at 150 C for 2 hours"
        _, result = self.prepare(text_columns=["Reference", "DOI", "Journal", "Details"])
        self.assertEqual(len(result["data"]), 3)
        self.assertEqual(result["audit"]["D1_D2_excluded"], {"processing_history_scope_exclusion": 1})
        self.assertEqual(result["row_mapping"]["preparation_status"].tolist(),
                         ["retained", "excluded", "retained", "retained"])
        self.assertIn("processing_history_scope_exclusion",
                      result["row_mapping"].iloc[1]["preparation_reason"])
        self.assert_original_fields_preserved(result)

    def test_keywords_in_explicit_arbitrary_id_column_do_not_exclude_rows(self):
        _, result = self.prepare(text_columns=["sample code"])
        self.assertEqual(len(result["data"]), 4)
        self.assertEqual(result["audit"]["D2_text_columns"], [])
        self.assertEqual(result["audit"]["D2_configured_ID_column_excluded"], "sample code")
        self.assertEqual(result["audit"]["D1_D2_excluded"], {})
        self.assert_original_fields_preserved(result)

    def test_recommendation_parses_with_complete_semantic_arguments(self):
        path = self.write_input("input 'quoted' & table.csv")
        output = self.directory / "preparation 'quoted' output"
        source = self.directory / "pinned source argument"
        source.mkdir()
        result = self.layer.prepare_dataset(
            path, target="target", property_name="custom property audit", target_name="Display 'CO2' audit",
            unit="custom physical unit", already_log=True, direction="low", tiers=(.15, .25),
            id_column="sample code", condition_columns=["Temperature C", "Protocol"],
            text_columns=["Reference", "Details", "sample code"], skip_influence=True,
            source=str(source), output_dir=output)
        audit = result["audit"]
        argv = audit["recommended_evaluation_argv"]
        self.assertEqual(shlex.split(audit["recommended_evaluation_command"]), argv)
        self.assertNotIn("--auto-dir", argv)
        self.assertEqual(argv[:6], [sys.executable, str(SKILL_ROOT / "scripts" / "agent_runtime.py"),
                                   "run", "--script", "inrange_evaluation.py", "--"])
        parsed = {}

        def capture(args):
            parsed.update(vars(args))
            return 0

        # argparse itself is real: unsupported flags or missing required values
        # fail this call before capture() can be invoked.
        with patch.object(self.inrange, "run", side_effect=capture) as execute:
            self.assertEqual(self.inrange.main(argv[argv.index("--") + 1:]), 0)
        execute.assert_called_once()
        expected = {
            "input": str(path.resolve()), "target": "target", "smiles_column": "SMILES",
            "property": "custom property audit", "target_name": "Display 'CO2' audit",
            "unit": "custom physical unit", "direction": "low", "id_column": "sample code",
            "source": str(source), "condition_columns": ["Temperature C", "Protocol"],
            "metadata_columns": ["Details"], "already_log": True, "skip_influence": True,
            "output_dir": str(output.resolve() / "evaluation"),
        }
        for key, value in expected.items():
            self.assertEqual(parsed[key], value, key)
        self.assertEqual(self.inrange.parse_tiers(parsed["tiers"]), [.15, .25])
        self.assert_original_fields_preserved(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--skill-root", type=Path)
    options, remaining = parser.parse_known_args()
    if options.skill_root is not None:
        SKILL_ROOT = options.skill_root.expanduser().resolve()
    unittest.main(argv=[sys.argv[0], *remaining])
