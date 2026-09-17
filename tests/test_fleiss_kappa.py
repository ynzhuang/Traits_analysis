"""
Tests for Fleiss' kappa, the multi-reviewer agreement statistic.

`calculate_fleiss_kappa` is the statistical core of the agreement analysis and
the one piece of it that is pure arithmetic -- no model, no network, no
fixtures. Every expected value below is derived by hand from the definition
rather than recorded from a previous run, so these tests fail if the
computation drifts rather than merely changing.

Notation follows the implementation: the input is a matrix whose rows are
criteria and whose columns are reviewers, each cell 1 (trait present) or
0 (absent).
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_criteria_decomposition_agreement import calculate_fleiss_kappa


class TestFleissKappaGuards(unittest.TestCase):
    """Degenerate inputs return 0.0 rather than raising."""

    def test_empty_matrix_returns_zero(self):
        self.assertEqual(calculate_fleiss_kappa([]), 0.0)

    def test_none_matrix_returns_zero(self):
        self.assertEqual(calculate_fleiss_kappa(None), 0.0)

    def test_two_reviewers_returns_zero(self):
        """Fleiss' kappa is undefined below three reviewers.

        Two-reviewer agreement is Cohen's kappa; the implementation declines
        rather than silently computing something that is not Fleiss'.
        """
        self.assertEqual(calculate_fleiss_kappa([[1, 1], [0, 0]]), 0.0)

    def test_single_reviewer_returns_zero(self):
        self.assertEqual(calculate_fleiss_kappa([[1], [0]]), 0.0)


class TestFleissKappaValues(unittest.TestCase):
    """Hand-derived values across the range of the statistic."""

    def test_perfect_agreement_balanced_marginals(self):
        """Every reviewer agrees, and the two categories are equally used.

        rows [1,1,1] and [0,0,0]: all 3 pairs agree in each row, so
        P_observed = 1.0. Three of six ratings are 'present', so
        p_present = p_absent = 0.5 and P_expected = 0.5^2 + 0.5^2 = 0.5.
        kappa = (1.0 - 0.5) / (1 - 0.5) = 1.0
        """
        self.assertAlmostEqual(
            calculate_fleiss_kappa([[1, 1, 1], [0, 0, 0]]), 1.0, places=6
        )

    def test_unanimous_present_is_defined_as_one(self):
        """All ratings in one category makes P_expected = 1.0.

        kappa is then 0/0. The implementation resolves that case explicitly:
        perfect observed agreement returns 1.0.
        """
        self.assertEqual(calculate_fleiss_kappa([[1, 1, 1], [1, 1, 1]]), 1.0)

    def test_unanimous_absent_is_defined_as_one(self):
        self.assertEqual(calculate_fleiss_kappa([[0, 0, 0], [0, 0, 0]]), 1.0)

    def test_agreement_worse_than_chance_is_negative(self):
        """rows [1,0,0] and [0,1,1].

        Each row has exactly one agreeing pair out of three, so
        P_observed = 1/3. Three of six ratings are 'present', so
        P_expected = 0.5.
        kappa = (1/3 - 1/2) / (1 - 1/2) = -1/3
        """
        self.assertAlmostEqual(
            calculate_fleiss_kappa([[1, 0, 0], [0, 1, 1]]), -1.0 / 3.0, places=6
        )

    def test_partial_agreement(self):
        """rows [1,1,1] (unanimous) and [1,0,0] (split).

        Row 1: 3/3 pairs agree. Row 2: 1/3 pairs agree.
        P_observed = (1 + 1/3) / 2 = 2/3.
        Four of six ratings are 'present', so p_present = 2/3 and
        P_expected = (2/3)^2 + (1/3)^2 = 5/9.
        kappa = (2/3 - 5/9) / (1 - 5/9) = (1/9) / (4/9) = 0.25
        """
        self.assertAlmostEqual(
            calculate_fleiss_kappa([[1, 1, 1], [1, 0, 0]]), 0.25, places=6
        )

    def test_result_is_bounded_above_by_one(self):
        """No input should produce a coefficient above 1.0."""
        matrices = [
            [[1, 1, 1], [0, 0, 0]],
            [[1, 1, 1, 1], [0, 0, 0, 0]],
            [[1, 0, 1], [0, 1, 0], [1, 1, 1]],
        ]
        for matrix in matrices:
            with self.subTest(matrix=matrix):
                self.assertLessEqual(calculate_fleiss_kappa(matrix), 1.0)

    def test_scales_past_three_reviewers(self):
        """Four unanimous reviewers over balanced categories still give 1.0."""
        self.assertAlmostEqual(
            calculate_fleiss_kappa([[1, 1, 1, 1], [0, 0, 0, 0]]), 1.0, places=6
        )


if __name__ == "__main__":
    unittest.main()
