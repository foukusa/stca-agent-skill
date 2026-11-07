#!/usr/bin/env python3
"""Create a fresh, pinned STCA release environment without changing the algorithm.

Use the emitted Python and source paths directly; do not run the convenience
bootstrap afterward. Existing directories are never changed or removed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv

from stca_runtime import UPSTREAM_COMMIT, UPSTREAM_URL, verify_source


def run(command: list[str], *, timeout: int = 300) -> None:
    """Send progress to stderr so stdout remains one machine-readable JSON object."""
    subprocess.run(command, check=True, stdout=sys.stderr, timeout=timeout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-dir", required=True, help="New directory for the isolated Python environment; must not exist.")
    parser.add_argument("--source", help="Optional existing clean checkout at the pinned STCA revision; otherwise clone into the new environment.")
    parser.add_argument("--dependency-mode", choices=("linux-hashed", "portable-pinned"), help="Default: hashed wheels on Linux x86_64; exact version pins on other systems. Only Linux has been validated.")
    args = parser.parse_args(argv)
    try:
        if sys.version_info[:2] != (3, 12):
            raise ValueError("This release environment requires CPython 3.12. Run this script with python3.12.")
        if platform.python_implementation() != "CPython":
            raise ValueError("This release environment is prepared for CPython, not an alternative interpreter.")
        destination = Path(args.env_dir).expanduser().absolute()
        if destination.exists() or destination.is_symlink():
            raise ValueError("--env-dir already exists. Choose a new directory; this installer never overwrites an environment.")
        linux_x86 = sys.platform == "linux" and platform.machine().lower() in ("x86_64", "amd64")
        mode = args.dependency_mode or ("linux-hashed" if linux_x86 else "portable-pinned")
        if mode == "linux-hashed" and not linux_x86:
            raise ValueError("linux-hashed is only for Linux x86_64. Use portable-pinned and verify the installation on this platform.")
        assets = Path(__file__).resolve().parent.parent / "assets"
        lock_name = "requirements-py312-linux-x86_64.lock" if mode == "linux-hashed" else "requirements-py312.txt"
        lock = assets / lock_name
        if not lock.is_file():
            raise ValueError(f"Missing bundled dependency file: {lock_name}")
        runtime = Path(__file__).resolve().with_name("stca_runtime.py")
        if not runtime.is_file():
            raise ValueError("Place this script next to stca_runtime.py inside the complete STCA skill.")
        source = verify_source(args.source) if args.source else None
        run(["git", "--version"], timeout=15)
        # mkdir(exist_ok=False) makes ownership of the new directory explicit.
        destination.mkdir(parents=True, exist_ok=False)
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(destination)
        python = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        install = [str(python), "-m", "pip", "install", "--disable-pip-version-check",
                   "--no-input", "--retries", "0", "--timeout", "15",
                   "--index-url", "https://pypi.org/simple", "--only-binary=:all:",
                   "--report", str(destination / "stca-pip-install.json")]
        if mode == "linux-hashed":
            install.append("--require-hashes")
        install.extend(["-r", str(lock)])
        run(install)
        run([str(python), "-m", "pip", "check"], timeout=30)
        if source is None:
            source = destination / "stca-source"
            run(["git", "clone", "--no-checkout", UPSTREAM_URL, str(source)], timeout=120)
            run(["git", "-C", str(source), "checkout", "--detach", UPSTREAM_COMMIT], timeout=30)
        source = verify_source(source)
        result = subprocess.run([str(python), str(runtime), "--source", str(source), "doctor"],
                                capture_output=True, text=True, check=True, timeout=60)
        receipt = json.loads(result.stdout)
        receipt.update({
            "environment_kind": "fresh-isolated-release-environment",
            "system_site_packages": False,
            "dependency_mode": mode,
            "dependency_file": lock_name,
            "dependency_file_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
            "runtime_platform": platform.platform(),
            "release_validation_scope": "Linux x86_64 / CPython 3.12; macOS and Windows require their own installation check.",
            "next_step": "Use this python and set STCA_SOURCE to source (or pass --source). Run the requested STCA task with this recorded environment. Do not run bootstrap afterward.",
        })
        (destination / "stca-environment.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"stca-setup: {error}", file=sys.stderr)
        print("No dependency versions were substituted. An incomplete newly created environment, if any, has been retained for inspection; choose another new path after correcting the cause.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
