"""Statistical edge cases whose errors would invalidate reported conclusions."""
import unittest
import numpy as np
from sklearn.metrics import roc_auc_score

from src.stats import (auc_summary, bootstrap_auc, choose_threshold, compound_verdict,
                       metrics, paired_auc_difference, paired_gap_difference,
                       stratified_indices, top_label_ece)


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        self.y = np.array([0, 0, 0, 1, 1, 1])
        self.good = np.array([.1, .2, .3, .7, .8, .9])

    def test_rank_bootstrap_matches_independent_sklearn_with_ties(self):
        p = np.array([.1, .5, .5, .5, .9, .9])
        indices = stratified_indices(self.y, 31, 7)
        actual = bootstrap_auc(self.y, p, indices)[0]
        expected = np.array([roc_auc_score(self.y[i], p[i]) for i in indices])
        np.testing.assert_allclose(actual, expected)
        self.assertTrue(np.all(self.y[indices].sum(axis=1) == 3))

    def test_identical_methods_have_exact_zero_paired_interval(self):
        p = np.stack([self.good, self.good[::-1], np.ones(6) * .5])
        result = paired_auc_difference(self.y, p, p, 71)
        self.assertEqual(result['ci95'], [0., 0.])
        self.assertEqual(result['direction'], 'no_detectable_difference')

    def test_detectable_difference_and_reversed_direction(self):
        good = np.tile(self.good, (3, 1))
        bad = 1 - good
        result = paired_auc_difference(self.y, good, bad, 31)
        self.assertEqual(result['mean'], 1.)
        self.assertEqual(result['direction'], 'a_better')
        reverse = paired_auc_difference(self.y, bad, good, 31)
        self.assertEqual(reverse['direction'], 'b_better')

    def test_seed_noise_blocks_overstated_gain(self):
        a = np.stack([self.good, self.good, 1 - self.good])
        b = np.ones((3, 6)) * .5
        result = paired_auc_difference(self.y, a, b, 31)
        self.assertGreater(result['ci95'][0], 0)
        self.assertEqual(result['direction'], 'no_detectable_difference')

    def test_gap_uses_two_cohorts_and_appropriate_direction(self):
        good = np.tile(self.good, (3, 1))
        result = paired_gap_difference(self.y, good, good, self.y, 1 - good, good, 31)
        self.assertEqual(result['mean'], 1.)
        self.assertEqual(result['direction'], 'a_larger_gap')

    def test_threshold_is_chosen_from_validation_scores(self):
        threshold = choose_threshold(self.y, self.good)
        self.assertEqual(threshold, .7)
        self.assertEqual(metrics(self.y, self.good, threshold)['macro_f1'], 1.)

    def test_ece_endpoint_and_wrong_confident_predictions(self):
        self.assertEqual(top_label_ece(self.y, self.y.astype(float)), 0.)
        self.assertEqual(top_label_ece(self.y, 1. - self.y), 1.)

    def test_invalid_probabilities_and_missing_seed_fail(self):
        with self.assertRaises(ValueError):
            metrics(self.y, np.ones(6) * np.nan)
        with self.assertRaises(ValueError):
            auc_summary(self.y, np.tile(self.good, (2, 1)), 31)

    def test_compound_logic_does_not_convert_nondetection_to_support(self):
        self.assertEqual(compound_verdict(['supported', 'inconclusive']), 'inconclusive')
        self.assertEqual(compound_verdict(['rejected', 'inconclusive']), 'rejected')
        self.assertEqual(compound_verdict(['supported', 'supported']), 'supported')


if __name__ == '__main__':
    unittest.main()
