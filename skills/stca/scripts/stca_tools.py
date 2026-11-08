#!/usr/bin/env python3
"""Export frozen STCA constraints and intersect rules on the same candidate rows.

This adapter calls the pinned author's package. It does not learn rules, alter
prefix families, reinterpret the EC reversal, or evaluate measured properties.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from stca_runtime import environment_receipt, load_stca
from stca_io import read_csv_frame
from prepare_hcap import hcap_smiles


PROFILES = ("tg-high", "ec-low", "ec-high")
PROTOCOLS = ("paper", "source_locked")
# Exact named recipes in the pinned author's STCA.for_profile implementation.
# A generic source-only fit is not evidence of the source_locked recipe.
NAMED_PROTOCOL_RECIPES = {
    "paper_tg_core_v1": ("paper", "core_harmonic", True),
    "paper_ec_family_v15_core_v1": ("paper", "core_harmonic", True),
    "tg_source_f1_as_v1": ("source_locked", "source_as", False),
    "ec_v15_family_source_as_v1": ("source_locked", "source_as", False),
}

# User-facing property routing. STCA has native Tg/EC profiles; the published
# paper also evaluates transfer of Tg-derived thermal rules to Tm/Td/TC and
# EC-derived electrical rules to epsilon-AC. Each objective keeps its own
# direction and tier; there is no shared global "joint tier".
PROPERTY_ALIASES = {
    "tg": "tg", "glass_transition": "tg", "glass transition": "tg",
    "glass-transition temperature": "tg", "玻璃化转变温度": "tg",
    "tm": "tm", "melting_temperature": "tm", "melting temperature": "tm", "熔点": "tm",
    "td": "td", "decomposition_temperature": "td", "decomposition temperature": "td",
    "thermal_decomposition_temperature": "td", "分解温度": "td",
    "tc": "tc", "thermal_conductivity": "tc", "thermal conductivity": "tc", "导热系数": "tc",
    "ec": "ec", "electrical_conductivity": "ec", "electrical conductivity": "ec", "电导率": "ec",
    "epsilon": "epsilon_ac", "epsilon_ac": "epsilon_ac", "eps": "epsilon_ac",
    "eps_ac": "epsilon_ac", "ε": "epsilon_ac", "ε-ac": "epsilon_ac",
    "permittivity": "epsilon_ac", "dielectric_constant": "epsilon_ac",
    "dielectric constant": "epsilon_ac", "介电常数": "epsilon_ac",
}
PROPERTY_LABELS = {
    "tg": "Tg", "tm": "Tm", "td": "Td", "tc": "TC",
    "ec": "EC", "epsilon_ac": "ε-AC",
}
PROPERTY_SLUGS = {
    "tg": "tg", "tm": "tm", "td": "td", "tc": "tc",
    "ec": "ec", "epsilon_ac": "epsilon_ac",
}
THERMAL_TIERS = (0.30, 0.20, 0.10)
ELECTRICAL_TIERS = (0.20, 0.15, 0.10, 0.05)
# Reference thresholds reported in the paper/SI. They are explanatory and are
# not used to overwrite a user-specified tier or measured-data cutoff.
PAPER_REFERENCE_THRESHOLDS = {
    ("tg", "high"): {0.30: {"value": 204.0, "unit": "degC"},
                       0.20: {"value": 238.0, "unit": "degC"},
                       0.10: {"value": 275.0, "unit": "degC"}},
    ("tm", "high"): {0.30: {"value": 274.0, "unit": "degC"},
                       0.20: {"value": 284.0, "unit": "degC"},
                       0.10: {"value": 340.0, "unit": "degC"}},
    ("td", "high"): {0.30: {"value": 472.0, "unit": "degC"},
                       0.20: {"value": 500.0, "unit": "degC"},
                       0.10: {"value": 537.0, "unit": "degC"}},
    ("tc", "high"): {0.30: {"value": 0.26, "unit": "W/(m·K)"},
                       0.20: {"value": 0.32, "unit": "W/(m·K)"},
                       0.10: {"value": 0.40, "unit": "W/(m·K)"}},
    ("ec", "high"): {0.20: {"value": -4.26760624, "unit": "log10(S/cm)"},
                         0.15: {"value": -3.467070153, "unit": "log10(S/cm)"},
                         0.10: {"value": -2.37675071, "unit": "log10(S/cm)"},
                         0.05: {"value": -1.050233376, "unit": "log10(S/cm)"}},
    ("ec", "low"): {0.20: {"value": -12.7721133, "unit": "log10(S/cm)"},
                        0.15: {"value": -13.64915558, "unit": "log10(S/cm)"},
                        0.10: {"value": -14.7212464, "unit": "log10(S/cm)"},
                        0.05: {"value": -15.979303655, "unit": "log10(S/cm)"}},
    ("epsilon_ac", "high"): {0.20: {"value": 4.47, "unit": "dimensionless"},
                               0.15: {"value": 5.01, "unit": "dimensionless"},
                               0.10: {"value": 6.03, "unit": "dimensionless"},
                               0.05: {"value": 9.33, "unit": "dimensionless"}},
    ("epsilon_ac", "low"): {0.20: {"value": 2.69, "unit": "dimensionless"},
                              0.15: {"value": 2.60, "unit": "dimensionless"},
                              0.10: {"value": 2.50, "unit": "dimensionless"},
                              0.05: {"value": 2.29, "unit": "dimensionless"}},
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _object_hash(obj) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _json(path: Path):
    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON value: {value}")

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Repeated JSON key: {key}")
            result[key] = value
        return result

    if path.stat().st_size > 10_000_000:
        raise ValueError("Configuration exceeds 10 MB.")
    return json.loads(path.read_text(encoding="utf-8-sig"),
                      parse_constant=reject_constant, object_pairs_hook=unique_keys)


def _write_json(path: Path, obj):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _new_directory(path) -> Path:
    result = Path(path).expanduser().resolve()
    if result.exists():
        raise FileExistsError(f"Output directory already exists: {result}; choose a new directory.")
    result.parent.mkdir(parents=True, exist_ok=True)
    result.mkdir()
    return result


def _tier(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Each tier must be a numeric fraction such as 0.20.")
    if not math.isfinite(value) or not 0 < value < 1:
        raise ValueError("Tier must be strictly between 0 and 1.")
    return float(value)


def _named_protocol(artifact: dict):
    """Interpret saved recipe metadata without changing the frozen artifact."""
    provenance = artifact["provenance"]
    recorded = provenance.get("paired_protocol")
    protocol_id = provenance.get("protocol_id")
    recipe = NAMED_PROTOCOL_RECIPES.get(protocol_id)
    if recipe is None:
        if recorded is not None:
            raise ValueError("Saved paired_protocol cannot be verified from a known pinned named recipe.")
        return None, "not_a_known_named_recipe"
    protocol, selection, uses_external_labels = recipe
    if (provenance.get("selection_protocol") != selection or
            provenance.get("external_labels_used_for_fit") is not uses_external_labels):
        raise ValueError("Saved protocol_id conflicts with its selection protocol or external-label flag.")
    config = artifact.get("training_config")
    if config is not None and (not isinstance(config, dict) or
                               config.get("protocol_id") != protocol_id or
                               config.get("selection") != selection):
        raise ValueError("Saved training_config conflicts with the named protocol provenance.")
    if recorded is not None and recorded != protocol:
        raise ValueError("Saved paired_protocol conflicts with the named training recipe.")
    return protocol, "verified_paired_protocol" if recorded is not None else "known_pinned_recipe"


def _load_model(stca, spec: dict, base_dir: Path):
    profile, model_file = spec.get("profile"), spec.get("model")
    if bool(profile) == bool(model_file):
        raise ValueError("Specify exactly one of profile or model.")
    protocol = spec.get("protocol")
    if protocol is not None and protocol not in PROTOCOLS:
        raise ValueError("Protocol must be paper or source_locked.")
    if profile:
        if profile not in PROFILES:
            raise ValueError(f"Unknown profile {profile!r}; choose {PROFILES}.")
        if protocol is None:
            raise ValueError("A pretrained profile requires an explicit protocol.")
        model = stca.load_pretrained(profile, protocol=protocol, warn=False)
        origin = {"kind": "pretrained_profile", "profile": profile, "protocol": protocol}
    else:
        if not isinstance(model_file, str):
            raise ValueError("Model must be a JSON filename.")
        path = Path(model_file).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        path = path.resolve()
        model = stca.ScreeningModel.load(path)
        origin = {"kind": "saved_model", "path": str(path), "file_sha256": _sha256(path)}
    artifact = model.artifact
    saved_protocol, protocol_basis = _named_protocol(artifact)
    if protocol is not None and saved_protocol != protocol:
        raise ValueError(
            f"Requested protocol {protocol!r} differs from the verified saved named protocol "
            f"{saved_protocol!r}; preserve the model's own recipe."
        )
    metadata = {
        "origin": origin,
        "artifact_sha256": _object_hash(artifact),
        "package_version": artifact.get("package_version"),
        "paired_protocol": model.provenance.get("paired_protocol"),
        "resolved_protocol": saved_protocol,
        "protocol_resolution": protocol_basis,
        "protocol_id": model.provenance.get("protocol_id"),
        "selection_protocol": model.provenance.get("selection_protocol"),
        "external_labels_used_for_fit": model.provenance.get("external_labels_used_for_fit"),
        "provenance": model.provenance,
        "custom_data_contract": _custom_contract(artifact),
        "generic_protocol_retained": saved_protocol is None,
    }
    return model, metadata


def _custom_contract(artifact: dict) -> dict:
    caller = artifact.get("provenance", {}).get("caller_metadata", {})
    contract = caller.get("custom_data_contract", {}) if isinstance(caller, dict) else {}
    if not isinstance(contract, dict):
        raise ValueError("Saved custom_data_contract must be an object.")
    return contract


def _property_token(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A property must be a nonempty string.")
    key = re.sub(r"\s+", " ", value.strip().lower().replace("–", "-").replace("—", "-"))
    return PROPERTY_ALIASES.get(key, key)


def _check_target_metadata(requirement: dict, model):
    """Check requested target against saved semantics; never guess equivalences."""
    a = model.artifact
    contract = _custom_contract(a)
    actual = contract.get("property", a["target_name"])
    requested = requirement.get("property")
    transfer = requested is not None and _property_token(requested) != _property_token(actual)
    allowed = requirement.get("allow_transfer", False)
    if not isinstance(allowed, bool):
        raise ValueError("allow_transfer must be a boolean.")
    if transfer and not allowed:
        raise ValueError(
            f"Requested property {requested!r} differs from model property {actual!r}. "
            "Cross-property screening requires explicit allow_transfer:true and is an unvalidated transfer hypothesis."
        )
    direction = requirement.get("direction")
    if direction is not None and direction != a["direction"]:
        raise ValueError("Requested direction conflicts with the frozen model direction.")
    declared_source = requirement.get("source_property")
    if declared_source is not None and _property_token(declared_source) != _property_token(actual):
        raise ValueError("source_property conflicts with the saved model target.")
    if not transfer and requirement.get("objective_unit") is not None:
        actual_unit = contract.get("original_unit", a["target_unit"])
        if str(requirement["objective_unit"]).strip() != str(actual_unit).strip():
            raise ValueError(f"Requested unit does not match saved unit {actual_unit!r}; no implicit unit conversion is performed.")
    return {
        "requested_property": requested or actual,
        "source_property": actual,
        "cross_property_transfer": transfer,
        "allow_transfer": allowed,
        "measured_target_performance_known": False,
        "performance_warning": (
            "Cross-property structural proxy only. The trial includes weak and negative transfer; "
            "no target-property cutoff or performance guarantee follows from this rule."
            if transfer else "Rule compliance is not a measured-property success guarantee."
        ),
    }


def _target_metadata(artifact: dict, entry: dict) -> dict:
    contract = _custom_contract(artifact)
    transform = contract.get("transform", "none")
    kind = transform.get("kind", transform.get("name", "none")) if isinstance(transform, dict) else transform
    model_cutoff = entry.get("train_cutoff")
    physical_cutoff = model_cutoff
    original_unit = contract.get("original_unit", artifact["target_unit"])
    model_unit = contract.get("model_unit", artifact["target_unit"])
    log_pattern = r"log10\s*\(\s*([^()]+?)\s*\)"
    original_log_unit = re.fullmatch(log_pattern, str(original_unit).strip(), re.IGNORECASE)
    model_log_unit = re.fullmatch(log_pattern, str(model_unit).strip(), re.IGNORECASE)
    already_log = bool(contract.get("already_log", False) or original_log_unit)
    physical_unit = original_unit
    if model_log_unit is not None:
        physical_unit = model_log_unit.group(1)
    elif original_log_unit is not None:
        physical_unit = original_log_unit.group(1)
    elif already_log:
        # A logarithmic value without a declared base unit cannot be relabelled.
        physical_unit = None
    if kind not in (None, "none", "identity", "log10"):
        # Unknown transformations are not inverted by assumption.
        physical_cutoff = None
    elif (kind == "log10" or already_log or model_log_unit is not None) and model_cutoff is not None:
        try:
            physical_cutoff = 10.0 ** float(model_cutoff)
        except OverflowError:
            physical_cutoff = None
        if physical_cutoff is not None and (not math.isfinite(physical_cutoff) or physical_cutoff <= 0):
            physical_cutoff = None
    if physical_unit is None:
        physical_cutoff = None
    return {
        "name": artifact["target_name"], "unit": artifact["target_unit"],
        "direction": artifact["direction"],
        "reference_train_cutoff": model_cutoff,
        "model_space_cutoff": model_cutoff,
        "model_space_unit": model_unit,
        "physical_train_cutoff": physical_cutoff,
        "physical_unit": physical_unit,
        "target_transform": transform,
        "input_already_logarithmic": already_log,
        "label_comparison": ">=" if artifact["direction"] == "high" else "<=",
        "cutoff_role": "Stored training-label boundary; not a property prediction or guarantee for a selected structure.",
    }


def _maccs_definition(key: int):
    """Read installed RDKit definitions; the generated fingerprint stays authoritative."""
    try:
        from rdkit import rdBase
        from rdkit.Chem import MACCSkeys
    except ImportError:
        return {"status": "rdkit_unavailable", "verification": "RDKit MACCS bit only; no inferred chemical name"}
    value = MACCSkeys.smartsPatts.get(key)
    item = {"rdkit_version": rdBase.rdkitVersion, "verification": "MACCSkeys.GenMACCSKeys(mol)[key]"}
    if value is not None and value[0] != "?":
        pattern, count = value
        item.update({"status": "installed_rdkit_smarts_definition", "smarts": pattern,
                     "count_parameter": int(count),
                     "bit_one_activation": ("has_substructure_match" if count == 0
                                            else f"unique_substructure_match_count > {count}"),
                     "bit_zero_meaning": "The bit-one activation criterion is not met; for a count key this need not mean no matches."})
    else:
        item.update({"status": "rdkit_special_or_undefined_key",
                     "note": "Use RDKit's complete MACCS generator; do not replace this key with a guessed SMARTS."})
    return item


def _constraint(stca, model, metadata, tier):
    artifact = model.artifact
    key = format(tier, ".12g")
    if key not in artifact["tiers"]:
        raise ValueError(f"Tier {tier} is unavailable; available tiers: {model.tiers}. No interpolation is performed.")
    entry = artifact["tiers"][key]
    try:
        rule = model.rule_for(tier)
    except stca.NoValidRuleError:
        rule = None
    literals = []
    if rule is not None:
        for position, required_value in zip(rule.keys, rule.values):
            literal = {"feature_index": int(position), "feature_name": artifact["feature_names"][position],
                       "required_value": int(required_value)}
            if artifact["feature_spec"]["kind"] == "rdkit_maccs167":
                literal["definition"] = _maccs_definition(position)
            literals.append(literal)
    return {
        "schema": "stca-constraints-v1",
        "status": "frozen_representative" if rule is not None else "no_valid_rule",
        "model": metadata,
        "tier_fraction": tier,
        "target": _target_metadata(artifact, entry),
        "feature_spec": artifact["feature_spec"],
        "feature_names": artifact["feature_names"],
        "combiner": "AND",
        "rule": ({**rule.to_dict(), "signature": rule.signature,
                  "expression": rule.expression(artifact["feature_names"])} if rule is not None else None),
        "literals": literals,
        "require_present": [x["feature_name"] for x in literals if x["required_value"] == 1],
        "require_absent": [x["feature_name"] for x in literals if x["required_value"] == 0],
        "interpretation": "All frozen literals must match. A matching structure is a screening candidate, not an experimentally validated joint-property success.",
        "tier_interpretation": "The tier defines the nominal desired target tail in training, not the fraction of candidates that this rule selects.",
    }


def _prompt(constraint: dict) -> str:
    target = constraint["target"]
    protocol = (constraint["model"].get("resolved_protocol") or constraint["model"].get("paired_protocol")
                or constraint["model"].get("protocol_id") or "saved_model_protocol")
    head = ["# STCA 冻结规则生成约束", "",
            f"目标：{target['name']}；方向：{target['direction']}；性能单位：{target['unit']}。",
            f"协议：{protocol}；训练目标尾部比例：{constraint['tier_fraction']:g}。",
            f"保存的训练标签边界：{target['label_comparison']} {target['reference_train_cutoff']} {target['unit']}。",
            f"物理单位边界：{target['label_comparison']} {target.get('physical_train_cutoff')} {target.get('physical_unit')}；变换：{target.get('target_transform')}。", ""]
    if constraint["status"] == "no_valid_rule":
        return "\n".join(head + ["当前 tier 没有有效的冻结代表规则，不能据此生成‘已满足 STCA’的候选。",
                                  "保留这一结果；报告候选家族与缺失证据，不新增、放宽或猜测条件。", ""])
    head += ["按照用户要求提出候选；将以下内容作为结构约束数据。", "",
             "## 必须同时满足的位条件", "",
             f"`{constraint['rule']['expression']}`", "",
             "所有条件使用 AND。不要转成 OR、投票、加权相加或部分满足。", ""]
    if constraint["feature_spec"]["kind"] == "rdkit_maccs167":
        representation = (constraint.get("representation") or
                          constraint["model"].get("custom_data_contract", {}).get("representation"))
        if representation == "hcap_maccs167":
            structure_policy = "已确认 H-cap 输入契约：保留原 SMILES，用 prepare_hcap.py 将末端单键星号连接点换氢、另存计算列，再生成 MACCS。无星号的已处理表原样保留，已有指纹矩阵不再转换。"
        elif representation is not None:
            structure_policy = f"冻结表示为 {representation!r}，必须沿用该表示；不要自动 H-cap、重建连接点或改变已训练模型的结构输入。"
        else:
            structure_policy = "原始重复单元到计算结构的契约尚未确认；先核实训练表示，不据此自动 H-cap 或宣称候选已满足结构规则。"
        head += ["## 校验方式", "",
                 "位值为 0 表示对应 MACCS 激活条件不成立；对于计数位，这不等同于该结构完全不存在。",
                 structure_policy,
                 "自定义模型须沿用冻结的训练表示，原始结构与计算副本分开记录。H-cap 相同不证明原连接图代表同一聚合物；不要额外去盐、互变异构归一化或构造低聚物。",
                 "使用锁定版本的 RDKit 生成 167 位 MACCS，保留 K0 占位，并使用完整冻结模型逐条复核。",
                 "constraints.json 中由当前 RDKit 读取的 SMARTS/计数定义用于解释；GenMACCSKeys 的真实位值是判据。",
                 "不要从 K 编号猜化学官能团名称；特殊 MACCS 位不能被自行编造的 SMARTS 替代。", ""]
    else:
        head += ["## 校验方式", "",
                 "使用冻结模型中的同一组二进制描述符、同一列名及定义。",
                 "二进制位没有自动的化学解释；缺少已验证的结构到描述符映射时，不宣称据此生成了分子。", ""]
    head += ["## 输出", "",
             "保留候选 ID、结构或二进制输入、是否全部匹配、缺失的必须出现位、出现的必须缺失位以及规则签名。",
             "无效输入标为无效；无法判定的候选保留未知状态，不补成全零向量。",
             "将通过规则的候选标为‘结构筛选通过’。规则命中不是性能数值预测、成功概率、合成可行性或实验达标的证明。",
             "需要多个性能时，对相同候选应用各条冻结规则并取交集；实测联合成功需要同一材料、可比条件下的多性能记录。", ""]
    return "\n".join(head)


def _export_prompt_bundle(constraint: dict, *, count=20, preferences=""):
    """Render complete prompts only for a verified H-cap MACCS contract.

    A descriptive fallback is an export result with an explicit unavailable
    status, never a silently weakened or allegedly complete generation prompt.
    """
    reason = detail = None
    if constraint["status"] != "frozen_representative" or constraint.get("rule") is None:
        reason, detail = "no_valid_rule", "No valid frozen representative exists at the selected tier."
    elif constraint["feature_spec"].get("kind") != "rdkit_maccs167":
        reason, detail = "unsupported_features", "Custom binary descriptors have no verified molecular generation mapping."
    else:
        metadata = constraint["model"]
        representation = metadata.get("custom_data_contract", {}).get("representation")
        basis = "saved_custom_data_contract"
        if representation is None:
            origin, provenance = metadata.get("origin", {}), metadata.get("provenance", {})
            profile = origin.get("profile")
            known_protocol = ("paper_tg_core_v1" if profile == "tg-high" else
                              "paper_ec_family_v15_core_v1" if profile in {"ec-low", "ec-high"} else None)
            if (origin.get("kind") == "pretrained_profile" and origin.get("protocol") == "paper"
                    and metadata.get("resolved_protocol") == "paper" and known_protocol is not None
                    and metadata.get("protocol_id") == known_protocol
                    and provenance.get("preset_profile") == profile
                    and provenance.get("kind") == "verified_refit_paper"
                    and provenance.get("verification_source") == "author_uploaded_results_20260921"):
                # The named profiles consume already prepared archived SMILES.
                # Author confirmation of their upstream H-cap preparation is
                # recorded in references/provenance.md; core as_provided is not
                # an instruction to change the original repeat-unit contract.
                representation = "hcap_maccs167"
                basis = "verified_named_paper_profile_author_confirmed_hcap"
        if representation is None:
            reason, detail = "representation_unconfirmed", "The saved model does not declare a confirmed H-cap input contract."
        elif representation != "hcap_maccs167":
            reason, detail = "unsupported_representation", f"The frozen representation {representation!r} cannot be changed to H-cap."
        else:
            constraint["representation"] = representation
            constraint["generation_representation_provenance"] = {
                "basis": basis, "reference": "references/provenance.md" if basis.startswith("verified_named") else
                "model.custom_data_contract.representation",
            }
    if reason is None:
        try:
            from generation_prompt import render_prompt
            english = render_prompt(constraint, language="en", count=count, preferences=preferences)
            chinese = render_prompt(constraint, language="zh-CN", count=count, preferences=preferences)
        except (ValueError, TypeError, OSError, ImportError) as exc:
            reason, detail = "render_rejected", f"{type(exc).__name__}: {exc}"
        else:
            return {"prompt.md": chinese, "prompt.en.md": english, "prompt.zh-CN.md": chinese}, {
                "status": "rendered", "kind": "complete_generation_prompt", "reason": None,
                "requested_count": count,
                "files": {"default": "prompt.md", "en": "prompt.en.md", "zh-CN": "prompt.zh-CN.md"},
                "generation_executed": False,
            }
    summary = ("# 冻结约束说明（不是完整生成 prompt）\n\n"
               f"完整生成 prompt 当前不可用：`{reason}`。{detail}\n\n"
               "下文仅保留冻结约束摘要；不要将其标为已生成或已核验的聚合物候选。\n\n"
               + _prompt(constraint))
    return {"prompt.md": summary}, {
        "status": "not_available", "kind": "constraint_summary", "reason": reason,
        "detail": detail, "requested_count": count, "files": {"summary": "prompt.md"},
        "generation_executed": False,
    }


def export_rules(args, stca) -> int:
    spec = {"profile": args.profile, "model": args.model, "protocol": args.protocol}
    model, metadata = _load_model(stca, spec, Path.cwd())
    tier = _tier(args.tier)
    constraint = _constraint(stca, model, metadata, tier)
    rules = model.rules(tier=tier)
    receipt = environment_receipt(args.source)
    receipt.update({"operation": "export-rules", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "model": metadata, "tier": tier, "training_performed": False})
    constraint["runtime"] = receipt
    prompts, prompt_status = _export_prompt_bundle(
        constraint, count=getattr(args, "count", 20), preferences=getattr(args, "preferences", ""))
    constraint["prompt_generation"] = prompt_status
    receipt["prompt_generation"] = prompt_status
    output = _new_directory(args.output_dir)
    rules.to_csv(output / "rules.csv", index=False)
    _write_json(output / "constraints.json", constraint)
    for filename, prompt in prompts.items():
        (output / filename).write_text(prompt, encoding="utf-8")
    _write_json(output / "prompt_generation.json", prompt_status)
    _write_json(output / "manifest.json", receipt)
    print(json.dumps({"output_directory": str(output), "status": constraint["status"],
                      "family_rule_count": len(rules), "representative": constraint["rule"],
                      "prompt_generation": prompt_status},
                     ensure_ascii=False))
    return 0


def _normalise_property(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Each objective needs a nonempty property name.")
    key = value.strip().lower().replace("–", "-").replace("—", "-")
    key = re.sub(r"\s+", " ", key)
    canonical = PROPERTY_ALIASES.get(key)
    if canonical is None:
        raise ValueError(
            f"Unsupported property {value!r}. Supported properties are Tg, Tm, Td, TC, EC and ε-AC."
        )
    return canonical


def _normalise_direction(value, property_name: str) -> str:
    if value is None and property_name in {"tg", "tm", "td", "tc"}:
        return "high"
    if not isinstance(value, str):
        raise ValueError("Each EC or ε-AC objective needs direction='high' or direction='low'.")
    aliases = {
        "high": "high", "higher": "high", "max": "high", "maximize": "high",
        "top": "high", "高": "high", "提高": "high",
        "low": "low", "lower": "low", "min": "low", "minimize": "low",
        "bottom": "low", "低": "low", "降低": "low",
    }
    result = aliases.get(value.strip().lower())
    if result is None:
        raise ValueError("Objective direction must be high or low.")
    if property_name in {"tg", "tm", "td", "tc"} and result != "high":
        raise ValueError("Published thermal transfer rules support the high direction for Tg, Tm, Td and TC.")
    return result


def _objective_identity(objective: dict, prop_slug: str, direction: str, tier: float, index: int):
    raw_name = objective.get("name") or f"{prop_slug}_{direction}_{index + 1}"
    name = re.sub(r"[^A-Za-z0-9_]", "_", str(raw_name))
    if not re.match(r"[A-Za-z]", name):
        name = "objective_" + name
    name = name[:48]
    return name, objective.get("label") or f"{objective['property']} {direction} ({tier:g})"


def _route_objective(objective: dict, index: int, *, base_dir=None, stca=None) -> tuple[dict, dict]:
    if not isinstance(objective, dict):
        raise ValueError("Each objective must be a JSON object.")
    allowed = {"name", "property", "direction", "tier", "cutoff", "unit", "protocol", "label", "model", "allow_transfer"}
    extras = set(objective) - allowed
    if extras:
        raise ValueError(f"Unknown objective fields: {sorted(extras)}")
    if objective.get("tier") is None:
        raise ValueError("Each objective requires an explicit tier. A physical cutoff never chooses the nearest paper tier.")
    tier = _tier(objective["tier"])
    cutoff = objective.get("cutoff")
    if cutoff is not None and (isinstance(cutoff, bool) or not isinstance(cutoff, (int, float)) or not math.isfinite(cutoff)):
        raise ValueError("Objective cutoff metadata must be finite.")
    if "allow_transfer" in objective and not isinstance(objective["allow_transfer"], bool):
        raise ValueError("allow_transfer must be true or false.")
    if "label" in objective and not isinstance(objective["label"], str):
        raise ValueError("Objective label must be a string.")
    if objective.get("model") is not None:
        if stca is None:
            raise ValueError("Saved-model objective planning requires the pinned runtime.")
        prop = objective.get("property")
        _property_token(prop)
        direction = objective.get("direction")
        if direction not in ("high", "low"):
            raise ValueError("Saved-model objectives require explicit direction high or low.")
        model, metadata = _load_model(stca, objective, Path(base_dir or Path.cwd()))
        if format(tier, ".12g") not in model.artifact["tiers"]:
            raise ValueError(f"Tier {tier} not available in the saved model.")
        name, label = _objective_identity(objective, re.sub(r"[^a-z0-9]", "_", prop.lower()), direction, tier, index)
        requirement = {
            "name": name, "label": label, "model": metadata["origin"]["path"], "tier": tier,
            "property": prop, "direction": direction, "tier_source": "user_tier",
            "allow_transfer": objective.get("allow_transfer", False),
            "objective_cutoff": cutoff, "objective_unit": objective.get("unit"),
        }
        if objective.get("protocol") is not None:
            requirement["protocol"] = objective["protocol"]
        checked = _check_target_metadata(requirement, model)
        requirement.update({"source_property": checked["source_property"],
                            "transfer_role": "explicit_saved_model_transfer" if checked["cross_property_transfer"] else "saved_model_native"})
        return {**requirement, "domain": "saved_model", "model_metadata": metadata,
                "target_evidence": checked, "cutoff_metadata_only": True}, requirement

    prop = _normalise_property(objective.get("property"))
    direction = _normalise_direction(objective.get("direction"), prop)
    domain = "thermal" if prop in {"tg", "tm", "td", "tc"} else "electrical"
    if prop in {"tg", "tm", "td", "tc"}:
        profile, source_property, available = "tg-high", "Tg", THERMAL_TIERS
    else:
        profile = "ec-high" if direction == "high" else "ec-low"
        source_property, available = "EC", ELECTRICAL_TIERS
    transfer = prop not in {"tg", "ec"}
    if transfer and objective.get("allow_transfer") is not True:
        raise ValueError(f"{PROPERTY_LABELS[prop]} uses a cross-property paper proxy; add allow_transfer:true or supply a target-specific saved model.")
    if not any(abs(tier - allowed_tier) < 1e-12 for allowed_tier in available):
        raise ValueError(f"Tier {tier:g} unavailable for {PROPERTY_LABELS[prop]}; choose {list(available)}.")
    protocol = objective.get("protocol", "paper")
    if protocol not in PROTOCOLS:
        raise ValueError("Objective protocol must be paper or source_locked.")
    transfer_role = "native" if not transfer else f"{source_property}-derived cross-property structural proxy"
    name, label = _objective_identity(objective, PROPERTY_SLUGS[prop], direction, tier, index)
    requirement = {
        "name": name, "label": label, "profile": profile, "protocol": protocol, "tier": tier,
        "property": PROPERTY_LABELS[prop], "direction": direction,
        "source_property": source_property, "transfer_role": transfer_role,
        "tier_source": "user_tier", "allow_transfer": objective.get("allow_transfer", False),
        "objective_cutoff": cutoff, "objective_unit": objective.get("unit"),
    }
    return {**requirement, "domain": domain,
            "paper_reference_threshold": PAPER_REFERENCE_THRESHOLDS.get((prop, direction), {}).get(tier),
            "cutoff_mapping": None, "cutoff_metadata_only": True,
            "target_evidence": {"cross_property_transfer": transfer,
                                "measured_target_performance_known": False,
                                "performance_warning": "Cross-property rule compliance is a transfer hypothesis; negative transfer is possible." if transfer else "Rule compliance is not property confirmation."}}, requirement


def plan_objectives(args) -> int:
    source_path = Path(args.objectives).expanduser().resolve()
    source = _json(source_path)
    if not isinstance(source, dict):
        raise ValueError("Objective specification must be a JSON object.")
    allowed = {
        "schema", "id_column", "smiles_column", "hcap_before_maccs",
        "hcap_output_column", "objectives",
    }
    extras = set(source) - allowed
    if extras:
        raise ValueError(f"Unknown objective specification fields: {sorted(extras)}")
    if source.get("schema", "stca-objectives-v1") != "stca-objectives-v1":
        raise ValueError("Unsupported objective specification schema.")
    objectives = source.get("objectives")
    if not isinstance(objectives, list) or not objectives:
        raise ValueError("Provide at least one objective.")
    id_column = source.get("id_column")
    smiles_column = source.get("smiles_column", "SMILES")
    hcap_before_maccs = source.get("hcap_before_maccs", True)
    hcap_output_column = source.get("hcap_output_column", "stca_calculation_smiles_hcap")
    if id_column is not None and (not isinstance(id_column, str) or not id_column.strip()):
        raise ValueError("id_column must be null/omitted or a nonempty arbitrary column name.")
    if not isinstance(smiles_column, str) or not smiles_column.strip():
        raise ValueError("smiles_column must be a nonempty string.")
    if not isinstance(hcap_before_maccs, bool):
        raise ValueError("hcap_before_maccs must be true or false.")
    if (not isinstance(hcap_output_column, str) or not hcap_output_column.strip() or
            hcap_output_column == smiles_column):
        raise ValueError("hcap_output_column must be a nonempty calculation-only column distinct from smiles_column.")
    normalised, requirements, names = [], [], set()
    saved_runtime = load_stca(getattr(args, "source", None)) if any(isinstance(x, dict) and x.get("model") is not None for x in objectives) else None
    for index, objective in enumerate(objectives):
        plan, requirement = _route_objective(objective, index, base_dir=source_path.parent, stca=saved_runtime)
        if requirement["name"] in names:
            raise ValueError(f"Repeated generated objective name: {requirement['name']}")
        names.add(requirement["name"])
        normalised.append(plan)
        requirements.append(requirement)
    config = {
        "schema": "stca-joint-config-v1",
        "id_column": id_column,
        "smiles_column": smiles_column,
        "hcap_before_maccs": hcap_before_maccs,
        "hcap_output_column": hcap_output_column,
        "requirements": requirements,
    }
    result = {
        "schema": "stca-objective-plan-v1",
        "source": {"path": str(source_path), "sha256": _sha256(source_path)},
        "combiner": "AND" if len(requirements) > 1 else "single_objective",
        "objective_count": len(requirements),
        "objectives": normalised,
        "joint_config": config,
        "interpretation": (
            "Each objective keeps its own property, direction and explicit tier. Cross-property proxies "
            "require allow_transfer:true and carry no measured target-performance guarantee. "
            "Cutoff metadata never selects or changes a tier. Saved custom models retain their own target contract."
        ),
    }
    output = _new_directory(args.output_dir)
    _write_json(output / "objective_plan.json", result)
    _write_json(output / "joint_config.json", config)
    print(json.dumps({"output_directory": str(output), "objective_count": len(requirements),
                      "joint_config": str(output / "joint_config.json")}, ensure_ascii=False))
    return 0


def _config_object(config: dict) -> dict:
    config = json.loads(json.dumps(config, ensure_ascii=False))
    if not isinstance(config, dict):
        raise ValueError("Joint configuration must be a JSON object.")
    allowed = {
        "schema", "id_column", "smiles_column", "hcap_before_maccs",
        "hcap_output_column", "features", "requirements",
    }
    if set(config) - allowed:
        raise ValueError(f"Unknown joint configuration fields: {sorted(set(config) - allowed)}")
    if "schema" in config and config["schema"] != "stca-joint-config-v1":
        raise ValueError("Unsupported joint configuration schema.")
    id_column = config.get("id_column")
    if id_column is not None and (not isinstance(id_column, str) or not id_column.strip()):
        raise ValueError("id_column must be null/omitted or a nonempty arbitrary column name.")
    config["id_column"] = id_column
    smiles_column = config.get("smiles_column", "SMILES")
    if not isinstance(smiles_column, str) or not smiles_column.strip():
        raise ValueError("smiles_column must be a nonempty column name.")
    config["smiles_column"] = smiles_column
    hcap_before_maccs = config.get("hcap_before_maccs", True)
    if not isinstance(hcap_before_maccs, bool):
        raise ValueError("hcap_before_maccs must be true or false.")
    config["hcap_before_maccs"] = hcap_before_maccs
    hcap_output_column = config.get("hcap_output_column", "stca_calculation_smiles_hcap")
    if (not isinstance(hcap_output_column, str) or not hcap_output_column.strip() or
            hcap_output_column == smiles_column):
        raise ValueError("hcap_output_column must be a distinct nonempty calculation-only column name.")
    config["hcap_output_column"] = hcap_output_column
    features = config.get("features")
    if features is not None:
        if (not isinstance(features, list) or not features or
                any(not isinstance(x, str) or not x for x in features) or len(set(features)) != len(features)):
            raise ValueError("features must be an explicit nonempty list of distinct binary column names.")
        if config["id_column"] is not None and config["id_column"] in features:
            raise ValueError("The identifier must not be used as a binary descriptor.")
    requirements = config.get("requirements")
    if not isinstance(requirements, list) or len(requirements) < 1:
        raise ValueError("Screening requires at least one frozen model requirement.")
    names = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise ValueError("Each requirement must be an object.")
        extras = set(requirement) - {
            "name", "label", "profile", "model", "protocol", "tier",
            "property", "direction", "source_property", "transfer_role", "tier_source",
            "objective_cutoff", "objective_unit", "allow_transfer",
        }
        if extras:
            raise ValueError(f"Unknown requirement fields: {sorted(extras)}")
        name = requirement.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,47}", name):
            raise ValueError("Each requirement needs a name starting with a letter and containing only letters, digits or underscores.")
        if name in names:
            raise ValueError(f"Repeated requirement name: {name}")
        names.add(name)
        if "label" in requirement and not isinstance(requirement["label"], str):
            raise ValueError("Requirement labels must be strings.")
        requirement["tier"] = _tier(requirement.get("tier"))
    return config


def _config(path: Path) -> dict:
    return _config_object(_json(path))


def _read_candidates(path: Path, config: dict):
    frame = read_csv_frame(path)
    required = list(config.get("features") or [config["smiles_column"]])
    if config["id_column"] is not None:
        required.insert(0, config["id_column"])
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Candidate columns missing: {sorted(missing)}")
    if any(name.startswith("stca_") for name in frame.columns):
        raise ValueError("Input contains reserved stca_ output columns; use the original candidate table.")
    if config["id_column"] is None:
        ids = frame.index.to_series().map(lambda index: f"row-{index + 1:06d}").astype("string")
        identity = {
            "id_column": None,
            "output_id_column": "stca_candidate_id",
            "source": "generated_from_input_row_position",
            "arbitrary_text_ids_preserved": True,
            "used_as_model_feature": False,
        }
    else:
        ids = frame[config["id_column"]].astype("string")
        if ids.str.strip().eq("").any() or ids.duplicated().any():
            raise ValueError(
                "The configured candidate identifier column must contain nonempty unique values. "
                "Its name and values are otherwise arbitrary and are never used as model features."
            )
        identity = {
            "id_column": config["id_column"],
            "output_id_column": config["id_column"],
            "source": "user_supplied_arbitrary_text_identifier",
            "arbitrary_text_ids_preserved": True,
            "used_as_model_feature": False,
        }
    return frame, ids, identity


def _conflicts(constraints: list[tuple[str, dict]]) -> tuple[list, list]:
    schemas = {}
    targets = {}
    for name, constraint in constraints:
        schema = _object_hash({"spec": constraint["feature_spec"], "names": constraint["feature_names"]})
        mapping = schemas.setdefault(schema, {})
        for literal in constraint["literals"]:
            feature = literal["feature_name"]
            mapping.setdefault(feature, {0: [], 1: []})[literal["required_value"]].append(name)
        target = constraint["target"]
        cutoff = target["reference_train_cutoff"]
        if cutoff is not None:
            group = targets.setdefault((target["name"], target["unit"]), {"high": [], "low": []})
            group[target["direction"]].append((float(cutoff), name))
    literal_conflicts = []
    for schema, features in schemas.items():
        for feature, values in features.items():
            if values[0] and values[1]:
                literal_conflicts.append({"feature_schema_sha256": schema, "feature": feature,
                                          "required_zero_by": values[0], "required_one_by": values[1]})
    target_conflicts = []
    for (target, unit), values in targets.items():
        if not values["high"] or not values["low"]:
            continue
        lower, lower_name = max(values["high"])
        upper, upper_name = min(values["low"])
        if lower > upper:
            target_conflicts.append({"target_name": target, "target_unit": unit,
                                     "required_lower_bound": lower, "required_upper_bound": upper,
                                     "lower_requirement": lower_name, "upper_requirement": upper_name,
                                     "interpretation": "Stored target intervals do not overlap if they describe the same physical quantity and conditions."})
    return literal_conflicts, target_conflicts


def _candidate_matrix(frame, config: dict, models, *, np, pd, maccs_from_smiles):
    """Build the exact calculation representation without replacing raw structures."""
    features = config.get("features")
    calculation = {
        "input_structure_column": None,
        "calculation_structure_column": None,
        "hcap_before_maccs": False,
        "original_structure_preserved": True,
        "reverse_hcap_conversion_attempted": False,
        "interpretation": (
            "The original repeat-unit SMILES remains authoritative for presentation. "
            "H-cap is a calculation-only copy; connection points are not reconstructed from the capped molecule."
        ),
    }
    extra_columns = {}
    if features:
        for _, model, _, _ in models:
            if model.artifact["feature_names"] != features:
                raise ValueError("Every model must use exactly the declared binary feature schema, including order.")
        binary = frame[features].apply(pd.to_numeric, errors="coerce")
        valid = (binary.isin([0, 1]) & np.isfinite(binary)).all(axis=1)
        if any(model.artifact["feature_spec"]["kind"] == "rdkit_maccs167" for _, model, _, _ in models):
            valid &= binary.iloc[:, 0].eq(0)
        audit = pd.DataFrame({
            "input_valid": valid,
            "input_error": np.where(valid, "", "invalid_binary_feature_or_MACCS_dummy_bit"),
        })
        calculation.update({
            "representation": "explicit_binary_features",
            "feature_count": len(features),
        })
        return binary, audit, valid, extra_columns, calculation

    if any(model.artifact["feature_spec"]["kind"] != "rdkit_maccs167" for _, model, _, _ in models):
        raise ValueError("SMILES input requires MACCS models; declare features explicitly for binary models.")

    original_column = config["smiles_column"]
    raw_smiles = frame[original_column].astype("string").fillna("").tolist()
    calculation_column = config["hcap_output_column"]
    hcap_enabled = config["hcap_before_maccs"]
    contracts = []
    for _, model, _, _ in models:
        contract = _custom_contract(model.artifact)
        representation = contract.get("representation")
        if representation == "hcap_maccs167" and not hcap_enabled and any("*" in x for x in raw_smiles):
            raise ValueError("Saved model was trained on H-cap MACCS, but input contains raw connection points while H-cap is disabled.")
        if representation in {"as_provided_maccs167", "raw_maccs167"} and hcap_enabled:
            raise ValueError("Saved model requires its as-provided MACCS representation; H-cap cannot be enabled silently.")
        if representation not in (None, "hcap_maccs167", "as_provided_maccs167", "raw_maccs167"):
            raise ValueError(f"Unsupported saved training representation {representation!r}.")
        contracts.append(representation or "legacy_unspecified")
    calculation["saved_representation_contracts"] = contracts
    prepared, counts, hcap_errors = [], [], []
    for value in raw_smiles:
        if not hcap_enabled:
            prepared.append(value)
            counts.append(0)
            hcap_errors.append("")
            continue
        try:
            capped, count = hcap_smiles(value)
        except (ValueError, RuntimeError) as exc:
            prepared.append("")
            counts.append(0)
            hcap_errors.append(str(exc))
        else:
            prepared.append(capped)
            counts.append(count)
            hcap_errors.append("")

    X, audit = maccs_from_smiles(prepared, errors="report")
    valid = audit["input_valid"].astype(bool) & pd.Series([not error for error in hcap_errors], index=frame.index)
    combined_errors = []
    for index, error in enumerate(hcap_errors):
        if error:
            combined_errors.append("hcap_error: " + error)
        else:
            combined_errors.append(str(audit.iloc[index]["input_error"]))
    audit = audit.copy()
    audit["input_valid"] = valid.to_numpy()
    audit["input_error"] = combined_errors
    extra_columns[calculation_column] = prepared
    extra_columns["stca_hcap_connection_atoms_replaced"] = counts
    calculation.update({
        "representation": "rdkit_maccs167",
        "input_structure_column": original_column,
        "calculation_structure_column": calculation_column,
        "hcap_before_maccs": hcap_enabled,
        "hcap_changed_row_count": int(sum(count > 0 for count in counts)),
        "original_structure_preserved": True,
        "final_presentation_structure_column": original_column,
    })
    return X, audit, valid, extra_columns, calculation


def _candidate_duplicates(frame, config, audit, candidate_ids, valid):
    """Report identity ambiguity; never merge or discard candidates."""
    if config.get("features"):
        return {"status": "structure_audit_unavailable_binary_input", "rows_dropped": 0}
    from collections import defaultdict
    from rdkit import Chem
    original = defaultdict(list)
    hcap = defaultdict(list)
    original_canonical = {}
    for i, text in enumerate(frame[config["smiles_column"]].tolist()):
        try:
            mol = Chem.MolFromSmiles(str(text))
            canon = None if mol is None else Chem.MolToSmiles(mol, canonical=True)
        except (ValueError, RuntimeError):
            canon = None
        if canon is not None:
            original[canon].append(i)
            original_canonical[i] = canon
        if bool(valid.iloc[i]) and "canonical_smiles" in audit:
            hcap[str(audit.iloc[i]["canonical_smiles"])].append(i)
    def record(canon, positions):
        return {"canonical_smiles": canon, "row_positions": positions,
                "candidate_ids": [str(candidate_ids.iloc[i]) for i in positions]}
    duplicates = [record(k, v) for k, v in original.items() if len(v) > 1]
    collisions = [record(k, v) for k, v in hcap.items()
                  if len({original_canonical.get(i) for i in v if i in original_canonical}) > 1]
    return {"status": "audited", "canonical_original_duplicate_groups": duplicates,
            "hcap_collision_groups": collisions, "rows_dropped": 0,
            "policy": "Report only. H-cap equality does not identify the same polymer; original connections remain authoritative."}


def _run_candidate_screen(*, input_path: Path, config_path: Path | None, config: dict,
                          output_dir, stca, source) -> int:
    import numpy as np
    import pandas as pd
    from stca.chemistry import maccs_from_smiles

    frame, candidate_ids, identity = _read_candidates(input_path, config)
    models = []
    constraints = []
    for requirement in config["requirements"]:
        base_dir = config_path.parent if config_path is not None else Path.cwd()
        model, metadata = _load_model(stca, requirement, base_dir)
        metadata["target_evidence"] = _check_target_metadata(requirement, model)
        constraint = _constraint(stca, model, metadata, requirement["tier"])
        models.append((requirement, model, metadata, constraint))
        constraints.append((requirement["name"], constraint))

    features = config.get("features")
    X, audit, valid, extra_columns, calculation = _candidate_matrix(
        frame, config, models, np=np, pd=pd, maccs_from_smiles=maccs_from_smiles,
    )
    candidate_audit = _candidate_duplicates(frame, config, audit, candidate_ids, valid)
    out = frame.copy()
    out.insert(0, "stca_row_position", range(len(frame)))
    if config["id_column"] is None:
        out.insert(1, "stca_candidate_id", candidate_ids.to_numpy())
    for name, values in extra_columns.items():
        out[name] = values
    out["stca_input_valid"] = valid.to_numpy()
    out["stca_input_error"] = audit["input_error"].to_numpy()
    if "canonical_smiles" in audit:
        out["stca_canonical_smiles"] = audit["canonical_smiles"].to_numpy()
    masks, requirement_reports = [], []
    for requirement, model, metadata, constraint in models:
        name, tier = requirement["name"], requirement["tier"]
        prefix = f"stca_{name}__"
        selected = pd.Series(pd.NA, index=frame.index, dtype="boolean")
        missing = pd.Series(pd.NA, index=frame.index, dtype="string")
        unexpected = missing.copy()
        if constraint["rule"] is not None and valid.any():
            subset = X.loc[valid] if features else X[valid.to_numpy()]
            screened = model.screen_fingerprints(subset, tier=tier)
            good_positions = frame.index[valid]
            selected.loc[good_positions] = screened["selected"].to_numpy(dtype=bool)
            missing.loc[good_positions] = screened["missing_required_present"].to_numpy()
            unexpected.loc[good_positions] = screened["unexpected_present"].to_numpy()
        out[prefix + "selected"] = selected
        out[prefix + "rule_status"] = constraint["status"]
        out[prefix + "rule_name"] = constraint["rule"]["name"] if constraint["rule"] else None
        out[prefix + "rule_signature"] = constraint["rule"]["signature"] if constraint["rule"] else None
        out[prefix + "missing_required_present"] = missing
        out[prefix + "unexpected_present"] = unexpected
        masks.append(selected)
        requirement_reports.append({
            "name": name, "label": requirement.get("label", name),
            "property": requirement.get("property"),
            "direction": requirement.get("direction"),
            "source_property": requirement.get("source_property"),
            "transfer_role": requirement.get("transfer_role"),
            "target_evidence": metadata.get("target_evidence"),
            "objective_cutoff_role": "metadata_only_not_evaluated_without_measured_labels",
            "tier_source": requirement.get("tier_source"),
            "objective_cutoff": requirement.get("objective_cutoff"),
            "objective_unit": requirement.get("objective_unit"),
            "tier": tier, "status": constraint["status"],
            "assessed_count": int(selected.notna().sum()),
            "selected_count": int(selected.fillna(False).sum()),
            "unknown_count": int(selected.isna().sum()),
            "target": constraint["target"], "rule": constraint["rule"],
            "model": metadata,
        })
    flags = pd.concat(masks, axis=1)
    assessed = valid & flags.notna().all(axis=1)
    joint = pd.Series(pd.NA, index=frame.index, dtype="boolean")
    joint.loc[assessed] = flags.loc[assessed].all(axis=1).to_numpy(dtype=bool)
    out["stca_joint__selected"] = joint
    status = pd.Series("unknown_no_valid_rule", index=frame.index, dtype="string")
    status.loc[~valid] = "invalid_input"
    status.loc[assessed & ~joint.fillna(False)] = "not_selected"
    status.loc[assessed & joint.fillna(False)] = "selected"
    out["stca_joint__status"] = status
    literal_conflicts, target_conflicts = _conflicts(constraints)
    single_requirement = len(requirement_reports) == 1
    operation_name = "screen-candidates" if single_requirement else "joint-screen"
    receipt = environment_receipt(source)
    receipt.update({"operation": operation_name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "input": {"path": str(input_path), "sha256": _sha256(input_path)},
                    "configuration": ({"path": str(config_path), "sha256": _sha256(config_path)}
                                      if config_path is not None else {"kind": "command_line_single_requirement"}),
                    "models": [r["model"] for r in requirement_reports],
                    "training_performed": False, "measured_joint_properties_evaluated": False})
    summary = {
        "schema": "stca-candidate-screen-summary-v1",
        "operation": ("frozen_structural_rule_screen" if single_requirement
                      else "frozen_structural_rule_intersection"),
        "combiner": "single_rule" if single_requirement else "AND",
        "row_identity": {**identity, "unique_nonempty_ids": True,
                         "same_input_rows_used_for_every_requirement": True},
        "structure_representation": calculation,
        "candidate_audit": candidate_audit,
        "input_count": len(frame), "valid_input_count": int(valid.sum()),
        "invalid_input_count": int((~valid).sum()), "joint_assessed_count": int(assessed.sum()),
        "joint_selected_count": int(joint.fillna(False).sum()),
        "joint_unknown_count": int(joint.isna().sum()),
        "requirements": requirement_reports, "literal_conflicts": literal_conflicts,
        "stored_target_interval_conflicts": target_conflicts,
        "primary_output": "results.csv",
        "audit_output": "rows.csv",
        "interpretation": "The same candidate satisfies all selected structural rules. No joint measured-property success rate or success probability is inferred.",
        "unknown_policy": "Any invalid input or unavailable representative keeps joint_selected unknown, even if another rule returns false.",
        "conflict_interpretation": "Direct contradictions make the combined bit conditions unsatisfiable. Absence of direct bit conflicts does not prove a chemically feasible structure or compatible physical conditions.",
        "runtime": receipt,
    }
    output = _new_directory(output_dir)
    # The primary user-facing file restores the original repeat-unit structure
    # by using the untouched input column. H-cap/canonical calculation structures
    # remain only in rows.csv for auditability; no lossy reverse conversion is
    # attempted after wildcard atoms have been replaced by hydrogen.
    calculation_only = {
        config.get("hcap_output_column"),
        "stca_canonical_smiles",
    }
    presentation = out.drop(columns=[name for name in calculation_only if name in out.columns])
    presentation.to_csv(output / "results.csv", index=False)
    out.to_csv(output / "rows.csv", index=False)
    _write_json(output / "summary.json", summary)
    _write_json(output / "candidate_audit.json", candidate_audit)
    _write_json(output / "manifest.json", receipt)
    _write_json(output / "joint_constraints.json", {"schema": "stca-joint-constraints-v1", "combiner": "AND",
                                                    "requirements": [{"name": name, **c} for name, c in constraints]})
    print(json.dumps({"output_directory": str(output), "input_count": len(frame),
                      "valid_input_count": summary["valid_input_count"],
                      "joint_selected_count": summary["joint_selected_count"],
                      "joint_unknown_count": summary["joint_unknown_count"],
                      "literal_conflict_count": len(literal_conflicts)}, ensure_ascii=False))
    return 0


def joint_screen(args, stca) -> int:
    config_path = Path(args.config).expanduser().resolve()
    input_path = Path(args.input).expanduser().resolve()
    config = _config(config_path)
    return _run_candidate_screen(
        input_path=input_path,
        config_path=config_path,
        config=config,
        output_dir=args.output_dir,
        stca=stca,
        source=args.source,
    )


def screen_candidates(args, stca) -> int:
    """Apply one frozen rule while keeping the original repeat-unit SMILES."""
    requirement = {
        "name": "screen",
        "label": args.label or f"{args.profile or 'saved model'} ({args.tier:g})",
        "profile": args.profile,
        "model": args.model,
        "protocol": args.protocol,
        "tier": _tier(args.tier),
        "property": args.property,
        "direction": args.direction,
        "source_property": args.source_property,
        "transfer_role": args.transfer_role,
        "allow_transfer": getattr(args, "allow_transfer", False),
        "tier_source": "user_tier",
        "objective_cutoff": None,
        "objective_unit": None,
    }
    # Remove optional metadata fields only; exactly one profile/model remains.
    requirement = {key: value for key, value in requirement.items() if value is not None}
    config = _config_object({
        "schema": "stca-joint-config-v1",
        "id_column": args.id_column,
        "smiles_column": args.smiles_column,
        "hcap_before_maccs": not args.input_is_hcap,
        "hcap_output_column": args.hcap_output_column,
        "requirements": [requirement],
    })
    return _run_candidate_screen(
        input_path=Path(args.input).expanduser().resolve(),
        config_path=None,
        config=config,
        output_dir=args.output_dir,
        stca=stca,
        source=args.source,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Clean pinned STCA source checkout; otherwise use the runtime cache.")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser(
        "plan-objectives",
        help="Map user property objectives to independent STCA profiles/tiers and write a joint-screen config.",
    )
    plan.add_argument("--objectives", required=True, help="JSON file using schema stca-objectives-v1.")
    plan.add_argument("--output-dir", required=True, help="A new output directory.")
    export = commands.add_parser("export-rules", help="Export the complete retained family and frozen representative constraints.")
    model_group = export.add_mutually_exclusive_group(required=True)
    model_group.add_argument("--profile", choices=PROFILES)
    model_group.add_argument("--model", help="Saved STCA model JSON; its own protocol is retained.")
    export.add_argument("--protocol", choices=PROTOCOLS, help="Required for a profile; if supplied with a model it must match its saved protocol.")
    export.add_argument("--tier", type=float, required=True)
    export.add_argument("--count", type=int, default=20, help="Requested candidate count in the generated prompt; default 20.")
    export.add_argument("--preferences", default="", help="Chemical preferences to include in complete generation prompts.")
    export.add_argument("--output-dir", required=True, help="A new output directory; existing directories are never overwritten.")
    screen = commands.add_parser(
        "screen-candidates",
        help=("Apply one frozen STCA rule to raw repeat-unit SMILES. H-cap is calculation-only; "
              "the original star-containing SMILES remains the primary output structure."),
    )
    screen_model = screen.add_mutually_exclusive_group(required=True)
    screen_model.add_argument("--profile", choices=PROFILES)
    screen_model.add_argument("--model", help="Saved STCA model JSON; its own protocol is retained.")
    screen.add_argument("--protocol", choices=PROTOCOLS, help="Required with --profile; optional consistency check with --model.")
    screen.add_argument("--tier", type=float, required=True)
    screen.add_argument("--input", required=True)
    screen.add_argument("--id-column", help="Optional arbitrary identifier column. Omit it to generate row-000001 style receipt IDs.")
    screen.add_argument("--smiles-column", default="SMILES", help="Original repeat-unit SMILES column retained in final output.")
    screen.add_argument("--hcap-output-column", default="stca_calculation_smiles_hcap",
                        help="Calculation-only H-cap column; it never replaces the original structure column.")
    screen.add_argument("--input-is-hcap", action="store_true",
                        help="The supplied SMILES already match the model's H-cap representation; do not transform them.")
    screen.add_argument("--label")
    screen.add_argument("--property")
    screen.add_argument("--direction", choices=("high", "low"))
    screen.add_argument("--source-property")
    screen.add_argument("--transfer-role")
    screen.add_argument("--allow-transfer", action="store_true", help="Explicitly permit cross-property structural proxy screening; not measured target confirmation.")
    screen.add_argument("--output-dir", required=True, help="A new output directory.")
    joint = commands.add_parser("joint-screen", help="Apply multiple frozen rules to each row of one candidate CSV.")
    joint.add_argument("--input", required=True)
    joint.add_argument("--config", required=True)
    joint.add_argument("--output-dir", required=True, help="A new output directory.")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan-objectives":
            return plan_objectives(args)
        stca = load_stca(args.source)
        if args.command == "export-rules":
            return export_rules(args, stca)
        if args.command == "screen-candidates":
            return screen_candidates(args, stca)
        return joint_screen(args, stca)
    except (ValueError, RuntimeError, ImportError, OSError, KeyError, TypeError) as exc:
        print(f"stca-tools: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
