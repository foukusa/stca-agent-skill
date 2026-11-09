#!/usr/bin/env python3
"""Agent-owned runtime discovery/preparation; never asks users to run shell setup."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time

from stca_runtime import UPSTREAM_COMMIT, UPSTREAM_URL, cache_root, verify_source
from runtime_discovery import discover_interpreters

SCRIPTS = Path(__file__).resolve().parent
RECEIPT = cache_root() / "agent-runtime.json"
ALLOWED = {"rule_library.py", "auto_screen.py", "custom_fit.py", "evaluate_custom.py",
           "stca_tools.py", "data_cleaning.py", "prepare_hcap.py", "data_readiness.py",
           "generation_prompt.py", "generation_session.py", "audit_dataset.py", "task_menu.py", "user_rule_library.py",
           "inrange_evaluation.py", "morgan_evaluation.py", "auto_data_layer.py", "fingerprint_contract.py"}


def receipt():
    """Read the newest complete receipt; incomplete writes never become state."""
    try:
        paths = [RECEIPT, *RECEIPT.parent.glob(RECEIPT.stem + "-*.json")]
        paths = sorted((path for path in paths if path.is_file() and not path.is_symlink()),
                       key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)
    except OSError:
        return {}
    complete, legacy = [], None
    for path in paths:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                continue
            if value.get("schema") == "stca-agent-runtime-receipt-v2":
                record = value["record"]
                payload = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
                if (isinstance(record, dict) and value.get("complete") is True
                        and hashlib.sha256(payload).hexdigest() == value.get("record_sha256")):
                    complete.append((int(value.get("created_at_ns", path.stat().st_mtime_ns)),
                                     path.name, record))
            elif path == RECEIPT and "schema" not in value:
                # Read-only compatibility for previous interpreter hints. The
                # interpreter is still probed; cached source is never trusted.
                legacy = value
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return max(complete, key=lambda item: item[:2])[2] if complete else legacy or {}


_last_discovery = {}


def candidates(explicit=None):
    global _last_discovery
    _last_discovery = discover_interpreters(explicit, receipt().get("python"))
    return [record["python"] for record in _last_discovery["candidates"]]


def inspect_runtimes(mode="fit", python=None, dependency_mode="compatible"):
    """Read-only discovery and actual dependency checks; never installs."""
    global _last_discovery
    _last_discovery = {}
    paths = candidates(python)
    discovery = dict(_last_discovery)
    origins = {item["python"]: item["origin"] for item in discovery.get("candidates", [])}
    examined, ready = [], None
    deadline = time.monotonic() + 35
    for candidate in paths:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            discovery.setdefault("notes", []).append("runtime_probe_time_budget_reached")
            break
        value = probe(candidate, mode, dependency_mode, timeout=min(12, remaining))
        examined.append({"python": candidate, "origin": origins.get(candidate, "candidate"),
                         "ready": bool(value.get("ready")),
                         "errors": value.get("errors", [value["error"]] if value.get("error") else []),
                         "diagnostic": value.get("diagnostic")})
        if value.get("ready"):
            ready = value
            break
    discovery.update({"examined": examined, "candidate_count": len(paths),
                      "selected_python": ready.get("python") if ready else None,
                      "installs_performed": False})
    return ready, discovery


def probe(python, mode, dependency_mode="compatible", timeout=30):
    command = [python, str(SCRIPTS / "runtime_compat.py"), "--mode", mode]
    if dependency_mode == "locked":
        command.append("--locked")
    result = None
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        value = json.loads(result.stdout)
        if not isinstance(value, dict) or "ready" not in value:
            raise ValueError("Runtime probe did not return a readiness record.")
        return value
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {"ready": False, "python": python, "error": str(exc),
                "diagnostic": result.stderr[-2000:] if result is not None else None}


def existing_source(explicit=None):
    # Explicit configuration is authoritative: a damaged selected tree must
    # produce one clear error rather than silently trigger another clone.
    selected = explicit or os.environ.get("STCA_SOURCE")
    return str(verify_source(selected))


def save(value):
    """Create a new complete record without rename, deletion or overwriting."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    envelope = {"schema": "stca-agent-runtime-receipt-v2", "complete": True,
                "created_at_ns": time.time_ns(),
                "record_sha256": hashlib.sha256(payload).hexdigest(), "record": value}
    data = (json.dumps(envelope, indent=2, allow_nan=False) + "\n").encode()
    try:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        path = RECEIPT if not RECEIPT.exists() else RECEIPT.with_name(
            f"{RECEIPT.stem}-{time.time_ns()}-{secrets.token_hex(6)}.json")
        try:
            handle = path.open("xb")
        except FileExistsError:
            # A concurrent first writer won; create our own immutable record.
            path = RECEIPT.with_name(f"{RECEIPT.stem}-{time.time_ns()}-{secrets.token_hex(6)}.json")
            handle = path.open("xb")
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except PermissionError as exc:
        raise PermissionError(f"Cannot save the runtime receipt in {RECEIPT.parent}. "
            "Use an authorized writable task workspace or authorize this exact cache path. "
            "No permissions, source verifier or existing files were changed.") from exc
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
    """Verify the packaged author snapshot; ordinary preparation is offline."""
    return str(verify_source())


def ensure(mode="fit", python=None, source=None, allow_install=True, dependency_mode="compatible"):
    if dependency_mode not in {"compatible", "locked"}:
        raise ValueError("dependency_mode must be compatible or locked.")
    found_source = existing_source(source)
    ready, discovery = inspect_runtimes(mode, python, dependency_mode)
    if python and not ready:
        raise RuntimeError("The explicitly selected Python did not pass the required runtime checks; "
                           "no alternative interpreter or environment was substituted. " +
                           json.dumps(discovery, ensure_ascii=False))
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
                     "source_prepared_now": prepared_source, "runtime_discovery": discovery})
    if not allow_install:
        raise RuntimeError("No compatible prepared runtime. Agent runtime preparation is required before calculation. " + json.dumps(discovery, ensure_ascii=False))
    setup_python = setup_interpreter(mode, python, dependency_mode)
    if not setup_python:
        setup_python = acquire_interpreter(dependency_mode)
    if not setup_python:
        requirement = "CPython 3.12 for the explicit archival lock" if dependency_mode == "locked" else "CPython >=3.10"
        raise RuntimeError(f"This host has no {requirement} runtime for automatic dependency preparation. Rule lookup and generation prompts remain available without calculation.")
    destination = cache_root() / ("managed-0.1.0-" + secrets.token_hex(4))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if mode == "chem":
        return save({**prepare_chem(setup_python, destination, dependency_mode), "runtime_discovery": discovery})
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
    return save({**prepared, "mode": mode, "managed_by_agent": True, "installed_now": True, "runtime_discovery": discovery})


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
    parser.add_argument("--source", help="Explicit verified author snapshot or clean checkout; ordinarily use the bundled offline source")
    parser.add_argument("--no-install", action="store_true")
    parser.add_argument("--dependency-mode", choices=("compatible", "locked"), default="compatible",
                        help="Compatible installed packages by default; locked is an explicit archival option")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("ensure")
    check.add_argument("--mode", choices=("fit", "chem"), default="fit")
    inspect = sub.add_parser("discover", help="Read-only interpreter and dependency discovery; never installs")
    inspect.add_argument("--mode", choices=("fit", "chem"), default="fit")
    run = sub.add_parser("run")
    run.add_argument("--script", choices=sorted(ALLOWED), required=True)
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.action == "discover":
            ready, discovery = inspect_runtimes(args.mode, args.python, args.dependency_mode)
            print(json.dumps({"ready": bool(ready), "runtime": ready, "discovery": discovery}, ensure_ascii=False))
            return 0 if ready else 2
        if args.action == "ensure":
            print(json.dumps(ensure(args.mode, args.python, args.source, not args.no_install, args.dependency_mode)))
            return 0
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        if stdlib_operation(args.script, arguments):
            interpreter = sys.executable
            if args.python:
                interpreter = setup_interpreter("stdlib", args.python, args.dependency_mode)
                if not interpreter:
                    raise RuntimeError("The explicitly selected Python is unavailable or incompatible; no substitute was used.")
            return subprocess.run([interpreter, str(SCRIPTS / args.script), *arguments]).returncode
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
