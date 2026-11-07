#!/usr/bin/env python3
"""Build the GitHub-source and OpenAI-plugin archives from this release tree."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import zipfile

ROOT_FILES = (
    "README.md", "LICENSE", "PUBLISHER_LICENSE_NOTES.md", "THIRD_PARTY_NOTICES.md",
    "CITATION.cff", "CHANGELOG.md", "PUBLISH_STEPS.zh-CN.md", "plugin.json",
    "LISTING_TEXT.txt", "ZENODO_METADATA.txt", "BRAND.md", ".gitignore",
)
ROOT_DIRS = ("skills", "assets", "examples", "tools", "validation", "docs")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="dist", help="New output directory; must not exist.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    if not isinstance(version, str) or not version or any(c not in "0123456789.-abcdefghijklmnopqrstuvwxyz" for c in version):
        raise ValueError("Use a safe explicit release version.")
    out = Path(args.output_dir).expanduser().resolve()
    if out.exists():
        raise ValueError("Output directory exists. Choose a new directory.")
    files = []
    for name in ROOT_FILES:
        path = root / name
        if path.is_file():
            files.append(path)
    for directory in ROOT_DIRS:
        for path in (root / directory).rglob("*"):
            if path.is_symlink():
                raise ValueError("Release source contains a symlink.")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc" and path.name != ".DS_Store":
                files.append(path)
    required = [root / "plugin.json", root / "skills/stca/SKILL.md", root / "assets/stca-logo.png"]
    if any(p not in files for p in required):
        raise ValueError("Missing plugin manifest, STCA skill or logo.")
    files = sorted(set(files), key=lambda p: p.relative_to(root).as_posix())
    out.mkdir(parents=True, exist_ok=False)
    result = []
    for name, prefix in (
        (f"stca-github-release-{version}.zip", "stca-agent-skill/"),
        (f"stca-openai-plugin-{version}.zip", ""),
    ):
        archive = out / name
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path in files:
                info = zipfile.ZipInfo(prefix + path.relative_to(root).as_posix(), date_time=(2026, 11, 7, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100644 << 16)
                z.writestr(info, path.read_bytes())
        result.append({"file": str(archive), "file_count": len(files), "size_bytes": archive.stat().st_size})
    print(json.dumps({"archives": result}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

