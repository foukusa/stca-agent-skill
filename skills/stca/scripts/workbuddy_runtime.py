#!/usr/bin/env python3
"""Restore WorkBuddy's shallow runtime package without changing its algorithms.

Preparation uses only the standard library, verifies every bundled resource,
reads the installation without writing into it, and restores the original
resource hierarchy in a content-addressed user cache. Calculation and LLM
workflow behavior remain owned by the restored STCA instructions and scripts.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import unicodedata
import zlib


SCHEMA = "stca-workbuddy-runtime-v1"
PAYLOAD = Path(__file__).resolve().parents[1] / "assets" / "runtime_payload.json"
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024
HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
REQUIRED_FILES = {"SKILL.md", "scripts/agent_runtime.py", "assets/platform-release.json"}
CACHE_MARKER = ".stca-runtime-complete.json"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key!r}")
        result[key] = value
    return result


def _json(data):
    return json.loads(data, object_pairs_hook=_unique_object)


def _hash(value, label):
    if not isinstance(value, str) or HEX_DIGEST.fullmatch(value) is None:
        raise ValueError(f"Invalid SHA-256 for {label}.")
    return value


def _decode(value, label):
    if not isinstance(value, str):
        raise ValueError(f"Base64 data must be text: {label}.")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"Invalid base64 data: {label}.") from exc


def _safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value or ":" in value:
        raise ValueError(f"Unsafe runtime resource path: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} or part.endswith((".", " ")) for part in parts):
        raise ValueError(f"Unsafe runtime resource path: {value!r}")
    # These names are device aliases on Windows rather than ordinary files.
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    if any(part.split(".", 1)[0].upper() in reserved for part in parts):
        raise ValueError(f"Reserved runtime resource path: {value!r}")
    return parts


def load_payload(path=PAYLOAD):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("The installed runtime payload must be a regular file.")
    if path.stat().st_size > MAX_PAYLOAD_BYTES:
        raise ValueError("The installed runtime payload exceeds the supported size.")
    outer = _json(path.read_bytes())
    manifest_path = path.parent / "platform-release.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("The WorkBuddy release manifest is missing or unsafe.")
    manifest = _json(manifest_path.read_bytes())
    version = manifest.get("package_version") if isinstance(manifest, dict) else None
    if (not isinstance(version, str) or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None
            or manifest.get("platform") != "workbuddy"):
        raise ValueError("Invalid WorkBuddy release version or platform.")
    if not isinstance(outer, dict) or outer.get("schema") != SCHEMA or outer.get("version") != version:
        raise ValueError("WorkBuddy payload version does not match its release manifest.")
    encoding = outer.get("payload_encoding")
    if encoding not in {"zlib+base64", "lzma+base85"}:
        raise ValueError("Unsupported runtime payload encoding.")
    expected = _hash(outer.get("payload_sha256"), "runtime payload")
    count = outer.get("file_count")
    if type(count) is not int or count < 1:
        raise ValueError("The runtime payload has no valid file count.")
    if encoding == "zlib+base64":
        encoded = _decode(outer.get("payload"), "runtime payload")
        try:
            decoder = zlib.decompressobj()
            raw = decoder.decompress(encoded, MAX_PAYLOAD_BYTES + 1)
        except zlib.error as exc:
            raise ValueError("The runtime payload is not valid zlib data.") from exc
        incomplete = bool(decoder.unconsumed_tail or not decoder.eof or decoder.unused_data)
    else:
        value = outer.get("payload")
        if not isinstance(value, str):
            raise ValueError("Base85 runtime payload must be text.")
        try:
            encoded = base64.b85decode(value.encode("ascii"))
            if base64.b85encode(encoded).decode("ascii") != value:
                raise ValueError("Non-canonical base85 runtime payload.")
        except (ValueError, UnicodeError) as exc:
            raise ValueError("Invalid base85 runtime payload.") from exc
        try:
            decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
            raw = decoder.decompress(encoded, max_length=MAX_PAYLOAD_BYTES + 1)
        except lzma.LZMAError as exc:
            raise ValueError("The runtime payload is not valid bounded LZMA data.") from exc
        incomplete = not decoder.eof or bool(decoder.unused_data)
    if len(raw) > MAX_PAYLOAD_BYTES or incomplete:
        raise ValueError("The runtime payload is incomplete, oversized, or has trailing data.")
    if _digest(raw) != expected:
        raise ValueError("Runtime payload SHA-256 mismatch.")
    inner = _json(raw)
    records = inner.get("files") if isinstance(inner, dict) else None
    if not isinstance(records, dict) or len(records) != count:
        raise ValueError("Runtime payload file count does not match its contents.")
    files = {}
    normalized_paths = set()
    for relative, record in records.items():
        _safe_relative(relative)
        if relative == CACHE_MARKER:
            raise ValueError("The runtime payload uses a reserved completion-marker path.")
        normalized = unicodedata.normalize("NFC", relative).casefold()
        if normalized in normalized_paths:
            raise ValueError(f"Runtime resource path collision: {relative!r}")
        normalized_paths.add(normalized)
        if not isinstance(record, dict) or set(record) != {"sha256", "data"}:
            raise ValueError(f"Invalid runtime resource record: {relative!r}")
        expected_file = _hash(record.get("sha256"), relative)
        data = _decode(record.get("data"), relative)
        if _digest(data) != expected_file:
            raise ValueError(f"Runtime resource SHA-256 mismatch: {relative!r}")
        files[relative] = {"sha256": expected_file, "data": data}
    for relative in files:
        parents = relative.split("/")[:-1]
        for length in range(1, len(parents) + 1):
            parent = unicodedata.normalize("NFC", "/".join(parents[:length])).casefold()
            if parent in normalized_paths:
                raise ValueError(f"Runtime resource file/directory collision: {relative!r}")
    if not REQUIRED_FILES.issubset(files):
        raise ValueError("Runtime payload lacks its instructions or agent entry point.")
    restored_manifest = _json(files["assets/platform-release.json"]["data"])
    if (not isinstance(restored_manifest, dict) or restored_manifest.get("package_version") != version
            or restored_manifest.get("platform") != "workbuddy"):
        raise ValueError("Restored runtime version does not match its WorkBuddy package.")
    _verify_visible_author_source(path.parent.parent, manifest, files)
    return expected, files


def _verify_visible_author_source(installed, manifest, files):
    """Verify the review-visible source mirror against the complete payload."""
    declaration = manifest.get("visible_author_source")
    if declaration is None:
        # Older published packages had only the verified runtime payload.
        # New packages declare the visible mirror and may never omit it.
        if tuple(map(int, manifest["package_version"].split("."))) >= (0, 1, 3):
            raise ValueError("The visible author-source declaration is missing.")
        return
    if not isinstance(declaration, dict) or set(declaration) != {"layout", "layout_sha256", "file_count"}:
        raise ValueError("Invalid visible author-source declaration.")
    if declaration["layout"] != "author_source/layout.json":
        raise ValueError("Invalid visible author-source layout path.")
    directory = installed / "author_source"
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("The visible author_source directory is missing or unsafe.")
    path = installed / declaration["layout"]
    try:
        data = _regular_bytes(path)
    except (OSError, RuntimeError) as exc:
        raise ValueError("The visible author-source layout is missing or unsafe.") from exc
    if _digest(data) != _hash(declaration["layout_sha256"], "visible author-source layout"):
        raise ValueError("Visible author-source layout SHA-256 mismatch.")
    layout = _json(data)
    if (not isinstance(layout, dict) or layout.get("schema") != "stca-workbuddy-visible-author-source-v1"
            or layout.get("original_directory") != "assets/author_source"):
        raise ValueError("Invalid visible author-source layout.")
    mapping = layout.get("files")
    prefix = "assets/author_source/"
    source = {name[len(prefix):]: record for name, record in files.items() if name.startswith(prefix)}
    if (not isinstance(mapping, dict) or set(mapping) != set(source)
            or type(declaration["file_count"]) is not int or declaration["file_count"] != len(source)):
        raise ValueError("Visible author-source inventory differs from the complete runtime payload.")
    original = _json(source.get("source_manifest.json", {}).get("data", b"{}"))
    original_files = original.get("files") if isinstance(original, dict) else None
    if (not isinstance(original_files, dict)
            or set(source) != set(original_files) | {"source_manifest.json"}
            or not {"LICENSE", "NOTICE"}.issubset(original_files)):
        raise ValueError("The original author-source integrity manifest is incomplete.")
    for relative, digest in original_files.items():
        if source[relative]["sha256"] != digest:
            raise ValueError("Original author-source SHA-256 mismatch: " + relative)
    expected_paths = {"author_source/layout.json"}
    for relative, record in mapping.items():
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "encoding", "stored_sha256"}:
            raise ValueError("Invalid visible author-source mapping: " + relative)
        target = record["path"]
        parts = _safe_relative(target)
        if len(parts) != 2 or parts[0] != "author_source" or target in expected_paths:
            raise ValueError("Unsafe or duplicate visible author-source path: " + str(target))
        expected_paths.add(target)
        expected = source[relative]
        if record["sha256"] != expected["sha256"]:
            raise ValueError("Visible author-source mapping SHA-256 mismatch: " + relative)
        try:
            visible = _regular_bytes(installed / target)
        except (OSError, RuntimeError) as exc:
            raise ValueError("Visible author-source file is missing or unsafe: " + target) from exc
        if _digest(visible) != _hash(record["stored_sha256"], "visible author-source file"):
            raise ValueError("Visible author-source stored SHA-256 mismatch: " + target)
        if record["encoding"] == "xz":
            try:
                decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
                visible = decoder.decompress(visible, max_length=MAX_PAYLOAD_BYTES + 1)
            except lzma.LZMAError as exc:
                raise ValueError("Invalid compressed visible author source: " + target) from exc
            if len(visible) > MAX_PAYLOAD_BYTES or not decoder.eof or decoder.unused_data:
                raise ValueError("Incomplete, oversized or trailing visible author source: " + target)
        elif record["encoding"] != "raw":
            raise ValueError("Unsupported visible author-source encoding: " + target)
        if _digest(visible) != expected["sha256"] or visible != expected["data"]:
            raise ValueError("Visible author-source file differs from the original: " + target)
    actual_paths = {"author_source/" + entry.name for entry in directory.iterdir()}
    if actual_paths != expected_paths:
        raise ValueError("Unexpected resource in the visible author_source directory.")


def _cache_base():
    explicit = os.environ.get("STCA_WORKBUDDY_CACHE_DIR")
    if explicit:
        base = Path(explicit).expanduser()
    elif os.environ.get("STCA_CACHE_DIR"):
        base = Path(os.environ["STCA_CACHE_DIR"]).expanduser() / "workbuddy-runtime"
    else:
        # WorkBuddy's ordinary permission boundary is the current task folder.
        # Keep created resources there unless the user explicitly chose a cache.
        base = Path.cwd() / ".stca-runtime" / "workbuddy-runtime"
    if base.is_symlink():
        raise RuntimeError("The WorkBuddy runtime cache directory cannot be a symlink.")
    base.mkdir(parents=True, exist_ok=True)
    if not base.is_dir():
        raise RuntimeError("The WorkBuddy runtime cache is not a directory.")
    return base.resolve()


def _runtime_environment():
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("STCA_CACHE_DIR", str(Path.cwd() / ".stca-runtime" / "backend"))
    return env


def _regular_bytes(path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    if path.is_symlink():
        raise RuntimeError(f"Cached runtime resource is a symlink: {path.name}")
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise RuntimeError(f"Cached runtime resource is not a regular file: {path.name}")
        return handle.read()


def _verify_cache(root, files, *, expected=None):
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("The cached runtime root is missing or is a symlink.")
    if expected is not None:
        try:
            marker = _json(_regular_bytes(root / CACHE_MARKER))
        except (OSError, ValueError) as exc:
            raise RuntimeError("The cached runtime is incomplete: its completion marker is missing or invalid. "
                               "No cached code was executed; retain this directory for diagnosis and use "
                               "an authorized writable cache directory.") from exc
        if marker != {"schema": SCHEMA + "-cache", "payload_sha256": expected, "file_count": len(files)}:
            raise RuntimeError("The cached runtime completion marker does not match this package.")
    expected_directories = {""}
    for relative in files:
        parts = relative.split("/")
        expected_directories.update("/".join(parts[:i]) for i in range(1, len(parts)))
        current = root
        for part in parts[:-1]:
            current = current / part
            if current.is_symlink() or not current.is_dir():
                raise RuntimeError(f"Cached runtime directory is missing or unsafe: {relative}")
        path = root.joinpath(*parts)
        try:
            data = _regular_bytes(path)
        except OSError as exc:
            raise RuntimeError(f"Cached runtime resource is missing or unreadable: {relative}") from exc
        if _digest(data) != files[relative]["sha256"]:
            raise RuntimeError(f"Cached runtime resource changed: {relative}")
    # Extra modules and bytecode could shadow the verified source. Reject them
    # without deleting or changing the cache; execution uses no-bytecode mode.
    for parent, directories, filenames in os.walk(root, followlinks=False):
        directory = Path(parent)
        for name in directories + filenames:
            if (directory / name).is_symlink():
                raise RuntimeError("The cached runtime contains a symlink.")
        for name in directories:
            path = directory / name
            relative = path.relative_to(root).as_posix()
            if relative not in expected_directories:
                raise RuntimeError(f"Unexpected cached runtime directory: {relative}")
        for name in filenames:
            path = directory / name
            relative = path.relative_to(root).as_posix()
            if relative not in files and not (relative == CACHE_MARKER and expected is not None):
                raise RuntimeError(f"Unexpected cached runtime resource: {relative}")


def prepare(payload_path=PAYLOAD):
    expected, files = load_payload(payload_path)
    base = _cache_base()
    root = base / expected
    if root.is_symlink():
        raise RuntimeError("The cached runtime root cannot be a symlink.")
    cache_hit = root.exists()
    if cache_hit:
        _verify_cache(root, files, expected=expected)
    else:
        try:
            root.mkdir(exist_ok=False)
        except FileExistsError:
            # Another preparation owns this exact cache. Only a fully committed,
            # independently verified cache can be reused; never infer readiness.
            _verify_cache(root, files, expected=expected)
            cache_hit = True
        if not cache_hit:
            # Append-only materialization needs only ordinary file creation.
            # The completion marker is written last, after every resource was
            # independently verified. An interrupted/denied write stays visibly
            # incomplete and is never executed or silently cleaned up.
            for relative, record in files.items():
                path = root.joinpath(*relative.split("/"))
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as handle:
                    handle.write(record["data"])
            _verify_cache(root, files)
            with (root / CACHE_MARKER).open("xb") as handle:
                handle.write((json.dumps({"schema": SCHEMA + "-cache", "payload_sha256": expected,
                                         "file_count": len(files)}, sort_keys=True) + "\n").encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            _verify_cache(root, files, expected=expected)
    return {
        "runtime_skill_dir": str(root),
        "skill_instructions": str(root / "SKILL.md"),
        "scripts_dir": str(root / "scripts"),
        "assets_dir": str(root / "assets"),
        "payload_sha256": expected,
        "verified_files": len(files),
        "cache_hit": cache_hit,
        "backend_cache_dir": _runtime_environment()["STCA_CACHE_DIR"],
    }


def run_agent_runtime(arguments):
    """Run the full bundled agent through the visible shallow entry point."""
    try:
        ready = prepare()
        runtime = Path(ready["runtime_skill_dir"])
        env = _runtime_environment()
        return subprocess.run(
            [sys.executable, str(runtime / "scripts" / "agent_runtime.py"), *arguments],
            env=env,
        ).returncode
    except (ValueError, OSError, RuntimeError) as exc:
        print("stca-workbuddy-runtime: " + str(exc), file=sys.stderr)
        return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("prepare", help="Verify and restore bundled resources without dependencies or network.")
    run = sub.add_parser("run", help="Delegate an unchanged STCA entry point from the restored runtime.")
    run.add_argument("--script", required=True)
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        ready = prepare()
        if args.action == "prepare":
            print(json.dumps(ready, ensure_ascii=False))
            return 0
        if re.fullmatch(r"[A-Za-z0-9_]+\.py", args.script) is None:
            raise ValueError("Choose a bundled script filename, without a directory.")
        runtime = Path(ready["runtime_skill_dir"])
        if not (runtime / "scripts" / args.script).is_file():
            raise ValueError("The requested bundled script does not exist.")
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        env = _runtime_environment()
        # Keep the user's current directory, including relative input/output
        # paths; imports resolve from the absolute restored script path.
        return subprocess.run(
            [sys.executable, str(runtime / "scripts" / "agent_runtime.py"),
             "run", "--script", args.script, "--", *arguments], env=env,
        ).returncode
    except (ValueError, OSError, RuntimeError) as exc:
        print("stca-workbuddy-runtime: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
