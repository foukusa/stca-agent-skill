"""Local discovery, strict overrides and Python-free launcher regression checks."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(os.environ.get("STCA_TEST_SKILL_DIR", Path(__file__).resolve().parents[1] / "skills/stca"))
sys.path.insert(0, str(SKILL / "scripts"))
import runtime_discovery as discovery
import agent_runtime as runtime


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="stca discovery ")
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.cwd = self.root / "project"
        self.home.mkdir(); self.cwd.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def python_at(self, prefix, windows=False):
        p = Path(prefix) / ("python.exe" if windows else "bin/python")
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text("fixture")
        return str(p)

    def discover(self, **kwargs):
        with patch.object(discovery.shutil, "which", return_value=None):
            return discovery.discover_interpreters(home=self.home, cwd=self.cwd,
                    environ={}, system="Darwin", **kwargs)

    def test_explicit_override_is_the_only_candidate_and_never_enumerates(self):
        with patch.object(discovery.subprocess, "run", side_effect=AssertionError("must not enumerate")):
            result = self.discover(explicit="/chosen/python", saved_python="/other/python")
        self.assertEqual(result["policy"], "explicit_only")
        self.assertEqual(result["candidates"], [{"python": "/chosen/python", "origin": "explicit_override"}])

    def test_previous_success_precedes_current_and_common_environments(self):
        project = self.python_at(self.cwd / ".venv")
        user = self.python_at(self.home / ".venvs/chem")
        result = self.discover(saved_python="/last/success/python")
        paths = [r["python"] for r in result["candidates"]]
        self.assertEqual(paths[0], "/last/success/python")
        self.assertIn(project, paths); self.assertIn(user, paths)
        self.assertLess(paths.index(project), paths.index(user))
        self.assertFalse(result["installs_performed"])
        self.assertFalse(result["recursive_disk_scan"])

    def test_inactive_external_conda_env_is_found_from_json(self):
        python = self.python_at(self.root / "external chemistry environment")
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0,
                json.dumps({"envs": [str(Path(python).parent.parent)]}), "")
        def which(name):
            return "/conda/conda" if name == "conda" else None
        with patch.object(discovery.shutil, "which", side_effect=which), patch.object(discovery.subprocess, "run", side_effect=run):
            result = discovery.discover_interpreters(home=self.home, cwd=self.cwd, environ={}, system="Darwin")
        self.assertIn({"python": python, "origin": "conda_env_list"}, result["candidates"])
        self.assertEqual(calls, [["/conda/conda", "env", "list", "--json"]])

    def test_conda_registry_and_uv_do_not_require_activated_environment(self):
        python = self.python_at(self.root / "registered chemistry")
        registry = self.home / ".conda/environments.txt"
        registry.parent.mkdir(); registry.write_text(str(Path(python).parent.parent) + "\n")
        uv = self.python_at(self.home / ".local/share/uv/python/cpython-3.10-platform")
        result = self.discover()
        self.assertIn({"python": python, "origin": "conda_environment_registry"}, result["candidates"])
        self.assertIn({"python": uv, "origin": "uv_python"}, result["candidates"])

    def test_bad_conda_inventory_does_not_hide_project_venv(self):
        python = self.python_at(self.cwd / ".venv")
        with patch.object(discovery.shutil, "which", side_effect=lambda name: "/conda" if name == "conda" else None), patch.object(discovery.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "not JSON", "")):
            result = discovery.discover_interpreters(home=self.home, cwd=self.cwd, environ={}, system="Darwin")
        self.assertIn(python, [r["python"] for r in result["candidates"]])
        self.assertIn("conda_inventory_unavailable", result["notes"])

    def test_windows_user_install_and_inactive_conda_locations(self):
        local = self.root / "Local AppData"
        installed = self.python_at(local / "Programs/Python/Python311", windows=True)
        conda = self.python_at(self.home / "miniconda3/envs/rdkit", windows=True)
        with patch.object(discovery.shutil, "which", return_value=None):
            result = discovery.discover_interpreters(home=self.home, cwd=self.cwd,
                environ={"LOCALAPPDATA": str(local)}, system="Windows")
        paths = [r["python"] for r in result["candidates"]]
        self.assertIn(installed, paths); self.assertIn(conda, paths)

    def test_candidate_count_is_bounded_even_with_many_environments(self):
        for n in range(130):
            self.python_at(self.home / ".venvs" / f"env-{n:03d}")
        result = self.discover()
        self.assertLessEqual(len(result["candidates"]), discovery.MAX_CANDIDATES)
        self.assertLessEqual(sum(r["origin"] == "user_venv" for r in result["candidates"]), discovery.MAX_CHILDREN)

    def test_explicit_failure_never_installs_or_substitutes_another_environment(self):
        failure = {"ready": False, "errors": ["rdkit missing"]}
        with patch.object(runtime, "existing_source", return_value=None), patch.object(runtime, "probe", return_value=failure), patch.object(runtime, "prepare_chem", side_effect=AssertionError("must not install")), patch.object(runtime, "setup_interpreter", side_effect=AssertionError("must not substitute")):
            with self.assertRaisesRegex(RuntimeError, "explicitly selected Python"):
                runtime.ensure("chem", python="/chosen/python")

    def test_diagnostics_include_examined_failure_and_selected_environment(self):
        with patch.object(runtime, "candidates", return_value=["/bad/python", "/good/python"]), patch.object(runtime, "probe", side_effect=[{"ready": False, "errors": ["rdkit missing"]}, {"ready": True, "python": "/good/python"}]):
            ready, result = runtime.inspect_runtimes("chem")
        self.assertEqual(ready["python"], "/good/python")
        self.assertEqual(result["examined"][0]["errors"], ["rdkit missing"])
        self.assertEqual(result["selected_python"], "/good/python")
        self.assertFalse(result["installs_performed"])

    def test_discover_command_never_prepares_dependencies(self):
        with patch.object(runtime, "inspect_runtimes", return_value=(None, {"examined": []})), patch.object(runtime, "ensure", side_effect=AssertionError("must not prepare")):
            with patch("builtins.print") as output:
                code = runtime.main(["discover", "--mode", "chem"])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(output.call_args.args[0])["ready"])

    def test_posix_first_launch_with_empty_path_and_spaces(self):
        prefix = self.home / ".venvs/chemistry environment"
        p = prefix / "bin/python"; p.parent.mkdir(parents=True)
        p.symlink_to(sys.executable)
        script = self.root / "show arguments.py"
        script.write_text("import json,sys;print(json.dumps({'python':sys.executable,'args':sys.argv[1:]}))")
        env = dict(os.environ, PATH="", HOME=str(self.home))
        for name in ("STCA_PY", "STCA_BOOTSTRAP_PY", "VIRTUAL_ENV", "CONDA_PREFIX"):
            env.pop(name, None)
        result = subprocess.run(["/bin/sh", str(SKILL / "scripts/launch_runtime.sh"), "--script", str(script), "argument with spaces"],
                                cwd=self.cwd, env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["python"], str(p))
        self.assertEqual(value["args"], ["argument with spaces"])

    def test_posix_bad_explicit_bootstrap_never_falls_back(self):
        script = self.root / "must-not-run.py"; script.write_text("raise Exception('unexpected fallback')")
        result = subprocess.run(["/bin/sh", str(SKILL / "scripts/launch_runtime.sh"), "--bootstrap-python", "/does/not/exist/python", "--script", str(script)],
                                env=dict(os.environ, STCA_PY=sys.executable), capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no other interpreter was substituted", result.stderr)
        self.assertNotIn("unexpected fallback", result.stderr)

    def test_posix_downstream_python_option_is_preserved(self):
        script = self.root / "show.py"; script.write_text("import json,sys;print(json.dumps(sys.argv[1:]))")
        result = subprocess.run(["/bin/sh", str(SKILL / "scripts/launch_runtime.sh"), "--script", str(script), "--python", sys.executable, "--no-install", "ensure"],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["--python", sys.executable, "--no-install", "ensure"])

    def test_posix_global_options_before_explicit_python_are_preserved(self):
        script = self.root / "show.py"; script.write_text("import json,sys;print(json.dumps(sys.argv[1:]))")
        result = subprocess.run(["/bin/sh", str(SKILL / "scripts/launch_runtime.sh"), "--script", str(script), "--no-install", "--python", sys.executable, "ensure"],
                                env=dict(os.environ, PATH=""), capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["--no-install", "--python", sys.executable, "ensure"])

    @unittest.skipUnless(os.environ.get("STCA_TEST_REAL_PYTHON"), "requires a prepared local RDKit interpreter")
    def test_actual_rdkit_environment_passes_without_install(self):
        python = os.environ["STCA_TEST_REAL_PYTHON"]
        with patch.object(runtime, "RECEIPT", self.root / "runtime.json"), patch.object(runtime, "existing_source", return_value=None), patch.object(runtime, "prepare_chem", side_effect=AssertionError("must not install")):
            result = runtime.ensure("chem", python=python, allow_install=False)
        self.assertTrue(result["ready"])
        self.assertFalse(result["installed_now"])
        self.assertEqual(result["functional_checks"]["maccs167_panel"]["bits"], 167)
        self.assertEqual(result["runtime_discovery"]["policy"], "explicit_only")
        self.assertTrue((self.root / "runtime.json").is_file())

    @unittest.skipUnless(os.environ.get("STCA_TEST_REAL_PYTHON"), "requires a prepared local RDKit interpreter")
    def test_actual_saved_rdkit_environment_is_discovered_before_current_python(self):
        python = os.environ["STCA_TEST_REAL_PYTHON"]
        receipt = self.root / "runtime.json"
        receipt.write_text(json.dumps({"python": python}))
        with patch.object(runtime, "RECEIPT", receipt), patch.object(runtime, "existing_source", return_value=None), patch.object(runtime, "prepare_chem", side_effect=AssertionError("must not install")):
            result = runtime.ensure("chem", allow_install=False)
        self.assertTrue(result["ready"])
        self.assertEqual(result["runtime_discovery"]["examined"][0]["origin"], "previous_success")
        self.assertEqual(len(result["runtime_discovery"]["examined"]), 1)
        self.assertFalse(result["installed_now"])

    @unittest.skipUnless(os.environ.get("STCA_TEST_REAL_PYTHON"), "requires a prepared local fit interpreter")
    def test_actual_fit_runtime_passes_functional_api_checks_without_install(self):
        ready, report = runtime.inspect_runtimes("fit", os.environ["STCA_TEST_REAL_PYTHON"])
        self.assertTrue(ready and ready["ready"], report)
        self.assertTrue(ready["functional_checks"]["fit_apis"]["tsne_max_iter_api"])
        self.assertFalse(report["installs_performed"])


if __name__ == "__main__":
    unittest.main()
