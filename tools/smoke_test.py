#!/usr/bin/env python3
"""Run the public STCA candidate fixture through the actual pinned workflow.

This checks H-cap, original paper EC5 screening, exact rule export, and a
same-candidate Tg20/EC5 structural intersection. It does not fit a model or
claim measured-property validation. Run with the recorded STCA interpreter.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def boolean(value: str) -> bool:
    if value.lower() not in ("true", "false"):
        raise RuntimeError(f"Expected a Boolean decision; received {value!r}.")
    return value.lower() == "true"


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, default=repo / "skills" / "stca")
    parser.add_argument("--python", default=sys.executable,
                        help="STCA interpreter path; defaults to this script's interpreter.")
    parser.add_argument("--source", type=Path,
                        help="Optional clean author checkout at the pinned revision.")
    parser.add_argument("--output-dir", type=Path,
                        help="New output directory. Defaults to a new temporary directory.")
    args = parser.parse_args()

    expected_path = repo / "examples" / "expected_screening.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    fixture = repo / "examples" / "candidates_10.csv"
    config = repo / "examples" / "joint_hcap.json"
    skill = args.skill_dir.expanduser().resolve()
    python = shutil.which(args.python) or os.path.abspath(os.path.expanduser(args.python))
    require(Path(python).is_file(), "The requested Python interpreter does not exist.")
    require((skill / "SKILL.md").is_file(), "--skill-dir must contain SKILL.md.")
    require(sha256(fixture) == expected["input_sha256"],
            "The public candidate fixture differs from the audited reference bytes.")

    if args.output_dir:
        out = args.output_dir.expanduser().resolve()
        out.mkdir(parents=True, exist_ok=False)
    else:
        out = Path(tempfile.mkdtemp(prefix="stca-smoke-"))
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    if args.source:
        env["STCA_SOURCE"] = str(args.source.expanduser().resolve())

    command_records: list[dict] = []

    def run(label: str, script: str, arguments: list[str]) -> str:
        command = [python, str(skill / "scripts" / script), *arguments]
        started = time.monotonic()
        result = subprocess.run(command, env=env, text=True, encoding="utf-8",
                                capture_output=True, check=False)
        (out / f"{label}.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (out / f"{label}.stderr.txt").write_text(result.stderr, encoding="utf-8")
        command_records.append({"step": label, "command": command,
                                "returncode": result.returncode,
                                "seconds": round(time.monotonic() - started, 3)})
        (out / "commands.json").write_text(
            json.dumps(command_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        require(result.returncode == 0,
                f"Step {label} failed. Read {out / (label + '.stderr.txt')}.")
        return result.stdout

    try:
        doctor = json.loads(run("01_doctor", "stca_runtime.py", ["doctor"]))
        require(doctor["commit"] == expected["upstream_commit"],
                "The author source revision differs from the release reference.")
        require(doctor["packages"]["rdkit"] == expected["rdkit_distribution_version"],
                "The RDKit distribution version differs from the release reference.")
        original_columns, original_rows = read_rows(fixture)
        ids = [row["ID"] for row in original_rows]
        require(ids == expected["row_order"], "Fixture IDs or row order changed.")
        expected_by_id = {row["ID"]: row for row in expected["candidates"]}

        hcap = out / "candidates_hcap.csv"
        run("02_hcap", "prepare_hcap.py", ["--input", str(fixture), "--output", str(hcap),
            "--id-column", "ID", "--smiles-column", "SMILES", "--output-column", "SMILES_hcap"])
        cap_columns, cap_rows = read_rows(hcap)
        require(len(cap_rows) == len(original_rows), "H-cap changed the number of rows.")
        require(cap_columns[:len(original_columns)] == original_columns,
                "H-cap changed the order of original columns.")
        for original, capped in zip(original_rows, cap_rows):
            require(all(capped[key] == original[key] for key in original_columns),
                    f"H-cap changed an original value for {original['ID']}.")
            require(capped["SMILES_hcap"] == expected_by_id[original["ID"]]["SMILES_hcap"],
                    f"Unexpected H-cap calculation structure for {original['ID']}.")
        require(sha256(fixture) == expected["input_sha256"], "The original fixture was modified.")

        screened = out / "ec_low_05_screen.csv"
        run("03_screen", "stca_runtime.py", ["run", "--", "screen", "--profile", "ec-low",
            "--protocol", "paper", "--tier", "0.05", "--input", str(hcap),
            "--smiles-column", "SMILES_hcap", "--errors", "report", "--output", str(screened)])
        _, screen_rows = read_rows(screened)
        require([row["ID"] for row in screen_rows] == ids, "Screening changed ID order.")
        for row in screen_rows:
            reference = expected_by_id[row["ID"]]
            require(boolean(row["input_valid"]) == reference["input_valid"],
                    f"Unexpected validity for {row['ID']}.")
            require(boolean(row["selected"]) == reference["ec_low_05_selected"],
                    f"Unexpected frozen EC5 decision for {row['ID']}.")
            require(row["rule_signature"] == expected["ec_low_05_rule_signature"],
                    "The EC5 representative rule changed.")
            require(row["unexpected_present"] == reference["unexpected_present"],
                    f"Unexpected EC5 failed-absence condition for {row['ID']}.")
            require(row["missing_required_present"] == reference["missing_required_present"],
                    f"Unexpected EC5 failed-presence condition for {row['ID']}.")

        rules = out / "ec_low_05_rules"
        run("04_export", "stca_tools.py", ["export-rules", "--profile", "ec-low", "--protocol",
            "paper", "--tier", "0.05", "--output-dir", str(rules)])
        constraints = json.loads((rules / "constraints.json").read_text(encoding="utf-8"))
        require(constraints["combiner"] == "AND", "The rule combiner is no longer AND.")
        require(constraints["rule"]["signature"] == expected["ec_low_05_rule_signature"],
                "Exported EC5 rule differs from the expected representative.")
        require(constraints["model"]["artifact_sha256"] == expected["ec_low_model_artifact_sha256"],
                "The frozen EC model content changed.")
        require(math.isclose(constraints["target"]["reference_train_cutoff"],
                             expected["ec_low_05_training_cutoff_log10_S_per_cm"],
                             abs_tol=1e-12, rel_tol=0.0), "The saved EC5 training cutoff changed.")
        require(sorted(constraints["require_present"]) == sorted(expected["ec_low_05_require_present"]),
                "Exported required-presence keys changed.")
        require(sorted(constraints["require_absent"]) == sorted(expected["ec_low_05_require_absent"]),
                "Exported required-absence keys changed.")
        require((rules / "prompt.md").is_file(), "The prompt export is missing.")

        joint = out / "joint_screen"
        run("05_joint", "stca_tools.py", ["joint-screen", "--input", str(hcap), "--config", str(config),
            "--output-dir", str(joint)])
        _, joint_rows = read_rows(joint / "rows.csv")
        joint_summary = json.loads((joint / "summary.json").read_text(encoding="utf-8"))
        require([row["ID"] for row in joint_rows] == ids, "Joint screening changed ID order.")
        for row in joint_rows:
            reference = expected_by_id[row["ID"]]
            require(boolean(row["stca_high_tg__selected"]) == reference["tg_high_20_selected"],
                    f"Unexpected Tg20 decision for {row['ID']}.")
            require(boolean(row["stca_low_ec__selected"]) == reference["ec_low_05_selected"],
                    f"Joint screen changed the EC5 decision for {row['ID']}.")
            require(boolean(row["stca_joint__selected"]) == reference["joint_selected"],
                    f"Unexpected joint structural decision for {row['ID']}.")
        require(joint_summary["joint_selected_count"] == expected["counts"]["joint_selected"],
                "The joint selection count changed.")
        require(joint_summary["invalid_input_count"] == 0, "Unexpected invalid joint inputs.")
        require(joint_summary["joint_unknown_count"] == 0, "Unexpected unknown joint decisions.")

        selected = [row["ID"] for row in screen_rows if boolean(row["selected"])]
        report = {
            "status": "PASS",
            "test_scope": "H-cap, frozen paper EC5 screening, rule export, same-candidate Tg20/EC5 intersection",
            "upstream_commit": doctor["commit"],
            "python_version": doctor["python_version"],
            "packages": doctor["packages"],
            "input_sha256": expected["input_sha256"],
            "input_count": len(original_rows),
            "valid_count": sum(boolean(row["input_valid"]) for row in screen_rows),
            "ec_low_05_selected_count": len(selected),
            "ec_low_05_selected_ids": selected,
            "joint_selected_count": joint_summary["joint_selected_count"],
            "original_columns_and_order_preserved": True,
            "original_input_unchanged": True,
            "frozen_model_content_matched": True,
            "training_performed": False,
            "measured_property_evaluation_performed": False,
            "interpretation": "Structural integration regression only; no physical property or novelty guarantee.",
        }
        (out / "smoke_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
        print(json.dumps({"status": "PASS", "selected": len(selected), "input": len(original_rows),
                          "output_directory": str(out)}, ensure_ascii=False))
        return 0
    except Exception as exc:
        (out / "smoke_report.json").write_text(
            json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"STCA smoke test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
