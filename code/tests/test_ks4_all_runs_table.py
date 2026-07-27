import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarking"))

from build_ks4_all_runs_table import (
    COMMON_ACCURACY_COLUMN,
    COMMON_FN_COLUMN,
    COMMON_FP_COLUMN,
    COMMON_GT_UNITS,
    COMMON_PRECISION_COLUMN,
    COMMON_RECALL_COLUMN,
    COMMON_TP_COLUMN,
    _write_markdown,
    build_table,
)


RESULTS = Path(__file__).resolve().parents[2] / "results" / "benchmarking"


class KilosortAllRunsTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = build_table(RESULTS)

    def test_contains_every_audited_run(self):
        self.assertEqual(len(self.table), 15)
        self.assertEqual(
            self.table.groupby("scope").size().to_dict(),
            {"5 min clip": 3, "20 min clip": 3, "full recording": 9},
        )

    def test_full_recording_configurations_are_unique(self):
        full = self.table.query("scope == 'full recording'")
        observed = set(
            zip(full["input"], full["Th_universal"], full["Th_learned"])
        )
        expected = {
            ("raw AP", 9.0, 8.0),
            ("raw AP", 9.0, 10.75),
            ("Full96 omission0", 9.0, 8.0),
            ("Full96 omission0", 9.0, 10.75),
            ("Full96 omission1", 9.0, 8.0),
            ("Full96 omission1", 9.0, 9.0),
            ("Full96 omission1", 9.0, 10.0),
            ("Full96 omission1", 9.0, 10.75),
            ("Full96 omission1", 10.0, 9.0),
        }
        self.assertEqual(observed, expected)

    def test_event_counts_use_fixed_common_seven(self):
        self.assertEqual(
            COMMON_GT_UNITS, (337, 664, 793, 1122, 1143, 1300, 2143)
        )
        full = self.table.query("scope == 'full recording'")
        self.assertTrue(
            full[COMMON_TP_COLUMN].add(full[COMMON_FN_COLUMN]).eq(749556).all()
        )
        self.assertTrue(
            full[COMMON_TP_COLUMN].eq(full["true_positive_injected_spikes"]).all()
        )
        self.assertTrue(
            full[COMMON_FP_COLUMN].eq(
                full["false_positive_spikes_in_matched_clusters"]
            ).all()
        )
        raw = full.query("input == 'raw AP' and Th_learned == 8").iloc[0]
        raw_10_75 = full.query(
            "input == 'raw AP' and Th_universal == 9 and Th_learned == 10.75"
        ).iloc[0]
        learned_10_75 = full.query(
            "input == 'Full96 omission1' and Th_universal == 9 "
            "and Th_learned == 10.75"
        ).iloc[0]
        omission0_10_75 = full.query(
            "input == 'Full96 omission0' and Th_universal == 9 "
            "and Th_learned == 10.75"
        ).iloc[0]
        self.assertEqual(raw[COMMON_FN_COLUMN], 220712)
        self.assertAlmostEqual(raw[COMMON_ACCURACY_COLUMN], 0.638708355849)
        self.assertAlmostEqual(raw[COMMON_PRECISION_COLUMN], 0.835865382453)
        self.assertAlmostEqual(raw[COMMON_RECALL_COLUMN], 0.70560590098)
        self.assertEqual(raw_10_75["gt_units_detected"], 3)
        self.assertEqual(raw_10_75[COMMON_TP_COLUMN], 274830)
        self.assertEqual(raw_10_75[COMMON_FN_COLUMN], 474726)
        self.assertEqual(raw_10_75[COMMON_FP_COLUMN], 3565)
        self.assertAlmostEqual(raw_10_75[COMMON_ACCURACY_COLUMN], 0.364122405372)
        self.assertAlmostEqual(raw_10_75[COMMON_PRECISION_COLUMN], 0.420697109171)
        self.assertAlmostEqual(raw_10_75[COMMON_RECALL_COLUMN], 0.366779562423)
        self.assertEqual(learned_10_75[COMMON_FN_COLUMN], 205862)
        self.assertAlmostEqual(
            learned_10_75[COMMON_ACCURACY_COLUMN], 0.647589645847
        )
        self.assertAlmostEqual(
            learned_10_75[COMMON_PRECISION_COLUMN], 0.826173324786
        )
        self.assertAlmostEqual(
            learned_10_75[COMMON_RECALL_COLUMN], 0.725321578476
        )
        self.assertEqual(omission0_10_75[COMMON_TP_COLUMN], 546055)
        self.assertEqual(omission0_10_75[COMMON_FN_COLUMN], 203501)
        self.assertEqual(omission0_10_75[COMMON_FP_COLUMN], 121759)
        self.assertAlmostEqual(
            omission0_10_75[COMMON_ACCURACY_COLUMN], 0.649731939868
        )
        twenty_8 = self.table.query(
            "scope == '20 min clip' and Th_learned == 8"
        ).iloc[0]
        twenty_9 = self.table.query(
            "scope == '20 min clip' and Th_learned == 9"
        ).iloc[0]
        self.assertEqual(twenty_8[COMMON_TP_COLUMN], 119215)
        self.assertEqual(twenty_8[COMMON_FN_COLUMN], 6510)
        self.assertEqual(twenty_9[COMMON_TP_COLUMN], 116546)
        self.assertEqual(twenty_9[COMMON_FN_COLUMN], 9179)
        self.assertEqual(twenty_8[COMMON_FP_COLUMN], 113209)
        self.assertEqual(twenty_9[COMMON_FP_COLUMN], 54971)
        self.assertLess(
            twenty_8[COMMON_TP_COLUMN], twenty_8["true_positive_injected_spikes"]
        )
        self.assertLess(
            twenty_8[COMMON_FP_COLUMN],
            twenty_8["false_positive_spikes_in_matched_clusters"],
        )

    def test_markdown_contains_all_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "all_runs.md"
            _write_markdown(self.table, destination)
            text = destination.read_text()
        self.assertIn("| full recording | raw AP | 9 | 8 |", text)
        self.assertIn("| full recording | raw AP | 9 | 10.75 |", text)
        self.assertIn("| full recording | Full96 omission0 | 9 | 8 |", text)
        self.assertIn("| full recording | Full96 omission0 | 9 | 10.75 |", text)
        self.assertIn("| full recording | Full96 omission1 | 9 | 10.75 |", text)
        self.assertIn("accuracy (fixed 7)", text)
        self.assertIn("precision (fixed 7)", text)
        self.assertIn("recall (fixed 7)", text)
        self.assertIn("TP spikes in fixed 7 GT units", text)
        self.assertIn("FN spikes in fixed 7 GT units", text)
        self.assertIn("FP spikes in fixed 7 GT-matched clusters", text)
        self.assertEqual(sum(line.startswith("| ") for line in text.splitlines()), 16)


if __name__ == "__main__":
    unittest.main()