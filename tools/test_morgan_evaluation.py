#!/usr/bin/env python3
"""Acceptance checks for real target-blind Morgan extrapolation partitions."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from rdkit import DataStructs

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/stca/scripts"
sys.path.insert(0, str(SCRIPTS))
from morgan_split import split_distance_holdout, distance_matrix
from morgan_evaluation import structural_split, heldout_targets


def fingerprint(indices):
    value = DataStructs.ExplicitBitVect(2048)
    for index in indices:
        value.SetBit(index)
    return value


class MorganDistanceAcceptance(unittest.TestCase):
    def synthetic(self):
        # Chemical neighborhoods with disjoint vocabularies; one anchor neighbor
        # deliberately enters the separating buffer at the strict .6 boundary.
        bits = ([0, 1, 2], [0, 1, 3], [0, 4, 5], [20, 21, 22],
                [20, 21, 23], [30, 31, 32], [30, 31, 33], [40, 41, 42])
        return [fingerprint(row) for row in bits], list(map(str, range(len(bits))))

    def test_every_heldout_observation_meets_exact_distance_and_groups_do_not_overlap(self):
        fps, groups = self.synthetic()
        result = split_distance_holdout(fps, groups, threshold=.6, min_source=2)
        self.assertEqual(result["audit"]["status"], "available")
        distances = distance_matrix(fps)
        nearest = distances[np.ix_(result["holdout"], result["source"])].min(axis=1)
        self.assertTrue(np.all(nearest >= .6))
        np.testing.assert_array_equal(nearest, result["holdout_nearest_source_distance"])
        self.assertFalse(set(result["source"]) & set(result["buffer"]))
        self.assertFalse(set(result["source"]) & set(result["holdout"]))
        self.assertFalse(result["audit"]["target_values_used"])
        self.assertTrue(result["audit"]["every_holdout_meets_distance"])

    def test_structural_tie_break_is_invariant_to_row_order_and_arbitrary_group_ids(self):
        fps, groups = self.synthetic()
        identities = [fp.ToBitString() for fp in fps]
        reference = split_distance_holdout(fps, groups, threshold=.6, min_source=2, identities=identities)
        order = np.asarray([7, 3, 1, 4, 0, 5, 2, 6])
        alternate = split_distance_holdout([fps[i] for i in order], [f"random-{i}" for i in order],
            threshold=.6, min_source=2, identities=[identities[i] for i in order])
        actual = np.empty(len(order), dtype=object)
        actual[order] = alternate["roles"]
        np.testing.assert_array_equal(reference["roles"], actual)

    def test_infeasible_distance_split_is_unavailable_with_no_fallback(self):
        fps = [fingerprint([0, 1, 2])] * 5
        result = split_distance_holdout(fps, list("abcde"), threshold=.5, min_source=2)
        self.assertEqual(result["audit"]["status"], "unavailable_insufficient_distance_separated_records")
        self.assertEqual(len(result["source"]), 0)
        self.assertTrue(result["audit"]["no_random_fallback"])

    def test_hcap_collision_and_duplicate_observations_stay_together(self):
        frame = pd.DataFrame({"SMILES": ["*C(C*)CC", "*C(C)C(C)*", "*CO*", "*c1ccccc1*", "*CS*", "*CCN*"],
                              "target": [1, 2000, 3, 4, 5, 6]})
        result = structural_split(frame, "SMILES", threshold=.5, min_source=1)
        rows = result["membership"].set_index("input_row_position")
        self.assertEqual(rows.loc[0, "canonical_hcap"], rows.loc[1, "canonical_hcap"])
        self.assertNotEqual(rows.loc[0, "canonical_original"], rows.loc[1, "canonical_original"])
        self.assertEqual(rows.loc[0, "protected_group"], rows.loc[1, "protected_group"])
        self.assertEqual(rows.loc[0, "role"], rows.loc[1, "role"])

    def test_target_mutation_cannot_change_split_or_structural_distances(self):
        smiles = ["*CC*", "*CO*", "*CS*", "*CN*", "*c1ccccc1*", "*CC(=O)O*", "*CF*", "*CCl"]
        frame = pd.DataFrame({"SMILES": smiles, "density": np.arange(8), "id": list("abcdefgh")})
        first = structural_split(frame, "SMILES", min_source=1)
        mutated = frame.copy()
        mutated["density"] = [1e100, -1e100, np.nan, "nonnumeric", 0, 15, 3, 9]
        mutated["id"] = list(reversed(list("abcdefgh")))
        second = structural_split(mutated, "SMILES", min_source=1)
        pd.testing.assert_frame_equal(first["membership"], second["membership"])
        self.assertEqual(first["audit"], second["audit"])

    def test_already_log_target_is_inverted_before_source_frozen_unit_conversion(self):
        frame = pd.DataFrame({"value": [2, 3, "missing", "inf", 0]})
        values = heldout_targets(frame, {"uploaded_target_already_logarithmic": True,
            "unit_conversion": {"multiplier": .01, "offset": 1}}, "value")
        np.testing.assert_allclose(values[[0, 1, 4]], [2, 11, 1.01])
        self.assertTrue(np.isnan(values[2]))
        self.assertTrue(np.isinf(values[3]))

    def test_zero_contact_angle_is_valid_numeric_not_dropped(self):
        frame = pd.DataFrame({"Water Contact Angle (deg)": [0, 90, ""]})
        values = heldout_targets(frame, {}, "Water Contact Angle (deg)")
        self.assertEqual(values[0], 0)
        self.assertTrue(np.isfinite(values[0]))


if __name__ == "__main__":
    unittest.main()
