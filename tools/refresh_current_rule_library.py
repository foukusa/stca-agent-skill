#!/usr/bin/env python3
"""Freeze current connection-preserving runs into the bundled open-data catalog.

Input: {"runs": [{"dataset_id": "PI_RHO", "run_dir": "/absolute/run"}, ...]}.
The root run's screening_summary.json supplies relative per-tier constraint
paths, so independent-tier dispatch output and singleton runs are supported.
Paper payloads are immutable. Current templates are refreshed from completed runs;
obsolete profiles are never retained or reintroduced.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys


CONTRACT = "original_connection_preserving_independent_tier_v1"
DEFAULT_TIERS = (0.1, 0.2, 0.3)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def key(tier):
    return format(float(tier), ".12g")


def identifier(dataset, method, direction, tier):
    return f"current-{dataset.lower().replace('_', '-')}-{method.lower()}-{direction}-{float(tier)*100:g}"


def contained(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Run resource escapes run directory: {relative}")
    return path


def evidence_root(run, constraints):
    for candidate in constraints.parents:
        if not candidate.is_relative_to(run):
            break
        if (candidate / "run_manifest.json").is_file() and (candidate / "cv_summary.json").is_file():
            return candidate
    raise ValueError(f"No actual per-tier run evidence for {constraints}")


def native_metric(method, tier, evroot):
    artifact = read(evroot / method.lower() / "model.json")
    entry = artifact.get("tiers", {}).get(key(tier), {})
    selected = next((r for r in entry.get("rules", [])
                     if r.get("rule", {}).get("name") == entry.get("selected_rule")), {})
    return selected.get("source_metrics", {})


def compact_provenance(dataset, method, tier, manifest, registry, evroot):
    settings = manifest.get("learning_settings", {})
    per_tier = manifest.get("per_tier_preparation", {}).get(key(tier), {})
    tier_settings = settings.get("preparation_by_tier", {}).get(key(tier), settings)
    return {
        "kind": "current_connection_preserving_full_data_rules",
        "contract": CONTRACT,
        "dataset": dataset,
        "learner": method,
        "source": registry["public_source"],
        "source_commit": registry.get("source_commit"),
        "source_paper_doi": registry.get("source_paper_doi"),
        "data_kind": registry["data_kind"],
        "source_input_sha256": manifest["input_sha256"],
        "input_record_n": manifest["original_input_row_n"],
        "training_record_n": per_tier.get("prepared_measurement_n", manifest["prepared_measurement_n"]),
        "protected_group_n": tier_settings.get("protected_group_n", manifest["protected_group_n"]),
        "fit_scope": "full_prepared_data_deployment",
        "original_repeat_unit_identity_preserved": True,
        "hcap_structure_not_used_to_merge_materials": True,
        "tier_independent": True,
        "tier": float(tier),
        "structural_role_fingerprint": {"name": "ECFP4", "kind": "Morgan", "radius": 2, "n_bits": 2048},
        "rule_fingerprint": "Hcap_MACCS167",
        "transform": tier_settings.get("transform"),
        "scan": tier_settings.get("scan"),
        "WRAcc_search": settings.get("WRAcc_search") if method == "WRAcc" else None,
        "evaluation_scope": manifest.get("evidence_status"),
        "CV_folds": settings.get("folds"),
        "CV_repeats": settings.get("repeats"),
        "entrypoint_sha256": manifest.get("entrypoint_sha256"),
        "preparation_audit_sha256": per_tier.get("preparation_audit_sha256", manifest.get("preparation_audit_sha256")),
        "fingerprint_matrix_sha256": per_tier.get("fingerprint_contract", manifest.get("fingerprint_contract", {})).get("matrix_sha256"),
        "source_run_summary_sha256": sha((evroot / "screening_summary.json").read_bytes()),
    }


def refresh(args):
    skill = Path(args.skill).expanduser().resolve()
    repository = Path(args.repository).expanduser().resolve()
    root = skill / "assets/rule_library"
    original = read(root / "catalog.json")
    catalog = copy.deepcopy(original)
    old = {e["id"]: e for e in original["entries"]}
    sources = {row["dataset"]: row for row in csv.DictReader(
        (repository / "examples/open_data/dataset_registry.csv").open(encoding="utf-8-sig"))}
    datasets = set(sources)
    spec = read(args.spec)
    sys.path.insert(0, str(skill / "scripts"))
    from generation_prompt import render_prompt
    from rule_library import RuleLibrary

    plans, updated, records, seen = {}, [], [], set()
    protected = {name: sha((root / name).read_bytes())
                 for e in original["entries"] if e["id"].startswith("paper-")
                 for name in [e["constraints"], *e["prompts"].values()]}
    for supplied in spec["runs"]:
        dataset = supplied["dataset_id"]
        if dataset not in sources:
            raise ValueError(f"Unknown dataset: {dataset}")
        run = Path(supplied["run_dir"]).expanduser().resolve()
        summary = read(run / "screening_summary.json")
        requested = {float(q) for q in supplied.get("tiers", DEFAULT_TIERS)}
        for tier in summary["tiers"]:
            q = float(tier["fraction"])
            if q not in requested:
                continue
            pair = (dataset, q)
            if pair in seen:
                raise ValueError(f"Duplicate dataset/tier evidence: {pair}")
            seen.add(pair)
            primary = tier.get("recommended_method")
            for method in ("STCA", "WRAcc"):
                source = tier["methods"][method]
                constraint_path = contained(run, source["constraints"])
                exported = read(constraint_path)
                evroot = evidence_root(run, constraint_path)
                manifest = read(evroot / "run_manifest.json")
                cv = read(evroot / "cv_summary.json")["methods"][method][key(q)]
                if (manifest["learning_settings"]["tiers"] != [q]
                        and (manifest["learning_settings"].get("preparation_scope") != "independent_per_tier"
                             or key(q) not in manifest.get("per_tier_preparation", {}))):
                    raise ValueError(f"Expected independent singleton evidence: {pair} {evroot}")
                if manifest.get("status") not in ("completed", "completed_with_storage_warning"):
                    raise ValueError(f"Incomplete calculation: {evroot}")
                representation = exported.get("representation") or exported.get("model", {}).get("custom_data_contract", {}).get("representation")
                if representation != "hcap_maccs167":
                    raise ValueError(f"Unexpected calculation representation: {constraint_path}")
                new_id = identifier(dataset, method, summary["direction"], q)
                if new_id not in old:
                    raise ValueError(f"Missing current catalog template: {new_id}")
                template = copy.deepcopy(old[new_id])
                if dataset == "AD_GAP":
                    template.update(property="H-capped isolated-monomer HOMO–LUMO gap",
                                    property_zh="氢封端孤立单体 HOMO–LUMO 能隙")
                entry = copy.deepcopy(template)
                provenance = compact_provenance(dataset, method, q, manifest, sources[dataset], evroot)
                full = native_metric(method, q, evroot)
                reference = {
                    "status": "inrange_cv_evaluated" if cv.get("status") == "evaluated" else "reference_inconclusive",
                    "evaluation_kind": "grouped_5fold_cv_repeated_3",
                    "evaluation_scope": "Grouped out-of-fold evaluation conditional on this tier's full-data preparation and scan selection.",
                    "evidence_source": "current_profile_evidence.json",
                    "cv_folds": manifest["learning_settings"]["folds"],
                    "cv_repeats": manifest["learning_settings"]["repeats"],
                    "cv_grouping": "protected_original_and_hcap_related_components",
                    "cv_metric_aggregation": "pooled OOF metrics per repeat, then mean and sample SD",
                    "cv_label_cutoff_scope": "training fold only",
                    "AS_definition": "(MCC + Precision + F1) / 3",
                    "full_data_n": provenance["training_record_n"],
                    "full_data_positive_n": full.get("positive_n"),
                    "full_data_selected_n": full.get("selected_n"),
                    "full_data_insample_precision": full.get("precision"),
                    "full_data_insample_recall": full.get("recall"),
                    "screened_input_n": source["original_input_n"],
                    "screened_input_selected_n": source["selected_n"],
                    "screened_input_unknown_n": source["unknown_n"],
                    "physical_cutoff": tier["physical_cutoff"],
                    "physical_unit": tier["unit"],
                    "evaluable": cv.get("status") == "evaluated",
                    "experiment_id": CONTRACT,
                }
                for metric in ("precision", "recall", "f1", "mcc", "AS"):
                    reference[f"cv_{metric}"] = cv.get(f"{metric}_mean")
                    reference[f"cv_{metric}_sd"] = cv.get(f"{metric}_sd")
                is_primary = method == primary
                role = "primary" if is_primary else "alternative"
                entry.update(id=new_id, preferred=is_primary, user_visible=True, legacy=False,
                             status=exported.get("status"), available=bool(exported.get("rule") and exported["rule"].get("keys")),
                             is_primary=is_primary, method_role=role,
                             alternative_id=identifier(dataset, "WRAcc" if method == "STCA" else "STCA", summary["direction"], q),
                             primary_id=identifier(dataset, primary or "STCA", summary["direction"], q),
                             title=f"{dataset} · {method}: {template['property']}, Top {q*100:g}% ({role})",
                             title_zh=f"{dataset} · {method}：{template['property_zh']}，Top {q*100:g}%（{'主推' if is_primary else '备选'}）",
                             constraints=f"entries/{new_id}/constraints.json",
                             prompts={lang: f"entries/{new_id}/prompt.{lang}.md" for lang in ("en", "zh-CN")},
                             provenance=provenance, reference_evaluation=reference,
                             experiment_id=CONTRACT)
                entry.pop("supersedes", None)
                target = copy.deepcopy(exported["target"])
                target.update(name=template["property"], unit=tier["unit"],
                              physical_cutoff=tier["physical_cutoff"], model_cutoff=target.get("model_space_cutoff"),
                              model_unit=target.get("model_space_unit", tier["unit"]), operator=tier["operator"])
                rule = copy.deepcopy(exported.get("rule"))
                payload = {
                    "schema": "stca-library-constraints-v1", "version": "0.1.0",
                    "status": exported.get("status"), "catalog_id": new_id,
                    "property": template["property"], "property_zh": template["property_zh"],
                    "dataset_id": dataset, "learner": method, "method": method,
                    "direction": summary["direction"], "tier": q, "tier_fraction": q,
                    "is_primary": is_primary, "alternative_id": entry["alternative_id"],
                    "representation": "hcap_maccs167", "structure_kind": "polymer_repeat_unit",
                    "metadata": {"model_type": "frozen_literal_rule", "learner": method, "kind": CONTRACT},
                    "model": {"model_type": "frozen_literal_rule", "learner": method,
                              "origin": {"kind": CONTRACT, "dataset_id": dataset, "name": new_id},
                              "frozen_rule_sha256": sha(encoded(rule)), "provenance": provenance,
                              "custom_data_contract": copy.deepcopy(exported["model"].get("custom_data_contract", {}))},
                    "target": target, "feature_spec": copy.deepcopy(exported["feature_spec"]),
                    "feature_names": copy.deepcopy(exported["feature_names"]),
                    "combiner": "AND", "rule": rule, "literals": copy.deepcopy(exported.get("literals", [])),
                    "require_present": copy.deepcopy(exported.get("require_present", [])),
                    "require_absent": copy.deepcopy(exported.get("require_absent", [])),
                    "provenance": provenance, "reference_evaluation": reference,
                    "interpretation": exported.get("interpretation"),
                    "tier_interpretation": exported.get("tier_interpretation"),
                }
                payload["feature_spec"]["smiles_policy"] = "H-capped calculation-only derivative; original repeat-unit connection graph is preserved."
                plans[entry["constraints"]] = encoded(payload)
                for lang in ("en", "zh-CN"):
                    if rule and rule.get("keys"):
                        prompt = render_prompt(payload, language=lang, count=20, structure_kind="polymer_repeat_unit")
                    else:
                        prompt = "No valid frozen rule was learned for this target; generation is unavailable.\n" if lang == "en" else "该目标未学得有效冻结结构规则，当前不能据此生成。\n"
                    plans[entry["prompts"][lang]] = prompt.encode()
                updated.append(entry)
                records.append({"id": new_id, "dataset": dataset, "method": method,
                                "tier": q, "primary": is_primary, "cutoff": tier["physical_cutoff"],
                                "unit": tier["unit"], "operator": tier["operator"],
                                "input_n": source["original_input_n"], "prepared_n": provenance["training_record_n"],
                                "selected_n": source["selected_n"], "unknown_n": source["unknown_n"],
                                "cv_AS": cv.get("AS_mean"), "cv_AS_sd": cv.get("AS_sd"),
                                "rule": source.get("rule"), "status": source.get("status"), "source_input_sha256": manifest["input_sha256"],
                                "transform": provenance["transform"], "scan": provenance["scan"],
                                "fingerprint_matrix_sha256": provenance["fingerprint_matrix_sha256"]})

    expected = {(dataset, q) for dataset in datasets for q in DEFAULT_TIERS}
    if not args.allow_partial and seen != expected:
        raise ValueError(f"Expected all 36 dataset/tier pairs; missing={sorted(expected-seen)}, extra={sorted(seen-expected)}")
    updated_ids = {entry["id"] for entry in updated}
    # Published packages contain only paper rules and this calculation contract.
    # Partial maintenance refreshes retain other current entries, never obsolete profiles.
    catalog["entries"] = [entry for entry in catalog["entries"]
                          if entry["id"].startswith(("paper-", "current-"))
                          and entry["id"] not in updated_ids] + updated
    current = [entry for entry in catalog["entries"] if entry["id"].startswith("current-")]
    primary_counts = {m: sum(e.get("is_primary") is True and e.get("method") == m for e in current) for m in ("STCA", "WRAcc")}
    available = sum(entry.get("available", True) for entry in current)
    catalog.update(evidence_scope="Paper rules retain their exact author conditions; current open-data rules use original-connection-preserving independent-tier preparation, grouped cross-validation and full-data refits.",
                   latest_evidence="current_profile_evidence.json",
                   current_contract=CONTRACT,
                   counts={"retained": len(catalog["entries"]),
                           "visible": sum(e.get("user_visible", True) for e in catalog["entries"]),
                           "published_visible": sum(e["id"].startswith("paper-") and e.get("user_visible", True) for e in catalog["entries"]),
                           "current_visible": len(current), "latest_visible": 0,
                           "current_available_rules": available,
                           "current_unavailable_results": len(current)-available,
                           "legacy_hidden": sum(not e.get("user_visible", True) for e in catalog["entries"]),
                           "current_primary_by_learner": primary_counts})
    plans["catalog.json"] = encoded(catalog)
    plans["current_profile_evidence.json"] = encoded({"schema": "stca-current-catalog-evidence-v1", "contract": CONTRACT, "rules": records})
    lines = ["# STCA rule and prompt library", "",
             "Choose a source, property and percentage. Each exact rule is an AND conjunction; recommended and alternative methods remain separate.", "",
             f"Version 0.1.0. {len(catalog['entries'])} catalog results: 11 STCA paper rules and {len(current)} current open-data method results ({available} available open-data rules).", "",
             "Current open-data rules preserve original polymer connection graphs and prepare each percentage independently. Physical boundaries describe the training objective; matching a rule does not measure a candidate's property.", "",
             "| Rule ID | Source / property | Method | Percentage / boundary | Role |",
             "|---|---|---|---|---|"]
    for entry in catalog["entries"]:
        if not entry.get("user_visible", True):
            continue
        if entry["id"].startswith("paper-"):
            target = read(root/entry["constraints"])["target"]
            boundary = f"{'Top' if entry['direction']=='high' else 'Bottom'} {entry['tier']*100:g}%; {target['operator']} {target['physical_cutoff']:.10g} {entry['unit']}"
            role = "paper rule"
        else:
            t = read(root/entry["constraints"])["target"] if entry["constraints"] not in plans else json.loads(plans[entry["constraints"]])["target"]
            boundary = f"Top {entry['tier']*100:g}%; {t['operator']} {t['physical_cutoff']:.10g} {entry['unit']}"
            role = entry["method_role"] if entry.get("available", True) else "no valid rule; generation unavailable"
        lines.append(f"| `{entry['id']}` | {entry['dataset']} / {entry['property']} | {entry.get('method','STCA')} | {boundary} | {role} |")
    plans["index.md"] = ("\n".join(lines)+"\n").encode()
    if args.apply:
        for relative, payload in plans.items():
            target = root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        retained_directories = {entry["id"] for entry in catalog["entries"]}
        for directory in (root / "entries").iterdir():
            if directory.is_dir() and directory.name not in retained_directories:
                import shutil
                shutil.rmtree(directory)
        for relative, expected_hash in protected.items():
            if sha((root/relative).read_bytes()) != expected_hash:
                raise AssertionError(f"Paper rule payload changed: {relative}")
        library = RuleLibrary(root)
        for entry in updated:
            constraint, _ = library.constraints(entry["id"])
            for lang in ("en", "zh-CN"):
                saved, _ = library.prompt(entry["id"], lang)
                if constraint.get("rule") and constraint["rule"].get("keys"):
                    assert saved.decode() == render_prompt(constraint, language=lang, count=20, structure_kind="polymer_repeat_unit")
        evidence_path = repository/"validation/current_open_data_rules.json"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_bytes(plans["current_profile_evidence.json"])
        compact_rows = [{k:v for k,v in row.items() if k not in ("scan",)} for row in records]
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(compact_rows[0]))
        writer.writeheader();writer.writerows(compact_rows)
        (repository/"examples/open_data/current_rule_metrics.csv").write_text(output.getvalue(), encoding="utf-8")
        update_public_rule_tables(repository, catalog)
        update_density_example(skill, repository, catalog, plans, render_prompt)
    return {"applied": args.apply, "contract": CONTRACT, "datasets": len({d for d,q in seen}),
            "dataset_tier_pairs": len(seen), "new_rules": len(updated), "historical_payloads_checked": len(protected),
            "planned_files": len(plans), "counts": catalog["counts"]}


def update_public_rule_tables(repository, catalog):
    """Keep the public prompt links and method recommendations from one catalog."""
    current = {entry["id"]: entry for entry in catalog["entries"] if entry["id"].startswith("current-")}
    for language, filename in (("en", "RULE_LIBRARY.md"), ("zh-CN", "RULE_LIBRARY.zh-CN.md")):
        path = repository/"docs"/filename
        text = path.read_text()
        text = text.replace("entries/latest-", "entries/current-")
        lines = []
        for line in text.splitlines():
            if line.startswith("|") and "entries/current-" in line:
                cells = line.split("|")
                for i, cell in enumerate(cells):
                    identifiers = re.findall(r"entries/(current-[^/]+)/prompt\.(?:en|zh-CN)\.md", cell)
                    if not identifiers:
                        continue
                    if any(name not in current for name in identifiers):
                        continue
                    entries = sorted((current[name] for name in identifiers),
                                     key=lambda entry: (entry.get("is_primary") is not True, entry["method"]))
                    options = []
                    for entry in entries:
                        if not entry.get("available", True):
                            role = "未得有效规则" if language == "zh-CN" else "No valid rule"
                        else:
                            role = ("主推" if entry["is_primary"] else "备选") if language == "zh-CN" else ("Primary" if entry["is_primary"] else "Alternative")
                        options.append(f"{role} [{entry['method']}](../skills/stca/assets/rule_library/entries/{entry['id']}/prompt.{language}.md)")
                    cells[i] = " " + " · ".join(options) + " "
                line = "|".join(cells)
            lines.append(line)
        text = "\n".join(lines)+"\n"
        old_en = "Bundled rules and scores retain the settings used to create them. New learning selects the WRAcc condition-count limit inside the training partition by default; a fixed limit or no limit can also be requested. This does not rewrite bundled rules or their catalog scores."
        new_en = "The current open-data rules use the same original-structure preparation and independent percentage settings as new learning. Relearning the same source file with the same columns, settings and software environment reproduces the corresponding rule. WRAcc chooses its condition-count limit within the training data; you may also specify a fixed limit or no limit. Saved rules retain their exact conditions."
        text = text.replace(old_en, new_en)
        text = text.replace("Each tier offers complete **STCA and WRAcc** rules, marked primary and alternative.",
                            "Each tier returns separate **STCA and WRAcc** results and rule-availability status; available rules are marked primary or alternative.")
        text = text.replace("每档同时提供 **STCA 与 WRAcc** 两套完整规则，标出主推与备选。",
                            "每档分别提供 **STCA 与 WRAcc** 的结果与规则可用状态，有效规则标出主推与备选。")
        text = text.replace("现成目录的规则及评分保留其生成时的设置。新的数据学习默认在训练分区内部选择 WRAcc 条件数，可指定固定上限或不设上限；这不会自动改写现成规则或目录中的评分。",
                            "当前开源规则与重新学习采用相同的原始结构处理和逐百分比独立设置。同一来源文件、列名、学习设置与程序环境下，重新学习应重现对应规则。WRAcc 在训练数据内部选择条件数上限，也可指定固定上限或不设上限；保存后的规则保留精确条件。")
        path.write_text(text)


def update_density_example(skill, repository, catalog, plans, render_prompt):
    entries = {entry["id"]: entry for entry in catalog["entries"]}
    sid = "current-pi-rho-stca-high-30"
    wid = "current-pi-rho-wracc-high-30"
    if sid not in entries or wid not in entries:
        return
    source_path = skill/"assets/examples/radonpy_density_case.json"
    case = read(source_path)
    stca = read(skill/"assets/rule_library"/entries[sid]["constraints"])
    wracc = read(skill/"assets/rule_library"/entries[wid]["constraints"])
    def example(identifier, constraint):
        ref = constraint["reference_evaluation"]
        return {"id": identifier, "method": constraint["method"], "fraction": 0.3,
                "physical_operator": constraint["target"]["operator"],
                "physical_cutoff": constraint["target"]["physical_cutoff"],
                "rule": constraint["rule"]["expression"],
                "expected_selected": ref["screened_input_selected_n"],
                "expected_not_selected": ref["screened_input_n"]-ref["screened_input_selected_n"]-ref["screened_input_unknown_n"],
                "expected_unknown": ref["screened_input_unknown_n"],
                "physical_cutoff_policy": "keep_frozen_source_cutoff; never_recalculate_from_candidate_table"}
    primary_id, alternative_id = (sid, wid) if entries[sid]["is_primary"] else (wid, sid)
    constraints = {sid: stca, wid: wracc}
    case["existing_rule"] = example(primary_id, constraints[primary_id])
    case["alternative_method_rule"] = example(alternative_id, constraints[alternative_id])
    case["recommended_method"] = constraints[primary_id]["method"]
    case["selection_policy"] = {
        "default_screening_method": "catalog_primary", "honor_explicit_method": True,
        "generation": "reuse_exact_rule_already_selected_in_conversation"}
    # The published five-proposal illustration deliberately names STCA.
    # It must not change a conversation's selected method or screening default.
    case["generation"]["static_example_rule_id"] = sid
    case["relearn"].update(contract=CONTRACT, tier_independent=True,
                          comparison="same_source_columns_and_default_settings_reproduce_current_bundled_rule",
                          original_connection_graphs_preserved=True,
                          expected_top30_transform=stca["provenance"]["transform"],
                          expected_top30_scan=stca["provenance"]["scan"])
    source_path.write_bytes(encoded(case))
    (repository/"examples/radonpy_density/case.json").write_bytes(encoded(case))
    for language in ("en", "zh-CN"):
        prompt = render_prompt(stca, language=language, count=5, structure_kind="polymer_repeat_unit")
        (repository/f"examples/radonpy_density/generation_prompt.{language}.md").write_text(prompt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    print(json.dumps(refresh(parser.parse_args()), ensure_ascii=False, indent=2))
