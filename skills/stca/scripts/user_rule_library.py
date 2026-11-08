#!/usr/bin/env python3
"""Persist user-learned STCA rules outside the installed skill, using stdlib only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import secrets
import stat
import sys
import zipfile

from generation_prompt import render_prompt
from stca_tools import _custom_contract, _target_metadata
from frozen_literal_model import FrozenLiteralModel, MODEL_TYPE as LITERAL_MODEL_TYPE

SCHEMA = "stca-user-rule-library-v1"
SKILL_ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def parse_json(data):
    def invalid(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Repeated JSON key: {key}")
            result[key] = value
        return result
    return json.loads(data.decode("utf-8-sig"), parse_constant=invalid, object_pairs_hook=unique)


def read_json(path):
    return parse_json(Path(path).read_bytes())


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def library_root(path):
    supplied = Path(path).expanduser().absolute()
    if supplied.is_symlink():
        raise ValueError("The user rule library cannot be a symlink.")
    root = supplied.resolve()
    if root == SKILL_ROOT.parent or root.is_relative_to(SKILL_ROOT.parent):
        raise ValueError("Save learned rules in the user's workspace, outside the installed skill.")
    if root.exists() and not root.is_dir():
        raise ValueError("The user rule library must be a directory.")
    return root


def _name(value):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200 or any(ord(c) < 32 for c in value):
        raise ValueError("Use a nonempty, single-line friendly name of at most 200 characters.")
    return value.strip()


def _tier(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value < 1:
        raise ValueError("A saved rule needs a finite tier strictly between 0 and 1.")
    return format(value, ".12g")


def valid_identifier(value):
    return (isinstance(value, str) and value.startswith("rules-") and len(value) == 30
            and all(c in "0123456789abcdef" for c in value[6:]))


def validate_model(model):
    if not isinstance(model, dict) or model.get("schema_version") != 1:
        raise ValueError("Unsupported saved STCA model schema.")
    if model.get("direction") not in {"high", "low"} or not model.get("target_name") or not model.get("target_unit"):
        raise ValueError("Saved model target metadata is incomplete.")
    if model.get("n_features") != 167 or model.get("feature_spec", {}).get("kind") != "rdkit_maccs167":
        raise ValueError("This learned polymer-rule library requires a MACCS167 model.")
    if model.get("feature_names") != [f"K{i}" for i in range(167)]:
        raise ValueError("The model must preserve the original MACCS167 key numbering.")
    if not isinstance(model.get("tiers"), dict) or not model["tiers"]:
        raise ValueError("The model contains no tiers.")
    model_type = model.get("model_type")
    if model_type == LITERAL_MODEL_TYPE:
        FrozenLiteralModel.from_artifact(model)
    elif model_type is not None:
        raise ValueError(f"Unsupported saved model_type {model_type!r}.")
    elif model.get("learner", "STCA") != "STCA":
        raise ValueError("A non-STCA learner requires the explicit frozen literal model format.")


def validate_constraint(model, constraint):
    if not isinstance(constraint, dict) or constraint.get("schema") != "stca-constraints-v1":
        raise ValueError("Save an exported stca-constraints-v1 rule with its model.")
    if constraint.get("status") != "frozen_representative" or not constraint.get("rule"):
        raise ValueError("A no-rule result cannot be saved as a usable frozen rule.")
    if constraint.get("model", {}).get("artifact_sha256") != canonical_hash(model):
        raise ValueError("The constraints do not belong to this exact saved model.")
    learner = model.get("learner", "STCA")
    literal = model.get("model_type") == LITERAL_MODEL_TYPE
    for source in [constraint, constraint.get("model", {})]:
        if not isinstance(source, dict):
            raise ValueError("Constraint model metadata must be an object.")
        if (literal and source.get("learner") != learner) or source.get("learner", learner) != learner:
            raise ValueError("Constraint learner differs from its exact saved model.")
        if literal and source.get("model_type") != LITERAL_MODEL_TYPE:
            raise ValueError("Constraint model_type differs from its exact saved model.")
    key = _tier(constraint.get("tier_fraction"))
    tier = model["tiers"].get(key)
    if not isinstance(tier, dict) or not tier.get("selected_rule"):
        raise ValueError(f"The model has no frozen representative at tier {key}.")
    target = constraint.get("target", {})
    if not isinstance(target, dict):
        raise ValueError("Constraint target metadata must be an object.")
    for exported, original in [("name", "target_name"), ("unit", "target_unit"), ("direction", "direction")]:
        if target.get(exported) != model[original]:
            raise ValueError(f"Constraint target {exported} differs from the saved model.")
    cutoff = target.get("model_space_cutoff", target.get("reference_train_cutoff"))
    if cutoff != tier.get("train_cutoff"):
        raise ValueError("Constraint cutoff differs from its saved model tier.")
    if constraint.get("feature_spec") != model.get("feature_spec") or constraint.get("feature_names") != model.get("feature_names"):
        raise ValueError("Constraint fingerprint metadata differs from its model.")
    expected_target = _target_metadata(model, tier)
    for field in ["model_space_cutoff", "model_space_unit", "physical_train_cutoff", "physical_unit",
                  "target_transform", "input_already_logarithmic", "label_comparison"]:
        if target.get(field) != expected_target[field]:
            raise ValueError(f"Constraint target {field} differs from the model's saved transformation.")
    contract = _custom_contract(model)
    if contract.get("representation") != "hcap_maccs167" or constraint.get("model", {}).get("custom_data_contract") != contract:
        raise ValueError("The model and constraints must retain their actual H-cap data contract.")
    family = tier.get("rules")
    if not isinstance(family, list) or any(not isinstance(item, dict) or not isinstance(item.get("rule"), dict) for item in family):
        raise ValueError("The saved tier rule family is malformed.")
    selected = [item.get("rule") for item in family
                if item.get("rule", {}).get("name") == tier["selected_rule"]]
    if len(selected) != 1:
        raise ValueError("The model's frozen representative is ambiguous or absent.")
    expected, actual = selected[0], constraint["rule"]
    for field in ["keys", "values", "name", "family"]:
        if expected.get(field) != actual.get(field):
            raise ValueError(f"The exported {field} differs from the selected frozen representative.")
    signature = "STCA|AND|" + "&".join(f"K{k}={v}" for k, v in sorted(zip(expected["keys"], expected["values"])))
    if actual.get("signature") != signature:
        raise ValueError("The exported signature differs from its exact frozen conditions.")
    # Rendering also checks exact expressions, bit conflicts, H-cap semantics,
    # target units, and the literal definitions that the LLM will receive.
    render_prompt(constraint, "en", 20)
    return key


def save_entry(root, name, model_path, constraint_paths, count=20, preferences="", imported_from=None):
    """Save a new rule set without overwriting or renaming existing files."""
    model_bytes = Path(model_path).resolve().read_bytes()
    constraints = [Path(path).resolve().read_bytes() for path in constraint_paths]
    return _save_entry_bytes(root, name, model_bytes, constraints, count, preferences, imported_from)


def _save_entry_bytes(root, name, model_bytes, constraints, count=20, preferences="", imported_from=None):
    root = library_root(root)
    name = _name(name)
    if not isinstance(preferences, str):
        raise ValueError("Chemical preferences must be text.")
    model = parse_json(model_bytes)
    validate_model(model)
    payload = {"model.json": model_bytes}
    rules, seen = [], set()
    for captured in constraints:
        constraint = parse_json(captured)
        key = validate_constraint(model, constraint)
        if key in seen:
            raise ValueError(f"Tier {key} was supplied more than once.")
        seen.add(key)
        base = f"tiers/{key}"
        constraint_file = base + "/constraints.json"
        payload[constraint_file] = captured
        prompts = {}
        for language in ["en", "zh-CN"]:
            relative = base + f"/prompt.{language}.md"
            payload[relative] = render_prompt(constraint, language, count, preferences).encode()
            prompts[language] = relative
        rules.append({"tier": constraint["tier_fraction"], "constraints": constraint_file,
                      "prompts": prompts, "target": constraint["target"],
                      "learner": model.get("learner", "STCA"),
                      "rule_signature": constraint["rule"]["signature"]})
    if not rules:
        raise ValueError("Provide at least one usable exported tier.")
    root.mkdir(parents=True, exist_ok=True)
    identifier = "rules-" + secrets.token_hex(12)
    destination = root / identifier
    if destination.exists():
        raise FileExistsError("Generated rule ID already exists; no record was replaced.")
    record = {"schema": SCHEMA, "version": "0.1.0", "id": identifier, "name": name,
              "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "property": model["target_name"], "unit": model["target_unit"], "direction": model["direction"],
              "learner": model.get("learner", "STCA"), "model_type": model.get("model_type"),
              "tiers": sorted(float(key) for key in seen), "rules": sorted(rules, key=lambda item: item["tier"]),
              "model": {"file": "model.json", "sha256": digest(model_bytes), "artifact_sha256": canonical_hash(model)},
              "generation_defaults": {"count": count, "preferences": preferences},
              "files": {name: digest(data) for name, data in payload.items()},
              "source_csv_copied": False}
    if imported_from:
        record["imported_from"] = imported_from
    # Validate the complete intended record before creating its directory.
    # A missing/partial record.json never becomes a usable library entry.
    _validate_record_data(record, identifier, payload)
    destination.mkdir(exist_ok=False)
    for relative, data in payload.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
    # Commit marker LAST: a failed write leaves an incomplete unique entry for
    # inspection, rather than requiring delete/rename permissions to roll back.
    # Filesystem PermissionError is deliberately not suppressed or bypassed.
    with (destination / "record.json").open("xb") as handle:
        handle.write(json_bytes(record))
    return {"status": "saved", "next_action": "continue_conversation", "entry": show_entry(root, identifier)}


def _entry_path(root, identifier):
    if not valid_identifier(identifier):
        raise ValueError("Invalid saved-rule ID.")
    root = library_root(root)
    path = root / identifier
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Saved rule set was not found.")
    return path


def _validate_record(path):
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Saved rule set must be a regular directory.")
    resources = {}
    for resource in path.rglob("*"):
        if resource.is_symlink():
            raise ValueError("Saved rule resources cannot be symlinks.")
        if resource.is_file():
            resources[resource.relative_to(path).as_posix()] = resource.read_bytes()
        elif not resource.is_dir():
            raise ValueError("Saved rule resources must be regular files.")
    if "record.json" not in resources:
        raise ValueError("Saved rule set is incomplete: record.json was not committed.")
    record = parse_json(resources.pop("record.json"))
    return _validate_record_data(record, path.name, resources)


def _validate_record_data(record, identifier, resources):
    """Validate the same bounded record contract on disk or in an archive."""
    if not isinstance(record, dict) or record.get("schema") != SCHEMA or record.get("id") != identifier or not valid_identifier(identifier):
        raise ValueError("Invalid saved-rule record.")
    files, rules = record.get("files"), record.get("rules")
    if not isinstance(files, dict) or not files or not isinstance(rules, list) or not rules:
        raise ValueError("Saved record has no complete resources and rules.")
    if not isinstance(record.get("model"), dict) or record["model"].get("file") != "model.json" or "model.json" not in files:
        raise ValueError("Saved record model must refer to its own model.json.")
    _name(record.get("name"))
    if record["model"].get("sha256") != files["model.json"]:
        raise ValueError("Saved model byte hash differs from its resource manifest.")
    referenced = {"model.json"}
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("prompts"), dict) or set(rule["prompts"]) != {"en", "zh-CN"}:
            raise ValueError("Saved rule must retain both complete prompt languages.")
        references = [rule.get("constraints"), *rule["prompts"].values()]
        if any(not isinstance(name, str) or name not in files for name in references):
            raise ValueError("Saved rule points to an unlisted resource.")
        referenced.update(references)
    if referenced != set(files):
        raise ValueError("Saved record contains unexpected resources.")
    if set(resources) != set(files):
        raise ValueError("Saved rule set has unexpected or missing resource files.")
    for relative, expected in files.items():
        item = PurePosixPath(relative)
        if item.is_absolute() or ".." in item.parts or "\\" in relative or ":" in relative or str(item) != relative:
            raise ValueError("Saved resource escapes its rule directory.")
        if digest(resources[relative]) != expected:
            raise ValueError(f"Saved resource is missing or has changed: {relative}")
    model = parse_json(resources[record["model"]["file"]])
    validate_model(model)
    if record["model"].get("artifact_sha256") != canonical_hash(model):
        raise ValueError("Saved model hash differs from its record.")
    learner = model.get("learner", "STCA")
    literal = model.get("model_type") == LITERAL_MODEL_TYPE
    if ((literal and record.get("learner") != learner) or record.get("learner", learner) != learner
            or record.get("model_type") != model.get("model_type")):
        raise ValueError("Saved display learner/model_type differs from its model.")
    for field, expected in [("property", model["target_name"]), ("unit", model["target_unit"]), ("direction", model["direction"])]:
        if record.get(field) != expected:
            raise ValueError(f"Saved display {field} differs from its model.")
    actual_tiers = []
    for rule in record["rules"]:
        constraint = parse_json(resources[rule["constraints"]])
        key = validate_constraint(model, constraint)
        if float(key) != rule["tier"]:
            raise ValueError("Saved rule tier differs from its constraints.")
        if rule.get("target") != constraint["target"] or rule.get("rule_signature") != constraint["rule"]["signature"]:
            raise ValueError("Saved rule display metadata differs from its constraints.")
        if (literal and rule.get("learner") != learner) or rule.get("learner", learner) != learner:
            raise ValueError("Saved rule learner differs from its model.")
        actual_tiers.append(float(key))
    if len(set(actual_tiers)) != len(actual_tiers) or record.get("tiers") != sorted(actual_tiers):
        raise ValueError("Saved tier list is incomplete or contains duplicate rules.")
    return {**record, "learner": learner, "model_type": model.get("model_type")}


def show_entry(root, identifier):
    path = _entry_path(root, identifier)
    record = _validate_record(path)
    return {**record, "directory": str(path), "model_path": str(path / "model.json"),
            "usable_rules": [{**rule, "constraints_path": str(path / rule["constraints"]),
                               "prompt_paths": {language: str(path / relative) for language, relative in rule["prompts"].items()}}
                              for rule in record["rules"]]}


def list_entries(root):
    root = library_root(root)
    entries, errors = [], []
    if root.exists():
        for path in sorted(root.glob("rules-*")):
            try:
                entry = show_entry(root, path.name)
                entries.append({key: entry[key] for key in ["id", "name", "property", "unit", "direction", "learner", "model_type", "tiers", "created_at_utc", "directory", "model_path"]})
            except (ValueError, OSError, KeyError, TypeError) as exc:
                errors.append({"id": path.name, "error": str(exc)})
    return {"schema": SCHEMA, "entries": entries, "invalid_entries": errors}


def export_entry(root, identifier, output):
    entry = show_entry(root, identifier)
    path = Path(entry["directory"])
    output = Path(output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
        for relative in sorted(["record.json", *entry["files"]]):
            archive.write(path / relative, arcname=identifier + "/" + relative)
    return {"status": "exported", "id": identifier, "output": str(output), "sha256": digest(output.read_bytes())}


def import_entry(root, archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        if len(infos) > 512 or sum(item.file_size for item in infos) > MAX_ARCHIVE_BYTES:
            raise ValueError("Saved-rule archive exceeds the supported size.")
        names = set()
        for info in infos:
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename or ":" in info.filename or str(path) != info.filename or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("Saved-rule archive contains unsafe paths or symlinks.")
            if info.filename in names:
                raise ValueError("Saved-rule archive contains duplicate paths.")
            names.add(info.filename)
        records = [name for name in names if name.endswith("/record.json") and len(PurePosixPath(name).parts) == 2]
        if len(records) != 1:
            raise ValueError("A saved-rule archive must contain exactly one rule set.")
        record = parse_json(archive.read(records[0]))
        identifier = PurePosixPath(records[0]).parts[0]
        if not valid_identifier(identifier) or not isinstance(record, dict) or not isinstance(record.get("files"), dict):
            raise ValueError("Saved-rule archive has an invalid rule ID or resource manifest.")
        expected = {identifier + "/record.json", *(identifier + "/" + name for name in record.get("files", {}))}
        if names != expected:
            raise ValueError("Saved-rule archive contains unexpected or missing resources.")
        # Read only the declared, bounded files; do not extract an archive or
        # create temporary directories whose cleanup may require extra rights.
        resources = {name: archive.read(identifier + "/" + name) for name in record["files"]}
        verified = _validate_record_data(record, identifier, resources)
        defaults = verified.get("generation_defaults", {})
        return _save_entry_bytes(root, verified["name"], resources["model.json"],
                                 [resources[rule["constraints"]] for rule in verified["rules"]],
                                 defaults.get("count", 20), defaults.get("preferences", ""),
                                 imported_from={"id": identifier, "archive_sha256": digest(Path(archive_path).read_bytes())})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-dir", default=str(Path.cwd() / "stca-rules"))
    commands = parser.add_subparsers(dest="command", required=True)
    save = commands.add_parser("save")
    save.add_argument("--name", required=True)
    save.add_argument("--model", required=True)
    save.add_argument("--constraints", nargs="+", required=True)
    save.add_argument("--count", type=int, default=20)
    save.add_argument("--preferences", default="")
    commands.add_parser("list")
    show = commands.add_parser("show"); show.add_argument("id")
    export = commands.add_parser("export"); export.add_argument("id"); export.add_argument("--output", required=True)
    importing = commands.add_parser("import"); importing.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "save":
            result = save_entry(args.library_dir, args.name, args.model, args.constraints, args.count, args.preferences)
        elif args.command == "list":
            result = list_entries(args.library_dir)
        elif args.command == "show":
            result = show_entry(args.library_dir, args.id)
        elif args.command == "export":
            result = export_entry(args.library_dir, args.id, args.output)
        else:
            result = import_entry(args.library_dir, args.input)
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print("user-rule-library: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
