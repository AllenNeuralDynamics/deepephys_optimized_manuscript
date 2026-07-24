import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarking"))

from ks4_parameter_sweep import (
    BASELINE_PARAMS,
    FIRST_SWEEP,
    build_params,
    changed_paths,
    compact_json,
)


class KilosortParameterSweepTests(unittest.TestCase):
    def test_frozen_baseline_matches_executed_controls(self):
        self.assertEqual(BASELINE_PARAMS["min_drift_channels"], 64)
        self.assertFalse(BASELINE_PARAMS["skip_motion_correction"])
        sorter = BASELINE_PARAMS["sorter"]
        self.assertEqual(sorter["Th_universal"], 9)
        self.assertEqual(sorter["Th_learned"], 8)
        self.assertEqual(sorter["Th_single_ch"], 6)
        self.assertEqual(sorter["whitening_range"], 32)
        self.assertTrue(sorter["do_CAR"])
        self.assertEqual(sorter["highpass_cutoff"], 300)
        self.assertFalse(sorter["skip_kilosort_preprocessing"])

    def test_first_sweep_changes_only_learned_threshold(self):
        self.assertEqual(FIRST_SWEEP, (9.0, 10.0))
        for threshold in FIRST_SWEEP:
            candidate = build_params(threshold)
            self.assertEqual(changed_paths(candidate), ["sorter.Th_learned"])
            self.assertEqual(candidate["sorter"]["Th_learned"], threshold)

    def test_candidates_do_not_mutate_baseline(self):
        candidate = build_params(9)
        candidate["sorter"]["Th_universal"] = 99
        self.assertEqual(BASELINE_PARAMS["sorter"]["Th_universal"], 9)

    def test_compact_payload_round_trips(self):
        candidate = build_params(10)
        self.assertEqual(json.loads(compact_json(candidate)), candidate)

    def test_rejects_nonpositive_threshold(self):
        with self.assertRaisesRegex(ValueError, "must be positive"):
            build_params(0)


if __name__ == "__main__":
    unittest.main()