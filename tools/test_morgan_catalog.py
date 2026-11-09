"""Reject mis-scoped validation evidence before freezing public rule profiles."""
import copy
import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refresh_morgan_rule_library import reference_metrics, template_for, validate_split, refresh


def independent_split():
    return {"status": "available", "fingerprint": {"family": "Morgan", "radius": 2,
            "bits": 2048, "metric": "1-Tanimoto"}, "target_values_used": False,
            "candidate_ids_used": False, "distance_threshold": .5,
            "nearest_source_distance_min": .51, "every_holdout_meets_distance": True,
            "protected_group_overlap_n": 0, "buffer_used_for_learning": False,
            "source_n": 80, "holdout_n": 20, "buffer_n": 10, "protected_group_n": 100}


class MorganCatalogTests(unittest.TestCase):
    def test_rejects_posthoc_cv_distance_diagnostic_and_holdout_leakage(self):
        for field, value in [("target_values_used", True), ("candidate_ids_used", True),
                             ("buffer_used_for_learning", True), ("protected_group_overlap_n", 1),
                             ("nearest_source_distance_min", .49), ("every_holdout_meets_distance", False),
                             ("status", "unavailable")]:
            with self.subTest(field=field):
                audit = independent_split()
                audit[field] = value
                with self.assertRaises(ValueError):
                    validate_split(audit)
        audit = independent_split()
        audit["fingerprint"]["radius"] = 1
        with self.assertRaises(ValueError):
            validate_split(audit)

    def test_holdout_metrics_are_distinct_from_tuning_and_full_table_screening(self):
        tier = {"physical_cutoff": 1.25, "unit": "g/cm3"}
        method = {"original_input_n": 110, "selected_n": 35, "unknown_n": 0,
                  "holdout_metrics": {"status": "evaluated", "physical_cutoff": 1.25,
                                      "n": 20, "AS": .3, "precision": .4}}
        reference = reference_metrics(tier, method, independent_split(),
                                      {"status": "evaluated", "AS_mean": .8, "AS_sd": .02},
                                      {"status": "evaluated", "AS": .6})
        self.assertEqual(reference["holdout_AS"], .3)
        self.assertEqual(reference["source_inner_AS"], .6)
        self.assertEqual(reference["source_grouped_cv_AS"], .8)
        self.assertEqual(reference["screened_input_selected_n"], 35)
        self.assertEqual(reference["holdout_n"], 20)
        self.assertNotIn("cv_AS", reference)
        changed = copy.deepcopy(method)
        changed["holdout_metrics"]["physical_cutoff"] = 1.3
        with self.assertRaises(ValueError):
            reference_metrics(tier, changed, independent_split(), {})
        with self.assertRaises(ValueError):
            reference_metrics(tier, {**method, "holdout_metrics": {}}, independent_split(), {})

    def test_water_case_template_has_polymer_property_identity(self):
        entry = template_for("OPENPOLY_WCA", "STCA", "high", .3, {}, {"unit": "degree"})
        self.assertEqual(entry["id"], "current-openpoly-wca-stca-high-30")
        self.assertEqual(entry["property"], "Water contact angle")
        self.assertEqual(entry["property_zh"], "水接触角")
        with self.assertRaises(ValueError):
            template_for("UNKNOWN", "STCA", "high", .3, {}, {"unit": "degree"})

    def test_refresh_preserves_paper_and_rejects_delivered_model_substitution(self):
        """Exercise the freezer on a source-fit fixture, then corrupt one model."""
        repository = Path(__file__).resolve().parents[1]
        bundled = repository / "skills/stca/assets/rule_library"
        catalog = json.loads((bundled / "catalog.json").read_text())
        paper = next(e for e in catalog["entries"] if e["id"].startswith("paper-"))
        template = next(e for e in catalog["entries"] if e["id"].startswith("current-") and e.get("available"))
        original_constraint = json.loads((bundled / template["constraints"]).read_text())
        with tempfile.TemporaryDirectory(prefix="stca-morgan-freeze-") as folder:
            base = Path(folder)
            repo, run = base / "repo", base / "run"
            skill = repo / "skills/stca"
            library = skill / "assets/rule_library"
            (repo / "examples/open_data").mkdir(parents=True)
            (repo / "validation").mkdir()
            library.mkdir(parents=True)
            (library / "catalog.json").write_text(json.dumps({**catalog, "entries": [paper]}))
            protected = {}
            for relative in [paper["constraints"], *paper["prompts"].values()]:
                destination = library / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(bundled / relative, destination)
                protected[relative] = destination.read_bytes()
            # Runtime imports must resolve to the real maintained implementation.
            (skill / "scripts").symlink_to(repository / "skills/stca/scripts", target_is_directory=True)
            registry = repo / "examples/open_data/dataset_registry.csv"
            with registry.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["dataset", "unit", "public_source", "data_kind"])
                writer.writeheader()
                writer.writerow({"dataset": "OPENPOLY_WCA", "unit": "deg", "public_source": "https://example.org/OpenPoly.csv", "data_kind": "experimental"})
            run.mkdir()
            audit = independent_split()
            (run / "split_audit.json").write_text(json.dumps(audit))
            (run / "run_manifest.json").write_text(json.dumps({"entrypoint": "morgan_evaluation.py", "input_sha256": "raw-input",
                "all_target_dependent_preparation_fit_scope": "source_only", "holdout_labels_used_for_fit_or_selection": False,
                "buffer_used_for_fit_or_selection": False, "original_input_row_n": 110}))
            (run / "source_inner_selection.json").write_text(json.dumps({"scope": "source_only_strict_morgan_validation",
                "holdout_labels_used": False, "status": "unavailable", "tiers": {}}))
            tier = {"fraction": .3, "physical_cutoff": 86.5, "operator": ">=", "unit": "deg", "recommended_method": "STCA", "methods": {}}
            source_tier = copy.deepcopy(tier)
            for method in ("STCA", "WRAcc"):
                constraint = copy.deepcopy(original_constraint)
                constraint["target"]["physical_cutoff"] = 86.5
                relative = f"{method.lower()}/tier_0.3/constraints.json"
                for root in (run, run / "source_fit"):
                    destination = root / relative
                    destination.parent.mkdir(parents=True)
                    destination.write_text(json.dumps(constraint))
                    (root / method.lower() / "model.json").write_text("{}")
                source_tier["methods"][method] = {"constraints": relative}
                tier["methods"][method] = {"constraints": relative, "original_input_n": 110, "selected_n": 30,
                    "unknown_n": 0, "status": "rule_fitted", "rule": constraint["rule"]["expression"],
                    "holdout_metrics": {"status": "evaluated", "physical_cutoff": 86.5, "AS": .4}}
            source = run / "source_fit"
            (source / "screening_summary.json").write_text(json.dumps({"tiers": [source_tier]}))
            (source / "run_manifest.json").write_text(json.dumps({"status": "completed", "input_sha256": "source-input",
                "prepared_measurement_n": 80, "learning_settings": {"tiers": [.3], "transform": "none", "scan": {"step": .1}}}))
            (source / "cv_summary.json").write_text(json.dumps({"methods": {m: {"0.3": {"status": "evaluated", "AS_mean": .8}} for m in ("STCA", "WRAcc")}}))
            (run / "screening_summary.json").write_text(json.dumps({"direction": "high", "holdout_used_for_method_or_tier_selection": False, "tiers": [tier]}))
            spec = base / "spec.json"
            spec.write_text(json.dumps({"runs": [{"dataset_id": "OPENPOLY_WCA", "run_dir": str(run), "tiers": [.3]}]}))
            args = SimpleNamespace(repository=str(repo), skill=str(skill), spec=str(spec), apply=True, allow_partial=True)
            receipt = refresh(args)
            self.assertEqual(receipt["new_rules"], 2)
            for relative, payload in protected.items():
                self.assertEqual((library / relative).read_bytes(), payload)
            entry = json.loads((library / "entries/current-openpoly-wca-stca-high-30/constraints.json").read_text())
            self.assertEqual(entry["provenance"]["fit_scope"], "source_only_frozen_model")
            self.assertEqual(entry["reference_evaluation"]["holdout_AS"], .4)
            (run / "stca/model.json").write_text('{"replaced":true}')
            with self.assertRaisesRegex(ValueError, "Delivered model differs"):
                refresh(args)


if __name__ == "__main__":
    unittest.main()
