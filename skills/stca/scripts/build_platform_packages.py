#!/usr/bin/env python3
"""Export the existing STCA skill for DeepSeek Harness and WorkBuddy.

This changes host metadata and adds host instructions only. It neither
changes the computational scripts nor installs or publishes the archives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


CORE_SCRIPTS = (
    "audit_dataset.py", "prepare_hcap.py", "setup_locked_environment.py",
    "stca_io.py", "stca_runtime.py", "stca_tools.py",
)
PUBLICATION_FILES = (
    "LICENSE", "THIRD_PARTY_NOTICES.md", "PUBLISHER_LICENSE_NOTES.md", "CITATION.cff",
)
PLATFORMS = ("deepseek-harness", "workbuddy")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_payload(skill: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for directory in ("scripts", "references", "assets"):
        for path in sorted((skill / directory).rglob("*")):
            relative = path.relative_to(skill)
            if path.is_symlink():
                raise ValueError(f"Skill resource is a symlink: {relative}")
            if not path.is_file() or "__pycache__" in relative.parts or path.suffix == ".pyc":
                continue
            if relative.parts[:2] in (("assets", "platforms"), ("assets", "publication")):
                continue
            if relative.as_posix() in ("scripts/build_platform_packages.py", "assets/icon.svg"):
                continue
            files[relative.as_posix()] = path.read_bytes()
    for name in PUBLICATION_FILES:
        files[name] = (skill / "assets" / "publication" / name).read_bytes()
    required = ["scripts/" + n for n in CORE_SCRIPTS] + [
        "assets/stca-logo.png", "assets/objectives_example.json",
        "references/platform-runtime.md", "references/deepseek-harness.md",
        "references/workbuddy.md",
    ]
    for name in required:
        if name not in files:
            raise ValueError(f"Missing portable resource: {name}")
    return files


def frontmatter(meta: dict) -> str:
    required = ("name", "description")
    if meta["platform"] == "workbuddy":
        required += ("display_name", "display_name_en", "description_zh", "description_en", "version", "author")
    fields = meta["frontmatter"]
    for name in required:
        if not isinstance(fields.get(name), str) or not fields[name].strip():
            raise ValueError(f"Missing {meta['platform']} metadata: {name}")
    if fields["name"] != "stca":
        raise ValueError("Keep the STCA skill identity.")
    if len(fields["description"]) > 500:
        raise ValueError("Keep the routing description within the default Harness catalog limit.")
    return "---\n" + "".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}\n" for key, value in fields.items()
    ) + "---\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="New output directory; existing directories are not overwritten.")
    parser.add_argument("--platform", choices=("all", *PLATFORMS), default="all")
    args = parser.parse_args()
    skill = Path(__file__).resolve().parents[1]
    match = re.fullmatch(r"---\r?\n.*?\r?\n---\r?\n(.*)",
                         (skill / "SKILL.md").read_text(encoding="utf-8"), re.DOTALL)
    if not match:
        raise ValueError("The source SKILL.md must have YAML frontmatter.")
    body = match.group(1)
    base = source_payload(skill)
    out = args.output_dir.expanduser().resolve()
    if out.exists():
        raise ValueError("Output directory exists. Choose a new directory.")
    selected = PLATFORMS if args.platform == "all" else (args.platform,)
    prepared = []
    for platform_name in selected:
        meta = json.loads((skill / "assets" / "platforms" / f"{platform_name}.json").read_text(encoding="utf-8"))
        version = meta["package_version"]
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError("Use an explicit semantic release version.")
        files = dict(base)
        files["SKILL.md"] = (frontmatter(meta) + "\n> " + meta["entry_note"] + "\n\n" + body).encode("utf-8")
        manifest = {
            "skill": "stca", "platform": platform_name, "package_version": version,
            "upstream_commit": "5951b0ef23d63edc8f7e803aaaffa5e4168288f6",
            "official_documentation_checked": "2026-11-07",
            "official_docs": meta["official_docs"],
            "core_scripts_sha256": {n: sha256(files["scripts/" + n]) for n in CORE_SCRIPTS},
            "common_instruction_body_sha256": sha256(body.encode("utf-8")),
            "platform_end_to_end_tested": False,
            "public_market_submission_performed": False,
            "publisher_license_confirmation_required": True,
        }
        files["assets/platform-release.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        checksums = "".join(sha256(data) + "  " + name + "\n" for name, data in sorted(files.items()))
        files["SHA256SUMS.txt"] = checksums.encode("utf-8")
        prepared.append((f"stca-{platform_name}-{version}.zip", files))
    out.mkdir(parents=True, exist_ok=False)
    archives = []
    for name, files in prepared:
        archive = out / name
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for relative, data in sorted(files.items()):
                info = zipfile.ZipInfo("stca/" + relative, date_time=(2026, 11, 7, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, data)
        archives.append({"file": str(archive), "files": len(files), "bytes": archive.stat().st_size,
                         "sha256": sha256(archive.read_bytes())})
    print(json.dumps({"archives": archives}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
