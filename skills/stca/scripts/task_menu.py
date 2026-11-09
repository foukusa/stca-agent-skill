#!/usr/bin/env python3
"""Read STCA's conversational task overview without scientific dependencies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


TASKS_FILE = Path(__file__).resolve().parents[1] / "assets" / "starter_tasks.json"
CATALOG_ROOT = TASKS_FILE.parent / "rule_library"
RETURN_COMMANDS = {"返回", "上一级", "主菜单", "返回主菜单", "back", "main menu", "return", "menu", "0"}
SOURCE_LABELS = {
    "my_rules": {"zh-CN": "已保存的规则文件", "en": "Saved rule files"},
    "paper": {"zh-CN": "STCA 论文", "en": "STCA paper"},
    "gas": {"zh-CN": "GAS 实测数据", "en": "GAS measured data"},
    "radonpy": {"zh-CN": "RadonPy 计算数据", "en": "RadonPy computed data"},
    "adept": {"zh-CN": "ADEPT 计算数据", "en": "ADEPT computed data"},
}
EVIDENCE_LABELS = {
    "paper_implementation": ("STCA 论文实现", "STCA paper implementation"),
    "published_evidence": ("论文规则", "Published rule"),
    "historical_evidence": ("历史记录", "Historical record"),
    "reference_enrichment_observed": ("有富集记录", "Recorded enrichment"),
    "no_reference_coverage": ("已评估数据中零覆盖", "Zero coverage in reference data"),
    "no_demonstrated_enrichment": ("尚未显示富集", "Enrichment not demonstrated"),
    "reference_inconclusive": ("证据不足", "Inconclusive evidence"),
    "user_saved_rule": ("已保存的冻结规则", "Saved frozen rule"),
    "inrange_cv_evaluated": ("范围内交叉验证", "In-range cross-validation"),
}


def load_tasks(path=TASKS_FILE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "stca-starter-tasks-v1":
        raise ValueError("Invalid STCA starter-task schema.")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 3:
        raise ValueError("The STCA workflow catalog must contain three tasks.")
    if [t.get("number") for t in tasks] != [1, 2, 3]:
        raise ValueError("STCA task numbers must be 1, 2 and 3.")
    if len({t.get("id") for t in tasks}) != 3:
        raise ValueError("STCA task IDs must be distinct.")
    for task in tasks:
        for key in ("title", "user_prompt"):
            if any(not isinstance(task.get(key, {}).get(lang), str) or
                   not task[key][lang].strip() for lang in ("en", "zh-CN")):
                raise ValueError(f"Task {task.get('id')} is missing bilingual {key}.")
        if task["number"] in (1, 2) and task.get("default_tiers") != [0.1, 0.2, 0.3]:
            raise ValueError("The default target tiers must be 10%, 20% and 30%.")
        if task["number"] == 3 and task.get("default_tiers") is not None:
            raise ValueError("Generation uses the selected exact rule tier, without implicit tier expansion.")
    modes = tasks[2].get("generation_modes", [])
    if [(mode.get("id"), mode.get("number")) for mode in modes] != [("preview", 1), ("direct", 2)]:
        raise ValueError("Generation must offer preview and direct modes.")
    return data


def saved_rules(directory):
    """Read friendly workspace records; never create or modify a library."""
    from user_rule_library import list_entries
    return list_entries(directory)


def physical_target(constraint):
    """Expose frozen physical thresholds without confusing a log model scale."""
    target = constraint.get("target", {})
    builtin = constraint.get("schema") == "stca-library-constraints-v1"
    cutoff = target.get("physical_cutoff" if builtin else "physical_train_cutoff")
    unit = target.get("unit" if builtin else "physical_unit")
    direction = constraint.get("direction", target.get("direction"))
    comparison = target.get("operator" if builtin else "label_comparison")
    comparison = comparison or (">=" if direction == "high" else "<=")
    return {"physical_cutoff": cutoff, "physical_unit": unit,
            "physical_comparison": comparison,
            "physical_cutoff_status": "available" if cutoff is not None and unit else "not_provided"}


def rule_options(directory, language="zh-CN", catalog_root=CATALOG_ROOT, *, include_hidden_ids=()):
    """List current choices; retain hidden exact rules only when explicitly named."""
    from rule_library import RuleLibrary, read_json
    from user_rule_library import show_entry
    groups = {key: {"source": key, "title": labels[language], "properties": []}
              for key, labels in SOURCE_LABELS.items()}
    indexed = {key: {} for key in groups}
    unavailable = []
    explicit_ids = set(include_hidden_ids)

    def add(source, prop, direction, unit, option):
        key = (prop, direction, unit)
        if key not in indexed[source]:
            item = {"property": prop, "direction": direction, "unit": unit, "choices": []}
            indexed[source][key] = item
            groups[source]["properties"].append(item)
        indexed[source][key]["choices"].append(option)

    def evidence(status):
        labels = EVIDENCE_LABELS.get(status, EVIDENCE_LABELS["reference_inconclusive"])
        return {"status": status, "label": labels[0 if language == "zh-CN" else 1],
                "caution": status in {"no_reference_coverage", "no_demonstrated_enrichment", "reference_inconclusive"}}

    saved = saved_rules(directory)
    unavailable.extend({"kind": "saved", **item} for item in saved["invalid_entries"])
    for summary in saved["entries"]:
        entry = show_entry(directory, summary["id"])
        for rule in entry["usable_rules"]:
            constraint = read_json(rule["constraints_path"])
            stored = constraint.get("rule")
            if not isinstance(stored, dict) or not stored.get("keys"):
                unavailable.append({"kind": "saved", "id": entry["id"], "reason": "no_frozen_conditions"})
                continue
            tier = rule["tier"]
            add("my_rules", entry["name"], entry["direction"], entry["unit"], {
                "id": f"{entry['id']}@{tier:.12g}", "kind": "saved", "tier": tier,
                "saved_rule_id": entry["id"], "constraints_path": rule["constraints_path"],
                "model_path": entry["model_path"], "prompt_paths": rule["prompt_paths"],
                "method": entry.get("learner", constraint.get("model", {}).get("learner", "STCA")),
                **physical_target(constraint),
                "evidence": evidence("user_saved_rule"),
            })

    library = RuleLibrary(catalog_root)
    visible, explicit_hidden = 0, 0
    for entry in library.entries.values():
        is_visible = entry.get("user_visible", True)
        if not is_visible and entry["id"] not in explicit_ids:
            continue
        if is_visible:
            visible += 1
        else:
            explicit_hidden += 1
        dataset = str(entry.get("dataset", ""))
        source = ("paper" if entry.get("provenance", {}).get("kind") == "paper" else
                  "gas" if dataset.startswith("GAS_") else
                  "radonpy" if dataset.startswith("PI_") else
                  "adept" if dataset.startswith("AD_") else None)
        if source is None:
            unavailable.append({"kind": "builtin", "id": entry["id"], "reason": "unclassified_source"})
            continue
        try:
            constraint, path = library.constraints(entry["id"])
            rule = constraint.get("rule")
            if not isinstance(rule, dict) or not rule.get("keys"):
                raise ValueError("no_frozen_conditions")
            prompt_paths = {lang: str(library.path(relative)) for lang, relative in entry["prompts"].items()}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            unavailable.append({"kind": "builtin", "id": entry["id"], "reason": str(exc)})
            continue
        prop = entry.get("property_zh", entry["property"]) if language == "zh-CN" else entry["property"]
        add(source, prop, entry["direction"], entry["unit"], {
            "id": entry["id"], "kind": "builtin", "tier": entry["tier"],
            "constraints_path": str(path), "prompt_paths": prompt_paths,
            "method": entry.get("method", "STCA"),
            "is_primary": entry.get("is_primary"), "alternative_id": entry.get("alternative_id"),
            "user_visible": bool(is_visible), "legacy": bool(entry.get("legacy", False)),
            "selection_scope": "current_catalog" if is_visible else "explicit_hidden_rule",
            "preparation_profile": entry.get("preparation_profile"),
            "superseded_by": entry.get("superseded_by"),
            **({"legacy_notice": "明确选择的历史冻结规则；保留原条件和阈值。"
                if language == "zh-CN" else "Explicitly selected legacy frozen rule; original conditions and cutoff are retained."}
               if entry.get("legacy", False) else {}),
            **physical_target(constraint),
            "reference_evaluation": entry.get("reference_evaluation"),
            "publication_alignment": entry.get("publication_alignment"),
            "evidence": evidence("paper_implementation" if source == "paper" else
                                 (entry.get("reference_evaluation") or {}).get("status", "reference_inconclusive")),
        })
    for group in groups.values():
        for prop in group["properties"]:
            prop["choices"].sort(key=lambda item: (item["tier"], item.get("is_primary") is False, item.get("method", "STCA")))
    return {"schema": "stca-rule-choice-menu-v1", "version": library.catalog.get("version"),
            "language": language, "retained_builtin_entries": len(library.entries),
            "visible_builtin_entries": visible, "explicit_hidden_builtin_entries": explicit_hidden,
            "groups": list(groups.values()),
            "unavailable_entries": unavailable}


def display_rules(options):
    zh = options["language"] == "zh-CN"
    print("请选择规则来源、性质和百分比；例如“RadonPy，高密度，Top 30%”。" if zh else
          'Choose a rule source, property and percentage, for example "RadonPy, high density, Top 30%".')
    for group in options["groups"]:
        print(f"\n{group['title']}")
        if not group["properties"]:
            print("- 暂无已保存规则，可上传有标签的数据总结规则。" if zh else "- No saved rules yet; upload labelled data to learn rules.")
        for prop in group["properties"]:
            tail = "Top" if prop["direction"] == "high" else "Bottom"
            def label(item):
                role = ("主推" if zh else "primary") if item.get("is_primary") is True else (("备选" if zh else "alternative") if item.get("is_primary") is False else item["evidence"]["label"])
                if item.get("legacy"):
                    role = "历史规则，明确选择" if zh else "legacy, explicitly selected"
                return f"{tail} {item['tier']*100:g}% ({item.get('method', 'STCA')}, {role})"
            choices = " · ".join(label(item) for item in prop["choices"])
            print(f"- {prop['property']} [{prop['unit']}]：{choices}")
    if options["unavailable_entries"]:
        print("\n缺少有效冻结条件或未通过完整性检查的条目暂不列为可选规则。" if zh else
              "\nEntries without valid frozen conditions or passing integrity checks are unavailable.")
    print("选定后再执行；已明确指定规则时直接使用，不重复询问。" if zh else
          "Execution starts after selection. An explicitly specified rule is used directly without asking again.")


def resolve_rules(options, requested):
    available = {choice["id"]: choice for group in options["groups"]
                 for prop in group["properties"] for choice in prop["choices"]}
    missing = [identifier for identifier in requested if identifier not in available]
    if missing:
        unavailable = {entry["id"] for entry in options.get("unavailable_entries", [])}
        unknown = [identifier for identifier in missing if identifier not in unavailable]
        if unknown:
            raise ValueError("Unknown rule ID in this catalog: " + ", ".join(unknown))
        raise ValueError("The specified rule is unavailable in this choice menu: " + ", ".join(missing))
    return [available[identifier] for identifier in requested]


def generation_plan(task, mode, selected_rules, language):
    """Describe an agent orchestration gate; never generate or approve a prompt."""
    rule_missing = not selected_rules
    if rule_missing:
        state, action = "awaiting_rule_selection", "choose_rule_and_wait"
    elif mode is None:
        state, action = "awaiting_generation_mode", "choose_generation_mode_and_wait"
    elif mode == "preview":
        state, action = "awaiting_prompt_review_and_confirmation", "prepare_complete_prompt_and_wait_for_confirmation"
    else:
        state, action = "ready_for_current_llm", "generate_with_current_llm_then_verify"
    helper = str(Path(__file__).resolve().with_name("generation_session.py"))
    prepare = None
    if selected_rules and mode is not None:
        prepare = ["<agent-python>", helper, "prepare", "--constraints",
                   *(rule["constraints_path"] for rule in selected_rules), "--mode", mode,
                   "--count", str(task["default_count"]), "--language", language,
                   "--output-dir", "<new-user-workspace-session-directory>"]
    return {
        "generation_mode": mode,
        "generation_mode_required": mode is None,
        "generation_mode_options": [
            {"id": item["id"], "number": item["number"],
             "title": item["title"][language], "description": item["description"][language]}
            for item in task["generation_modes"]],
        "generation_policy": task["generation_policy"],
        "generation_gate": {
            "state": state, "generation_allowed": bool(selected_rules) and mode == "direct",
            "rule_selection_complete": not rule_missing,
            "confirmation_required": mode == "preview",
            "full_prompt_display_required": mode == "preview",
            "revision_invalidates_confirmation": True,
            "generator": "current_llm", "exact_verification_required": True,
            "prompt_file_alone_completes_generation": False,
            "confirmation_source": "observed_explicit_user_confirmation_of_current_prompt",
        },
        "session_helper": {
            "script": helper, "prepare_command_template": prepare,
            "confirm_command_template": ["<agent-python>", helper, "confirm", "--session",
                                         "<session.json>", "--confirmation-text", "<actual-observed-user-confirmation>"],
            "revise_command_template": ["<agent-python>", helper, "revise", "--session",
                                        "<session.json>", "--draft-file", "<user-adjustments.md>"],
            "status_command_template": ["<agent-python>", helper, "status", "--session",
                                        "<session.json>", "--include-prompt"],
            "user_workspace_only": True,
            "revision_note": "The helper rerenders all frozen scientific conditions; draft-file contains only the user's additional adjustments, not a replacement complete prompt.",
        },
        "next_action": action,
    }


def display_menu(data, language, saved):
    print(data["menu_title"][language])
    for task in data["tasks"]:
        print(f"- {task['title'][language]}")
    if saved["entries"]:
        print("\n已保存的规则文件（可继续筛选或生成）：" if language == "zh-CN" else "\nSaved rule files (available for screening or generation):")
        for entry in saved["entries"]:
            tail = "Top" if entry["direction"] == "high" else "Bottom"
            tiers = ", ".join(f"{tail} {tier*100:g}%" for tier in entry["tiers"])
            print(f"- {entry['name']} — {tiers}")
    if saved["invalid_entries"]:
        print("部分已保存条目未通过完整性检查，暂不用于筛选或生成。" if language == "zh-CN" else
              "Some saved entries failed integrity checks and are unavailable for screening or generation.")
    print("直接说明目标即可继续；也可要求重新显示任务。" if language == "zh-CN" else
          'Describe your next goal to continue, or ask to show the task overview again.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", help="Task number 1/2/3 or internal task ID")
    parser.add_argument("--task", dest="selected_task", help="Task number or internal task ID")
    parser.add_argument("--language", choices=("en", "zh-CN"), default="zh-CN")
    parser.add_argument("--library-dir", default=str(Path.cwd() / "stca-rules"),
                        help="Workspace learned-rule library to display; read-only")
    parser.add_argument("--rules", "--catalog", action="store_true", dest="show_rules",
                        help="Display readable built-in and saved rule choices")
    parser.add_argument("--rule", action="append", default=[],
                        help="Agent-resolved explicit rule ID; repeat for a stated multi-rule request")
    parser.add_argument("--generation-mode", choices=("preview", "direct"),
                        help="Task 3: preview the full prompt and await confirmation, or generate directly")
    args = parser.parse_args(argv)
    try:
        if args.task and args.selected_task:
            raise ValueError("Select the task once, either positionally or with --task.")
        data = load_tasks()
        selected = args.selected_task or args.task
        saved = saved_rules(args.library_dir)
        if args.show_rules:
            display_rules(rule_options(args.library_dir, args.language, include_hidden_ids=args.rule))
            return 0
        if selected is None or selected.strip().casefold() in RETURN_COMMANDS:
            if args.generation_mode:
                raise ValueError("Generation modes apply only to task 3.")
            display_menu(data, args.language, saved)
            return 0
        task = next((t for t in data["tasks"] if selected in
                     (str(t["number"]), t["id"])), None)
        if task is None:
            raise ValueError("Unknown task. Choose 1, 2 or 3.")
        if args.generation_mode and task["number"] != 3:
            raise ValueError("Generation modes apply only to task 3.")
        options = rule_options(args.library_dir, args.language, include_hidden_ids=args.rule) if task["number"] in (2, 3) else None
        if args.rule and options is None:
            raise ValueError("Explicit existing rules apply to tasks 2 or 3, not data learning.")
        selected_rules = resolve_rules(options, args.rule) if args.rule else []
        rule_missing = options is not None and not selected_rules
        generation = generation_plan(task, args.generation_mode, selected_rules, args.language) if task["number"] == 3 else {}
        print(json.dumps({"schema": data["schema"], "version": data["version"],
                          "language": args.language,
                          "number": task["number"], "id": task["id"],
                          "title": task["title"][args.language],
                          "user_prompt": task["user_prompt"][args.language],
                          "workflow": task["workflow"],
                          "agent_steps": task["agent_steps"],
                          "ask_only_if_missing": task["ask_only_if_missing"],
                          "default_tiers": task["default_tiers"],
                          "percentage_policy": task["percentage_policy"],
                          "method_policy": task["method_policy"],
                          "required_summary_columns": task["required_summary_columns"],
                          "on_complete": task.get("on_complete", "continue_conversation"),
                          "interaction_policy": data.get("interaction_policy", {}),
                          "score_explanation": data.get("score_explanation", {}).get(args.language),
                          "state_policy": data.get("state_policy", {}),
                          "saved_rules": saved["entries"],
                          "saved_rule_errors": saved["invalid_entries"],
                          "choice_required": rule_missing or generation.get("generation_mode_required", False),
                          "rule_choice_required": rule_missing,
                          "rule_options": options if rule_missing else None,
                          "selected_rules": selected_rules,
                          "next_action": "choose_rule_and_wait" if rule_missing else "execute_requested_task",
                          **generation,
                          **({"default_count": task["default_count"]} if
                             "default_count" in task else {})},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("stca-task-menu: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
