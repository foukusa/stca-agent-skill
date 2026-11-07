#!/usr/bin/env python3
"""Run the author's pinned STCA implementation without copying its algorithm."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

from stca_io import CSV_POLICY, read_csv_frame, read_csv_records

UPSTREAM_URL = "https://github.com/foukusa/polymer-stca.git"
UPSTREAM_COMMIT = "5951b0ef23d63edc8f7e803aaaffa5e4168288f6"
RDKIT_VERSION = "2025.9.4"


def cache_root() -> Path:
    configured = os.environ.get("STCA_CACHE_DIR")
    if configured:
        return Path(configured).expanduser().resolve() / UPSTREAM_COMMIT
    base = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return base / "stca-skill" / UPSTREAM_COMMIT


def source_root(source_path=None) -> Path:
    value = source_path or os.environ.get("STCA_SOURCE")
    return Path(value).expanduser().resolve() if value else cache_root() / "source"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(f"Cannot inspect STCA source: {result.stderr.strip()}")
    return result.stdout.strip()


def verify_source(source_path=None) -> Path:
    root = source_root(source_path)
    if not root.is_dir():
        raise RuntimeError("STCA source is not available. Run stca_runtime.py bootstrap --chem first.")
    if not shutil.which("git"):
        raise RuntimeError("Git is required to verify the pinned STCA source.")
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise RuntimeError("--source must name the STCA checkout root.")
    if _git(root, "rev-parse", "HEAD") != UPSTREAM_COMMIT:
        raise RuntimeError(f"Source revision does not match the skill's pinned revision {UPSTREAM_COMMIT}.")
    # Include untracked importable code: an extra module could shadow the reviewed implementation.
    changed = _git(root, "status", "--porcelain", "--untracked-files=all", "--", "src", "pyproject.toml", "LICENSE", "NOTICE")
    if changed:
        raise RuntimeError("STCA source or licensing files have local changes. Use a clean pinned checkout.")
    if not (root / "src" / "stca" / "__init__.py").is_file():
        raise RuntimeError("The pinned checkout has no STCA package.")
    return root


def load_stca(source_path=None):
    """Load only the verified source tree; do not fall back to an unrelated installation."""
    root = verify_source(source_path)
    existing = sys.modules.get("stca")
    expected = root / "src" / "stca" / "__init__.py"
    if existing is not None and Path(existing.__file__).resolve() != expected.resolve():
        raise RuntimeError("Another STCA installation is already imported in this process.")
    sys.path.insert(0, str(root / "src"))
    module = importlib.import_module("stca")
    if Path(module.__file__).resolve() != expected.resolve():
        raise RuntimeError("Imported STCA does not match the verified source.")
    return module


def environment_receipt(source_path=None) -> dict:
    root = verify_source(source_path)
    versions = {}
    for name in ("numpy", "pandas", "scipy", "rdkit"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "repository": UPSTREAM_URL,
        "commit": UPSTREAM_COMMIT,
        "source": str(root),
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "packages": versions,
        "fingerprint_version_note": "Version recorded; historical per-record MACCS parity is not implied.",
        "csv_input_policy": CSV_POLICY,
        "adapter_files_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(Path(__file__).resolve().parent.glob("*.py"))
        },
    }


def bootstrap(args) -> int:
    root = source_root(args.source)
    if not root.exists():
        if args.source:
            raise RuntimeError("The explicitly supplied source directory does not exist.")
        root.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", UPSTREAM_URL, str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "checkout", "--detach", UPSTREAM_COMMIT], check=True)
    verify_source(root)
    env_root = cache_root() / f"python-{sys.version_info.major}.{sys.version_info.minor}"
    python = env_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(env_root)
    check = subprocess.run(
        [str(python), "-c", "import numpy,pandas,scipy"], capture_output=True
    )
    if check.returncode:
        subprocess.run([str(python), "-m", "pip", "install", "numpy>=1.24", "pandas>=2.0", "scipy>=1.10"], check=True)
    if args.chem:
        check = subprocess.run(
            [str(python), "-c", "import rdkit; assert rdkit.__version__ == '2025.09.4'"],
            capture_output=True,
        )
        if check.returncode:
            subprocess.run([str(python), "-m", "pip", "install", f"rdkit=={RDKIT_VERSION}"], check=True)
    # Run the receipt using the interpreter that subsequent skill commands must use.
    subprocess.run([str(python), str(Path(__file__).resolve()), "--source", str(root), "doctor"], check=True)
    return 0


def _has_option(argv, name):
    return any(arg == name or arg.startswith(name + "=") for arg in argv)


def run_upstream(args) -> int:
    argv = args.upstream_args
    if argv[:1] == ["--"]:
        argv = argv[1:]
    if not argv:
        raise RuntimeError("Supply an STCA command after run --.")
    command = argv[0]
    help_requested = any(x in argv for x in ("-h", "--help", "--version"))
    if not help_requested:
        protocol_required = (command in ("profiles", "train-profile") or
                             (command in ("inspect", "screen", "evaluate") and _has_option(argv, "--profile")))
        if protocol_required and not _has_option(argv, "--protocol"):
            raise RuntimeError("Choose --protocol explicitly: paper for archival rules, source_locked for source-only selection.")
        if command in ("screen", "evaluate") and not _has_option(argv, "--tier"):
            raise RuntimeError("Supply --tier explicitly; a tier is a target fraction, not the fraction selected by a rule.")
        if command in ("train", "train-profile"):
            def value_for(flag):
                for i, item in enumerate(argv):
                    if item == flag and i + 1 < len(argv):
                        return argv[i + 1]
                    if item.startswith(flag + "="):
                        return item.split("=", 1)[1]
                return None
            features = value_for("--features")
            if features:
                forbidden = {value_for("--target"), value_for("--group-column"), value_for("--split-column")}
                if set(x.strip() for x in features.split(",")) & (forbidden - {None}):
                    raise RuntimeError("Feature columns must not include the target, group ID, or split label.")
    load_stca(args.source)
    from stca import cli as upstream_cli
    # The pinned CLI's default CSV reader can coerce leading-zero IDs and infer
    # an index from malformed row widths. Replace only that I/O boundary for
    # this invocation; preserve the author's algorithm and restore the module.
    original_csv_reader = upstream_cli._csv
    upstream_cli._csv = read_csv_frame
    try:
        if command == "import-family" and not help_requested:
            # This auxiliary command has its own specialized numeric reader.
            # Validate its record widths without changing its numeric schema.
            for i, item in enumerate(argv):
                if item == "--input" and i + 1 < len(argv):
                    read_csv_records(argv[i + 1])
                elif item.startswith("--input="):
                    read_csv_records(item.split("=", 1)[1])
        status = upstream_cli.main(argv)
    finally:
        upstream_cli._csv = original_csv_reader
    if status != 0 or help_requested:
        return status
    # Keep the upstream's outputs unchanged and write a small separate execution receipt.
    def output_for(flag):
        for i, item in enumerate(argv):
            if item == flag and i + 1 < len(argv):
                return Path(argv[i + 1])
            if item.startswith(flag + "="):
                return Path(item.split("=", 1)[1])
        return None
    out_dir, out_file = output_for("--output-dir"), output_for("--output")
    if out_dir is not None:
        receipt = out_dir / "skill_run_manifest.json"
    elif out_file is not None and out_file.is_file():
        receipt = out_file.with_name(out_file.name + ".manifest.json")
    else:
        return status
    metadata = environment_receipt(args.source)
    metadata["arguments"] = argv
    metadata["input_files"] = []
    for flag in ("--input", "--selection-input", "--model"):
        path = output_for(flag)
        if path is not None and path.is_file():
            metadata["input_files"].append({"role":flag,"path":str(path.resolve()),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    receipt.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return status


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Clean checkout at the exact pinned revision; defaults to the skill cache.")
    subs = parser.add_subparsers(dest="command", required=True)
    boot = subs.add_parser("bootstrap", help="Fetch pinned author source and prepare a separate Python environment.")
    boot.add_argument("--chem", action="store_true", help="Install the recorded RDKit version for SMILES workflows.")
    subs.add_parser("doctor", help="Verify source identity and show actual runtime versions.")
    run = subs.add_parser("run", help="Call the original CLI, with explicit protocol/tier checks.")
    run.add_argument("upstream_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.command == "bootstrap":
            return bootstrap(args)
        if args.command == "doctor":
            load_stca(args.source)
            print(json.dumps(environment_receipt(args.source), ensure_ascii=False, indent=2))
            return 0
        return run_upstream(args)
    except (RuntimeError, ValueError, ImportError, OSError, subprocess.CalledProcessError) as exc:
        print(f"stca-skill: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
