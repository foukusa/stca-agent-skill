#!/usr/bin/env python3
"""Regression tests for WRAcc depth search and training-only selection."""
from __future__ import annotations

import itertools
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np


SKILL_DIR = Path(os.environ.get(
    "STCA_TEST_SKILL_DIR", str(Path(__file__).resolve().parents[1] / "skills" / "stca")))
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import wracc_search
import inrange_evaluation as inrange


def legacy_beam(matrix, truth, depth=3, width=30, min_support=5):
    """Independent saved NumPy baseline, including its exact tie order."""
    n = len(truth)
    if not n or not np.any(truth) or np.all(truth):
        return None
    prevalence = float(np.mean(truth))
    keys = [j for j in range(1, matrix.shape[1]) if matrix[:, j].min() != matrix[:, j].max()]
    literals = [(j, value) for j in keys for value in (0, 1)]
    beam, best = [((), np.ones(n, dtype=bool))], None
    for _ in range(depth):
        candidates = {}
        for existing, mask in beam:
            used = {j for j, _ in existing}
            for literal in literals:
                if literal[0] in used:
                    continue
                combination = tuple(sorted(existing + (literal,)))
                if combination in candidates:
                    continue
                selected = mask & (matrix[:, literal[0]] == literal[1])
                support = int(selected.sum())
                if support < min_support:
                    continue
                score = support / n * (float(np.mean(truth[selected])) - prevalence)
                if score > 0:
                    candidates[combination] = (score, selected)
        ordered = sorted(candidates.items(), key=lambda kv: (-kv[1][0], len(kv[0]), kv[0]))[:width]
        beam = [(rule, details[1]) for rule, details in ordered]
        if ordered:
            candidate = ordered[0]
            if best is None or (-candidate[1][0], len(candidate[0]), candidate[0]) < (-best[1][0], len(best[0]), best[0]):
                best = candidate
    return None if best is None else {"literals": list(best[0]), "wracc": float(best[1][0])}


def conjunction_fixture():
    features = np.repeat(np.asarray(list(itertools.product((0, 1), repeat=4)), dtype=np.int8), 8, axis=0)
    matrix = np.column_stack((np.zeros(len(features), dtype=np.int8), features))
    return matrix, (features == 1).all(axis=1)


class WRAccSearchTests(unittest.TestCase):
    def test_cap_three_preserves_original_rules_and_exact_float(self):
        for seed in range(10):
            rng = np.random.default_rng(seed)
            matrix = rng.integers(0, 2, (91, 9), dtype=np.int8)
            matrix[:, 0] = 0
            truth = (matrix[:, 2] == 1) & ((matrix[:, 5] == 0) | (rng.random(91) < .2))
            with self.subTest(seed=seed):
                old = legacy_beam(matrix, truth)
                new = wracc_search.search_wracc(matrix, truth, caps=(3,))["caps"]["3"]
                self.assertIsNotNone(old)
                self.assertEqual(list(map(tuple, new["literals"])), old["literals"])
                self.assertEqual(new["wracc"], old["wracc"])
                self.assertEqual(inrange.beam_wracc(matrix, truth, depth=3), old)

    def test_fixed_depth_above_three_can_improve_training_wracc(self):
        matrix, truth = conjunction_fixture()
        result = wracc_search.search_wracc(matrix, truth, caps=(3, 4, 10, None))
        three, four = result["caps"]["3"], result["caps"]["4"]
        self.assertGreater(four["wracc"], three["wracc"])
        self.assertEqual(four["length"], 4)
        self.assertEqual(four["support"], 8)
        self.assertEqual(result["caps"]["10"], four)
        self.assertEqual(result["caps"]["unlimited"], four)
        new = inrange.beam_wracc(matrix, truth, depth=4)
        self.assertEqual(new["wracc"], four["wracc"])
        self.assertEqual(list(map(tuple, new["literals"])), list(map(tuple, four["literals"])))

    def test_unlimited_does_not_stop_on_score_plateau(self):
        bit = np.tile((0, 1), 20).astype(np.int8)
        matrix = np.column_stack((np.zeros(len(bit), dtype=np.int8), *[bit] * 6))
        result = wracc_search.search_wracc(matrix, bit.astype(bool), caps=(1, None))
        self.assertEqual(result["maximum_varying_keys"], 6)
        self.assertEqual(result["last_depth"], 6)
        self.assertEqual(result["caps"]["unlimited"], result["caps"]["1"])
        self.assertEqual(result["caps"]["unlimited"]["length"], 1)

    def test_rule_uses_distinct_nonconstant_nonzero_keys(self):
        matrix, truth = conjunction_fixture()
        matrix = np.column_stack((matrix, np.ones(len(matrix), dtype=np.int8)))
        result = wracc_search.search_wracc(matrix, truth, caps=(None,))["caps"]["unlimited"]
        literals = result["literals"]
        keys = [key for key, _ in literals]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertNotIn(0, keys)
        self.assertNotIn(5, keys)
        self.assertTrue(all(value in (0, 1) for _, value in literals))

    def test_empty_one_class_and_constant_inputs_remain_no_rule(self):
        inputs = [(np.zeros((0, 3), dtype=np.int8), np.zeros(0, dtype=bool)),
                  (np.zeros((10, 3), dtype=np.int8), np.zeros(10, dtype=bool)),
                  (np.zeros((10, 3), dtype=np.int8), np.ones(10, dtype=bool)),
                  (np.zeros((10, 3), dtype=np.int8), np.arange(10) < 5)]
        for matrix, truth in inputs:
            with self.subTest(n=len(truth), positive_n=int(truth.sum())):
                result = wracc_search.search_wracc(matrix, truth, caps=(3, None))
                self.assertIsNone(result["caps"]["3"])
                self.assertIsNone(result["caps"]["unlimited"])

    def test_user_limits_are_explicit_and_invalid_limits_rejected(self):
        for supplied, expected in (("auto", "auto"), ("unlimited", "unlimited"), ("10", 10), (1, 1)):
            with self.subTest(supplied=supplied):
                self.assertEqual(wracc_search.normalize_wracc_limit(supplied), expected)
        for supplied in (0, -1, "0", "-2", "3.5", "nonsense"):
            with self.subTest(supplied=supplied):
                with self.assertRaises((ValueError, TypeError)):
                    wracc_search.normalize_wracc_limit(supplied)


class WRAccTrainingSelectionTests(unittest.TestCase):
    def learner(self, *, limit="auto", matrix=None, target=None, groups=None, direction="high"):
        default_matrix, _ = conjunction_fixture()
        if matrix is None:
            matrix = default_matrix
        if target is None:
            target = matrix[:, 1] * 3.0 + matrix[:, 2] * 2.0 + np.arange(len(matrix)) / 1000
        if groups is None:
            groups = np.asarray([f"g{i // 2}" for i in range(len(matrix))])
        return inrange.Learners(matrix, target, groups, [.3], direction, {}, "toy", "unit",
                               wracc_max_literals=limit, wracc_length_folds=3)

    def test_auto_only_reads_the_supplied_training_partition(self):
        first = self.learner()
        positions = np.r_[np.arange(40), np.arange(80, 120)]
        excluded = np.setdiff1d(np.arange(len(first.target)), positions)
        selection = first.select_wracc_length(positions, .3)
        changed_matrix, changed_target = first.matrix.copy(), first.target.copy()
        changed_matrix[excluded] = 1 - changed_matrix[excluded]
        changed_target[excluded] = np.linspace(-1e9, 1e9, len(excluded))
        second = self.learner(matrix=changed_matrix, target=changed_target, groups=first.groups)
        changed_selection = second.select_wracc_length(positions, .3)
        self.assertEqual(selection, changed_selection)
        self.assertEqual(selection["selection_status"], "selected_by_training_only_grouped_inner_cv")
        self.assertEqual(selection["training_positions"], positions.tolist())

    def test_inner_folds_preserve_groups_and_use_only_their_training_quantile(self):
        learner = self.learner()
        positions = np.r_[np.arange(40), np.arange(80, 120)]
        selection = learner.select_wracc_length(positions, .3)
        held_out = []
        non_global_threshold = False
        global_threshold = inrange.cutoff(learner.target[positions], .3, learner.direction)
        for fold in selection["inner_folds"]:
            train, test = np.asarray(fold["train_positions"]), np.asarray(fold["test_positions"])
            self.assertFalse(set(train) & set(test))
            self.assertEqual(set(train) | set(test), set(positions))
            self.assertFalse(set(learner.groups[train]) & set(learner.groups[test]))
            self.assertEqual(fold["protected_group_overlap_n"], 0)
            expected = inrange.cutoff(learner.target[train], .3, learner.direction)
            self.assertEqual(fold["training_cutoff_model"], expected)
            non_global_threshold |= expected != global_threshold
            held_out.extend(test.tolist())
        self.assertEqual(sorted(held_out), sorted(positions.tolist()))
        self.assertTrue(non_global_threshold, "Fixture must expose accidental global-quantile labeling.")

    def test_selection_scores_are_pooled_inner_oof_using_each_training_cutoff(self):
        for direction in ("high", "low"):
            with self.subTest(direction=direction):
                learner = self.learner(direction=direction)
                positions = np.arange(len(learner.target))
                selection = learner.select_wracc_length(positions, .3)
                by_position = {int(position): local for local, position in enumerate(positions)}
                truth = np.zeros(len(positions), dtype=bool)
                predictions = {wracc_search.cap_name(cap): np.full(len(positions), -1, dtype=np.int8)
                               for cap in wracc_search.DEFAULT_CAPS}
                for fold in selection["inner_folds"]:
                    test = np.asarray(fold["test_positions"], dtype=int)
                    local_test = [by_position[int(position)] for position in test]
                    truth[local_test] = inrange.labels(learner.target[test], fold["training_cutoff_model"], direction)
                    for name, entry in fold["candidates"].items():
                        mask = inrange.rule_mask(learner.matrix[test], entry["rule"])
                        if mask is not None:
                            predictions[name][local_test] = mask.astype(np.int8)
                for candidate in selection["candidates"]:
                    prediction = predictions[wracc_search.cap_name(candidate["max_literals"])]
                    if (prediction < 0).any():
                        self.assertIsNone(candidate["AS"])
                        self.assertNotEqual(candidate["status"], "evaluated")
                    else:
                        expected = inrange.scores(truth, prediction == 1)
                        self.assertEqual(candidate["AS"], expected["AS"])
                        self.assertEqual(candidate["status"], expected["status"])

    def test_exact_validation_score_ties_prefer_smaller_cap(self):
        learner = self.learner()
        real_scores = inrange.scores
        def tied_scores(truth, prediction):
            return {**real_scores(truth, prediction), "AS": .5}
        with patch.object(inrange, "scores", side_effect=tied_scores):
            selection = learner.select_wracc_length(np.arange(len(learner.target)), .3)
        self.assertTrue(all(item["status"] == "evaluated" for item in selection["candidates"]))
        self.assertEqual(selection["selected_max_literals"], 1)

    def test_user_fixed_or_unlimited_depth_does_not_run_inner_selection(self):
        for setting in (1, 10, "unlimited"):
            with self.subTest(setting=setting):
                learner = self.learner(limit=setting)
                with patch.object(inrange, "grouped_folds", side_effect=AssertionError("Not requested")):
                    selection = learner.select_wracc_length(np.arange(20), .3)
                self.assertEqual(selection["selected_max_literals"], setting)
                self.assertEqual(selection["selection_status"], "user_specified")
                self.assertEqual(selection["inner_folds_used"], 0)
                self.assertEqual(selection["inner_folds"], [])

    def test_incomplete_inner_rules_are_unavailable_not_dropped_or_false_filled(self):
        learner = self.learner()
        real_search = inrange.search_wracc
        call_n = 0
        def incomplete_search(matrix, truth, **kwargs):
            nonlocal call_n
            result = real_search(matrix, truth, **kwargs)
            call_n += 1
            if call_n == 1:
                result["caps"] = {name: None for name in result["caps"]}
            return result
        with patch.object(inrange, "search_wracc", side_effect=incomplete_search):
            selection = learner.select_wracc_length(np.arange(len(learner.target)), .3)
        self.assertEqual(selection["selection_status"], "unavailable")
        self.assertEqual(selection["selected_max_literals"], "unlimited")
        self.assertEqual(selection["fallback_reason"], "no_cap_has_complete_two_class_inner_OOF_evidence")
        self.assertTrue(all(item["status"] == "unavailable_missing_inner_rule" for item in selection["candidates"]))
        self.assertTrue(all(item["AS"] is None for item in selection["candidates"]))
        self.assertTrue(all(item["unknown_prediction_n"] > 0 for item in selection["candidates"]))

    def test_too_few_protected_groups_reports_unvalidated_fallback(self):
        learner = self.learner(groups=np.repeat("same", 128))
        selection = learner.select_wracc_length(np.arange(128), .3)
        self.assertEqual(selection["selection_status"], "unavailable")
        self.assertEqual(selection["fallback_reason"], "insufficient_protected_groups")
        self.assertEqual(selection["selected_max_literals"], "unlimited")
        self.assertEqual(selection["inner_folds_used"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
