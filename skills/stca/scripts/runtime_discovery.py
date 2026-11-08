#!/usr/bin/env python3
"""Bounded, read-only discovery of local Python environments.

A path is only a candidate. The caller must execute its actual runtime probe
before using it. Discovery never installs packages or scans the whole disk.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

MAX_CANDIDATES = 96
MAX_CHILDREN = 32
PYTHON_COMMANDS = ("python3", "python", *(f"python3.{n}" for n in range(10, 16)))


def _children(root, pattern="*"):
    try:
        return sorted(root.glob(pattern))[:MAX_CHILDREN]
    except (OSError, ValueError):
        return []


def discover_interpreters(explicit=None, saved_python=None, *, environ=None,
                          cwd=None, home=None, system=None):
    env = dict(os.environ if environ is None else environ)
    task_home = Path.home() if home is None else Path(home)
    task_cwd = Path.cwd() if cwd is None else Path(cwd)
    host = system or platform.system()
    windows = host == "Windows"
    results, notes, seen = [], [], set()

    def add(value, origin, *, require_file=False):
        if not value or len(results) >= MAX_CANDIDATES:
            return
        value = os.path.expandvars(os.path.expanduser(str(value)))
        path = Path(value)
        if not path.is_absolute() and len(path.parts) == 1:
            value = shutil.which(value) or value
            path = Path(value)
        if require_file and not path.is_file():
            return
        # Do not resolve symlinks: venv interpreter paths carry environment identity.
        key = value.casefold() if windows else value
        if key not in seen:
            seen.add(key)
            results.append({"python": value, "origin": origin})

    def prefix(path, origin):
        path = Path(path)
        for relative in (("python.exe", "Scripts/python.exe") if windows else ("bin/python", "bin/python3")):
            candidate = path / relative
            if candidate.is_file():
                add(candidate, origin, require_file=True)
                break

    if explicit:
        add(explicit, "explicit_override")
        return {"policy": "explicit_only", "candidates": results, "notes": notes}
    add(saved_python, "previous_success")
    add(env.get("STCA_PY"), "STCA_PY")
    add(sys.executable, "current_interpreter")
    for variable in ("VIRTUAL_ENV", "CONDA_PREFIX"):
        if env.get(variable):
            prefix(env[variable], variable)
    for command in PYTHON_COMMANDS:
        add(shutil.which(command), "PATH:" + command)

    # Project and user virtualenvs precede large distribution inventories.
    for name in (".venv", "venv", ".env"):
        prefix(task_cwd / name, "project_venv")

    conda_roots = [task_home / name for name in
                   ("miniconda3", "anaconda3", "miniforge3", "mambaforge", "micromamba")]
    if windows:
        local = env.get("LOCALAPPDATA")
        if local:
            conda_roots += [Path(local) / name for name in ("miniconda3", "anaconda3", "miniforge3")]
        for value in (env.get("ProgramData"), env.get("PROGRAMDATA")):
            if value:
                conda_roots += [Path(value) / name for name in ("miniconda3", "anaconda3", "miniforge3")]
    else:
        conda_roots += [Path(p) for p in ("/opt/conda", "/opt/miniconda3", "/opt/anaconda3",
                                        "/opt/homebrew/Caskroom/miniforge/base", "/usr/local/Caskroom/miniforge/base")]

    registry = task_home / ".conda/environments.txt"
    try:
        if registry.is_file() and registry.stat().st_size <= 65536:
            for value in registry.read_text(encoding="utf-8").splitlines()[:64]:
                if value.strip():
                    prefix(value.strip(), "conda_environment_registry")
    except (OSError, UnicodeError):
        notes.append("conda_environment_registry_unreadable")

    # Conda's JSON inventory also finds named environments outside standard roots.
    conda_commands = [env.get("CONDA_EXE"), shutil.which("conda")]
    for root in conda_roots:
        candidate = root / ("Scripts/conda.exe" if windows else "bin/conda")
        if candidate.is_file():
            conda_commands.append(str(candidate))
    attempted = set()
    for conda in conda_commands:
        if not conda or conda in attempted:
            continue
        attempted.add(conda)
        if len(attempted) > 2:
            break
        try:
            process = subprocess.run([conda, "env", "list", "--json"], capture_output=True,
                                     text=True, timeout=6)
            if process.returncode:
                notes.append("conda_inventory_failed")
                continue
            value = json.loads(process.stdout)
            paths = value.get("envs", []) if isinstance(value, dict) else []
            if not isinstance(paths, list):
                notes.append("conda_inventory_invalid_env_list")
                continue
            for path in paths[:64]:
                if isinstance(path, str):
                    prefix(path, "conda_env_list")
        except (OSError, ValueError, subprocess.TimeoutExpired):
            notes.append("conda_inventory_unavailable")

    # Large fallback directory inventories must not crowd out Conda's own list.
    for root in (task_home / ".venvs", task_home / ".virtualenvs",
                 task_home / ".local/share/virtualenvs"):
        for child in _children(root):
            prefix(child, "user_venv")
    for child in _children(task_home / ".local/share/uv/python"):
        prefix(child, "uv_python")

    for root in conda_roots:
        prefix(root, "common_conda_base")
        for child in _children(root / "envs"):
            prefix(child, "common_conda_env")

    if windows:
        local = env.get("LOCALAPPDATA")
        if local:
            for child in _children(Path(local) / "Programs/Python", "Python*"):
                prefix(child, "windows_python")
        for root in [env.get("ProgramFiles"), env.get("ProgramFiles(x86)")]:
            if root:
                for child in _children(Path(root), "Python*"):
                    prefix(child, "windows_python")
        py = shutil.which("py")
        if py:
            try:
                process = subprocess.run([py, "-0p"], capture_output=True, text=True, timeout=6)
                for line in (process.stdout + "\n" + process.stderr).splitlines()[:64]:
                    match = re.search(r"([A-Za-z]:\\.*?python(?:\d+(?:\.\d+)*)?\.exe)\s*$", line, re.I)
                    if match:
                        add(match.group(1), "windows_py_launcher", require_file=True)
            except (OSError, subprocess.TimeoutExpired):
                notes.append("windows_py_inventory_unavailable")
    else:
        for directory in (Path("/opt/homebrew/bin"), Path("/usr/local/bin"), Path("/usr/bin")):
            for name in PYTHON_COMMANDS:
                add(directory / name, "system_python", require_file=True)
        for root in (Path("/Library/Frameworks/Python.framework/Versions"),
                     task_home / "Library/Python"):
            for child in _children(root):
                prefix(child, "macos_python")
    return {"policy": "bounded_local_environment_discovery_v1", "candidates": results,
            "notes": list(dict.fromkeys(notes)), "maximum_candidates": MAX_CANDIDATES,
            "recursive_disk_scan": False, "installs_performed": False}
