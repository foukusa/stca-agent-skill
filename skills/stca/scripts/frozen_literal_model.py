#!/usr/bin/env python3
"""Versioned exact-AND adapter for already frozen STCA or WRAcc conditions.

This module never trains either learner.  Artifact creation, loading and rule
inspection use only the standard library; numerical imports occur at screening.
The historical ``STCA|AND|`` signature identifies conditions, not their learner.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path


MODEL_TYPE = "stca_frozen_literal_model_v1"
LEARNERS = {"STCA", "WRAcc"}
FEATURE_NAMES = [f"K{i}" for i in range(167)]


class NoValidLiteralRuleError(ValueError):
    """The tier explicitly abstains because it has no frozen representative."""


def _copy(value):
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError) as exc:
        raise ValueError("Frozen literal artifacts require finite JSON values only.") from exc


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError(f"{label} must be nonempty single-line text.")
    return value


def _tier_key(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value < 1:
        raise ValueError("Tier must be a finite fraction strictly between 0 and 1.")
    return format(value, ".12g")


@dataclass(frozen=True)
class LiteralRule:
    keys: tuple[int, ...]
    values: tuple[int, ...]
    name: str = "frozen_rule"
    family: str = "exact_and"

    def __post_init__(self):
        object.__setattr__(self, "keys", tuple(self.keys))
        object.__setattr__(self, "values", tuple(self.values))
        if not self.keys or len(self.keys) != len(self.values):
            raise ValueError("A frozen rule requires equal nonempty keys/values; empty rules must abstain.")
        if any(isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 166 for k in self.keys):
            raise ValueError("Frozen MACCS rule keys must be original integer indices 1..166; K0 is a dummy.")
        if len(set(self.keys)) != len(self.keys):
            raise ValueError("Duplicate or contradictory frozen rule keys.")
        if any(isinstance(v, bool) or not isinstance(v, int) or v not in (0, 1) for v in self.values):
            raise ValueError("Frozen rule values must be integer 0 or 1.")
        _text(self.name, "Rule name")
        _text(self.family, "Rule family")

    @property
    def signature(self):
        return "STCA|AND|" + "&".join(f"K{k}={v}" for k, v in sorted(zip(self.keys, self.values)))

    def expression(self, names=None):
        return " AND ".join(f"{names[k] if names is not None else 'K'+str(k)}={v}" for k, v in zip(self.keys, self.values))

    def to_dict(self):
        return {"keys": list(self.keys), "values": list(self.values), "name": self.name, "family": self.family}

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) != {"keys", "values", "name", "family"}:
            raise ValueError("Frozen rule must contain exactly keys, values, name and family.")
        if not isinstance(value["keys"], list) or not isinstance(value["values"], list):
            raise ValueError("Frozen keys and values must be JSON lists.")
        return cls(**value)


def create_model_artifact(*, target_name, target_unit, direction, feature_spec,
                          tiers, learner, custom_data_contract, provenance=None):
    """Return a validated artifact from caller-supplied exact frozen conditions.

    ``tiers`` maps canonical fractional strings to ``selected_rule``, ``rules``
    (records with a ``rule`` dictionary), and ``train_cutoff``.  A missing or
    empty conjunction is represented by ``selected_rule=None`` and abstains.
    ``train_cutoff=None`` retains an unknown boundary without guessing it.
    """
    if not isinstance(tiers, dict) or not tiers:
        raise ValueError("Provide a nonempty dictionary of frozen tiers.")
    normalized = _copy(tiers)
    for key, entry in normalized.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("rules"), list):
            raise ValueError("Each frozen tier requires a rules list.")
        # Empty conjunctions are unavailable, never a rule matching every row.
        usable, empty_names = [], set()
        for record in entry["rules"]:
            if not isinstance(record, dict) or not isinstance(record.get("rule"), dict):
                raise ValueError("Each frozen rule record requires a rule object.")
            rule = record["rule"]
            if rule.get("keys") == [] and rule.get("values") == []:
                empty_names.add(rule.get("name"))
            else:
                usable.append(record)
        entry["rules"] = usable
        chosen = entry.get("selected_rule")
        if chosen in empty_names or chosen is None:
            entry["selected_rule"] = None
            entry["status"] = "no_valid_rule"
            entry.setdefault("no_valid_rule_reason", "No nonempty frozen representative was supplied.")
        else:
            entry["status"] = "frozen_representative"
    if not isinstance(custom_data_contract, dict) or not isinstance(provenance or {}, dict):
        raise ValueError("Data contract and provenance must be objects.")
    provenance = _copy(provenance or {})
    caller = provenance.setdefault("caller_metadata", {})
    if not isinstance(caller, dict):
        raise ValueError("provenance.caller_metadata must be an object.")
    if "custom_data_contract" in caller and caller["custom_data_contract"] != custom_data_contract:
        raise ValueError("Provenance and supplied data contracts disagree.")
    caller["custom_data_contract"] = _copy(custom_data_contract)
    provenance.setdefault("kind", "frozen_literal_rules")
    provenance.setdefault("protocol_id", "frozen_literal_model_v1")
    provenance.setdefault("selection_protocol", "caller_supplied_frozen_conditions")
    provenance["training_performed_by_adapter"] = False
    if "learner" in provenance and provenance["learner"] != learner:
        raise ValueError("Provenance learner conflicts with the supplied learner.")
    provenance["learner"] = learner
    artifact = {"schema_version": 1, "model_type": MODEL_TYPE,
                "adapter_version": "1", "learner": learner,
                "n_features": 167, "feature_names": FEATURE_NAMES,
                "feature_spec": feature_spec, "target_name": target_name,
                "target_unit": target_unit, "direction": direction,
                "custom_data_contract": custom_data_contract, "tiers": normalized,
                "provenance": provenance,
                "signature_namespace": "STCA|AND| (historical exact-condition identifier; not learner attribution)"}
    return FrozenLiteralModel.from_artifact(artifact).artifact


class FrozenLiteralModel:
    """Read and screen exact frozen conditions without invoking STCA fitting."""

    def __init__(self, artifact):
        obj = _copy(artifact)
        if not isinstance(obj, dict) or type(obj.get("schema_version")) is not int or obj["schema_version"] != 1 or obj.get("model_type") != MODEL_TYPE:
            raise ValueError("Unsupported frozen literal model schema/model_type.")
        if obj.get("learner") not in LEARNERS:
            raise ValueError("Frozen literal learner must be STCA or WRAcc.")
        if obj.get("direction") not in {"high", "low"}:
            raise ValueError("Frozen model direction must be high or low.")
        _text(obj.get("target_name"), "Target name")
        _text(obj.get("target_unit"), "Target unit")
        if obj.get("n_features") != 167 or obj.get("feature_names") != FEATURE_NAMES:
            raise ValueError("Frozen literal models require original MACCS167 columns K0..K166.")
        if not isinstance(obj.get("feature_spec"), dict) or obj["feature_spec"].get("kind") != "rdkit_maccs167":
            raise ValueError("Frozen literal models require rdkit_maccs167.")
        if not isinstance(obj.get("provenance"), dict) or not isinstance(obj.get("custom_data_contract"), dict):
            raise ValueError("Frozen provenance and data contract must be objects.")
        if obj["provenance"].get("learner") != obj["learner"]:
            raise ValueError("Frozen provenance learner differs from model learner.")
        caller = obj["provenance"].get("caller_metadata", {})
        if not isinstance(caller, dict) or caller.get("custom_data_contract") != obj["custom_data_contract"]:
            raise ValueError("Frozen data contract must agree with provenance.")
        if not isinstance(obj.get("tiers"), dict) or not obj["tiers"]:
            raise ValueError("Frozen tiers must be a nonempty object.")
        for key, entry in obj["tiers"].items():
            try:
                canonical = _tier_key(float(key))
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid frozen tier key.") from exc
            if key != canonical or not isinstance(entry, dict) or not isinstance(entry.get("rules"), list):
                raise ValueError("Frozen tiers require canonical keys and rule lists.")
            names = set()
            for record in entry["rules"]:
                if not isinstance(record, dict) or not isinstance(record.get("source_metrics", {}), dict):
                    raise ValueError("Malformed frozen rule record/source_metrics.")
                rule = LiteralRule.from_dict(record.get("rule"))
                if rule.name in names:
                    raise ValueError("Frozen rule names must be unique within each tier.")
                names.add(rule.name)
            chosen = entry.get("selected_rule")
            if chosen is not None and chosen not in names:
                raise ValueError("Selected frozen rule is missing from its tier.")
            expected = "no_valid_rule" if chosen is None else "frozen_representative"
            if entry.get("status", expected) != expected:
                raise ValueError("Frozen tier status conflicts with its selected rule.")
            cutoff = entry.get("train_cutoff")
            if cutoff is not None and (isinstance(cutoff, bool) or not isinstance(cutoff, (int, float)) or not math.isfinite(cutoff)):
                raise ValueError("Frozen train_cutoff must be finite or null.")
        self._artifact = obj

    @classmethod
    def from_artifact(cls, artifact):
        return cls(artifact)

    @classmethod
    def load(cls, path):
        def reject(value):
            raise ValueError(f"Nonfinite JSON value: {value}")
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"Repeated JSON key: {key}")
                result[key] = value
            return result
        return cls(json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=reject, object_pairs_hook=unique))

    @property
    def artifact(self):
        return _copy(self._artifact)

    @property
    def provenance(self):
        return self.artifact["provenance"]

    @property
    def tiers(self):
        return tuple(float(key) for key in self._artifact["tiers"])

    def _entry(self, tier):
        key = _tier_key(tier)
        if key not in self._artifact["tiers"]:
            raise ValueError(f"Tier {tier} is unavailable; available tiers: {self.tiers}. No interpolation is performed.")
        return self._artifact["tiers"][key]

    def rule_for(self, tier, *, rule_name=None):
        entry = self._entry(tier)
        chosen = rule_name if rule_name is not None else entry.get("selected_rule")
        if chosen is None:
            raise NoValidLiteralRuleError(f"No valid frozen rule at tier {tier}; the model abstains.")
        for record in entry["rules"]:
            if record["rule"]["name"] == chosen:
                return LiteralRule.from_dict(record["rule"])
        raise ValueError(f"Unknown frozen rule {chosen!r} at tier {tier}.")

    def screen_fingerprints(self, X, *, tier=0.20):
        import numpy as np
        import pandas as pd

        rule = self.rule_for(tier)
        if isinstance(X, pd.DataFrame) and list(X.columns) != FEATURE_NAMES:
            raise ValueError("Fingerprint columns must exactly preserve K0..K166 and their order.")
        a = np.asarray(X)
        if a.ndim != 2 or a.shape[1] != 167:
            raise ValueError("Fingerprint matrix must have 167 columns.")
        if a.dtype.kind not in "biuf" or not np.isfinite(a).all() or not np.isin(a, (0, 1)).all():
            raise ValueError("Fingerprint matrix must contain finite binary values only.")
        if np.any(a[:, 0] != 0):
            raise ValueError("MACCS K0 is a dummy and must remain zero.")
        flags = a[:, rule.keys] == np.asarray(rule.values)
        names = self._artifact["feature_names"]
        missing = [";".join(names[k] for k, v in zip(rule.keys, rule.values) if v == 1 and row[k] != 1) for row in a]
        forbidden = [";".join(names[k] for k, v in zip(rule.keys, rule.values) if v == 0 and row[k] != 0) for row in a]
        return pd.DataFrame({"row_position": np.arange(len(a)), "input_valid": True,
                             "selected": np.all(flags, axis=1), "rule_name": rule.name,
                             "tier": float(tier), "target_direction": self._artifact["direction"],
                             "matched_literals": flags.sum(axis=1), "required_literals": len(rule.keys),
                             "missing_required_present": missing, "unexpected_present": forbidden,
                             "rule_signature": rule.signature, "learner": self._artifact["learner"],
                             "profile_kind": self._artifact["provenance"].get("kind")})

    def rules(self, *, tier=0.20):
        import pandas as pd

        entry, rows = self._entry(tier), []
        for record in entry["rules"]:
            rule = LiteralRule.from_dict(record["rule"])
            rows.append({"rule_name": rule.name, "selected": rule.name == entry.get("selected_rule"),
                         "family": rule.family, "literal_n": len(rule.keys), "signature": rule.signature,
                         "expression": rule.expression(self._artifact["feature_names"]),
                         "learner": self._artifact["learner"],
                         **{f"source_{k}": v for k, v in record.get("source_metrics", {}).items()}})
        return pd.DataFrame(rows)
