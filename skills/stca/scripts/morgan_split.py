#!/usr/bin/env python3
"""Target-blind ECFP4 distance holdout with an explicit separating buffer."""
from __future__ import annotations

import hashlib
import math
import numpy as np


def distance_matrix(fingerprints):
    """Exact 1-Tanimoto distances; no projection or approximate neighbors."""
    from rdkit import DataStructs
    matrix = np.empty((len(fingerprints), len(fingerprints)), dtype=np.float64)
    for index, fingerprint in enumerate(fingerprints):
        matrix[index] = 1.0 - np.asarray(DataStructs.BulkTanimotoSimilarity(fingerprint, fingerprints))
    return matrix


def split_distance_holdout(fingerprints, groups, *, threshold=.5, holdout_fraction=.2,
                           min_source=10, min_holdout=2, identities=None):
    """Select a peripheral structural neighborhood, then buffer its neighbors.

    The anchor is the protected group with the greatest mean ECFP4 distance to
    the table. Its nearest protected groups form the requested holdout. Every
    remaining group with ANY member less than ``threshold`` from ANY holdout
    member becomes buffer. Labels and candidate IDs never enter this decision.
    A large buffer is reported; it is never silently put back in training.
    """
    if not math.isfinite(threshold) or not 0 < threshold <= 1:
        raise ValueError("Distance threshold must be in (0, 1].")
    if not math.isfinite(holdout_fraction) or not 0 < holdout_fraction < 1:
        raise ValueError("Holdout fraction must be in (0, 1).")
    if len(fingerprints) != len(groups) or len(fingerprints) < 3:
        raise ValueError("At least three structurally valid records are required.")
    groups = np.asarray(groups, dtype=str)
    members = {group: np.flatnonzero(groups == group) for group in np.unique(groups)}
    if len(members) < 3:
        raise ValueError("At least three protected structural groups are required.")
    distances = distance_matrix(fingerprints)
    # Stable structural hashes break numerical ties independently of row order,
    # arbitrary identifiers, target values and group-number assignment.
    if identities is None:
        identities = [fp.ToBitString() for fp in fingerprints]
    signatures = {g: hashlib.sha256("\n".join(sorted(str(identities[i]) for i in pos)).encode()).hexdigest()
                  for g, pos in members.items()}
    anchor = min(members, key=lambda g: (-round(float(distances[members[g]].mean()), 12), signatures[g]))
    ranked = sorted(members, key=lambda g: (float(distances[np.ix_(members[g], members[anchor])].min()), signatures[g]))
    desired = max(int(min_holdout), int(math.ceil(len(groups) * holdout_fraction)))
    held_groups, held_n = [], 0
    for group in ranked:
        held_groups.append(group)
        held_n += len(members[group])
        if held_n >= desired:
            break
    holdout = np.sort(np.concatenate([members[g] for g in held_groups]))
    source_groups, buffer_groups = [], []
    for group in members:
        if group in held_groups:
            continue
        nearest = float(distances[np.ix_(members[group], holdout)].min())
        (source_groups if nearest + 1e-12 >= threshold else buffer_groups).append(group)
    concat = lambda selected: np.sort(np.concatenate([members[g] for g in selected])).astype(int) if selected else np.array([], dtype=int)
    source, buffer = concat(source_groups), concat(buffer_groups)
    roles = np.full(len(groups), "buffer", dtype=object)
    roles[source], roles[holdout] = "source", "holdout"
    nearest = distances[np.ix_(holdout, source)].min(axis=1) if len(source) else np.full(len(holdout), np.nan)
    audit = {"schema": "stca-strict-morgan-split-v1", "method": "target_blind_peripheral_anchor_neighborhood_with_distance_buffer",
             "fingerprint": {"family": "Morgan", "radius": 2, "diameter": 4, "bits": 2048,
                             "input": "calculation_only_hcap", "metric": "1-Tanimoto"},
             "distance_threshold": float(threshold), "requested_holdout_fraction": float(holdout_fraction),
             "n": len(groups), "source_n": len(source), "holdout_n": len(holdout), "buffer_n": len(buffer),
             "protected_group_n": len(members), "source_group_n": len(source_groups),
             "holdout_group_n": len(held_groups), "buffer_group_n": len(buffer_groups),
             "protected_group_overlap_n": 0, "target_values_used": False, "candidate_ids_used": False,
             "anchor_structural_sha256": signatures[anchor], "anchor_rule": "maximum_mean_distance_then_structural_hash",
             "holdout_rule": "nearest_anchor_protected_groups_until_requested_row_count",
             "buffer_rule": "all_nonholdout_groups_with_any_member_distance_below_threshold_to_holdout",
             "buffer_used_for_learning": False, "no_random_fallback": True,
             "nearest_source_distance_min": float(nearest.min()) if len(source) else None,
             "nearest_source_distance_median": float(np.median(nearest)) if len(source) else None,
             "every_holdout_meets_distance": bool(len(source) and np.all(nearest + 1e-12 >= threshold)),
             "minimum_source_requested": int(min_source), "minimum_holdout_requested": int(min_holdout)}
    audit["status"] = "available" if len(source) >= min_source and len(holdout) >= min_holdout else "unavailable_insufficient_distance_separated_records"
    return {"source": source, "holdout": holdout, "buffer": buffer, "roles": roles,
            "holdout_nearest_source_distance": nearest, "audit": audit}
