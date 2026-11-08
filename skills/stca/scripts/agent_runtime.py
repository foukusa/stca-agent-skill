#!/usr/bin/env python3
"""Agent-owned runtime discovery/preparation; never asks users to run shell setup."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile

from stca_runtime import UPSTREAM_COMMIT, UPSTREAM_URL, cache_root, verify_source

SCRIPTS = Path(__file__).resolve().parent
RECEIPT = cache_root() / "agent-runtime.json"
ALLOWED = {"rule_library.py", "auto_screen.py", "custom_fit.py", "evaluate_custom.py",
           "stca_tools.py", "data_cleaning.py", "prepare_hcap.py", "data_readiness.py",
           "generation_prompt.py", "generation_session.py", "audit_dataset.py", "task_menu.py", "user_rule_library.py",
           "inrange_evaluation.py", "auto_data_layer.py"}


def receipt():
    try:
        value = json.loads(RECEIPT.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def candidates(explicit=None):
    saved = receipt()
    values = [explicit, sys.executable, os.environ.get("STCA_PY"), saved.get("python")]
    for name in ("VIRTUAL_ENV", "CONDA_PREFIX"):
        if os.environ.get(name):
            values.append(str(Path(os.environ[name]) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")))
    for command in ("python3", "python", "python3.10", "python3.11", "python3.12",
                    "python3.13", "python3.14", "python3.15"):
        values.append(shutil.which(command))
    unique = []
    for value in values:
        if value and str(value) not in unique:
            unique.append(str(value))
    return unique


def probe(python, mode, dependency_mode="compatible"):
    command = [python, str(SCRIPTS / "runtime_compat.py"), "--mode", mode]
    if dependency_mode == "locked":
        command.append("--locked")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        value = json.loads(result.stdout)
        if not isinstance(value, dict) or "ready" not in value:
            raise ValueError("Runtime probe did not return a readiness record.")
        return value
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {"ready": False, "python": python, "error": str(exc)}


def existing_source(explicit=None):
    for path in [explicit, os.environ.get("STCA_SOURCE"), receipt().get("source"), cache_root() / "source"]:
        if not path:
            continue
        try:
            return str(verify_source(path))
        except (ValueError, RuntimeError, OSError):
            continue
    return None


def save(value):
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RECEIPT.parent,
                                         prefix=RECEIPT.stem + "-", suffix=".tmp",
                                         delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(RECEIPT)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return value


def setup_interpreter(mode, python=None, dependency_mode="compatible"):
    """Reuse the first available CPython >=3.10; exact 3.12 is opt-in only."""
    for candidate in candidates(python):
        try:
            result = subprocess.run(
                [candidate, "-c", "import json,platform,sys;print(json.dumps({'version':list(sys.version_info[:2]),'implementation':platform.python_implementation()}))"],
                capture_output=True, text=True, timeout=10)
            if result.returncode:
                continue
            version = json.loads(result.stdout)
            number = tuple(version["version"])
            if version.get("implementation") != "CPython":
                continue
            if dependency_mode == "locked" and number == (3, 12):
                return candidate
            if dependency_mode == "compatible" and number >= (3, 10):
                return candidate
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
            continue
    return None


def acquire_interpreter(dependency_mode="compatible"):
    """Let an available uv prepare a user-cache Python, without global setup."""
    uv = shutil.which("uv")
    if not uv:
        return None
    target = "3.12" if dependency_mode == "locked" else "3.10"
    env = dict(os.environ)
    env["UV_PYTHON_INSTALL_DIR"] = str(cache_root() / "python")
    installed = subprocess.run([uv, "python", "install", target],
                               capture_output=True, text=True, timeout=180, env=env)
    if installed.returncode:
        raise RuntimeError("Agent Python preparation failed: " + installed.stderr[-6000:])
    found = subprocess.run([uv, "python", "find", target],
                           capture_output=True, text=True, timeout=30, env=env)
    if found.returncode:
        raise RuntimeError("Agent could not locate the prepared Python: " + found.stderr[-6000:])
    interpreter = found.stdout.strip()
    if not interpreter or "\n" in interpreter or not Path(interpreter).is_file():
        raise RuntimeError("Agent Python preparation did not return an executable file.")
    return interpreter


def prepare_chem(python, destination, dependency_mode="compatible"):
    """Prepare only a compatible RDKit wheel and its required dependencies."""
    uv = shutil.which("uv")
    create_command = ([uv, "venv", "--python", python, "--seed", str(destination)]
                      if uv else [python, "-m", "venv", str(destination)])
    created = subprocess.run(create_command,
                             capture_output=True, text=True, timeout=120)
    if created.returncode:
        raise RuntimeError("Agent chemistry environment creation failed: " + created.stderr[-6000:])
    interpreter = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    dependency = "rdkit==2025.9.4" if dependency_mode == "locked" else "rdkit>=2023.9"
    command = [str(interpreter), "-m", "pip", "install", "--disable-pip-version-check",
               "--no-input", "--retries", "0", "--timeout", "15",
               "--index-url", "https://pypi.org/simple", "--only-binary=:all:"]
    if dependency_mode == "locked":
        command += ["--report", str(destination / "stca-chem-pip-install.json")]
    command.append(dependency)
    installed = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if installed.returncode:
        raise RuntimeError("Agent chemistry dependency preparation failed: " + installed.stderr[-6000:])
    check = probe(str(interpreter), "chem", dependency_mode)
    if not check.get("ready"):
        raise RuntimeError("Prepared chemistry runtime did not pass verification: " + json.dumps(check))
    return {**check, "mode": "chem", "source": None, "managed_by_agent": True,
            "installed_now": True, "environment_kind": "isolated_RDKit_only",
            "requested_dependency": dependency,
            "dependency_policy": "Compatible wheel and functional MACCS checks; no fit stack or author source. An exact version is requested only in explicit locked mode.",
            "pip_install_report": str(destination / "stca-chem-pip-install.json") if dependency_mode == "locked" else None}


def prepare_source():
    """Obtain only the pinned author source when a compatible runtime exists."""
    if not shutil.which("git"):
        raise RuntimeError("This host cannot prepare the pinned STCA source because Git is unavailable.")
    destination = cache_root() / ("source-" + secrets.token_hex(4))
    destination.parent.mkdir(parents=True, exist_ok=True)
    commands = (["git", "clone", "--no-checkout", UPSTREAM_URL, str(destination)],
                ["git", "-C", str(destination), "checkout", "--detach", UPSTREAM_COMMIT])
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise RuntimeError("Agent source preparation failed: " + result.stderr[-6000:])
    return str(verify_source(destination))


def ensure(mode="fit", python=None, source=None, allow_install=True, dependency_mode="compatible"):
    if dependency_mode not in {"compatible", "locked"}:
        raise ValueError("dependency_mode must be compatible or locked.")
    found_source = existing_source(source)
    ready = None
    for candidate in candidates(python):
        inspected = probe(candidate, mode, dependency_mode)
        if inspected.get("ready"):
            ready = inspected
            break
    if ready:
        prepared_source = False
        if mode == "fit" and not found_source:
            if not allow_install:
                raise RuntimeError("A compatible runtime exists, but the pinned STCA source is unavailable and preparation is disabled.")
            found_source = prepare_source()
            prepared_source = True
        # Existing dependencies stay in place, including Python 3.10 hosts.
        return save({**ready, "mode": mode, "source": found_source,
                     "managed_by_agent": True, "installed_now": False,
                     "source_prepared_now": prepared_source})
    if not allow_install:
        raise RuntimeError("No compatible prepared runtime. Agent runtime preparation is required before calculation.")
    setup_python = setup_interpreter(mode, python, dependency_mode)
    if not setup_python:
        setup_python = acquire_interpreter(dependency_mode)
    if not setup_python:
        requirement = "CPython 3.12 for the explicit archival lock" if dependency_mode == "locked" else "CPython >=3.10"
        raise RuntimeError(f"This host has no {requirement} runtime for automatic dependency preparation. Rule lookup and generation prompts remain available without calculation.")
    destination = cache_root() / ("managed-0.1.0-" + secrets.token_hex(4))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if mode == "chem":
        return save(prepare_chem(setup_python, destination, dependency_mode))
    command = [setup_python, str(SCRIPTS / "setup_locked_environment.py"), "--env-dir", str(destination),
               "--dependency-mode", "portable-pinned" if dependency_mode == "locked" else "compatible"]
    if found_source:
        command += ["--source", found_source]
    # The ordinary installer resolves compatible wheels; exact pins are opt-in.
    result = subprocess.run(command, capture_output=True, text=True, timeout=600)
    if result.returncode:
        raise RuntimeError("Agent runtime preparation failed: " + result.stderr[-6000:])
    prepared = json.loads(result.stdout)
    check = probe(prepared["python"], mode, dependency_mode)
    if not check.get("ready"):
        raise RuntimeError("Prepared runtime did not pass verification: " + json.dumps(check))
    return save({**prepared, "mode": mode, "managed_by_agent": True, "installed_now": True})


def stdlib_operation(script, arguments):
    if script in {"generation_prompt.py", "generation_session.py", "task_menu.py", "user_rule_library.py"}:
        return True
    if script != "rule_library.py":
        return False
    # The library's global --library-dir may precede its subcommand.
    index = 0
    while index < len(arguments):
        item = arguments[index]
        if item == "--library-dir":
            index += 2
        elif item.startswith("--library-dir="):
            index += 1
        else:
            return item in {"list", "show", "prompt", "-h", "--help"}
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", help="Agent-provided existing interpreter, if known")
    parser.add_argument("--source", help="Agent-provided pinned source, if known")
    parser.add_argument("--no-install", action="store_true")
    parser.add_argument("--dependency-mode", choices=("compatible", "locked"), default="compatible",
                        help="Compatible installed packages by default; locked is an explicit archival option")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("ensure")
    check.add_argument("--mode", choices=("fit", "chem"), default="fit")
    run = sub.add_parser("run")
    run.add_argument("--script", choices=sorted(ALLOWED), required=True)
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.action == "ensure":
            print(json.dumps(ensure(args.mode, args.python, args.source, not args.no_install, args.dependency_mode)))
            return 0
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        if stdlib_operation(args.script, arguments):
            return subprocess.run([sys.executable, str(SCRIPTS / args.script), *arguments]).returncode
        # The standalone cleaning CLI imports pandas; prepare_hcap also records
        # a verified author-source receipt. Only bundled-rule checks are RDKit-only.
        mode = "chem" if args.script == "rule_library.py" else "fit"
        available = ensure(mode, args.python, args.source, not args.no_install, args.dependency_mode)
        env = dict(os.environ)
        if available.get("source"):
            env["STCA_SOURCE"] = available["source"]
        return subprocess.run([available["python"], str(SCRIPTS / args.script), *arguments], env=env).returncode
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("stca-agent-runtime: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
