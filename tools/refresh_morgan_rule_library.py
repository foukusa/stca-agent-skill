#!/usr/bin/env python3
"""Freeze source-fitted models with independently verified Morgan holdout evidence.

Input: {"runs": [{"dataset_id": "PI_RHO", "run_dir": "/absolute/run"}, ...]}.
Source-inner scores select the recommended learner. Holdout scores are reported
separately and never choose a rule, percentage, scan setting or learner.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys

from refresh_current_rule_library import (
    encoded, identifier, key, native_metric, read, sha, contained, evidence_root,
)

CONTRACT = "strict_morgan_source_v1"
DEFAULT_TIERS = (0.1, 0.2, 0.3)
METRICS = ("precision", "recall", "f1", "mcc", "AS")


def validate_split(audit):
    """Reject a CV diagnostic or incomplete separation masquerading as holdout."""
    if audit.get("status") != "available":
        raise ValueError("Strict Morgan split is not available; no rules may be advertised as extrapolation-validated.")
    fp = audit.get("fingerprint", {})
    if (fp.get("family") != "Morgan" or fp.get("radius") != 2
            or fp.get("bits") != 2048 or fp.get("metric") != "1-Tanimoto"):
        raise ValueError("Expected exact ECFP4 radius-2/2048-bit Tanimoto distances.")
    if audit.get("target_values_used") is not False or audit.get("candidate_ids_used") is not False:
        raise ValueError("Holdout membership must be determined without target labels or arbitrary candidate IDs.")
    threshold = audit.get("distance_threshold")
    if not isinstance(threshold, (int, float)) or not 0 < threshold <= 1:
        raise ValueError("Missing strict nearest-source distance threshold.")
    minimum = audit.get("nearest_source_distance_min")
    if (audit.get("every_holdout_meets_distance") is not True
            or not isinstance(minimum, (int, float)) or minimum + 1e-12 < threshold):
        raise ValueError("At least one holdout violates the nearest-source distance contract.")
    if audit.get("protected_group_overlap_n") != 0 or audit.get("buffer_used_for_learning") is not False:
        raise ValueError("Protected groups or separating buffer leaked into source training.")
    return copy.deepcopy(audit)


def source_evidence_root(run, method, fraction):
    source_fit = run / "source_fit"
    summary = read(source_fit / "screening_summary.json")
    tier = next(item for item in summary["tiers"] if float(item["fraction"]) == fraction)
    constraints = contained(source_fit, tier["methods"][method]["constraints"])
    return evidence_root(source_fit, constraints), constraints


def template_for(dataset, method, direction, fraction, old, registry):
    name = identifier(dataset, method, direction, fraction)
    if name in old:
        return copy.deepcopy(old[name])
    if dataset != "OPENPOLY_WCA":
        raise ValueError(f"No public catalog template for dataset {dataset}.")
    return {"id": name, "property": "Water contact angle", "property_zh": "水接触角",
            "direction": direction, "tier": fraction, "unit": registry["unit"],
            "dataset": dataset, "method": method, "learner": method}


def reference_metrics(tier, method_result, audit, source_cv, source_inner=None):
    """Keep held-out, source-inner and all-input screening numbers disjoint."""
    held = method_result.get("holdout_metrics", method_result.get("holdout", {}))
    if not held.get("status"):
        raise ValueError("Missing actual independent holdout evaluation status.")
    if held.get("physical_cutoff") != tier["physical_cutoff"]:
        raise ValueError("Holdout scoring must retain the source-frozen physical cutoff.")
    evaluable = held.get("status") == "evaluated"
    reference = {
        "status": "strict_morgan_holdout_evaluated" if evaluable else "strict_morgan_holdout_inconclusive",
        "evaluation_kind": "strict_morgan_distance_holdout",
        "evaluation_scope": "Independent original holdout labels; all label-dependent preparation and rule fitting use source records only.",
        "evidence_source": "current_profile_evidence.json", "experiment_id": CONTRACT,
        "fit_scope": "source_only_frozen_model", "cutoff_scope": "source_only",
        "distance_metric": "1-Tanimoto", "distance_threshold": audit["distance_threshold"],
        "minimum_holdout_nearest_source_distance": audit["nearest_source_distance_min"],
        "every_holdout_meets_distance": True, "source_n": audit["source_n"],
        "holdout_n": audit["holdout_n"], "buffer_n": audit["buffer_n"],
        "buffer_used_for_learning": False, "protected_group_overlap_n": 0,
        "physical_cutoff": tier["physical_cutoff"], "physical_unit": tier["unit"],
        "AS_definition": "(MCC + Precision + F1) / 3", "evaluable": evaluable,
        "holdout_metrics": held,
        "method_recommendation_scope": "source_inner_strict_morgan_validation_before_outer_holdout",
        "source_inner_evaluation_status": (source_inner or {}).get("status", "unavailable"),
        "source_inner_evaluation_scope": "Strict Morgan validation partition made within outer source only; outer holdout remains untouched.",
        "source_inner_metrics": copy.deepcopy(source_inner or {}),
        "source_grouped_cv_evaluation_scope": "Diagnostic grouped CV conditional on source-only preparation; not outer extrapolation or method recommendation.",
        "screened_input_n": method_result["original_input_n"],
        "screened_input_selected_n": method_result["selected_n"],
        "screened_input_unknown_n": method_result["unknown_n"],
    }
    for metric in METRICS:
        reference[f"holdout_{metric}"] = held.get(metric)
        reference[f"source_inner_{metric}"] = (source_inner or {}).get(metric)
        reference[f"source_grouped_cv_{metric}"] = source_cv.get(f"{metric}_mean")
        reference[f"source_grouped_cv_{metric}_sd"] = source_cv.get(f"{metric}_sd")
    return reference


def make_provenance(dataset, method, tier, registry, outer, source, audit, evroot, source_settings):
    per_tier = source.get("per_tier_preparation", {}).get(key(tier), {})
    tier_settings = source_settings.get("preparation_by_tier", {}).get(key(tier), source_settings)
    return {
        "kind": "source_fitted_distance_holdout_rules", "contract": CONTRACT,
        "dataset": dataset, "learner": method, "source": registry["public_source"],
        "source_commit": registry.get("source_commit"), "source_paper_doi": registry.get("source_paper_doi"),
        "data_kind": registry["data_kind"], "source_input_sha256": outer["input_sha256"],
        "training_input_sha256": source["input_sha256"],
        "input_record_n": outer.get("original_input_row_n", outer.get("original_input_rows")),
        "training_record_n": per_tier.get("prepared_measurement_n", source.get("prepared_measurement_n")),
        "source_record_n": audit["source_n"], "holdout_record_n": audit["holdout_n"], "buffer_record_n": audit["buffer_n"],
        "fit_scope": "source_only_frozen_model", "cutoff_scope": "source_only", "tier_independent": True,
        "original_repeat_unit_identity_preserved": True, "hcap_structure_not_used_to_merge_materials": True,
        "tier": tier, "structural_role_fingerprint": {"name": "ECFP4", "kind": "Morgan", "radius": 2, "n_bits": 2048},
        "rule_fingerprint": "Hcap_MACCS167", "transform": tier_settings.get("transform"),
        "scan": tier_settings.get("scan"), "WRAcc_search": source_settings.get("WRAcc_search") if method == "WRAcc" else None,
        "evaluation_scope": "strict_morgan_distance_holdout", "distance_threshold": audit["distance_threshold"],
        "minimum_holdout_nearest_source_distance": audit["nearest_source_distance_min"],
        "protected_group_n": audit["protected_group_n"],
        "entrypoint_sha256": outer.get("entrypoint_sha256"),
        "preparation_audit_sha256": per_tier.get("preparation_audit_sha256", source.get("preparation_audit_sha256")),
        "fingerprint_matrix_sha256": per_tier.get("fingerprint_contract", source.get("fingerprint_contract", {})).get("matrix_sha256"),
        "source_run_summary_sha256": sha((evroot / "screening_summary.json").read_bytes()),
        "split_audit_sha256": sha(encoded(audit)),
    }


def refresh(args):
    repository = Path(args.repository).expanduser().resolve()
    skill = Path(args.skill).expanduser().resolve()
    root = skill / "assets/rule_library"
    catalog = read(root / "catalog.json")
    old = {entry["id"]: entry for entry in catalog["entries"]}
    with (repository / "examples/open_data/dataset_registry.csv").open(encoding="utf-8-sig") as handle:
        registry = {row["dataset"]: row for row in csv.DictReader(handle)}
    spec = read(args.spec)
    sys.path.insert(0, str(skill / "scripts"))
    from generation_prompt import render_prompt
    from rule_library import RuleLibrary

    protected = {relative: sha((root / relative).read_bytes()) for entry in catalog["entries"]
                 if entry["id"].startswith("paper-") for relative in [entry["constraints"], *entry["prompts"].values()]}
    updated, records, plans, seen = [], [], {}, set()
    splits = {}
    for supplied in spec["runs"]:
        dataset = supplied["dataset_id"]
        if dataset not in registry:
            raise ValueError(f"Unknown dataset: {dataset}")
        run = Path(supplied["run_dir"]).expanduser().resolve()
        summary = read(run / "screening_summary.json")
        if summary.get("holdout_used_for_method_or_tier_selection") is not False:
            raise ValueError("Outer holdout must not choose a method or percentage.")
        outer = read(run / "run_manifest.json")
        if (outer.get("entrypoint") != "morgan_evaluation.py"
                or outer.get("all_target_dependent_preparation_fit_scope") != "source_only"
                or outer.get("holdout_labels_used_for_fit_or_selection") is not False
                or outer.get("buffer_used_for_fit_or_selection") is not False):
            raise ValueError("Run did not establish source-only preparation and untouched holdout/buffer.")
        audit = validate_split(read(run / "split_audit.json"))
        inner_selection = read(run / "source_inner_selection.json")
        if (inner_selection.get("scope") != "source_only_strict_morgan_validation"
                or inner_selection.get("holdout_labels_used") is not False):
            raise ValueError("Method recommendation must be fitted inside source only.")
        splits[dataset] = audit
        requested = {float(q) for q in supplied.get("tiers", DEFAULT_TIERS)}
        for tier in summary["tiers"]:
            q = float(tier["fraction"])
            if q not in requested:
                continue
            pair = (dataset, q)
            if pair in seen:
                raise ValueError(f"Duplicate dataset/tier: {pair}")
            seen.add(pair)
            primary = tier.get("recommended_method")
            for method in ("STCA", "WRAcc"):
                method_result = tier["methods"][method]
                constraints_path = contained(run, method_result["constraints"])
                exported = read(constraints_path)
                evroot, source_constraints = source_evidence_root(run, method, q)
                source_exported = read(source_constraints)
                if (exported.get("rule") != source_exported.get("rule")
                        or exported.get("target", {}).get("physical_cutoff") != source_exported.get("target", {}).get("physical_cutoff")):
                    raise ValueError("Delivered frozen rule or cutoff differs from source-only fitted artifact.")
                if sha((run / method.lower() / "model.json").read_bytes()) != sha((run / "source_fit" / method.lower() / "model.json").read_bytes()):
                    raise ValueError("Delivered model differs from source-only fitted model.")
                source_manifest = read(evroot / "run_manifest.json")
                if source_manifest.get("status") not in ("completed", "completed_with_storage_warning"):
                    raise ValueError(f"Source fitting incomplete: {evroot}")
                cv = read(evroot / "cv_summary.json")["methods"][method][key(q)]
                representation = exported.get("representation") or exported.get("model", {}).get("custom_data_contract", {}).get("representation")
                if representation != "hcap_maccs167":
                    raise ValueError(f"Expected Hcap MACCS167 source rule: {constraints_path}")
                template = template_for(dataset, method, summary["direction"], q, old, registry[dataset])
                name = template["id"]
                provenance = make_provenance(dataset, method, q, registry[dataset], outer, source_manifest,
                                             audit, evroot, source_manifest["learning_settings"])
                inner_tier = inner_selection.get("tiers", {}).get(key(q), {})
                inner_metrics = inner_tier.get(method, {})
                reference = reference_metrics(tier, method_result, audit, cv, inner_metrics)
                reference["source_inner_selection_status"] = inner_tier.get("status", inner_selection.get("status"))
                reference["source_inner_selection_reason"] = inner_tier.get("reason", inner_selection.get("reason"))
                rule = copy.deepcopy(exported.get("rule"))
                available = bool(rule and rule.get("keys"))
                is_primary = method == primary and available
                alternative = identifier(dataset, "WRAcc" if method == "STCA" else "STCA", summary["direction"], q)
                role = "primary" if is_primary else "alternative"
                entry = copy.deepcopy(template)
                entry.update(preferred=is_primary, user_visible=True, legacy=False,
                             status=exported.get("status"), available=available, is_primary=is_primary,
                             method_role=role, alternative_id=alternative,
                             primary_id=identifier(dataset, primary, summary["direction"], q) if primary else None,
                             title=f"{dataset} · {method}: {template['property']}, {'Top' if summary['direction']=='high' else 'Bottom'} {q*100:g}% ({role})",
                             title_zh=f"{dataset} · {method}：{template['property_zh']}，{'Top' if summary['direction']=='high' else 'Bottom'} {q*100:g}%（{'主推' if is_primary else '备选'}）",
                             constraints=f"entries/{name}/constraints.json",
                             prompts={lang: f"entries/{name}/prompt.{lang}.md" for lang in ("en", "zh-CN")},
                             provenance=provenance, reference_evaluation=reference, experiment_id=CONTRACT,
                             recommendation_reason=tier.get("recommendation_reason"))
                for obsolete in ("supersedes", "source_inner_eligible", "source_recommended_tier"):
                    entry.pop(obsolete, None)
                target = copy.deepcopy(exported["target"])
                target.update(name=template["property"], unit=tier["unit"], physical_cutoff=tier["physical_cutoff"],
                              model_cutoff=target.get("model_space_cutoff"), model_unit=target.get("model_space_unit", tier["unit"]),
                              operator=tier["operator"], cutoff_scope="source_only")
                payload = {
                    "schema": "stca-library-constraints-v1", "version": "0.1.0", "status": exported.get("status"),
                    "catalog_id": name, "property": template["property"], "property_zh": template["property_zh"],
                    "dataset_id": dataset, "learner": method, "method": method, "direction": summary["direction"],
                    "tier": q, "tier_fraction": q, "is_primary": is_primary, "alternative_id": alternative,
                    "representation": "hcap_maccs167", "structure_kind": "polymer_repeat_unit",
                    "metadata": {"model_type": "frozen_literal_rule", "learner": method, "kind": CONTRACT},
                    "model": {"model_type": "frozen_literal_rule", "learner": method,
                              "origin": {"kind": CONTRACT, "dataset_id": dataset, "name": name},
                              "frozen_rule_sha256": sha(encoded(rule)), "provenance": provenance,
                              "custom_data_contract": copy.deepcopy(exported["model"].get("custom_data_contract", {}))},
                    "target": target, "feature_spec": copy.deepcopy(exported["feature_spec"]),
                    "feature_names": copy.deepcopy(exported["feature_names"]), "combiner": "AND", "rule": rule,
                    "literals": copy.deepcopy(exported.get("literals", [])),
                    "require_present": copy.deepcopy(exported.get("require_present", [])),
                    "require_absent": copy.deepcopy(exported.get("require_absent", [])),
                    "provenance": provenance, "reference_evaluation": reference,
                    "interpretation": exported.get("interpretation"), "tier_interpretation": exported.get("tier_interpretation"),
                }
                payload["feature_spec"]["smiles_policy"] = "H-cap calculation copy only; original star repeat-unit SMILES preserved."
                plans[entry["constraints"]] = encoded(payload)
                for language in ("en", "zh-CN"):
                    prompt = render_prompt(payload, language=language, count=20, structure_kind="polymer_repeat_unit") if available else (
                        "No valid frozen rule was learned; generation is unavailable.\n" if language == "en" else "该目标未学得有效冻结结构规则，当前不能据此生成。\n")
                    plans[entry["prompts"][language]] = prompt.encode()
                updated.append(entry)
                record = {"id": name, "dataset": dataset, "method": method, "tier": q, "primary": is_primary,
                          "cutoff": tier["physical_cutoff"], "operator": tier["operator"], "unit": tier["unit"],
                          "input_n": method_result["original_input_n"], "source_n": audit["source_n"],
                          "prepared_source_n": provenance["training_record_n"], "holdout_n": audit["holdout_n"],
                          "buffer_n": audit["buffer_n"], "selected_n": method_result["selected_n"],
                          "unknown_n": method_result["unknown_n"], "available": available,
                          "distance_threshold": audit["distance_threshold"], "holdout_d_min": audit["nearest_source_distance_min"],
                          "holdout_status": reference["holdout_metrics"].get("status"),
                          "source_inner_AS": inner_metrics.get("AS"), "source_inner_status": inner_metrics.get("status"),
                          "source_grouped_cv_AS": cv.get("AS_mean"), "source_grouped_cv_AS_sd": cv.get("AS_sd"),
                          "transform": provenance["transform"], "scan": provenance["scan"],
                          "rule": method_result.get("rule"), "status": method_result.get("status"),
                          "source_input_sha256": provenance["source_input_sha256"],
                          "fingerprint_matrix_sha256": provenance["fingerprint_matrix_sha256"]}
                for metric in (*METRICS, "n", "positive_n", "negative_n", "selected_n", "tp", "fp", "fn", "tn"):
                    record[f"holdout_{metric}"] = reference["holdout_metrics"].get(metric)
                record["holdout_structure_n"] = audit["holdout_n"]
                record["holdout_valid_target_n"] = reference["holdout_metrics"].get("holdout_valid_target_n")
                record["holdout_evaluated_n"] = reference["holdout_metrics"].get("holdout_evaluated_n")
                record["holdout_unknown_prediction_n"] = reference["holdout_metrics"].get("holdout_unknown_prediction_n")
                records.append(record)
    expected = {(dataset, q) for dataset in registry for q in DEFAULT_TIERS}
    if not args.allow_partial and seen != expected:
        raise ValueError(f"Expected all registered dataset/tier pairs; missing={sorted(expected-seen)}, extra={sorted(seen-expected)}")
    ids = {e["id"] for e in updated}
    retained = [e for e in catalog["entries"] if e["id"].startswith("paper-")]
    if args.allow_partial:
        retained += [e for e in catalog["entries"] if e["id"].startswith("current-") and e["id"] not in ids]
    catalog["entries"] = retained + updated
    current = [e for e in catalog["entries"] if e["id"].startswith("current-")]
    available_n = sum(bool(e.get("available")) for e in current)
    catalog.update(current_contract=CONTRACT, latest_evidence="current_profile_evidence.json",
                   evidence_scope="Paper rules retain author conditions. Current open-data rules are frozen source-only models evaluated on an independent ECFP4/Tanimoto distance-separated holdout; source-internal scores choose the recommended method.",
                   counts={"retained": len(catalog["entries"]), "visible": len(catalog["entries"]),
                           "published_visible": len([e for e in retained if e["id"].startswith("paper-")]),
                           "current_visible": len(current), "latest_visible": 0, "current_available_rules": available_n,
                           "current_unavailable_results": len(current)-available_n, "legacy_hidden": 0,
                           "current_primary_by_learner": {m: sum(e.get("is_primary") is True and e["method"] == m for e in current) for m in ("STCA", "WRAcc")}})
    evidence = {"schema": "stca-current-morgan-catalog-evidence-v1", "contract": CONTRACT,
                "method_recommendation_scope": "source_inner_strict_morgan_validation_before_outer_holdout",
                "holdout_used_for_method_choice": False, "splits": splits, "rules": records}
    plans["catalog.json"] = encoded(catalog)
    plans["current_profile_evidence.json"] = encoded(evidence)
    plans["index.md"] = build_index(catalog, root, plans)
    if args.apply:
        for relative, payload in plans.items():
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        keep = {e["id"] for e in catalog["entries"]}
        for directory in (root / "entries").iterdir():
            if directory.is_dir() and directory.name not in keep:
                shutil.rmtree(directory)
        for relative, digest in protected.items():
            if sha((root / relative).read_bytes()) != digest:
                raise AssertionError(f"Author paper payload changed: {relative}")
        library = RuleLibrary(root)
        for entry in updated:
            constraint, _ = library.constraints(entry["id"])
            if entry["available"]:
                for language in ("en", "zh-CN"):
                    saved, _ = library.prompt(entry["id"], language)
                    assert saved.decode() == render_prompt(constraint, language=language, count=20, structure_kind="polymer_repeat_unit")
        (repository / "validation/current_open_data_rules.json").write_bytes(encoded(evidence))
        write_csv(repository / "examples/open_data/current_rule_metrics.csv", records)
        write_csv(repository / "examples/open_data/current_morgan_cases.csv", records)
        update_density_example(skill, repository, catalog, render_prompt)
    return {"applied": args.apply, "contract": CONTRACT, "datasets": len(splits),
            "dataset_tier_pairs": len(seen), "new_rules": len(updated),
            "paper_payloads_verified": len(protected), "planned_files": len(plans), "counts": catalog["counts"]}


def write_csv(path, rows):
    compact = [{k: (json.dumps(v, ensure_ascii=False, separators=(",", ":")) if isinstance(v, (dict, list)) else v)
                for k, v in row.items()} for row in rows]
    if not compact:
        return
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(compact[0]))
    writer.writeheader()
    writer.writerows(compact)
    path.write_text(output.getvalue(), encoding="utf-8")


def build_index(catalog, root, plans):
    lines = ["# STCA rule and prompt library", "", "Choose a property, source and percentage; use each complete AND rule as stored.", "",
             "Open-data rules use source-only learning and strict ECFP4/Tanimoto distance-separated holdout evaluation. Method recommendations use source-internal scores; independent holdout scores remain separate.", "",
             "| Rule ID | Source / property | Method | Percentage / boundary | Role |", "|---|---|---|---|---|"]
    for entry in catalog["entries"]:
        name = entry["constraints"]
        target = json.loads(plans[name])["target"] if name in plans else read(root / name)["target"]
        boundary = f"{'Top' if entry['direction']=='high' else 'Bottom'} {entry['tier']*100:g}%; {target['operator']} {target['physical_cutoff']:.10g} {entry['unit']}"
        role = "paper rule" if entry["id"].startswith("paper-") else entry["method_role"] if entry.get("available") else "no valid rule; generation unavailable"
        lines.append(f"| `{entry['id']}` | {entry['dataset']} / {entry['property']} | {entry.get('method','STCA')} | {boundary} | {role} |")
    return ("\n".join(lines) + "\n").encode()


def update_density_example(skill, repository, catalog, render_prompt):
    entries = {e["id"]: e for e in catalog["entries"]}
    ids = [f"current-pi-rho-{m}-high-30" for m in ("stca", "wracc")]
    if any(name not in entries or entries[name].get("experiment_id") != CONTRACT for name in ids):
        return
    constraints = {name: read(skill / "assets/rule_library" / entries[name]["constraints"]) for name in ids}
    path = skill / "assets/examples/radonpy_density_case.json"
    case = read(path)
    def display(name):
        c = constraints[name]
        ref = c["reference_evaluation"]
        return {"id": name, "method": c["method"], "fraction": 0.3,
                "physical_operator": c["target"]["operator"], "physical_cutoff": c["target"]["physical_cutoff"],
                "rule": c["rule"]["expression"] if c.get("rule") else None,
                "expected_selected": ref["screened_input_selected_n"],
                "expected_not_selected": ref["screened_input_n"] - ref["screened_input_selected_n"] - ref["screened_input_unknown_n"],
                "expected_unknown": ref["screened_input_unknown_n"],
                "physical_cutoff_policy": "keep_frozen_source_cutoff; never_recalculate_from_candidate_table",
                "independent_holdout": ref["holdout_metrics"], "minimum_holdout_distance": ref["minimum_holdout_nearest_source_distance"]}
    primary = next((name for name in ids if entries[name].get("is_primary")), None)
    if primary:
        alternative = next(name for name in ids if name != primary)
        case["existing_rule"] = display(primary)
        case["alternative_method_rule"] = display(alternative)
        case["recommended_method"] = constraints[primary]["method"]
    stca = constraints[ids[0]]
    case["relearn"].update(entrypoint="morgan_evaluation.py", contract=CONTRACT,
                          distance_threshold=0.5, holdout_fraction=0.2,
                          fit_scope="source_only_frozen_model", tier_independent=True,
                          expected_top30_transform=stca["provenance"]["transform"], expected_top30_scan=stca["provenance"]["scan"],
                          required_receipts=["run_manifest.json", "split_audit.json", "split_membership.csv", "holdout_metrics.json", "screening_summary.json", "source_fit/run_manifest.json"],
                          comparison="same_source_columns_distance_protocol_and_default_settings_reproduce_current_bundled_rule")
    path.write_bytes(encoded(case))
    (repository / "examples/radonpy_density/case.json").write_bytes(encoded(case))
    tasks_path = skill / "assets/starter_tasks.json"
    tasks = read(tasks_path)
    for example in tasks.get("example_cases", []):
        if example.get("id") == "radonpy_density" and primary:
            example["preferred_builtin_rule"] = primary
    tasks_path.write_bytes(encoded(tasks))
    if stca.get("rule"):
        for language in ("en", "zh-CN"):
            (repository / f"examples/radonpy_density/generation_prompt.{language}.md").write_text(
                render_prompt(stca, language=language, count=5, structure_kind="polymer_repeat_unit"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    print(json.dumps(refresh(parser.parse_args()), ensure_ascii=False, indent=2))
