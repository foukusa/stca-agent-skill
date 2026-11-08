#!/usr/bin/env python3
"""Deterministic signed-literal WRAcc beam search with configurable depth.

The beam and ranking are the same at every depth as the original adapter's
three-literal search. Integer masks accelerate support counts without merging
conjunctions or removing no-op extensions, which would change that search.
"""
from __future__ import annotations

import numpy as np

DEFAULT_CAPS = (1, 2, 3, 5, 10, None)


def normalize_wracc_limit(value):
    if value is None:
        return "unlimited"
    if isinstance(value, bool):
        raise ValueError("WRAcc maximum literals must be auto, unlimited, or a positive integer.")
    token = str(value).strip().lower()
    if token in ("auto", "unlimited"):
        return token
    try:
        number = int(token)
    except (TypeError, ValueError) as exc:
        raise ValueError("WRAcc maximum literals must be auto, unlimited, or a positive integer.") from exc
    if number < 1 or str(number) != token:
        raise ValueError("WRAcc maximum literals must be auto, unlimited, or a positive integer.")
    return number


def cap_name(cap):
    return "unlimited" if cap is None or cap == "unlimited" else str(int(cap))


def _mask_integer(value):
    return int.from_bytes(np.packbits(np.asarray(value, dtype=bool), bitorder="little").tobytes(), "little")


def _best_record(best):
    if best is None:
        return None
    return {"literals": list(best[0]), "wracc": float(best[1][0]),
            "length": len(best[0]), "support": best[1][1].bit_count()}


def search_wracc(matrix, truth, *, caps=DEFAULT_CAPS, width=30, min_support=5):
    """Return the cumulative best conjunction for each requested maximum depth.

    ``None``/``unlimited`` searches through all varying distinct keys or until
    the positive-scoring beam is empty. Score plateaus do not stop the search.
    Each requested cap selects by training WRAcc; validation selects *between*
    those caps elsewhere. Key zero is reserved and is never a candidate.
    """
    matrix = np.asarray(matrix)
    truth = np.asarray(truth, dtype=bool)
    if matrix.ndim != 2 or truth.ndim != 1 or len(matrix) != len(truth):
        raise ValueError("WRAcc expects a two-dimensional matrix and one truth value per row.")
    if width < 1 or min_support < 1:
        raise ValueError("WRAcc beam width and minimum support must be positive.")
    normalized = []
    for value in caps:
        parsed = normalize_wracc_limit(value)
        if parsed == "auto":
            raise ValueError("search_wracc requires fixed caps; auto is selected using training-only validation.")
        cap = None if parsed == "unlimited" else parsed
        if cap not in normalized:
            normalized.append(cap)
    if not normalized:
        raise ValueError("At least one WRAcc depth cap is required.")
    result = {"caps": {cap_name(cap): None for cap in normalized}, "maximum_varying_keys": 0,
              "last_depth": 0, "termination": "target_has_one_class", "score_cache_masks": 0,
              "beam_width": int(width), "minimum_support": int(min_support)}
    n = len(truth)
    if not n or not np.any(truth) or np.all(truth):
        return result
    if not np.all((matrix == 0) | (matrix == 1)):
        raise ValueError("WRAcc signed literals require binary features.")
    prevalence = float(np.mean(truth))
    keys = [j for j in range(1, matrix.shape[1]) if matrix[:, j].min() != matrix[:, j].max()]
    maximum = len(keys) if None in normalized else min(max(normalized), len(keys))
    result["maximum_varying_keys"] = len(keys)
    allmask = (1 << n) - 1
    positive = _mask_integer(truth)
    literal_masks = {(j, value): _mask_integer(matrix[:, j] == value) for j in keys for value in (0, 1)}
    literals = list(literal_masks)
    beam, best, scorecache = [((), allmask)], None, {}
    for depth in range(1, maximum + 1):
        candidates = {}
        for existing, mask in beam:
            used = {j for j, _ in existing}
            for literal in literals:
                if literal[0] in used:
                    continue
                combination = tuple(sorted(existing + (literal,)))
                if combination in candidates:
                    continue
                selected = mask & literal_masks[literal]
                wracc = scorecache.get(selected)
                if wracc is None:
                    support = selected.bit_count()
                    wracc = support / n * ((selected & positive).bit_count() / support - prevalence) if support >= min_support else -1.0
                    scorecache[selected] = wracc
                if wracc > 0:
                    candidates[combination] = (wracc, selected)
        ordered = sorted(candidates.items(), key=lambda kv: (-kv[1][0], len(kv[0]), kv[0]))[:width]
        beam = [(rule, details[1]) for rule, details in ordered]
        if ordered:
            candidate = ordered[0]
            if best is None or (-candidate[1][0], len(candidate[0]), candidate[0]) < (-best[1][0], len(best[0]), best[0]):
                best = candidate
        if depth in normalized:
            result["caps"][str(depth)] = _best_record(best)
        result["last_depth"] = depth
        if not beam:
            break
    # A cap beyond natural exhaustion has the same cumulative best rule.
    for cap in normalized:
        if cap is None or cap > result["last_depth"]:
            result["caps"][cap_name(cap)] = _best_record(best)
    result.update(termination=("no_varying_keys" if not keys else "beam_empty" if not beam else
                               "all_distinct_varying_keys_exhausted" if result["last_depth"] == len(keys) else "requested_maximum_depth_reached"),
                  score_cache_masks=len(scorecache))
    return result
