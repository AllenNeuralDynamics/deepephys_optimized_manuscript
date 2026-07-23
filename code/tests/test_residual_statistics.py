#!/usr/bin/env python3
"""Focused tests for residual distribution and whiteness statistics."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

SCORING = Path(__file__).resolve().parents[1] / "scoring"
sys.path.insert(0, str(SCORING))

from residual_statistics import analyze_domain
from export_residual_diagnostics import select_gt_free_starts


class ResidualStatisticsTests(unittest.TestCase):
    def test_white_gaussian_is_distinguished_from_colored_heavy_tailed_noise(self):
        random = np.random.default_rng(17)
        shape = (128, 128, 8)
        white = random.normal(size=shape)

        innovations = random.standard_t(df=5, size=shape)
        shared = random.standard_t(df=5, size=shape[:2] + (1,))
        colored = np.empty(shape, dtype=np.float64)
        colored[:, 0, :] = innovations[:, 0, :] + 0.8 * shared[:, 0, :]
        for sample_index in range(1, shape[1]):
            colored[:, sample_index, :] = (
                0.75 * colored[:, sample_index - 1, :]
                + innovations[:, sample_index, :]
                + 0.8 * shared[:, sample_index, :]
            )

        white_table, white_arrays = analyze_domain(
            white, white, sampling_frequency=30_000, max_lag=20
        )
        colored_table, colored_arrays = analyze_domain(
            colored, colored, sampling_frequency=30_000, max_lag=20
        )

        self.assertLess(
            white_table["mean_abs_autocorrelation"].median(),
            colored_table["mean_abs_autocorrelation"].median() / 5,
        )
        self.assertLess(
            white_table["normal_quantile_rmse"].median(),
            colored_table["normal_quantile_rmse"].median() / 2,
        )
        self.assertLess(
            np.median(np.abs(white_arrays["spatial_correlation"][~np.eye(8, dtype=bool)])),
            np.median(np.abs(colored_arrays["spatial_correlation"][~np.eye(8, dtype=bool)])) / 5,
        )
        self.assertGreater(
            white_table["spectral_flatness"].median(),
            colored_table["spectral_flatness"].median() + 0.3,
        )

    def test_rejects_zero_variance_channel(self):
        values = np.ones((4, 16, 3))
        with self.assertRaisesRegex(ValueError, "nonzero variance"):
            analyze_domain(values, values, sampling_frequency=30_000, max_lag=3)

    def test_gt_free_starts_are_spread_and_exclude_spikes(self):
        spikes = np.asarray([40, 100, 170, 260, 400])
        starts = select_gt_free_starts(spikes, num_samples=500, length=20, count=4)
        self.assertEqual(len(starts), 4)
        self.assertTrue(np.all(np.diff(starts) > 0))
        for start in starts:
            self.assertFalse(np.any((spikes >= start) & (spikes < start + 20)))
        midpoint_start = select_gt_free_starts(
            spikes, num_samples=500, length=20, count=1
        )[0]
        self.assertEqual(midpoint_start, 205)


if __name__ == "__main__":
    unittest.main()