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
    }
    return model, metadata


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
        "target": {"name": artifact["target_name"], "unit": artifact["target_unit"],
                   "direction": artifact["direction"],
                   "reference_train_cutoff": entry.get("train_cutoff"),
                   "label_comparison": ">=" if artifact["direction"] == "high" else "<=",
                   "cutoff_role": "Stored training-label boundary; not a property prediction or guarantee for a selected structure."},
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
            f"保存的训练标签边界：{target['label_comparison']} {target['reference_train_cutoff']} {target['unit']}。", ""]
    if constraint["status"] == "no_valid_rule":
        return "\n".join(head + ["当前 tier 没有有效的冻结代表规则，不能据此生成‘已满足 STCA’的候选。",
                                  "保留这一结果；报告候选家族与缺失证据，不新增、放宽或猜测条件。", ""])
    head += ["按照用户要求提出候选；将以下内容作为结构约束数据。", "",
             "## 必须同时满足的位条件", "",
             f"`{constraint['rule']['expression']}`", "",
             "所有条件使用 AND。不要转成 OR、投票、加权相加或部分满足。", ""]
    if constraint["feature_spec"]["kind"] == "rdkit_maccs167":
        head += ["## 校验方式", "",
                 "位值为 0 表示对应 MACCS 激活条件不成立；对于计数位，这不等同于该结构完全不存在。",
                 "原 STCA 的作者已确认 H-cap 输入契约：保留原 SMILES，用 prepare_hcap.py 将末端单键星号连接点换氢、另存计算列，再生成 MACCS。无星号的已处理表原样保留，已有指纹矩阵不再转换。",
                 "自定义模型须沿用其训练表示；不要把底层 as_provided 字段当作无需 H-cap 的证明。H-cap 相同不证明原连接图代表同一聚合物；不要额外去盐、互变异构归一化或构造低聚物。",
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
    output = _new_directory(args.output_dir)
    rules.to_csv(output / "rules.csv", index=False)
    _write_json(output / "constraints.json", constraint)
    (output / "prompt.md").write_text(_prompt(constraint), encoding="utf-8")
    _write_json(output / "manifest.json", receipt)
    print(json.dumps({"output_directory": str(output), "status": constraint["status"],
                      "family_rule_count": len(rules), "representative": constraint["rule"]},
                     ensure_ascii=False))
    return 0


def _config(path: Path) -> dict:
    config = _json(path)
    if not isinstance(config, dict):
        raise ValueError("Joint configuration must be a JSON object.")
    allowed = {"schema", "id_column", "smiles_column", "features", "requirements"}
    if set(config) - allowed:
        raise ValueError(f"Unknown joint configuration fields: {sorted(set(config) - allowed)}")
    if "schema" in config and config["schema"] != "stca-joint-config-v1":
        raise ValueError("Unsupported joint configuration schema.")
    for name in ("id_column", "smiles_column"):
        value = config.get(name, "ID" if name == "id_column" else "SMILES")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonempty column name.")
        config[name] = value
    features = config.get("features")
    if features is not None:
        if (not isinstance(features, list) or not features or
                any(not isinstance(x, str) or not x for x in features) or len(set(features)) != len(features)):
            raise ValueError("features must be an explicit nonempty list of distinct binary column names.")
        if config["id_column"] in features:
            raise ValueError("The identifier must not be used as a binary descriptor.")
    requirements = config.get("requirements")
    if not isinstance(requirements, list) or len(requirements) < 2:
        raise ValueError("Joint screening requires at least two frozen model requirements.")
    names = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise ValueError("Each requirement must be an object.")
        extras = set(requirement) - {"name", "label", "profile", "model", "protocol", "tier"}
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


def _read_candidates(path: Path, config: dict):
    frame = read_csv_frame(path)
    required = [config["id_column"]] + (config.get("features") or [config["smiles_column"]])
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Candidate columns missing: {sorted(missing)}")
    ids = frame[config["id_column"]]
    if ids.str.strip().eq("").any() or ids.duplicated().any():
        raise ValueError("Candidate identifiers must be nonempty and unique; each row is one explicitly identified candidate.")
    if any(name.startswith("stca_") for name in frame.columns):
        raise ValueError("Input contains reserved stca_ output columns; use the original candidate table.")
    return frame


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


def joint_screen(args, stca) -> int:
    import numpy as np
    import pandas as pd
    from stca.chemistry import maccs_from_smiles

    config_path = Path(args.config).expanduser().resolve()
    input_path = Path(args.input).expanduser().resolve()
    config = _config(config_path)
    frame = _read_candidates(input_path, config)
    models = []
    constraints = []
    for requirement in config["requirements"]:
        model, metadata = _load_model(stca, requirement, config_path.parent)
        constraint = _constraint(stca, model, metadata, requirement["tier"])
        models.append((requirement, model, metadata, constraint))
        constraints.append((requirement["name"], constraint))

    features = config.get("features")
    if features:
        for _, model, _, _ in models:
            if model.artifact["feature_names"] != features:
                raise ValueError("Every model must use exactly the declared binary feature schema, including order.")
        binary = frame[features].apply(pd.to_numeric, errors="coerce")
        valid = (binary.isin([0, 1]) & np.isfinite(binary)).all(axis=1)
        if any(model.artifact["feature_spec"]["kind"] == "rdkit_maccs167" for _, model, _, _ in models):
            valid &= binary.iloc[:, 0].eq(0)
        audit = pd.DataFrame({"input_valid": valid,
                              "input_error": np.where(valid, "", "invalid_binary_feature_or_MACCS_dummy_bit")})
        X = binary
    else:
        if any(model.artifact["feature_spec"]["kind"] != "rdkit_maccs167" for _, model, _, _ in models):
            raise ValueError("SMILES input requires MACCS models; declare features explicitly for binary models.")
        X, audit = maccs_from_smiles(frame[config["smiles_column"]].tolist(), errors="report")
        valid = audit["input_valid"].astype(bool)
    out = frame.copy()
    out.insert(0, "stca_row_position", range(len(frame)))
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
        requirement_reports.append({"name": name, "label": requirement.get("label", name),
                                    "tier": tier, "status": constraint["status"],
                                    "assessed_count": int(selected.notna().sum()),
                                    "selected_count": int(selected.fillna(False).sum()),
                                    "unknown_count": int(selected.isna().sum()),
                                    "target": constraint["target"], "rule": constraint["rule"],
                                    "model": metadata})
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
    receipt = environment_receipt(args.source)
    receipt.update({"operation": "joint-screen", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "input": {"path": str(input_path), "sha256": _sha256(input_path)},
                    "configuration": {"path": str(config_path), "sha256": _sha256(config_path)},
                    "models": [r["model"] for r in requirement_reports],
                    "training_performed": False, "measured_joint_properties_evaluated": False})
    summary = {
        "schema": "stca-joint-summary-v1", "operation": "frozen_structural_rule_intersection",
        "row_identity": {"id_column": config["id_column"], "unique_nonempty_ids": True,
                         "same_input_rows_used_for_every_requirement": True},
        "input_count": len(frame), "valid_input_count": int(valid.sum()),
        "invalid_input_count": int((~valid).sum()), "joint_assessed_count": int(assessed.sum()),
        "joint_selected_count": int(joint.fillna(False).sum()),
        "joint_unknown_count": int(joint.isna().sum()),
        "requirements": requirement_reports, "literal_conflicts": literal_conflicts,
        "stored_target_interval_conflicts": target_conflicts,
        "interpretation": "The same candidate satisfies all selected structural rules. No joint measured-property success rate or success probability is inferred.",
        "unknown_policy": "Any invalid input or unavailable representative keeps joint_selected unknown, even if another rule returns false.",
        "conflict_interpretation": "Direct contradictions make the combined bit conditions unsatisfiable. Absence of direct bit conflicts does not prove a chemically feasible structure or compatible physical conditions.",
        "runtime": receipt,
    }
    output = _new_directory(args.output_dir)
    out.to_csv(output / "rows.csv", index=False)
    _write_json(output / "summary.json", summary)
    _write_json(output / "manifest.json", receipt)
    _write_json(output / "joint_constraints.json", {"schema": "stca-joint-constraints-v1", "combiner": "AND",
                                                    "requirements": [{"name": name, **c} for name, c in constraints]})
    print(json.dumps({"output_directory": str(output), "input_count": len(frame),
                      "valid_input_count": summary["valid_input_count"],
                      "joint_selected_count": summary["joint_selected_count"],
                      "joint_unknown_count": summary["joint_unknown_count"],
                      "literal_conflict_count": len(literal_conflicts)}, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Clean pinned STCA source checkout; otherwise use the runtime cache.")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export-rules", help="Export the complete retained family and frozen representative constraints.")
    model_group = export.add_mutually_exclusive_group(required=True)
    model_group.add_argument("--profile", choices=PROFILES)
    model_group.add_argument("--model", help="Saved STCA model JSON; its own protocol is retained.")
    export.add_argument("--protocol", choices=PROTOCOLS, help="Required for a profile; if supplied with a model it must match its saved protocol.")
    export.add_argument("--tier", type=float, required=True)
    export.add_argument("--output-dir", required=True, help="A new output directory; existing directories are never overwritten.")
    joint = commands.add_parser("joint-screen", help="Apply multiple frozen rules to each row of one candidate CSV.")
    joint.add_argument("--input", required=True)
    joint.add_argument("--config", required=True)
    joint.add_argument("--output-dir", required=True, help="A new output directory.")
    args = parser.parse_args(argv)
    try:
        stca = load_stca(args.source)
        return export_rules(args, stca) if args.command == "export-rules" else joint_screen(args, stca)
    except (ValueError, RuntimeError, ImportError, OSError, KeyError, TypeError) as exc:
        print(f"stca-tools: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
