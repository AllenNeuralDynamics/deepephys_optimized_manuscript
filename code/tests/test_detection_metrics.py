import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scoring"))

from detection_metrics import standardized_separation, validate_frame_alignment


class DummyRecording:
    def __init__(self, sampling_frequency=30_000.0, segments=1, samples=1_000):
        self.sampling_frequency = sampling_frequency
        self.segments = segments
        self.samples = samples

    def get_sampling_frequency(self):
        return self.sampling_frequency

    def get_num_segments(self):
        return self.segments

    def get_num_samples(self, segment_index=0):
        return self.samples


class DummySorting:
    def __init__(self, spike_trains, sampling_frequency=30_000.0, segments=1):
        self.spike_trains = spike_trains
        self.sampling_frequency = sampling_frequency
        self.segments = segments
        self.unit_ids = list(spike_trains)

    def get_sampling_frequency(self):
        return self.sampling_frequency

    def get_num_segments(self):
        return self.segments

    def get_unit_spike_train(self, unit_id, segment_index=0):
        return self.spike_trains[unit_id]


class DetectionMetricTests(unittest.TestCase):
    def test_dprime_uses_distribution_means_and_variances(self):
        hits = np.array([2.0, 3.0, 4.0, 5.0])
        background = np.array([-1.0, 0.0, 1.0, 2.0])
        expected = (hits.mean() - background.mean()) / np.sqrt(
            0.5 * (hits.var() + background.var())
        )
        self.assertAlmostEqual(
            standardized_separation(hits, background), expected, places=12
        )

    def test_dprime_is_invariant_to_shared_offset_and_positive_scale(self):
        hits = np.array([1.0, 2.5, 3.0, 4.0])
        background = np.array([-2.0, -0.5, 0.0, 1.0])
        baseline = standardized_separation(hits, background)
        transformed = standardized_separation(7.0 * hits + 13.0, 7.0 * background + 13.0)
        self.assertAlmostEqual(baseline, transformed, places=12)

    def test_accepts_shared_integer_frame_coordinates(self):
        recording = DummyRecording()
        sorting = DummySorting({1: np.array([0, 25, 999], dtype=np.int64)})
        self.assertIsNone(validate_frame_alignment(recording, sorting))

    def test_rejects_sampling_frequency_mismatch(self):
        with self.assertRaisesRegex(ValueError, "sampling-frequency mismatch"):
            validate_frame_alignment(
                DummyRecording(),
                DummySorting({1: np.array([10])}, sampling_frequency=29_999.0),
            )

    def test_rejects_noninteger_spike_times(self):
        with self.assertRaisesRegex(ValueError, "integer frame indices"):
            validate_frame_alignment(
                DummyRecording(), DummySorting({1: np.array([10.5])})
            )


if __name__ == "__main__":
    unittest.main()