#!/usr/bin/env python3
"""Build four STCA release ZIPs, a standalone logo and SHA256SUMS (Python 3.9+).

Root publication files and plugin.json are authoritative. After a successful
build, their duplicated publication/version metadata is synchronized into
the exported skill source. Computational scripts are never changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT_FILES = (
    "README.md", "README.zh-CN.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "CITATION.cff", "CHANGELOG.md", "plugin.json", ".gitignore",
)
ROOT_DIRS = ("skills", "assets", "examples", "tools", "validation", "docs")
PUBLICATION_FILES = (
    "LICENSE", "CITATION.cff", "THIRD_PARTY_NOTICES.md",
)
PLATFORMS = ("deepseek-harness", "workbuddy")
EXCLUDED_DIRS = {
    "__MACOSX", "__pycache__", "venv", "env", "node_modules", "site-packages",
    "cache", "caches", "dist", "build", "output", "outputs", "results",
    "runs", "runtime", "tmp", "temp",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".log", ".tmp", ".bak", ".swp"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_source(root: Path) -> dict[str, bytes]:
    """Use explicit release roots; never follow symlinks or package local state."""
    files = {}

    def add(path: Path) -> None:
        if path.is_symlink():
            raise ValueError(f"Release source contains a symlink: {path}")
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"Release source is not a regular file: {path}")
        files[path.relative_to(root).as_posix()] = path.read_bytes()

    for name in ROOT_FILES:
        path = root / name
        if path.is_symlink() or path.exists():
            add(path)
    for name in ROOT_DIRS:
        directory = root / name
        if directory.is_symlink():
            raise ValueError(f"Release directory is a symlink: {directory}")
        if not directory.exists():
            continue
        if not directory.is_dir():
            raise ValueError(f"Release directory is not a directory: {directory}")
        for parent, directories, filenames in os.walk(directory, followlinks=False):
            current = Path(parent)
            for child in directories + filenames:
                if (current / child).is_symlink():
                    raise ValueError(f"Release source contains a symlink: {current / child}")
            directories[:] = sorted(
                child for child in directories
                if not child.startswith(".") and child not in EXCLUDED_DIRS
            )
            for child in sorted(filenames):
                path = current / child
                if child.startswith(".") or child.startswith("~$"):
                    continue
                if path.suffix.lower() in EXCLUDED_SUFFIXES or child.endswith("~"):
                    continue
                if child in {"SHA256SUMS.txt", "Thumbs.db", "desktop.ini"}:
                    continue
                add(path)
    required = {
        "plugin.json", "skills/stca/SKILL.md", "assets/stca-logo.png",
        "skills/stca/scripts/build_platform_packages.py", *PUBLICATION_FILES,
        *(f"skills/stca/assets/platforms/{platform}.json" for platform in PLATFORMS),
    }
    missing = sorted(required.difference(files))
    if missing:
        raise ValueError("Missing required release files: " + ", ".join(missing))
    return files


def write_archive(path: Path, files: dict[str, bytes], prefix: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, data in sorted(files.items()):
            info = zipfile.ZipInfo(prefix + relative, date_time=(2026, 11, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="dist", help="New output directory; must not exist.")
    args = parser.parse_args()
    if sys.version_info < (3, 9):
        parser.error("Python 3.9 or newer is required; no third-party packages are needed.")
    root = Path(__file__).absolute().parents[1]
    if root.is_symlink():
        raise ValueError("The release source directory must not be a symlink.")
    destination = Path(args.output_dir).expanduser().absolute()
    if destination.is_symlink() or destination.exists():
        raise ValueError("Output directory exists or is a symlink. Choose a new directory.")
    out = destination.resolve()
    for directory in ROOT_DIRS:
        if out == (root / directory).resolve() or (root / directory).resolve() in out.parents:
            raise ValueError("Place release output outside the packaged source directories.")

    original = collect_source(root)
    files = dict(original)
    manifest = json.loads(files["plugin.json"])
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("plugin.json version must be a release version such as 0.1.0.")
    synchronized = {}
    for name in PUBLICATION_FILES:
        synchronized[f"skills/stca/assets/publication/{name}"] = files[name]
    for platform in PLATFORMS:
        relative = f"skills/stca/assets/platforms/{platform}.json"
        metadata = json.loads(files[relative])
        if metadata.get("platform") != platform or not isinstance(metadata.get("frontmatter"), dict):
            raise ValueError(f"Invalid platform metadata: {relative}")
        metadata["package_version"] = version
        if "version" in metadata["frontmatter"]:
            metadata["frontmatter"]["version"] = version
        synchronized[relative] = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    files.update(synchronized)

    # Validate and build platform exports before changing source duplicates
    # or creating the requested output directory.
    with tempfile.TemporaryDirectory(prefix="stca-release-") as temporary:
        temporary_root = Path(temporary)
        stage = temporary_root / "source"
        for relative, data in files.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        platform_output = temporary_root / "platform-output"
        completed = subprocess.run(
            [sys.executable, "-B", str(stage / "skills/stca/scripts/build_platform_packages.py"),
             "--output-dir", str(platform_output), "--platform", "all"],
            capture_output=True, text=True,
        )
        if completed.returncode:
            raise ValueError("Platform export validation failed:\n" + (completed.stderr or completed.stdout))
        prepared = temporary_root / "release"
        prepared.mkdir()
        write_archive(prepared / f"stca-github-release-{version}.zip", files, "stca-agent-skill/")
        write_archive(prepared / f"stca-openai-plugin-{version}.zip", files, "")
        for platform in PLATFORMS:
            name = f"stca-{platform}-{version}.zip"
            shutil.copyfile(platform_output / name, prepared / name)
        (prepared / "STCA_logo.png").write_bytes(files["assets/stca-logo.png"])
        artifacts = sorted(prepared.iterdir())
        checksums = "".join(sha256(path.read_bytes()) + "  " + path.name + "\n" for path in artifacts)
        (prepared / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")

        # Do not overwrite metadata edited while the build was running.
        for relative in {"plugin.json", *PUBLICATION_FILES, *synchronized}:
            path = root / relative
            if path.is_symlink() or (path.read_bytes() if path.exists() else None) != original.get(relative):
                raise ValueError(f"Source changed during build; retry before publishing: {relative}")
        out.mkdir(parents=True, exist_ok=False)
        for path in sorted(prepared.iterdir()):
            shutil.copyfile(path, out / path.name)
        for relative, data in synchronized.items():
            if original.get(relative) != data:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)

    result = [
        {"file": str(out / path.name), "size_bytes": (out / path.name).stat().st_size,
         "sha256": sha256((out / path.name).read_bytes())}
        for path in artifacts
    ]
    print(json.dumps({"version": version, "artifacts": result,
                      "checksums": str(out / "SHA256SUMS.txt"),
                      "synchronized_source_files": sorted(synchronized)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
