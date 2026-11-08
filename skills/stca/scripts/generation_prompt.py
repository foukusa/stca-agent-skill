#!/usr/bin/env python3
"""Render copyable STCA generation prompts with the Python standard library.

This renderer does not generate structures or calculate fingerprints.  It consumes
frozen constraints and preserves their exact conjunction, target metadata and
available MACCS activation definitions in the bundled prompt templates.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys


_SCHEMAS = {"stca-library-constraints-v1", "stca-constraints-v1"}
_PLACEHOLDERS = {
    "COUNT", "OBJECTIVES", "EXACT_AND_CONDITIONS",
    "MACCS_LITERAL_SEMANTICS", "CHEMICAL_PREFERENCES",
    "GENERATION_TITLE", "CANDIDATE_KIND", "STRUCTURE_SUBJECT", "STRUCTURE_REPRESENTATION",
}
_SLOT = re.compile(r"\{\{([A-Z_]+)\}\}")
_LOG_UNIT = re.compile(r"log10\s*\(\s*([^()]+?)\s*\)", re.IGNORECASE)
STRUCTURE_KINDS = ("molecule", "polymer_repeat_unit")


def infer_structure_kind(smiles):
    """Describe valid original SMILES notation, not the material/property domain.

    Callers supply already parsed, valid SMILES. A dummy attachment atom is
    written with ``*`` in SMILES; unstarred input needs no invented attachments.
    Mixed notation is retained explicitly and needs a generation-time choice.
    """
    forms = {"polymer_repeat_unit" if "*" in value else "molecule" for value in smiles}
    return next(iter(forms)) if len(forms) == 1 else ("mixed" if forms else "unspecified")


def resolve_structure_kind(constraints, structure_kind=None):
    """Resolve output notation from an explicit choice or saved rule metadata.

    Legacy rules without this metadata keep their repeat-unit convention.
    Conflicting or mixed saved notation requires an explicit output choice.
    The MACCS representation and every frozen bit condition remain unchanged.
    """
    if structure_kind is not None:
        if structure_kind not in STRUCTURE_KINDS:
            raise ValueError("structure_kind must be 'molecule' or 'polymer_repeat_unit'.")
        return structure_kind
    values = [constraints] if isinstance(constraints, dict) else constraints
    if not isinstance(values, list) or not values:
        raise ValueError("constraints must be an object or a nonempty list of objects.")
    resolved = []
    for constraint in values:
        if not isinstance(constraint, dict):
            raise ValueError("Constraints must be objects.")
        declarations = []
        for source in (constraint, constraint.get("metadata"), constraint.get("model")):
            if not isinstance(source, dict):
                continue
            for metadata in (source, source.get("custom_data_contract")):
                if isinstance(metadata, dict) and metadata.get("structure_kind") is not None:
                    declarations.append(metadata["structure_kind"])
        if any(value not in STRUCTURE_KINDS for value in declarations):
            raise ValueError("Saved structure kind is mixed or unspecified; choose molecule or polymer_repeat_unit explicitly.")
        if len(set(declarations)) > 1:
            raise ValueError("Saved structure-kind declarations disagree; choose the output notation explicitly.")
        resolved.append(declarations[0] if declarations else "polymer_repeat_unit")
    if len(set(resolved)) > 1:
        raise ValueError("Selected rules use different structure kinds; choose the output notation explicitly.")
    return resolved[0]


def _structure_text(kind, zh):
    if kind == "molecule":
        return {
            "GENERATION_TITLE": "根据冻结 STCA 规则生成分子" if zh else "Generate molecules with frozen STCA rules",
            "CANDIDATE_KIND": "分子" if zh else "molecule",
            "STRUCTURE_SUBJECT": "分子" if zh else "molecule",
            "STRUCTURE_REPRESENTATION": (
                "## 分子表示\n\n"
                "- 在 `SMILES` 字段返回有效的普通分子 SMILES，使用合理价态，表示为单一连通分子。不要人为添加 `*` 连接原子。\n"
                "- 最终结果保留原始分子 SMILES。沿用冻结的 MACCS 计算契约：普通分子没有连接点时，H-cap 不改变结构；不要为计算添加星号或改变分子。\n"
                "- 返回不同的提案；没有证据时，不声称数据库新颖性、合成可行性或实测性质数值。" if zh else
                "## Molecular representation\n\n"
                "- Return valid ordinary molecular SMILES in the `SMILES` field, with chemically plausible valences and one connected molecule. Do not add artificial `*` attachment atoms.\n"
                "- Preserve each original molecular SMILES in the final output. Follow the frozen MACCS calculation contract: H-cap leaves molecules without attachment atoms unchanged. Do not add stars or alter the molecule for calculation.\n"
                "- Return distinct proposals; do not claim database novelty, synthetic feasibility, or measured property values without evidence."
            ),
        }
    return {
        "GENERATION_TITLE": "根据冻结 STCA 规则生成聚合物重复单元" if zh else "Generate polymer repeat units with frozen STCA rules",
        "CANDIDATE_KIND": "聚合物重复单元" if zh else "polymer repeat-unit",
        "STRUCTURE_SUBJECT": "重复单元" if zh else "repeat unit",
        "STRUCTURE_REPRESENTATION": (
            "## 重复单元表示\n\n"
            "- 在 `SMILES` 字段返回原始重复单元，恰好保留两个末端 `*` 连接原子。每个 `*` 仅有一个相邻原子，以单键连接。使用合理价态，表示为单一连通的重复单元。\n"
            "- 最终结构保留两个连接点。H-cap 仅是用于计算 MACCS 的独立副本：按照冻结模型的表示契约，将两个受支持的末端单键星号换成氢。不要用 H-cap 分子代替最终重复单元，也不要从 H-cap 反推连接点。\n"
            "- 返回不同的提案；没有证据时，不声称数据库新颖性、合成可行性或实测性质数值。" if zh else
            "## Repeat-unit representation\n\n"
            "- Return each original repeat unit in the `SMILES` field with exactly two terminal `*` attachment atoms. Each `*` must have one neighbor and a single attachment bond. Use chemically plausible valences and a single connected repeat unit.\n"
            "- Keep both attachment sites in the reported structure. H-cap is a separate computational copy used to calculate MACCS: replace the two supported terminal single-bond stars with hydrogen using the frozen model's representation contract. Never return the H-capped molecule in place of the repeat unit or reconstruct attachment sites from it.\n"
            "- Return distinct proposals; do not claim database novelty, synthetic feasibility, or measured property values without evidence."
        ),
    }


def _learner(constraint):
    """Retain the declared learner independently of the legacy signature prefix."""
    declarations = []
    for source in (constraint, constraint.get("metadata"), constraint.get("model")):
        if isinstance(source, dict):
            if source.get("learner") is not None:
                declarations.append(source["learner"])
            metadata = source.get("metadata")
            if isinstance(metadata, dict) and metadata.get("learner") is not None:
                declarations.append(metadata["learner"])
    if any(value not in {"STCA", "WRAcc"} for value in declarations):
        raise ValueError("Declared frozen-rule learner must be STCA or WRAcc.")
    if len(set(declarations)) > 1:
        raise ValueError("Frozen-rule learner declarations disagree.")
    return declarations[0] if declarations else None


def _text(value, label, *, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string.")
    value = value.strip()
    if value.casefold() in {"p", "u", "property", "target", "unit", "unknown", "n/a"}:
        raise ValueError(f"{label} contains an unresolved placeholder: {value!r}.")
    if "\n" in value or "\r" in value:
        raise ValueError(f"{label} must be a single line.")
    return value


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{label} must be a finite number.")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite number.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number.")
    return number


def _format_number(value):
    return str(int(value)) if value.is_integer() else repr(value)


def _key(value, label="MACCS key"):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer key in 1..166.")
    if isinstance(value, str):
        match = re.fullmatch(r"K?(\d+)", value.strip())
        if match:
            value = int(match.group(1))
    if not isinstance(value, int) or not 1 <= value <= 166:
        raise ValueError(f"{label} must be an integer key in 1..166.")
    return value


def _bit(value):
    if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
        raise ValueError("Rule values must be integer 0 or 1.")
    return value


def _source_label(constraint):
    for field in ("catalog_id", "entry_id", "id", "dataset_id", "source_label"):
        value = constraint.get(field)
        if isinstance(value, str) and value.strip():
            return _text(value, field)
    model = constraint.get("model")
    if isinstance(model, dict):
        origin = model.get("origin", {})
        if isinstance(origin, dict):
            for field in ("profile", "profile_name", "name"):
                value = origin.get(field)
                if isinstance(value, str) and value.strip():
                    return _text(value, "model origin")
        digest = model.get("artifact_sha256")
        if isinstance(digest, str) and re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            return "artifact_sha256=" + digest
    return constraint["schema"]


def _target(constraint):
    schema = constraint["schema"]
    target = constraint.get("target")
    if not isinstance(target, dict):
        raise ValueError("target must be an object.")
    if schema == "stca-library-constraints-v1":
        name = _text(constraint.get("property"), "property")
        direction = constraint.get("direction")
        tier = _number(constraint.get("tier"), "tier")
        physical = target.get("physical_cutoff")
        physical_unit = target.get("unit")
        model = target.get("model_cutoff")
        model_unit = target.get("model_unit")
        operator = target.get("operator")
    else:
        name = _text(target.get("name"), "target.name")
        direction = target.get("direction")
        tier = _number(constraint.get("tier_fraction"), "tier_fraction")
        physical = target.get("physical_train_cutoff")
        physical_unit = target.get("physical_unit")
        model = target.get("model_space_cutoff", target.get("reference_train_cutoff"))
        model_unit = target.get("model_space_unit", target.get("unit"))
        operator = target.get("label_comparison")
        # Validate even a legacy unit which is not selected for the display.
        if target.get("unit") is not None:
            _text(target["unit"], "target.unit")
    if direction not in {"high", "low"}:
        raise ValueError("direction must be 'high' or 'low'.")
    if not 0 < tier < 1:
        raise ValueError("The target tier fraction must be strictly between 0 and 1.")
    expected_operator = ">=" if direction == "high" else "<="
    if operator is not None and operator != expected_operator:
        raise ValueError("The target comparison operator conflicts with direction.")
    operator = expected_operator
    model_unit = _text(model_unit, "model unit", optional=True)
    model = _number(model, "model cutoff") if model is not None else None
    physical_unit = _text(physical_unit, "physical unit", optional=True)
    physical = _number(physical, "physical cutoff") if physical is not None else None
    if model is not None and model_unit is None:
        raise ValueError("A model cutoff requires a model unit.")
    if physical is not None and physical_unit is None:
        raise ValueError("A physical cutoff requires a physical unit.")
    if physical is not None and _LOG_UNIT.fullmatch(physical_unit):
        raise ValueError("physical cutoff cannot use a logarithmic unit; use model cutoff fields.")
    if physical is None and model is not None and model_unit is not None:
        log_unit = _LOG_UNIT.fullmatch(model_unit)
        if log_unit:
            # An explicit log10(unit) declaration supports one unambiguous inverse.
            try:
                inverted = 10.0 ** model
            except OverflowError:
                inverted = None
            if inverted is not None and math.isfinite(inverted) and inverted > 0:
                physical = inverted
                physical_unit = _text(log_unit.group(1), "physical unit")
    return {
        "name": name, "direction": direction, "tier": tier,
        "physical_cutoff": physical, "physical_unit": physical_unit,
        "model_cutoff": model, "model_unit": model_unit,
        "operator": operator, "source": _source_label(constraint),
        "learner": _learner(constraint),
    }


def _rule(constraint):
    if constraint.get("status") in {"no_valid_rule", "no_rule", "error"}:
        raise ValueError("The selected constraints do not contain a valid frozen rule.")
    feature_spec = constraint.get("feature_spec", {})
    if not isinstance(feature_spec, dict):
        raise ValueError("feature_spec must be an object when supplied.")
    if feature_spec.get("kind") not in (None, "rdkit_maccs167"):
        raise ValueError("This molecular prompt renderer requires a MACCS167 structure mapping.")
    # Core feature_spec.smiles_policy may describe an already H-capped calculation
    # input.  An explicit adapter representation is the original-structure
    # contract and must never be overwritten by this H-cap template.
    representations = []
    if constraint.get("representation") is not None:
        representations.append(constraint["representation"])
    model = constraint.get("model", {})
    if isinstance(model, dict):
        contract = model.get("custom_data_contract", {})
        if isinstance(contract, dict) and contract.get("representation") is not None:
            representations.append(contract["representation"])
    for representation in representations:
        if representation != "hcap_maccs167":
            raise ValueError("The bundled prompt requires hcap_maccs167; an explicit frozen representation cannot be changed.")
    rule = constraint.get("rule")
    if not isinstance(rule, dict):
        raise ValueError("rule must be a nonempty frozen rule object.")
    if constraint.get("combiner", "AND") != "AND":
        raise ValueError("Only an exact AND conjunction is supported.")
    keys, values = rule.get("keys"), rule.get("values")
    if not isinstance(keys, list) or not isinstance(values, list) or not keys or len(keys) != len(values):
        raise ValueError("rule.keys and rule.values must be nonempty lists of equal length.")
    literals = []
    seen = {}
    for raw_key, raw_value in zip(keys, values):
        key, value = _key(raw_key), _bit(raw_value)
        if key in seen and seen[key] != value:
            raise ValueError(f"Contradictory frozen bit requirements for K{key}.")
        if key not in seen:
            literals.append((key, value))
        seen[key] = value
    expression = " AND ".join(f"K{k}={v}" for k, v in literals)
    supplied_expression = rule.get("expression")
    if supplied_expression is not None:
        if not isinstance(supplied_expression, str):
            raise ValueError("rule.expression must be a string.")
        pieces = re.split(r"\s+AND\s+", supplied_expression.strip())
        parsed = {}
        for piece in pieces:
            match = re.fullmatch(r"K(\d+)\s*=\s*([01])", piece.strip())
            if not match:
                raise ValueError("rule.expression must use exact K<number>=0/1 AND literals.")
            key, value = int(match.group(1)), int(match.group(2))
            if key in parsed and parsed[key] != value:
                raise ValueError("rule.expression contains contradictory literals.")
            parsed[key] = value
        if parsed != seen:
            raise ValueError("rule.expression disagrees with rule.keys/rule.values.")
    signature = "STCA|AND|" + "&".join(f"K{k}={seen[k]}" for k in sorted(seen))
    if rule.get("signature") is not None and rule["signature"] != signature:
        raise ValueError("rule.signature disagrees with its exact frozen conditions.")
    definitions = {}
    supplied_literals = constraint.get("literals", [])
    if not isinstance(supplied_literals, list):
        raise ValueError("literals must be a list when supplied.")
    for literal in supplied_literals:
        if not isinstance(literal, dict):
            raise ValueError("Each literal definition must be an object.")
        key = _key(literal.get("feature_index", literal.get("feature_name")))
        if "feature_name" in literal and literal["feature_name"] != f"K{key}":
            raise ValueError("literal feature_name conflicts with its MACCS key.")
        required = _bit(literal.get("required_value"))
        if key not in seen or seen[key] != required:
            raise ValueError(f"Literal metadata for K{key} disagrees with the frozen rule.")
        definition = literal.get("definition", {})
        if not isinstance(definition, dict):
            raise ValueError(f"Definition for K{key} must be an object.")
        if key in definitions and definitions[key] != definition:
            raise ValueError(f"Conflicting MACCS definitions for K{key}.")
        definitions[key] = definition
    return {"literals": literals, "expression": expression, "signature": signature,
            "definitions": definitions}


def _objective_line(index, target, zh):
    tail = "Top" if target["direction"] == "high" else "Bottom"
    percent = _format_number(target["tier"] * 100)
    boundary = []
    if target["physical_cutoff"] is not None:
        label = "源训练物理边界" if zh else "source-training physical boundary"
        boundary.append(f"{label}: {target['operator']} {_format_number(target['physical_cutoff'])} {target['physical_unit']}")
    else:
        boundary.append("物理 cutoff 未提供" if zh else "physical cutoff not supplied")
    if target["model_cutoff"] is not None and (
        target["physical_cutoff"] is None or target["model_unit"] != target["physical_unit"]
    ):
        label = "模型尺度边界" if zh else "model-space boundary"
        boundary.append(f"{label}: {target['operator']} {_format_number(target['model_cutoff'])} {target['model_unit']}")
    source_label = "规则来源" if zh else "rule source"
    line = (f"{index}. {target['name']}; {target['direction']} / {tail} {percent}%; "
            + "; ".join(boundary) + f"; {source_label}: {target['source']}.")
    if target.get("learner"):
        label = "规则学习方法" if zh else "Rule learner"
        line += f" {label}: {target['learner']}."
    return line


def _semantics_line(key, value, definition, zh):
    prefix = f"- `K{key}={value}`: "
    if not definition:
        return prefix + ("此 artifact 未附激活定义；需用完整 MACCS167 计算核验，不猜测化学含义。" if zh else
                         "activation definition not bundled; verify with the complete MACCS167 generator, without guessing chemical meaning.")
    special = definition.get("status") == "rdkit_special_or_undefined_key" or definition.get("smarts") == "?"
    pieces = []
    if special:
        pieces.append("特殊/未定义键，使用完整 MACCS 算法" if zh else "special/undefined key; use the complete MACCS generator")
    else:
        smarts = definition.get("smarts")
        if smarts is not None:
            if not isinstance(smarts, str) or not smarts.strip():
                raise ValueError(f"SMARTS definition for K{key} must be nonempty text.")
            pieces.append(f"SMARTS `{smarts}`")
        activation = definition.get("bit_one_activation")
        count = definition.get("count_parameter")
        if count is not None:
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError(f"count_parameter for K{key} must be a nonnegative integer.")
            pieces.append(f"count_parameter={count}")
            expected = "has_substructure_match" if count == 0 else f"unique_substructure_match_count > {count}"
            if activation is None:
                activation = expected
            elif not isinstance(activation, str) or activation.strip() != expected:
                raise ValueError(f"count_parameter and bit_one_activation disagree for K{key}.")
        if activation is not None:
            if not isinstance(activation, str) or not activation.strip():
                raise ValueError(f"Activation definition for K{key} must be nonempty text.")
            label = "位 1 激活条件" if zh else "bit-one activation"
            pieces.append(f"{label}: `{activation}`")
        if not pieces:
            pieces.append("激活定义不可用，需完整 MACCS 计算" if zh else "activation definition unavailable; full MACCS calculation required")
    if value == 0:
        zero = definition.get("bit_zero_meaning")
        if zero is not None:
            if not isinstance(zero, str) or not zero.strip():
                raise ValueError(f"Zero-bit definition for K{key} must be nonempty text.")
            pieces.append(zero.strip())
        else:
            pieces.append("要求对应激活条件不成立；计数键不等于零匹配" if zh else
                          "the activation criterion must be false; a count key does not imply zero matches")
    version = definition.get("rdkit_version")
    if isinstance(version, str) and version.strip():
        pieces.append(f"definition RDKit {version.strip()}")
    return prefix + "; ".join(pieces) + "."


def render_prompt(constraints, language="zh-CN", count=20, preferences="", structure_kind=None):
    """Return a complete prompt for one rule or the AND intersection of rules.

    Accept ``stca-library-constraints-v1`` or exported
    ``stca-constraints-v1`` dictionaries, individually or as a nonempty list.
    Contradictory requirements and unresolved property/unit metadata raise
    ``ValueError``.  No scientific packages or model API are imported.
    """
    aliases = {"zh-CN": "zh-CN", "zh-cn": "zh-CN", "zh": "zh-CN", "en": "en"}
    if language not in aliases:
        raise ValueError("language must be 'zh-CN' or 'en'.")
    language = aliases[language]
    zh = language == "zh-CN"
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer.")
    if not isinstance(preferences, str):
        raise ValueError("preferences must be a string.")
    if isinstance(constraints, dict):
        constraints = [constraints]
    if not isinstance(constraints, list) or not constraints:
        raise ValueError("constraints must be an object or a nonempty list of objects.")
    kind = resolve_structure_kind(constraints, structure_kind)
    normalized, seen, shared_definitions = [], {}, {}
    for index, constraint in enumerate(constraints, start=1):
        if not isinstance(constraint, dict) or constraint.get("schema") not in _SCHEMAS:
            raise ValueError("Unsupported constraints schema.")
        target, rule = _target(constraint), _rule(constraint)
        for key, value in rule["literals"]:
            if key in seen and seen[key] != value:
                raise ValueError(f"Contradictory frozen bit requirements for K{key} across objectives.")
            seen[key] = value
            definition = rule["definitions"].get(key, {})
            if definition:
                if key in shared_definitions and shared_definitions[key] != definition:
                    raise ValueError(f"Conflicting MACCS definitions for K{key} across objectives.")
                shared_definitions[key] = definition
        normalized.append((index, target, rule))
    objectives = "\n".join(_objective_line(index, target, zh) for index, target, _ in normalized)
    rules = []
    for index, target, rule in normalized:
        label = "目标" if zh else "Objective"
        signature = "规则签名" if zh else "Rule signature"
        rules.append(f"{label} {index} — {target['name']}:\n\n`{rule['expression']}`\n\n{signature}: `{rule['signature']}`")
    semantics = "\n".join(_semantics_line(key, seen[key], shared_definitions.get(key, {}), zh)
                          for key in sorted(seen))
    if not preferences.strip():
        preferences = ("无额外化学偏好；在冻结条件内增加结构多样性。" if zh else
                       "No additional chemical preferences; diversify structures within the frozen constraints.")
    replacements = {"COUNT": str(count), "OBJECTIVES": objectives,
                    "EXACT_AND_CONDITIONS": "\n\n".join(rules),
                    "MACCS_LITERAL_SEMANTICS": semantics,
                    "CHEMICAL_PREFERENCES": preferences.strip()}
    replacements.update(_structure_text(kind, zh))
    template_path = Path(__file__).resolve().parents[1] / "assets" / "prompts" / f"generate.{language}.md"
    template = template_path.read_text(encoding="utf-8")
    if set(_SLOT.findall(template)) != _PLACEHOLDERS:
        raise ValueError("The bundled prompt template has unexpected or missing placeholders.")
    rendered = _SLOT.sub(lambda match: replacements[match.group(1)], template)
    if any(target.get("learner") == "WRAcc" for _, target, _ in normalized):
        if zh:
            rendered = rendered.replace("STCA 冻结规则", "冻结精确 AND 规则")
            rendered = rendered.replace("冻结 STCA 规则", "冻结精确 AND 规则")
            attribution = ("方法声明：标为 WRAcc 的条件来自 WRAcc 学习器，不是 STCA 算法的归纳结论。"
                           "历史 `STCA|AND|` 签名前缀仅标识精确位条件，不表示学习方法。")
        else:
            rendered = rendered.replace("frozen STCA rules", "frozen exact AND rules")
            attribution = ("Method attribution: conditions labelled WRAcc were learned by WRAcc and are not STCA training conclusions. "
                           "The historical `STCA|AND|` signature prefix identifies exact conditions, not the learner.")
        first, separator, rest = rendered.partition("\n")
        rendered = first + separator + "\n" + attribution + "\n" + rest
    if _SLOT.search(rendered):
        raise ValueError("An unresolved template placeholder remains in the prompt content.")
    return rendered


def _reject_json_constant(value):
    raise ValueError(f"Nonfinite JSON constant is not supported: {value}.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--constraints", type=Path, nargs="+", required=True,
                        help="Frozen constraints JSON file(s); multiple files are intersected with AND.")
    parser.add_argument("--language", choices=("zh-CN", "en"), default="zh-CN")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--preferences", default="")
    parser.add_argument("--structure-kind", choices=STRUCTURE_KINDS,
                        help="Output notation; defaults to the saved contract or legacy repeat-unit format.")
    parser.add_argument("--output", type=Path, required=True, help="New Markdown file; existing files are not overwritten.")
    args = parser.parse_args(argv)
    try:
        constraints = []
        for path in args.constraints:
            value = json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=_reject_json_constant)
            constraints.extend(value if isinstance(value, list) else [value])
        prompt = render_prompt(constraints, args.language, args.count, args.preferences, args.structure_kind)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(prompt)
    except (OSError, ValueError, TypeError) as exc:
        print(f"generation_prompt: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"output": str(args.output), "language": args.language,
                      "requested_count": args.count, "objectives": len(constraints),
                      "structure_kind": resolve_structure_kind(constraints, args.structure_kind),
                      "status": "prompt_rendered"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
