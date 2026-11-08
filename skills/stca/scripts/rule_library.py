#!/usr/bin/env python3
"""Agent backend for browsing, copying and applying the bundled STCA rule library.

Browsing and prompt copying use only the Python standard library. Screening
imports RDKit only when requested and applies the stored MACCS conditions
exactly; it never fits a model or generates proposals on behalf of the host LLM.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


CATALOG_SCHEMA = "stca-rule-library-v1"
CONSTRAINT_SCHEMA = "stca-library-constraints-v1"
DEFAULT_LIBRARY = Path(__file__).resolve().parents[1] / "assets" / "rule_library"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def invalid_constant(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid_constant)


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


class RuleLibrary:
    def __init__(self, directory=DEFAULT_LIBRARY):
        self.root = Path(directory).expanduser().resolve()
        self.catalog_path = self.path("catalog.json")
        self.catalog = read_json(self.catalog_path)
        if self.catalog.get("schema") != CATALOG_SCHEMA:
            raise ValueError(f"Expected catalog schema {CATALOG_SCHEMA}.")
        entries = self.catalog.get("entries")
        if not isinstance(entries, list):
            raise ValueError("Catalog entries must be a list.")
        self.entries = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("Each catalog entry must be an object.")
            identifier = entry.get("id")
            if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identifier):
                raise ValueError("Entry IDs must be safe single-component identifiers.")
            if identifier in self.entries:
                raise ValueError(f"Duplicate catalog ID: {identifier}")
            self.entries[identifier] = entry

    def path(self, relative):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError("Library resources must use nonempty relative paths.")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Library resource escapes the library directory.")
        if not path.is_file():
            raise FileNotFoundError(f"Missing library resource: {relative}")
        return path

    def entry(self, identifier):
        if identifier not in self.entries:
            raise ValueError(f"Unknown library rule {identifier!r}; list the available IDs first.")
        return self.entries[identifier]

    def constraints(self, identifier):
        entry = self.entry(identifier)
        path = self.path(entry.get("constraints"))
        constraints = read_json(path)
        if constraints.get("schema") != CONSTRAINT_SCHEMA:
            raise ValueError(f"Expected {CONSTRAINT_SCHEMA}: {identifier}")
        for key in ("property", "direction", "tier"):
            if constraints.get(key) != entry.get(key):
                raise ValueError(f"Catalog/constraint {key} mismatch: {identifier}")
        if constraints.get("representation") != "hcap_maccs167":
            raise ValueError(f"Unsupported calculation representation: {identifier}")
        if constraints.get("direction") not in ("high", "low"):
            raise ValueError(f"Invalid target direction: {identifier}")
        tier = constraints.get("tier")
        if isinstance(tier, bool) or not isinstance(tier, (int, float)) or not 0 < tier < 1:
            raise ValueError(f"Invalid target tier: {identifier}")
        target = constraints.get("target")
        if not isinstance(target, dict):
            raise ValueError(f"Target metadata must be an object: {identifier}")
        if entry.get("unit") is not None and target.get("unit") != entry["unit"]:
            raise ValueError(f"Catalog/constraint unit mismatch: {identifier}")
        expected = ">=" if constraints["direction"] == "high" else "<="
        if target.get("operator") not in (None, expected):
            raise ValueError(f"Constraint direction/operator mismatch: {identifier}")
        rule = constraints.get("rule")
        if rule is not None:
            if not isinstance(rule, dict):
                raise ValueError(f"Rule must be an object or null: {identifier}")
            keys, values = rule.get("keys"), rule.get("values")
            if (not isinstance(keys, list) or not keys or not isinstance(values, list)
                    or len(keys) != len(values) or len(set(keys)) != len(keys)):
                raise ValueError(f"Rule needs distinct aligned nonempty keys/values: {identifier}")
            if any(type(k) is not int or not 0 <= k <= 166 for k in keys):
                raise ValueError(f"MACCS keys must be integers in 0..166: {identifier}")
            if any(type(v) is not int or v not in (0, 1) for v in values):
                raise ValueError(f"MACCS required values must be integer 0 or 1: {identifier}")
        return constraints, path

    def prompt(self, identifier, language="zh-CN"):
        prompts = self.entry(identifier).get("prompts", {})
        if not isinstance(prompts, dict) or language not in prompts:
            raise ValueError(f"Prompt language {language!r} is unavailable for {identifier}.")
        path = self.path(prompts[language])
        payload = path.read_bytes()
        payload.decode("utf-8")  # Validate, without changing the copied bytes.
        return payload, path


def screen(library, identifiers, args):
    from rdkit import Chem, rdBase
    from rdkit.Chem import MACCSkeys
    from prepare_hcap import hcap_smiles
    from stca_io import read_csv_records

    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Select each library entry at most once.")
    selected = [(identifier, *library.constraints(identifier)) for identifier in identifiers]
    output = Path(args.output_dir).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Output directory exists; choose a new directory.")
    input_path, raw, header, records = read_csv_records(args.input)
    if not records:
        raise ValueError("Candidate CSV contains no records.")
    required = {args.smiles_column} | ({args.id_column} if args.id_column else set())
    if required - set(header):
        raise ValueError(f"Missing input columns: {sorted(required-set(header))}")
    if any(name.startswith("stca_") for name in header):
        raise ValueError("Supply original candidate fields; stca_ is reserved for screening output.")
    rows, presentation = [], []
    canonical_original = defaultdict(list)
    canonical_cap = defaultdict(list)
    original_identities = {}
    totals = {identifier: {"selected": 0, "assessed": 0, "unknown": 0} for identifier in identifiers}
    for position, record in enumerate(records):
        row = dict(record)
        row["stca_row_position"] = position
        if args.id_column is None:
            row["stca_candidate_id"] = f"row-{position+1:06d}"
        row["stca_calculation_smiles_hcap"] = ""
        row["stca_input_error"] = ""
        bits = None
        try:
            original = Chem.MolFromSmiles(record[args.smiles_column])
            if original is None:
                raise ValueError("Invalid original SMILES.")
            original_identity = Chem.MolToSmiles(original, canonical=True)
            canonical_original[original_identity].append(position)
            original_identities[position] = original_identity
            capped, count = hcap_smiles(record[args.smiles_column])
            mol = Chem.MolFromSmiles(capped)
            if mol is None:
                raise ValueError("Invalid calculation-only H-cap structure.")
            bits = MACCSkeys.GenMACCSKeys(mol)
            if len(bits) != 167:
                raise ValueError("RDKit MACCS representation is not 167 bits.")
            row["stca_calculation_smiles_hcap"] = capped
            row["stca_hcap_connection_atoms_replaced"] = count
            canonical_cap[Chem.MolToSmiles(mol, canonical=True)].append(position)
        except (ValueError, RuntimeError) as exc:
            row["stca_input_error"] = str(exc)
            row["stca_hcap_connection_atoms_replaced"] = ""
        row["stca_input_valid"] = bits is not None
        decisions = []
        for identifier, constraint, _ in selected:
            prefix = f"stca_{identifier}__"
            rule = constraint.get("rule")
            decision, missing, unexpected, failed = None, [], [], []
            if bits is not None and rule is not None:
                for key, value in zip(rule["keys"], rule["values"]):
                    actual = int(bits[key])
                    if actual != value:
                        (missing if value else unexpected).append(f"K{key}")
                        failed.append({"key": key, "required": value, "observed": actual})
                decision = not failed
            totals[identifier]["unknown" if decision is None else "assessed"] += 1
            totals[identifier]["selected"] += int(decision is True)
            row[prefix+"selected"] = "" if decision is None else decision
            row[prefix+"status"] = ("invalid_input_unknown" if bits is None else
                                     "no_frozen_rule_unknown" if rule is None else
                                     "selected" if decision else "not_selected")
            row[prefix+"missing_required_present"] = ";".join(missing) if decision is not None else ""
            row[prefix+"unexpected_present"] = ";".join(unexpected) if decision is not None else ""
            row[prefix+"failed_conditions"] = json.dumps(failed, ensure_ascii=False) if decision is not None else ""
            decisions.append(decision)
        joint = None if any(d is None for d in decisions) else all(decisions)
        row["stca_joint__selected"] = "" if joint is None else joint
        row["stca_joint__status"] = "unknown" if joint is None else "selected" if joint else "not_selected"
        rows.append(row)
        presentation.append({k: v for k, v in row.items() if k != "stca_calculation_smiles_hcap"})
    audit = {"canonical_original_duplicate_groups": [
        {"canonical_smiles": key, "row_positions": positions}
        for key, positions in canonical_original.items() if len(positions) > 1],
        "hcap_collision_groups": [
            {"canonical_smiles": key, "row_positions": positions}
            for key, positions in canonical_cap.items()
            if len({original_identities[i] for i in positions}) > 1],
        "records_merged": 0, "records_removed": 0}
    literals = defaultdict(set)
    for _, constraint, _ in selected:
        if constraint.get("rule"):
            for key, value in zip(constraint["rule"]["keys"], constraint["rule"]["values"]):
                literals[key].add(value)
    summary = {"schema": "stca-library-screen-v1", "integration_version": "0.1.0",
               "entries": identifiers, "combiner": "AND", "input_count": len(rows),
               "valid_input_count": sum(r["stca_input_valid"] for r in rows),
               "joint_selected_count": sum(r["stca_joint__selected"] is True for r in rows),
               "joint_unknown_count": sum(r["stca_joint__selected"] == "" for r in rows),
               "requirements": totals, "literal_conflicts": sorted(k for k, v in literals.items() if len(v) > 1),
               "primary_output": "results.csv", "audit_output": "rows.csv",
               "original_smiles_preserved": True, "representation": "hcap_maccs167",
               "training_performed": False, "physical_properties_predicted": False,
               "interpretation": "Exact frozen structural-rule compliance; measured property success is not inferred."}
    output.mkdir(parents=True)
    for name, data in (("results.csv", presentation), ("rows.csv", rows)):
        with (output/name).open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader(); writer.writerows(data)
    write_json(output/"summary.json", summary)
    write_json(output/"candidate_audit.json", audit)
    write_json(output/"constraints.json", {"schema": "stca-library-intersection-v1",
               "combiner": "AND", "requirements": [c for _, c, _ in selected]})
    write_json(output/"manifest.json", {"operation": "exact_library_rule_screen",
               "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "input_path": str(input_path), "input_sha256": hashlib.sha256(raw).hexdigest(),
               "catalog_sha256": digest(library.catalog_path),
               "constraints_sha256": {i: digest(p) for i, _, p in selected},
               "python": sys.executable, "rdkit_version": rdBase.rdkitVersion,
               "training_performed": False, "author_source_download_required": False})
    print(json.dumps({"output_directory": str(output), **summary}, ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-dir", default=str(DEFAULT_LIBRARY))
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List library metadata without scientific dependencies")
    listing.add_argument("--property")
    listing.add_argument("--direction", choices=("high", "low"))
    showing = commands.add_parser("show", help="Read one entry and its exact frozen conditions")
    showing.add_argument("id")
    prompting = commands.add_parser("prompt", help="Copy the stored prompt verbatim for the host LLM")
    prompting.add_argument("id")
    prompting.add_argument("--language", choices=("en", "zh-CN"), default="zh-CN")
    prompting.add_argument("--output")
    screening = commands.add_parser("screen", help="Apply one or more exact library rules to the same candidate rows")
    screening.add_argument("id", nargs="+")
    screening.add_argument("--input", required=True)
    screening.add_argument("--smiles-column", default="SMILES")
    screening.add_argument("--id-column")
    screening.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        library = RuleLibrary(args.library_dir)
        if args.command == "list":
            entries = [e for e in library.entries.values()
                       if (not args.property or str(e.get("property", "")).casefold() == args.property.casefold()
                           or str(e.get("property_zh", "")).casefold() == args.property.casefold())
                       and (not args.direction or e.get("direction") == args.direction)]
            print(json.dumps({"schema": CATALOG_SCHEMA, "version": library.catalog.get("version"),
                              "entries": entries}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "show":
            constraints, _ = library.constraints(args.id)
            print(json.dumps({"entry": library.entry(args.id), "constraints": constraints}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "prompt":
            payload, source = library.prompt(args.id, args.language)
            if args.output:
                destination = Path(args.output).expanduser().resolve()
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as handle:
                    handle.write(payload)
                print(json.dumps({"output": str(destination), "language": args.language,
                                  "content_sha256": hashlib.sha256(payload).hexdigest()}, ensure_ascii=False))
            else:
                if hasattr(sys.stdout, "buffer"):
                    sys.stdout.buffer.write(payload)
                else:
                    sys.stdout.write(payload.decode("utf-8"))
            return 0
        return screen(library, args.id, args)
    except (ValueError, OSError, ImportError, TypeError, KeyError) as exc:
        print(f"stca-library: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
