#!/usr/bin/env python3
"""Replay a real polymer workflow under create/read-only file permissions.

The integration cases use the local official RadonPy fixture when available.
They run in fresh Python processes so an unrelated imported STCA installation
cannot accidentally satisfy the bundled-source check.
"""
from __future__ import annotations

from contextlib import ExitStack, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SKILL = Path(os.environ.get("STCA_TEST_SKILL_DIR", str(Path(__file__).resolve().parents[1] / "skills/stca"))).resolve()
FIXTURE = Path(os.environ.get("STCA_RADONPY_FIXTURE", str(ROOT / "ecfp4_auto_validation/raw/PI1070.csv")))


def import_inrange():
    sys.path.insert(0, str(SKILL / "scripts"))
    spec = importlib.util.spec_from_file_location("restricted_inrange", SKILL / "scripts/inrange_evaluation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def worker(mode, fixture, destination):
    # Preload numerical packages before applying file-operation fault injection.
    import numpy  # noqa: F401
    import pandas as pd
    import scipy  # noqa: F401
    import sklearn  # noqa: F401
    from rdkit import Chem  # noqa: F401

    sys.dont_write_bytecode = True
    os.environ.pop("STCA_SOURCE", None)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    output = destination / "analysis"
    library = destination / "saved_rules"
    source = pd.read_csv(fixture, dtype=str, keep_default_na=False).iloc[:100].copy()
    source_file = destination / "PI1070_first100.csv"
    source.to_csv(source_file, index=False)
    os.environ["STCA_CACHE_DIR"] = str(destination / "runtime_cache")
    inrange = import_inrange()
    import user_rule_library

    real_save = user_rule_library.save_entry
    original_which = __import__("shutil").which
    original_run = subprocess.run
    intercepted_saves = []

    def no_git_lookup(program, *args, **kwargs):
        return None if Path(program).name.lower() in {"git", "git.exe"} else original_which(program, *args, **kwargs)

    def no_git_command(command, *args, **kwargs):
        if isinstance(command, (list, tuple)) and command and Path(str(command[0])).name.lower() in {"git", "git.exe"}:
            raise AssertionError("Ordinary bundled-source workflow attempted to execute Git")
        return original_run(command, *args, **kwargs)

    def first_rule_save_denied(*args, **kwargs):
        # The denied operation is real storage, after both methods' computed
        # files have become available. Do not change or fake their model data.
        name = args[1] if len(args) > 1 else kwargs["name"]
        intercepted_saves.append(name)
        if " STCA " in name:
            assert (output / "stca/model.json").is_file()
            assert (output / "wracc/model.json").is_file()
            raise PermissionError(13, "Simulated denied write to STCA rule directory", str(library))
        return real_save(*args, **kwargs)

    arguments = ["--input", str(source_file), "--smiles-column", "smiles",
                 "--id-column", "monomer_ID", "--target", "density",
                 "--target-name", "Density", "--unit", "g/cm3",
                 "--direction", "high", "--tiers", "0.30",
                 "--structure-kind", "polymer_repeat_unit", "--skip-influence",
                 "--folds", "2", "--repeats", "1", "--wracc-max-literals", "10",
                 "--output-dir", str(output), "--library-dir", str(library)]
    captured = io.StringIO()
    with ExitStack() as stack:
        stack.enter_context(patch("shutil.which", side_effect=no_git_lookup))
        stack.enter_context(patch("subprocess.run", side_effect=no_git_command))
        if mode == "create_only":
            for operation in ("os.rename", "os.replace", "os.unlink", "os.remove", "os.rmdir", "shutil.rmtree"):
                stack.enter_context(patch(operation, side_effect=PermissionError(13, "Simulated denied rename/delete operation")))
        elif mode == "first_library_denied":
            stack.enter_context(patch.object(user_rule_library, "save_entry", side_effect=first_rule_save_denied))
        else:
            raise ValueError(f"Unsupported worker mode: {mode}")
        with redirect_stdout(captured):
            exit_code = inrange.main(arguments)

    (destination / "command_stdout.jsonl").write_text(captured.getvalue(), encoding="utf-8")
    if exit_code:
        raise RuntimeError(f"Real restricted workflow exited {exit_code}; see {output}")
    manifest = json.loads((output / "run_manifest.json").read_text())
    summary = json.loads((output / "screening_summary.json").read_text())
    receipt = json.loads((output / "saved_rule_receipts.json").read_text())
    delivery = json.loads((output / "delivery_verification.json").read_text())
    assert delivery["status"] == "verified"
    assert manifest["learning_settings"]["target_column"] == "density"
    assert manifest["learning_settings"]["smiles_column"] == "smiles"
    assert manifest["runtime"]["source_integrity"]["requires_git"] is False

    methods = {}
    for method in ("STCA", "WRAcc"):
        directory = output / method.lower()
        model = json.loads((directory / "model.json").read_text())
        assert model["learner"] == method
        result = pd.read_csv(directory / "tier_0.3/screening/results.csv", dtype=str, keep_default_na=False)
        assert len(result) == len(source) == 100
        for column in source:
            assert result[column].tolist() == source[column].tolist(), column
        assert result["smiles"].str.contains("\\*", regex=True).any()
        assert (directory / "tier_0.3/prompt.zh-CN.md").is_file()
        assert (directory / "tier_0.3/prompt.en.md").is_file()
        methods[method] = {"selected": int(result["stca_joint__selected"].eq("True").sum()),
                           "row_n": len(result), "original_column_n": len(source.columns),
                           "save_status": receipt[method]["status"]}
    assert len(pd.read_csv(output / "all_rows_screening.csv")) == 100
    assert set(manifest["methods"]) == {"STCA", "WRAcc"}
    if mode == "create_only":
        assert manifest["status"] == summary["status"] == "completed"
        assert not summary["storage_warnings"]
        assert all(receipt[m]["status"] == "saved_and_exported" for m in methods)
        assert all((output / f"saved_{m.lower()}_rules.zip").is_file() for m in methods)
    else:
        assert manifest["status"] == summary["status"] == "completed_with_storage_warning"
        assert len(summary["storage_warnings"]) == 1
        assert summary["storage_warnings"][0]["method"] == "STCA"
        assert summary["storage_warnings"][0]["error_type"] == "PermissionError"
        assert receipt["STCA"]["status"] == "not_saved_storage_error"
        assert "save" not in receipt["STCA"]
        assert receipt["WRAcc"]["status"] == "saved_and_exported"
        assert len(intercepted_saves) == 2
        assert not summary["all_available_rule_sets_saved_and_exported"]
        assert "规则目录保存或规则包导出未全部完成" in (output / "recommendation.md").read_text()
    result = {"mode": mode, "status": manifest["status"], "Hcap": delivery["status"],
              "source_verification": manifest["runtime"]["source_integrity"],
              "methods": methods, "storage_warnings": summary["storage_warnings"]}
    (destination / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


class RestrictedWorkflowTests(unittest.TestCase):
    def invoke_worker(self, mode):
        with tempfile.TemporaryDirectory(prefix="stca-restricted-integration-") as directory:
            env = dict(os.environ, STCA_TEST_SKILL_DIR=str(SKILL), PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", mode,
                                     str(FIXTURE), str(Path(directory) / "run")],
                                    capture_output=True, text=True, env=env, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
            return json.loads(result.stdout.strip().splitlines()[-1])

    @unittest.skipUnless(FIXTURE.is_file(), "Local official RadonPy fixture is not available")
    def test_full_workflow_without_git_or_rename_or_delete(self):
        result = self.invoke_worker("create_only")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(set(result["methods"]), {"STCA", "WRAcc"})

    @unittest.skipUnless(FIXTURE.is_file(), "Local official RadonPy fixture is not available")
    def test_first_library_save_denied_preserves_both_methods(self):
        result = self.invoke_worker("first_library_denied")
        self.assertEqual(result["status"], "completed_with_storage_warning")
        self.assertEqual(result["methods"]["WRAcc"]["save_status"], "saved_and_exported")

    def test_export_permission_denied_does_not_claim_bundle_saved(self):
        inrange = import_inrange()
        import user_rule_library
        with patch.object(user_rule_library, "save_entry", return_value={"entry": {"id": "rules-test"}}), \
                patch.object(user_rule_library, "export_entry", side_effect=PermissionError(13, "export denied")):
            result = inrange.save_rule_delivery(library_dir=Path("unused-library"), name="test WRAcc",
                method="WRAcc", model_path=Path("existing-model.json"), constraints=[Path("existing-constraints.json")],
                output=Path("existing-output"), count=5, preferences="")
        self.assertEqual(result["status"], "saved_export_failed")
        self.assertIn("save", result)
        self.assertNotIn("export", result)
        self.assertEqual(result["storage_warning"]["operation"], "export_rule_bundle")
        self.assertTrue(result["computed_files_retained"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        unittest.main(verbosity=2)
