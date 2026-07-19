import importlib.util
from pathlib import Path
import unittest

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scoring" / "validation_loss_headroom.py"
SPEC = importlib.util.spec_from_file_location("validation_loss_headroom", SCRIPT)
HEADROOM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HEADROOM)


class FakeSorting:
    unit_ids = [1]

    def get_unit_spike_train(self, unit_id, segment_index=0):
        return np.array([450], dtype=np.int64)


class ValidationLossHeadroomTests(unittest.TestCase):
    def test_context_offsets_match_r5(self):
        offsets = HEADROOM.context_offsets(30, 30, 0, True, 1)
        self.assertEqual(offsets.size, 61)
        self.assertEqual(offsets[0], -30)
        self.assertEqual(offsets[-1], 0)
        self.assertNotIn(0, offsets[:-1])

    def test_validation_subset_matches_training_sampler(self):
        centers = HEADROOM.validation_centers(1_800_000, 30, 30, 0, 20_000)
        self.assertEqual(centers.size, 20_000)
        self.assertEqual(centers[0], 30)
        self.assertEqual(centers[-1], 1_799_940)
        np.testing.assert_array_equal(np.diff(centers), np.full(19_999, 90))

    def test_spike_support_uses_temporal_and_spatial_mask(self):
        raw = np.zeros((900, 4), dtype=np.float32)
        raw[448:453, 1] = -5
        raw[448:453, 2] = -3
        centers = np.arange(30, 870, 90)
        support, units = HEADROOM.spike_support(
            raw, centers, FakeSorting(), 0, 30_000, 1.5, 2.5, 0.5, 24, 0
        )
        self.assertEqual(int(support.sum()), 2)
        self.assertEqual(int(units.loc[0, "spikes_in_slice"]), 1)
        self.assertEqual(int(units.loc[0, "support_channels"]), 2)


if __name__ == "__main__":
    unittest.main()