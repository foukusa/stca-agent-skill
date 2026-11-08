"""Apply a newly frozen STCA model to every original uploaded observation.

This reporting adapter reuses ``stca_tools screen-candidates``. It neither fits
rules nor uses application counts to choose settings, percentages or splits.
Rows excluded from fitting remain eligible for structural-rule application.
"""
from __future__ import annotations

from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
from pathlib import Path


def _write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def _columns(original_columns):
    """Keep even user-supplied stca_ fields; never overwrite an input field."""
    fields = (
        "input_row_position", "role", "used_for_training", "used_for_evaluation",
        "cleaning_excluded", "exclusion_reason", "duplicate_of_input_row",
        "evidence", "tier", "property", "direction", "cutoff_model_space",
        "model_unit", "cutoff_physical", "physical_unit", "operator",
        "selected", "status", "reason", "input_valid", "input_error",
        "rule_status", "rule_name", "rule_signature", "failed_conditions",
    )
    occupied = set(original_columns)
    mapping = {}
    for field in fields:
        base = "stca_learning_" + field
        candidate, suffix = base, 2
        while candidate in occupied:
            candidate = f"{base}_{suffix}"
            suffix += 1
        occupied.add(candidate)
        mapping[field] = candidate
    return mapping


def _positions(frame, membership, excluded, cleaning, source_value, evaluation_value):
    """Only actual retained source/holdout memberships confer those roles."""
    n = len(frame)
    included = set(cleaning["row_mapping"]["cleaned_original_positions"])
    removed = set(cleaning["row_mapping"]["excluded_original_positions"])
    if included & removed or included | removed != set(range(n)):
        raise ValueError("Cleaning row mapping does not partition every uploaded row.")
    assigned = {}
    if "input_row_position" not in membership or "role" not in membership:
        raise ValueError("Split membership lacks original row positions or roles.")
    for row in membership.to_dict("records"):
        position = int(row["input_row_position"])
        if position not in included or position in assigned:
            raise ValueError("Split membership has duplicate or excluded original row positions.")
        value = row["role"]
        if value not in (source_value, evaluation_value):
            raise ValueError(f"Unrecognized retained data role {value!r}.")
        assigned[position] = "source" if value == source_value else "holdout"
    if set(assigned) != included:
        raise ValueError("Split membership does not cover exactly the retained upload rows.")
    position_column = cleaning["row_position_column"]
    reason_column = cleaning["exclusion_reason_column"]
    duplicate_column = cleaning["duplicate_reference_column"]
    exclusions = {int(row[position_column]): row for row in excluded.to_dict("records")}
    if set(exclusions) != removed:
        raise ValueError("Excluded-row table disagrees with the cleaning row mapping.")
    result = []
    for position in range(n):
        role = assigned.get(position, "unassigned")
        exclusion = exclusions.get(position, {})
        result.append({
            "input_row_position": position, "role": role,
            "used_for_training": role == "source",
            "used_for_evaluation": role == "holdout",
            "cleaning_excluded": position in removed,
            "exclusion_reason": exclusion.get(reason_column, ""),
            "duplicate_of_input_row": exclusion.get(duplicate_column, ""),
            "evidence": {"source": "source_resubstitution",
                         "holdout": "held_out_rule_application",
                         "unassigned": "training_excluded_rule_application"}[role],
        })
    return result


def _failed_conditions(row, rule, feature_names):
    """Expand the authoritative screen's complete mismatch lists to literals."""
    missing = set(filter(None, row["stca_screen__missing_required_present"].split(";")))
    unexpected = set(filter(None, row["stca_screen__unexpected_present"].split(";")))
    failures = []
    for key, required in zip(rule["keys"], rule["values"]):
        name = feature_names[key]
        mismatch = missing if required == 1 else unexpected
        if name in mismatch:
            mismatch.remove(name)
            failures.append({"key": int(key), "feature": name,
                             "required": int(required), "observed": 1 - int(required)})
    if missing or unexpected:
        raise ValueError("Screen returned mismatches outside the frozen representative.")
    selected = _boolean(row["stca_screen__selected"], "selected")
    if selected == bool(failures):
        raise ValueError("Screen selected flag and frozen-rule mismatch list disagree.")
    return failures


def _boolean(value, label):
    if value not in ("True", "False"):
        raise ValueError(f"Screen returned an unexpected {label} boolean {value!r}.")
    return value == "True"


def screen_uploaded_rows(*, frame, smiles_column, model_path, tiers, output_dir,
                         cleaning, excluded, membership, source_value="source",
                         evaluation_value="holdout", source=None,
                         input_sha256=None):
    """Write every upload row at every tier, with distinct training provenance.

    ``frame`` is the untouched text-valued, header-normalized upload. The
    cleaner's exclusion/membership mapping is authoritative for participation;
    a missing target never prevents a valid structure from being screened.
    Execution failures are contained per tier and reported without fake scores.
    """
    import pandas as pd
    import stca_tools
    from stca_io import read_csv_frame

    output = Path(output_dir).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Upload-screening output exists; choose a new directory.")
    if smiles_column not in frame:
        raise ValueError(f"Original structure column {smiles_column!r} is unavailable.")
    tiers = tuple(float(q) for q in tiers)
    if not tiers or len(set(tiers)) != len(tiers) or any(not 0 < q < 1 for q in tiers):
        raise ValueError("Specify distinct tier fractions strictly between zero and one.")
    participation = _positions(frame, membership, excluded, cleaning,
                               source_value, evaluation_value)
    model_path = Path(model_path).expanduser().resolve()
    artifact = json.loads(model_path.read_text(encoding="utf-8"))
    mapping = _columns(frame.columns)
    original_rows = frame.to_dict("records")
    output.mkdir(parents=True)
    _write_json(output / "column_mapping.json", {
        "original_columns": list(frame.columns), "result_columns": mapping,
        "original_fields_overwritten": False,
        "input_row_position_base": 0,
    })
    # No user ID is used as a unique key. Repeated/empty identifiers and reserved
    # user fields remain untouched in presentation and map by physical record.
    screen_input = output / "calculation_input.csv"
    pd.DataFrame({"SMILES": frame[smiles_column].tolist()}).to_csv(screen_input, index=False)
    long_tables, summaries = [], []
    for tier in tiers:
        key = format(float(tier), ".12g")
        tier_dir = output / "tiers" / ("tier_" + key.replace(".", "p"))
        tier_dir.mkdir(parents=True)
        entry = artifact.get("tiers", {}).get(key)
        metadata_error = None
        try:
            target = stca_tools._target_metadata(artifact, entry or {})
        except (ValueError, RuntimeError, KeyError, TypeError, AttributeError) as exc:
            metadata_error = {"error_type": type(exc).__name__, "reason": str(exc)}
            target = {"name": artifact.get("target_name"), "direction": artifact.get("direction"),
                      "model_space_cutoff": None, "model_space_unit": artifact.get("target_unit"),
                      "physical_train_cutoff": None, "physical_unit": None,
                      "label_comparison": None}
        common = {
            "tier": float(tier), "property": target["name"],
            "direction": target["direction"],
            "cutoff_model_space": target["model_space_cutoff"],
            "model_unit": target["model_space_unit"],
            "cutoff_physical": target["physical_train_cutoff"],
            "physical_unit": target["physical_unit"],
            "operator": target["label_comparison"],
        }
        rule_status, reason, tier_error = "no_valid_rule", "", None
        screened, rule = None, None
        if metadata_error:
            tier_error = metadata_error
            _write_json(tier_dir / "failure.json", tier_error)
            rule_status, reason = "screening_error", tier_error["reason"]
        elif entry is None:
            reason = f"Requested tier {tier:g} is absent from the frozen model; no interpolation."
        else:
            argv = []
            if source is not None:
                argv.extend(["--source", str(source)])
            argv.extend(["screen-candidates", "--model", str(model_path),
                         "--tier", key, "--input", str(screen_input),
                         "--smiles-column", "SMILES", "--output-dir", str(tier_dir / "screen")])
            try:
                with (tier_dir / "screen.stdout.log").open("x", encoding="utf-8") as stdout, \
                     (tier_dir / "screen.stderr.log").open("x", encoding="utf-8") as stderr, \
                     redirect_stdout(stdout), redirect_stderr(stderr):
                    code = stca_tools.main(argv)
                if code:
                    detail = (tier_dir / "screen.stderr.log").read_text().strip()
                    raise RuntimeError(f"Frozen screening exited {code}: {detail}")
                screen_dir = tier_dir / "screen"
                requirement = json.loads((screen_dir / "summary.json").read_text())["requirements"][0]
                constraint = json.loads((screen_dir / "joint_constraints.json").read_text())["requirements"][0]
                rule_status, rule = requirement["status"], constraint["rule"]
                screened = read_csv_frame(screen_dir / "results.csv").to_dict("records")
                if len(screened) != len(original_rows):
                    raise ValueError("Frozen screening did not return every uploaded row.")
                for position, row in enumerate(screened):
                    if int(row["stca_row_position"]) != position or row["SMILES"] != frame.iloc[position][smiles_column]:
                        raise ValueError("Frozen screening changed original row identity or SMILES.")
                if rule is None:
                    reason = "The requested tier has no valid frozen representative."
            except (ValueError, RuntimeError, OSError, KeyError, TypeError, ImportError) as exc:
                tier_error = {"error_type": type(exc).__name__, "reason": str(exc)}
                _write_json(tier_dir / "failure.json", tier_error)
                rule_status, reason, screened = "screening_error", str(exc), None
        result_rows = []
        try:
            for position, original in enumerate(original_rows):
                values = {**participation[position], **common, "selected": None,
                          "status": "no_valid_rule", "reason": reason,
                          "input_valid": None, "input_error": "",
                          "rule_status": rule_status,
                          "rule_name": rule["name"] if rule else None,
                          "rule_signature": rule["signature"] if rule else None,
                          "failed_conditions": "null"}
                if tier_error:
                    values["status"] = "screening_error"
                elif screened is not None:
                    row = screened[position]
                    valid = _boolean(row["stca_input_valid"], "input_valid")
                    values.update(input_valid=valid, input_error=row["stca_input_error"])
                    if not valid:
                        values.update(status="unknown", reason="Invalid or unsupported input structure; no rule decision.")
                    elif rule is None:
                        values["status"] = "no_valid_rule"
                    else:
                        selected = _boolean(row["stca_screen__selected"], "selected")
                        values.update(selected=selected, status="selected" if selected else "not_selected",
                                      failed_conditions=json.dumps(_failed_conditions(row, rule, artifact["feature_names"]), ensure_ascii=False))
                result_rows.append({**original, **{mapping[k]: v for k, v in values.items()}})
        except (ValueError, RuntimeError, KeyError, TypeError) as exc:
            # A reporting/schema inconsistency is a failed tier, never a false
            # structural prediction. Preserve its raw screen and all other tiers.
            tier_error = {"error_type": type(exc).__name__, "reason": str(exc)}
            if not (tier_dir / "failure.json").exists():
                _write_json(tier_dir / "failure.json", tier_error)
            result_rows = []
            for position, original in enumerate(original_rows):
                values = {**participation[position], **common,
                          "selected": None, "status": "screening_error", "reason": str(exc),
                          "input_valid": None, "input_error": "", "rule_status": "screening_error",
                          "rule_name": None, "rule_signature": None, "failed_conditions": "null"}
                result_rows.append({**original, **{mapping[k]: v for k, v in values.items()}})
            rule_status = "screening_error"
        table = pd.DataFrame(result_rows, columns=list(frame.columns) + list(mapping.values()))
        selected_table = table.loc[table[mapping["selected"]].eq(True)]
        table.to_csv(tier_dir / "results.csv", index=False)
        selected_table.to_csv(tier_dir / "selected.csv", index=False)
        counts = Counter(table[mapping["status"]])
        record = {**common, "rule_status": rule_status, "input_n": len(frame),
                  "selected_n": counts["selected"], "not_selected_n": counts["not_selected"],
                  "unknown_n": counts["unknown"], "no_valid_rule_n": counts["no_valid_rule"],
                  "screening_error_n": counts["screening_error"],
                  "valid_input_n": int(table[mapping["input_valid"]].eq(True).sum()),
                  "invalid_input_n": int(table[mapping["input_valid"]].eq(False).sum()),
                  "cleaning_excluded_n": len(excluded),
                  "results": str((tier_dir / "results.csv").relative_to(output)),
                  "selected_results": str((tier_dir / "selected.csv").relative_to(output)),
                  "error": tier_error}
        for role in ("source", "holdout", "unassigned"):
            role_mask = table[mapping["role"]].eq(role)
            record[role + "_n"] = int(role_mask.sum())
            record[role + "_selected_n"] = int((role_mask & table[mapping["selected"]].eq(True)).sum())
        summaries.append(record)
        long_tables.append(table)
    pd.concat(long_tables, ignore_index=True).to_csv(output / "results.csv", index=False)
    pd.DataFrame([{**r, "error": json.dumps(r["error"], ensure_ascii=False)} for r in summaries]).to_csv(output / "summary.csv", index=False)
    failed = [r["tier"] for r in summaries if r["error"]]
    unavailable = [r["tier"] for r in summaries if r["rule_status"] == "no_valid_rule"]
    status = "partial_failure" if failed else ("completed_with_unavailable_rules" if unavailable else "completed")
    summary = {
        "schema": "stca-learning-results-v1", "integration_version": "0.1.0", "status": status,
        "input_n": len(frame), "tiers": summaries, "failed_tiers": failed,
        "unavailable_rule_tiers": unavailable, "original_columns": list(frame.columns),
        "result_columns": mapping, "primary_output": "results.csv", "summary_table": "summary.csv",
        "original_smiles_preserved": True, "input_rows_dropped": 0,
        "training_exclusions_retained_for_structural_application": True,
        "excluded_role": "unassigned", "training_performed": False,
        "application_counts_used_for_tier_or_setting_selection": False,
        "physical_properties_predicted": False,
        "interpretation": "Frozen structural-rule application to all uploaded rows. Source rows are resubstitution; retained holdout rows keep their frozen role; cleaning-excluded rows are unassigned and are not holdout evaluation records. No performance metrics are calculated here.",
    }
    _write_json(output / "summary.json", summary)
    _write_json(output / "run_manifest.json", {
        "schema": "stca-learning-results-v1", "status": status,
        "model": str(model_path), "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "upload_sha256": input_sha256, "training_performed": False,
        "screening_implementation": "stca_tools.py screen-candidates",
        "original_row_mapping": "zero_based_input_record_position",
        "summary": "summary.json", "primary_output": "results.csv",
    })
    return summary
