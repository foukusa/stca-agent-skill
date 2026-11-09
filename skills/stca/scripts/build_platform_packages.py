#!/usr/bin/env python3
"""Export the existing STCA skill for DeepSeek Harness and WorkBuddy.

This changes host metadata and adds host instructions only. It neither
changes the computational scripts nor installs or publishes the archives.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path
import re
import zipfile


CORE_SCRIPTS = (
    "audit_dataset.py", "prepare_hcap.py", "setup_locked_environment.py",
    "stca_io.py", "stca_runtime.py", "stca_tools.py",
    "data_readiness.py", "custom_fit.py", "evaluate_custom.py",
    "data_cleaning.py", "auto_screen.py", "learning_results.py",
    "auto_data_layer.py", "inrange_evaluation.py", "morgan_evaluation.py", "morgan_split.py", "wracc_search.py", "source_integrity.py", "fingerprint_contract.py", "frozen_literal_model.py",
    "agent_runtime.py", "runtime_discovery.py", "rule_library.py", "generation_prompt.py", "generation_session.py", "runtime_compat.py", "task_menu.py", "user_rule_library.py",
)
PUBLICATION_FILES = (
    "LICENSE", "THIRD_PARTY_NOTICES.md", "CITATION.cff",
)
PLATFORMS = ("deepseek-harness", "workbuddy")
WORKBUDDY_MAX_EXPANDED_BYTES = 3 * 1024 * 1024
NOTICE_LAYOUT_HEADING = "\n## Included source files\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def publication_notice(data: bytes, source_directory: str, *, flattened: bool = False) -> bytes:
    """Describe the physical source layout of this particular distribution."""
    text = data.decode("utf-8").split(NOTICE_LAYOUT_HEADING, 1)[0].rstrip()
    location = source_directory.rstrip("/")
    description = (
        f"\nThe author implementation is included in `{location}`. Original license "
        f"and attribution files: `{location}/LICENSE` and `{location}/NOTICE`. "
        f"The unchanged original file-integrity manifest is `{location}/source_manifest.json`.\n"
    )
    if flattened:
        description += (
            f"`{location}/layout.json` maps every original source path to its visible "
            "flat filename, storage encoding and SHA-256. Python source, LICENSE, "
            "NOTICE and the original integrity manifest are ordinary readable files; "
            "model JSON resources use lossless `.xz` compression. All original file "
            "bytes are retained and checked after decoding. The "
            "complete original hierarchy is also included in the verified runtime "
            "payload and restored before calculations.\n"
        )
    return (text + "\n" + NOTICE_LAYOUT_HEADING + description).encode("utf-8")


def source_payload(skill: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for directory in ("scripts", "references", "assets", "validation"):
        for path in sorted((skill / directory).rglob("*")):
            relative = path.relative_to(skill)
            if path.is_symlink():
                raise ValueError(f"Skill resource is a symlink: {relative}")
            if not path.is_file() or "__pycache__" in relative.parts or path.suffix == ".pyc":
                continue
            if relative.parts[:2] in (("assets", "platforms"), ("assets", "publication")):
                continue
            if relative.as_posix() in ("scripts/build_platform_packages.py", "scripts/workbuddy_runtime.py", "assets/icon.svg"):
                continue
            files[relative.as_posix()] = path.read_bytes()
    for name in PUBLICATION_FILES:
        files[name] = (skill / "assets" / "publication" / name).read_bytes()
    files["THIRD_PARTY_NOTICES.md"] = publication_notice(
        files["THIRD_PARTY_NOTICES.md"], "assets/author_source")
    required = ["scripts/" + n for n in CORE_SCRIPTS] + [
        "scripts/launch_runtime.sh", "scripts/launch_runtime.ps1",
        "assets/stca-logo.png", "assets/objectives_example.json",
        "assets/rule_library/catalog.json", "assets/rule_library/index.md",
        "assets/prompts/generate.en.md", "assets/prompts/generate.zh-CN.md",
        "assets/requirements-compatible.txt", "assets/runtime_compatibility.json",
        "assets/starter_tasks.json", "assets/property_registry.json",
        "assets/examples/candidates.csv",
        "assets/examples/quick_start_candidates.csv",
        "assets/examples/adept_gap_case.json",
        "assets/examples/adept_gap_generation_examples.csv",
        "assets/rule_library/original_trial_evidence.json",
        "validation/historical_validation_20261107.json",
        "references/platform-runtime.md", "references/deepseek-harness.md",
        "references/workbuddy.md",
        "references/usage_examples.md",
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
    lines = ["---\n"]
    for key, value in fields.items():
        if isinstance(value, list):
            if not value or not all(isinstance(item, str) and item.strip() for item in value):
                raise ValueError(f"Invalid {meta['platform']} metadata list: {key}")
            lines.append(f"{key}:\n")
            lines.extend(f"  - {json.dumps(item, ensure_ascii=False)}\n" for item in value)
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}\n")
    return "".join(lines) + "---\n"


def workbuddy_payload(files: dict[str, bytes], version: str) -> bytes:
    """Keep the complete runtime byte-for-byte behind one shallow resource."""
    inner = json.dumps({"files": {
        name: {"sha256": sha256(data), "data": base64.b64encode(data).decode("ascii")}
        for name, data in sorted(files.items())
    }}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return (json.dumps({
        "schema": "stca-workbuddy-runtime-v1", "version": version,
        "payload_encoding": "lzma+base85", "payload_sha256": sha256(inner),
        "file_count": len(files),
        "payload": base64.b85encode(lzma.compress(inner, preset=6)).decode("ascii"),
    }, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def workbuddy_entry(meta: dict) -> bytes:
    body = '''
# STCA skill

Use natural language to learn and save rules from uploaded polymer data, screen
with existing rules, or ask the current LLM to generate and verify polymer repeat units.
WorkBuddy package version **{{PACKAGE_VERSION}}**. Keep original polymer SMILES, repeat-unit attachment points, and all frozen rule conditions.

## Prepare once, then continue the user's task

1. Resolve `SKILL_DIR` as the directory containing this installed `SKILL.md`.
   On macOS or Linux, use the bundled launcher to find Python automatically:

   ```bash
   sh "$SKILL_DIR/scripts/launch_runtime.sh" --script "$SKILL_DIR/scripts/workbuddy_runtime.py" prepare
   ```

   On Windows, use `scripts/launch_runtime.ps1` with the same `--script`
   target and `prepare` argument. Both launchers are self-contained; the user
   does not enter a Python path. An explicit `--bootstrap-python` path is an optional
   override, and must not silently fall back to another interpreter.

2. Read the **entire** file at `skill_instructions` in the returned JSON.
   Follow that file immediately and continue the user's request in this turn.
   Preparation alone is not task completion. Do not ask the user to execute
   commands, supply paths, or repackage files.
3. Use the returned `runtime_skill_dir` as **SKILL_DIR for every subsequent
   script, asset and reference**. All complete rules, bilingual prompts,
   examples and workflows are available there. Keep the current working
   directory for the user's relative input/output paths.
4. Never read `assets/runtime_payload.json` into the conversation. The bundled
   preparation script verifies and restores it automatically, without network
   access, scientific dependencies, or writes to the installed skill directory.
   Dependency discovery and preparation are managed by
   `scripts/agent_runtime.py` when a calculation is requested. This actual
   entry point is also included in this upload package: it restores the
   verified resources and forwards every argument to the complete runtime.

If no execution tool or Python is available, explain the actual missing
capability; do not claim that preparation or screening has completed.

## Continue the conversation

直接理解并执行用户的自然语言目标：从上传数据学习并筛选、用已有规则筛选，
或调用当前 LLM 按规则生成。目标不明确时才简短说明这些可选操作。
不要求固定编号菜单或平台“我的规则”页面。保存成功后显示真实文件位置和规则包，
用户接着说“用刚保存的规则筛选”或“按刚才的规则生成”即可。生成按用户选择
预览、调整并确认 prompt 后调用当前 LLM，或直接生成并核验。无法运行计算时
保留提案并标为待核验，不能把依赖导入失败计为无效结构或零通过。
默认百分比、STCA/WRAcc 双结果和推荐标准均遵循准备后的完整说明。
'''
    return (frontmatter(meta) + body.replace("{{PACKAGE_VERSION}}", meta["package_version"])).encode("utf-8")


def shallow_workbuddy_files(skill: Path, files: dict[str, bytes], meta: dict) -> dict[str, bytes]:
    payload = workbuddy_payload(files, meta["package_version"])
    payload_metadata = json.loads(payload)
    manifest = json.loads(files["assets/platform-release.json"])
    visible_source = visible_author_source(files)
    manifest["visible_author_source"] = {
        "layout": "author_source/layout.json",
        "layout_sha256": sha256(visible_source["author_source/layout.json"]),
        "file_count": len(visible_source) - 1,
    }
    entrypoints = {
        "scripts/workbuddy_runtime.py": (skill / "scripts/workbuddy_runtime.py").read_bytes(),
        "scripts/agent_runtime.py": workbuddy_agent_entry(),
        "scripts/launch_runtime.sh": (skill / "scripts/launch_runtime.sh").read_bytes(),
        "scripts/launch_runtime.ps1": (skill / "scripts/launch_runtime.ps1").read_bytes(),
    }
    manifest.update({
        "archive_layout": "root_SKILL_and_direct_child_files_only",
        "maximum_archive_path_components": 2,
        "maximum_upload_expanded_bytes": WORKBUDDY_MAX_EXPANDED_BYTES,
        "runtime_payload_encoding": payload_metadata["payload_encoding"],
        "runtime_payload_sha256": payload_metadata["payload_sha256"],
        "runtime_payload_files": len(files),
        "core_scripts_location": "verified_runtime_payload",
        "public_entrypoints_sha256": {name: sha256(data) for name, data in entrypoints.items()},
        "public_entrypoints": {
            "scripts/agent_runtime.py": "verified_restore_and_forward_agent_runtime",
            "scripts/workbuddy_runtime.py": "verified_runtime_restoration",
            "scripts/launch_runtime.sh": "posix_python_discovery_launcher",
            "scripts/launch_runtime.ps1": "windows_python_discovery_launcher",
        },
    })
    shallow = {name: files[name] for name in PUBLICATION_FILES}
    shallow["THIRD_PARTY_NOTICES.md"] = publication_notice(
        files["THIRD_PARTY_NOTICES.md"], "author_source", flattened=True)
    shallow.update(visible_source)
    shallow.update(entrypoints)
    shallow.update({
        "SKILL.md": workbuddy_entry(meta),
        "assets/runtime_payload.json": payload,
        "assets/stca-logo.png": files["assets/stca-logo.png"],
        "assets/platform-release.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    })
    shallow["SHA256SUMS.txt"] = "".join(
        sha256(data) + "  " + name + "\n" for name, data in sorted(shallow.items())
    ).encode("utf-8")
    if any(len(Path(name).parts) > 2 or Path(name).is_absolute() or ".." in Path(name).parts for name in shallow):
        raise ValueError("WorkBuddy export must contain only root or direct-child files.")
    validate_workbuddy_entry_resources(shallow)
    validate_workbuddy_size(shallow)
    return shallow


def visible_author_source(files: dict[str, bytes]) -> dict[str, bytes]:
    """Expose real, byte-exact author resources within WorkBuddy's depth limit."""
    prefix = "assets/author_source/"
    source = {name[len(prefix):]: data for name, data in files.items() if name.startswith(prefix)}
    if not {"LICENSE", "NOTICE", "source_manifest.json"}.issubset(source):
        raise ValueError("The author source, original license/notice or integrity manifest is missing.")
    original = json.loads(source["source_manifest.json"])
    declared = original.get("files")
    if not isinstance(declared, dict) or set(source) != set(declared) | {"source_manifest.json"}:
        raise ValueError("Author-source inventory differs from its original integrity manifest.")
    for relative, digest in declared.items():
        if sha256(source[relative]) != digest:
            raise ValueError("Author source differs from its original SHA-256: " + relative)
    visible = {}
    mapping = {}
    for relative, data in sorted(source.items()):
        name = "author_source/" + "__".join(relative.split("/"))
        encoding = "raw"
        stored = data
        if relative.startswith("src/stca/assets/") and relative.endswith(".json"):
            name += ".xz"
            encoding = "xz"
            stored = lzma.compress(data, preset=6)
        if name == "author_source/layout.json" or name.casefold() in {n.casefold() for n in visible}:
            raise ValueError("Flattened author-source filename collision: " + relative)
        visible[name] = stored
        mapping[relative] = {"path": name, "sha256": sha256(data),
                             "encoding": encoding, "stored_sha256": sha256(stored)}
    visible["author_source/layout.json"] = (json.dumps({
        "schema": "stca-workbuddy-visible-author-source-v1",
        "original_directory": "assets/author_source",
        "files": mapping,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return visible


def workbuddy_agent_entry() -> bytes:
    """Expose the referenced, usable runtime entry within the shallow upload."""
    return b'''#!/usr/bin/env python3
"""Run the complete STCA agent after verified WorkBuddy resource restoration.

This public entry preserves every command-line argument and the user's working
directory. The full calculation implementation is bundled in the verified
runtime payload; no network or scientific dependency is needed for restoration.
"""
import sys
sys.dont_write_bytecode = True
from workbuddy_runtime import run_agent_runtime

if __name__ == "__main__":
    raise SystemExit(run_agent_runtime(sys.argv[1:]))
'''


def validate_workbuddy_entry_resources(files: dict[str, bytes]) -> None:
    """Reject upload instructions that refer to an absent visible resource."""
    paths = set()
    for name in ("SKILL.md", "THIRD_PARTY_NOTICES.md"):
        entry = files.get(name, b"").decode("utf-8")
        # Local resources are written in code spans. External source URLs are
        # attribution, not claims about the installed package's file layout.
        paths.update(re.findall(r"`((?:scripts|assets|references|author_source|skills)/[A-Za-z0-9_./-]+|author_source)`", entry))
    missing = sorted(path for path in paths if path not in files
                     and not any(name.startswith(path.rstrip("/") + "/") for name in files))
    if missing:
        raise ValueError("WorkBuddy entry references missing bundled resources: " + ", ".join(missing))


def validate_workbuddy_size(files: dict[str, bytes]) -> int:
    """Enforce WorkBuddy's extracted-upload limit, including every file."""
    expanded = sum(len(data) for data in files.values())
    if expanded > WORKBUDDY_MAX_EXPANDED_BYTES:
        raise ValueError(
            f"WorkBuddy extracted package is {expanded} bytes; the maximum is "
            f"{WORKBUDDY_MAX_EXPANDED_BYTES} bytes. Keep all runtime resources "
            "and improve the lossless payload encoding before release."
        )
    return expanded


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
        if "version" in meta["frontmatter"] and meta["frontmatter"]["version"] != version:
            raise ValueError("Platform frontmatter version must match package_version.")
        files = dict(base)
        platform_body = body
        if platform_name == "workbuddy":
            platform_body, replacements = re.subn(
                r"版本保持 \*\*[0-9]+\.[0-9]+\.[0-9]+\*\*。",
                f"WorkBuddy 发布版本 **{version}**。", body, count=1)
            if replacements != 1:
                raise ValueError("Cannot locate the WorkBuddy instruction release version.")
            citation = files["CITATION.cff"].decode("utf-8")
            citation, replacements = re.subn(r"(?m)^version:.*$", f"version: '{version}'", citation, count=1)
            if replacements != 1:
                raise ValueError("Cannot locate the software citation version.")
            files["CITATION.cff"] = citation.encode("utf-8")
            reference = files["references/workbuddy.md"].decode("utf-8")
            reference, replacements = re.subn(
                r"版本 \*\*[0-9]+\.[0-9]+\.[0-9]+\*\*。",
                f"WorkBuddy 发布版本 **{version}**。", reference, count=1)
            if replacements != 1:
                raise ValueError("Cannot locate the WorkBuddy reference release version.")
            files["references/workbuddy.md"] = reference.encode("utf-8")
        files["SKILL.md"] = (frontmatter(meta) + "\n> " + meta["entry_note"] + "\n\n" + platform_body).encode("utf-8")
        manifest = {
            "skill": "stca", "platform": platform_name, "package_version": version,
            "upstream_commit": "5951b0ef23d63edc8f7e803aaaffa5e4168288f6",
            "official_documentation_checked": "2026-11-07",
            "official_docs": meta["official_docs"],
            "core_scripts_sha256": {n: sha256(files["scripts/" + n]) for n in CORE_SCRIPTS},
            "common_instruction_body_sha256": sha256(platform_body.encode("utf-8")),
            "platform_end_to_end_tested": False,
            "public_market_submission_performed": False,
            "publisher_license_confirmation_required": False,
        }
        files["assets/platform-release.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        checksums = "".join(sha256(data) + "  " + name + "\n" for name, data in sorted(files.items()))
        files["SHA256SUMS.txt"] = checksums.encode("utf-8")
        if platform_name == "workbuddy":
            files = shallow_workbuddy_files(skill, files, meta)
        prepared.append((f"stca-{platform_name}-{version}.zip", files, "" if platform_name == "workbuddy" else "stca/"))
    out.mkdir(parents=True, exist_ok=False)
    archives = []
    for name, files, prefix in prepared:
        archive = out / name
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for relative, data in sorted(files.items()):
                info = zipfile.ZipInfo(prefix + relative, date_time=(2026, 11, 7, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, data)
        archives.append({"file": str(archive), "files": len(files), "bytes": archive.stat().st_size,
                         "expanded_bytes": sum(len(data) for data in files.values()),
                         "sha256": sha256(archive.read_bytes())})
    print(json.dumps({"archives": archives}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
