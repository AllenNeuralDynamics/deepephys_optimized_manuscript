import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scoring"))

from template_support_sweep import (
    centered_time_slice,
    channel_supports,
    score_supports,
)


class TemplateSupportSweepTests(unittest.TestCase):
    def test_centered_time_slices_include_full_frozen_window(self):
        one_ms = centered_time_slice(1.0, 30_000.0, 45, 120)
        full = centered_time_slice(4.0, 30_000.0, 45, 120)
        self.assertEqual((one_ms.start, one_ms.stop), (30, 60))
        self.assertEqual((full.start, full.stop), (0, 120))

    def test_channel_supports_include_endpoint_and_nested_top_k(self):
        template = np.zeros((120, 5), dtype=float)
        template[45, :] = [10.0, 6.0, 4.9, 2.0, 1.0]
        supports = channel_supports(template, top_ks=(1, 2, 4))
        by_name = {name: channels for name, _, channels in supports}
        self.assertEqual(by_name["endpoint"].tolist(), [0, 1])
        self.assertEqual(by_name["top1"].tolist(), [0])
        self.assertEqual(by_name["top2"].tolist(), [0, 1])
        self.assertEqual(by_name["top4"].tolist(), [0, 1, 2, 3])

    def test_identical_domains_have_zero_gap_in_sample_and_crossfit(self):
        rng = np.random.default_rng(7)
        hits = rng.normal(0, 0.2, size=(8, 120, 3))
        background = rng.normal(0, 0.2, size=(12, 120, 3))
        hits[:, 42:49, 0] -= 3.0
        hits[:, 43:48, 1] -= 1.8
        frame = score_supports(
            hits,
            hits.copy(),
            background,
            background.copy(),
            sampling_frequency=30_000.0,
            nbefore=45,
            temporal_ms=(1.0, 4.0),
            top_ks=(1, 2),
        )
        self.assertEqual(len(frame), 3 * 2 * 3)
        self.assertTrue(np.allclose(frame["ddprime"], 0.0, rtol=0, atol=1e-12))
        self.assertEqual(
            set(frame.loc[frame.evaluation == "crossfit", "n_train_hits"]),
            {4},
        )
        self.assertEqual(
            set(frame.loc[frame.evaluation == "crossfit", "n_test_hits"]),
            {4},
        )

    def test_rejects_mismatched_window_shapes(self):
        windows = np.zeros((8, 120, 3), dtype=float)
        background = np.zeros((12, 120, 3), dtype=float)
        with self.assertRaisesRegex(ValueError, "raw and denoised hit"):
            score_supports(
                windows,
                windows[:, :, :2],
                background,
                background,
                sampling_frequency=30_000.0,
                nbefore=45,
            )


if __name__ == "__main__":
    unittest.main()