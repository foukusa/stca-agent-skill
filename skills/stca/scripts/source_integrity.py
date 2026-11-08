#!/usr/bin/env python3
"""Verify the unchanged author source shipped with this release, without Git."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

SOURCE_COMMIT = "5951b0ef23d63edc8f7e803aaaffa5e4168288f6"
SOURCE_REPOSITORY = "https://github.com/foukusa/polymer-stca.git"
MANIFEST_NAME = "source_manifest.json"
# This is part of the reviewed adapter, not a checksum supplied by an input tree.
TRUSTED_MANIFEST_SHA256 = "1be54abd9dabad06a03e8f93ff187eaeecfcfd6ebbef21bb127128f3d2856719"


def bundled_source_root():
    return Path(__file__).resolve().parent.parent / "assets" / "author_source"


def trusted_manifest():
    path = bundled_source_root() / MANIFEST_NAME
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("The bundled author-source manifest is missing or unsafe; reinstall the complete STCA package.")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != TRUSTED_MANIFEST_SHA256:
        raise RuntimeError("The bundled author-source manifest failed verification; do not patch the verifier. Reinstall the complete STCA package.")
    value = json.loads(payload)
    if (value.get("schema") != "stca-author-source-snapshot-v1"
            or value.get("commit") != SOURCE_COMMIT
            or value.get("repository") != SOURCE_REPOSITORY
            or not isinstance(value.get("files"), dict)):
        raise RuntimeError("The bundled author-source identity is invalid.")
    return value


def _tree_files(root, strict_root):
    """Reject extra source/resources and symlinks; never alter an input tree."""
    files = set()
    directories = [root] if strict_root else [root / "src"]
    for directory in directories:
        if directory.is_symlink() or not directory.is_dir():
            raise RuntimeError(f"Missing or unsafe author source directory: {directory}")
        for parent, children, names in os.walk(directory, followlinks=False):
            parent = Path(parent)
            for name in children + names:
                if (parent / name).is_symlink():
                    raise RuntimeError(f"Author source contains a symlink: {parent / name}")
            # Existing Git checkouts may have benign interpreter caches. The
            # source-only import loader never executes or writes these caches.
            if not strict_root:
                children[:] = [name for name in children if name != "__pycache__"]
            for name in names:
                path = parent / name
                if not path.is_file():
                    raise RuntimeError(f"Author source contains a nonregular file: {path}")
                relative = path.relative_to(root).as_posix()
                if strict_root and relative == MANIFEST_NAME:
                    continue
                files.add(relative)
    if not strict_root:
        files.update(("pyproject.toml", "LICENSE", "NOTICE"))
    return files


def verify_snapshot(source, *, strict_root=False):
    """Check exact tracked contents against the trusted release inventory."""
    supplied = Path(source).expanduser().absolute()
    if supplied.is_symlink() or not supplied.is_dir():
        raise RuntimeError(f"The specified author source directory is missing or unsafe: {supplied}")
    root = supplied.resolve()
    manifest = trusted_manifest()
    expected = manifest["files"]
    present = _tree_files(root, strict_root)
    if present != set(expected):
        missing = sorted(set(expected) - present)
        extra = sorted(present - set(expected))
        raise RuntimeError("Author-source inventory mismatch: "
                           + json.dumps({"missing": missing[:10], "extra": extra[:10]}))
    for relative, expected_hash in expected.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Missing or unsafe author source file: {relative}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise RuntimeError(f"Author-source checksum mismatch: {relative}; do not modify verification or the author algorithm.")
    supplied_manifest = root / MANIFEST_NAME
    if supplied_manifest.exists() and (supplied_manifest.is_symlink()
            or hashlib.sha256(supplied_manifest.read_bytes()).hexdigest() != TRUSTED_MANIFEST_SHA256):
        raise RuntimeError("The supplied author-source manifest is not the trusted release manifest.")
    return root


def source_identity(root, kind):
    manifest = trusted_manifest()
    return {"kind": kind, "repository": SOURCE_REPOSITORY, "commit": SOURCE_COMMIT,
            "path": str(root), "verification": "trusted_manifest_and_exact_source_inventory_sha256",
            "manifest_sha256": TRUSTED_MANIFEST_SHA256, "verified_file_n": len(manifest["files"]),
            "author_code_modified": False, "requires_git": kind == "clean_pinned_git_checkout"}
