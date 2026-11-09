#!/usr/bin/env python3
"""Build STCA platform ZIPs and publishable direct downloads (Python 3.9+).

Root publication files and plugin.json own the core release. Each platform
metadata file owns its package version so a platform patch is not reset.
After a successful build, duplicated metadata is synchronized into the skill
source. Computational scripts are never changed.
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
import tarfile
import tempfile
import zipfile

ROOT_FILES = (
    "README.md", "README.zh-CN.md", "README.DSH.md", "README.DSH.zh-CN.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "CITATION.cff", "CHANGELOG.md", "plugin.json", "package.json", ".gitignore", ".npmignore",
)
ROOT_DIRS = ("skills", "assets", "examples", "tools", "validation", "docs", "dsh")
PUBLICATION_FILES = (
    "LICENSE", "CITATION.cff", "THIRD_PARTY_NOTICES.md",
)
PLATFORMS = ("deepseek-harness", "workbuddy")
WORKBUDDY_MAX_EXPANDED_BYTES = 3 * 1024 * 1024
NOTICE_LAYOUT_HEADING = "\n## Included source files\n"
EXCLUDED_DIRS = {
    "__MACOSX", "__pycache__", "venv", "env", "node_modules", "site-packages",
    "cache", "caches", "dist", "build", "output", "outputs", "results",
    "runs", "runtime", "tmp", "temp",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".log", ".tmp", ".bak", ".swp"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def publication_notice(data: bytes, source_directory: str) -> bytes:
    """Make each standalone notice describe its real installation layout."""
    text = data.decode("utf-8").split(NOTICE_LAYOUT_HEADING, 1)[0].rstrip()
    location = source_directory.rstrip("/")
    return (text + "\n" + NOTICE_LAYOUT_HEADING +
            f"\nThe author implementation is included in `{location}`. Original license "
            f"and attribution files: `{location}/LICENSE` and `{location}/NOTICE`. "
            f"The unchanged original file-integrity manifest is `{location}/source_manifest.json`.\n").encode("utf-8")


def public_openai_metadata(data: bytes) -> bytes:
    """Map personal-skill targeting to the public submission product enum."""
    text = data.decode("utf-8")
    pattern = r"(?m)^policy:\n(?:[ \t]+[^\n]*(?:\n|$))+"
    match = re.search(pattern, text)
    if not match:
        raise ValueError("Missing OpenAI skill policy metadata.")
    body = match.group(0)
    products = re.findall(r"(?m)^\s*-\s*([A-Za-z]+)\s*$", body)
    if not products or set(products) - {"chatgpt", "codex", "api", "atlas", "CHAT", "CODEX"}:
        raise ValueError("Review the OpenAI product targeting before public submission.")
    fields = set(re.findall(r"(?m)^  ([a-z_]+):", body))
    if fields - {"products", "allow_implicit_invocation"}:
        raise ValueError("Unsupported public OpenAI skill policy field.")
    implicit = re.search(r"allow_implicit_invocation:\s*(true|false)", body)
    value = implicit.group(1) if implicit else "true"
    policy = "policy:\n  products:\n  - CHAT\n  - CODEX\n  allow_implicit_invocation: " + value + "\n"
    return (text[:match.start()] + policy + text[match.end():]).encode("utf-8")


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
        "package.json", "dsh/index.js", "dsh/cordis.patch.yml", "dsh/locale/en.json", "dsh/locale/zh-cn.json",
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


def validate_workbuddy_archive(path: Path) -> int:
    """Check the artifact against the upload service's actual size/layout limits."""
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len({entry.filename for entry in entries}) != len(entries):
            raise ValueError("WorkBuddy upload contains duplicate paths.")
        for entry in entries:
            relative = Path(entry.filename)
            if (relative.is_absolute() or ".." in relative.parts or len(relative.parts) > 2
                    or entry.is_dir() or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError("WorkBuddy upload must use root/direct-child ordinary files only.")
        expanded = sum(entry.file_size for entry in entries)
    if expanded > WORKBUDDY_MAX_EXPANDED_BYTES:
        raise ValueError(f"WorkBuddy upload expands to {expanded} bytes; the limit is "
                         f"{WORKBUDDY_MAX_EXPANDED_BYTES} bytes.")
    return expanded


def dsh_directory_payload(tarball: Path) -> dict[str, bytes]:
    """Make the GUI local-directory installer from the exact npm payload."""
    payload = {}
    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            relative = Path(member.name)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "package":
                raise ValueError("Unsafe path in DSH npm package.")
            if member.isdir():
                continue
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError("DSH package must contain ordinary files only.")
            name = Path(*relative.parts[1:]).as_posix()
            if name in payload:
                raise ValueError("Duplicate resource in DSH npm package.")
            payload[name] = archive.extractfile(member).read()
    if "package.json" not in payload or "dsh/index.js" not in payload:
        raise ValueError("DSH GUI directory requires its package manifest and plugin entry.")
    return payload


def native_skill_payload(files: dict[str, bytes]) -> dict[str, bytes]:
    """Export a complete standalone skill, without repository wrappers."""
    prefix = "skills/stca/"
    native = {
        relative[len(prefix):]: data
        for relative, data in files.items()
        if relative.startswith(prefix) and relative != prefix + "assets/icon.svg"
    }
    for name in PUBLICATION_FILES:
        native[name] = files[name]
    native["THIRD_PARTY_NOTICES.md"] = publication_notice(
        files["skills/stca/assets/publication/THIRD_PARTY_NOTICES.md"], "assets/author_source")
    metadata = "agents/openai.yaml"
    if metadata in native:
        native[metadata] = native[metadata].replace(b"assets/icon.svg", b"assets/stca-logo.png")
    required = {
        "SKILL.md", "agents/openai.yaml", "assets/stca-logo.png",
        "assets/rule_library/catalog.json", "assets/runtime_compatibility.json",
        "assets/starter_tasks.json", "scripts/task_menu.py",
        "assets/examples/adept_gap_case.json", "assets/examples/adept_gap_generation_examples.csv",
        "scripts/agent_runtime.py", "scripts/runtime_compat.py", "scripts/generation_session.py",
        "validation/historical_validation_20261107.json",
    }
    missing = sorted(required.difference(native))
    if missing:
        raise ValueError("Missing standalone skill files: " + ", ".join(missing))
    return native


def snapshot_downloads(root: Path, names: list[str]) -> dict[str, bytes | None]:
    """Never follow an existing download symlink or overwrite a concurrent edit."""
    directory = root / "downloads"
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise ValueError("downloads must be an ordinary directory, not a symlink.")
    existing = {}
    for name in names:
        path = directory / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"Download target is not an ordinary file: {name}")
        existing[name] = path.read_bytes() if path.exists() else None
    return existing


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
    for directory in (*ROOT_DIRS, "downloads"):
        if out == (root / directory).resolve() or (root / directory).resolve() in out.parents:
            raise ValueError("Place release output outside the packaged source directories.")

    original = collect_source(root)
    files = dict(original)
    manifest = json.loads(files["plugin.json"])
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("plugin.json version must be a release version such as 0.1.0.")
    synchronized = {}
    agent_metadata = "skills/stca/agents/openai.yaml"
    synchronized[agent_metadata] = public_openai_metadata(files[agent_metadata])
    for name in PUBLICATION_FILES:
        value = files[name]
        if name == "THIRD_PARTY_NOTICES.md":
            # The reusable template is path-neutral; platform exports append
            # their actual physical source paths, never repository-only paths.
            value = (value.decode("utf-8").split(NOTICE_LAYOUT_HEADING, 1)[0].rstrip() + "\n").encode("utf-8")
        synchronized[f"skills/stca/assets/publication/{name}"] = value
    platform_versions = {}
    for platform in PLATFORMS:
        relative = f"skills/stca/assets/platforms/{platform}.json"
        metadata = json.loads(files[relative])
        if metadata.get("platform") != platform or not isinstance(metadata.get("frontmatter"), dict):
            raise ValueError(f"Invalid platform metadata: {relative}")
        platform_version = metadata.get("package_version", version)
        if not isinstance(platform_version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", platform_version):
            raise ValueError(f"Invalid {platform} package version: {platform_version!r}")
        platform_versions[platform] = platform_version
        metadata["package_version"] = platform_version
        if "version" in metadata["frontmatter"]:
            metadata["frontmatter"]["version"] = platform_version
        synchronized[relative] = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    files.update(synchronized)
    installer_names = [
        f"stca-openai-skill-{version}.zip",
        f"stca-chatgpt-{version}.zip", f"stca-codex-{version}.zip",
        *(f"stca-{platform}-{platform_versions[platform]}.zip" for platform in PLATFORMS),
        f"stca-openai-plugin-{version}.zip",
        f"dsh-plugin-stca-{version}.tgz",
        f"dsh-plugin-stca-{version}.zip",
    ]
    downloads_before = snapshot_downloads(root, [*installer_names, "manifest.json"])

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
        # Installers are built only from source, never from previously generated
        # downloads. The repository archive is built last and contains these
        # exact installer bytes, without embedding its own ZIP.
        write_archive(prepared / f"stca-openai-plugin-{version}.zip", files, "")
        native = native_skill_payload(files)
        for platform in ("openai-skill", "chatgpt", "codex"):
            write_archive(prepared / f"stca-{platform}-{version}.zip", native, "stca/")
        for platform in PLATFORMS:
            name = f"stca-{platform}-{platform_versions[platform]}.zip"
            if platform == "workbuddy":
                workbuddy_expanded = validate_workbuddy_archive(platform_output / name)
            shutil.copyfile(platform_output / name, prepared / name)
        # DSH's Add plugin accepts an npm-compatible tarball, not a skill ZIP.
        # The same manifest/entry also makes the repository root Git-installable.
        dsh_manifest = json.loads(files["package.json"])
        if dsh_manifest.get("name") != "dsh-plugin-stca" or dsh_manifest.get("version") != version:
            raise ValueError("DSH package identity/version must match the release.")
        # npm users see DSH-specific product instructions; GitHub keeps the
        # multi-platform README and both dedicated DSH README sources.
        for npm_readme, dsh_readme in (("README.md", "README.DSH.md"),
                                       ("README.zh-CN.md", "README.DSH.zh-CN.md")):
            if dsh_readme not in files:
                raise ValueError(f"Missing DSH package documentation: {dsh_readme}")
            (stage / npm_readme).write_bytes(files[dsh_readme])
        packed = subprocess.run(
            ["npm", "pack", "--ignore-scripts", "--json", "--pack-destination", str(prepared)],
            cwd=stage, capture_output=True, text=True, timeout=120,
        )
        if packed.returncode:
            raise ValueError("DSH plugin packing failed:\n" + (packed.stderr or packed.stdout))
        packed_info = json.loads(packed.stdout)
        if len(packed_info) != 1 or packed_info[0].get("filename") != f"dsh-plugin-stca-{version}.tgz":
            raise ValueError("npm pack did not produce the expected DSH plugin tarball.")
        write_archive(prepared / f"dsh-plugin-stca-{version}.zip",
                      dsh_directory_payload(prepared / f"dsh-plugin-stca-{version}.tgz"),
                      f"dsh-plugin-stca-{version}/")
        downloads = {name: (prepared / name).read_bytes() for name in installer_names}
        download_manifest = {
            "schema": "stca-direct-downloads-v1", "version": version,
            "platform_versions": platform_versions,
            "shared_openai_skill": f"stca-openai-skill-{version}.zip",
            "compatibility_aliases": [f"stca-chatgpt-{version}.zip", f"stca-codex-{version}.zip"],
            "workbuddy_upload": {
                "archive": f"stca-workbuddy-{platform_versions['workbuddy']}.zip",
                "expanded_size_bytes": workbuddy_expanded,
                "maximum_expanded_size_bytes": WORKBUDDY_MAX_EXPANDED_BYTES,
                "maximum_archive_path_components": 2,
            },
            "files": [
                {"file": name, "size_bytes": len(data), "sha256": sha256(data)}
                for name, data in sorted(downloads.items())
            ],
        }
        downloads["manifest.json"] = (json.dumps(download_manifest, indent=2) + "\n").encode("utf-8")
        repository_files = dict(files)
        repository_files.update({"downloads/" + name: data for name, data in downloads.items()})
        write_archive(prepared / f"stca-github-release-{version}.zip", repository_files, "stca-agent-skill/")
        (prepared / "STCA_logo.png").write_bytes(files["assets/stca-logo.png"])
        artifacts = sorted(prepared.iterdir())
        checksums = "".join(sha256(path.read_bytes()) + "  " + path.name + "\n" for path in artifacts)
        (prepared / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")

        # Do not overwrite metadata edited while the build was running.
        for relative in {"plugin.json", *PUBLICATION_FILES, *synchronized}:
            path = root / relative
            if path.is_symlink() or (path.read_bytes() if path.exists() else None) != original.get(relative):
                raise ValueError(f"Source changed during build; retry before publishing: {relative}")
        if snapshot_downloads(root, [*installer_names, "manifest.json"]) != downloads_before:
            raise ValueError("Download files changed during build; retry before publishing.")
        out.mkdir(parents=True, exist_ok=False)
        for path in sorted(prepared.iterdir()):
            shutil.copyfile(path, out / path.name)
        for relative, data in synchronized.items():
            if original.get(relative) != data:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        download_directory = root / "downloads"
        download_directory.mkdir(parents=True, exist_ok=True)
        for name, data in downloads.items():
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(dir=download_directory, prefix="." + name + "-", delete=False) as handle:
                    temporary_path = Path(handle.name)
                    handle.write(data)
                temporary_path.chmod(0o644)
                temporary_path.replace(download_directory / name)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

    result = [
        {"file": str(out / path.name), "size_bytes": (out / path.name).stat().st_size,
         "sha256": sha256((out / path.name).read_bytes())}
        for path in artifacts
    ]
    print(json.dumps({"version": version, "artifacts": result,
                      "checksums": str(out / "SHA256SUMS.txt"),
                      "direct_downloads": [str(root / "downloads" / name) for name in sorted(downloads)],
                      "synchronized_source_files": sorted(synchronized)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
