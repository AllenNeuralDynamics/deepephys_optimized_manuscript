import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarking"))

from build_ks4_per_unit_snr_table import (
    _write_markdown,
    _write_paired_markdown,
    build_raw_vs_10_75,
    build_table,
)


REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "benchmarking"


class KilosortPerUnitSnrTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = build_table(RESULTS, REPO)
        cls.paired = build_raw_vs_10_75(cls.table)

    def test_contains_nine_conditions_for_each_reference_unit(self):
        self.assertEqual(len(self.table), 63)
        self.assertTrue(self.table.groupby("gt_unit_id").size().eq(9).all())
        self.assertEqual(
            self.table.drop_duplicates("gt_unit_id")["gt_unit_id"].tolist(),
            [2143, 793, 1143, 1122, 1300, 337, 664],
        )

    def test_snr_join_uses_route_specific_exact_checkpoint(self):
        unit = self.table.loc[self.table["gt_unit_id"].eq(2143)]
        raw = unit.loc[unit["input"].eq("raw AP")].iloc[0]
        omission0 = unit.loc[
            unit["input"].eq("Full96 omission0") & unit["Th_learned"].eq(8)
        ].iloc[0]
        omission0_10_75 = unit.loc[
            unit["input"].eq("Full96 omission0")
            & unit["Th_learned"].eq(10.75)
        ].iloc[0]
        omission1 = unit.loc[unit["input"].eq("Full96 omission1")].iloc[0]
        self.assertAlmostEqual(raw["raw_template_snr"], 16.433961868286133)
        self.assertEqual(raw["input_template_snr"], raw["raw_template_snr"])
        self.assertAlmostEqual(omission0["input_template_snr"], 21.42217254638672)
        self.assertEqual(
            omission0_10_75["input_template_snr"], omission0["input_template_snr"]
        )
        self.assertAlmostEqual(omission1["input_template_snr"], 25.585525512695312)

    def test_gt_event_total_is_invariant_across_conditions(self):
        totals = self.table["true_positive_injected_spikes"].add(
            self.table["false_negative_injected_spikes"]
        )
        counts = totals.groupby(self.table["gt_unit_id"]).nunique()
        self.assertTrue(counts.eq(1).all())

    def test_raw_10_75_loses_four_reference_units(self):
        raw = self.table.query(
            "input == 'raw AP' and Th_universal == 9 and Th_learned == 10.75"
        )
        detected = set(raw.loc[raw["accuracy"].gt(0), "gt_unit_id"])
        lost = set(raw.loc[raw["accuracy"].eq(0), "gt_unit_id"])
        self.assertEqual(detected, {793, 1143, 2143})
        self.assertEqual(lost, {337, 664, 1122, 1300})
        self.assertEqual(raw["true_positive_injected_spikes"].sum(), 274830)
        self.assertEqual(raw["false_negative_injected_spikes"].sum(), 474726)

    def test_raw_vs_10_75_pairing_matches_units_and_precision_deltas(self):
        self.assertEqual(len(self.paired), 7)
        self.assertEqual(
            self.paired["gt_unit_id"].tolist(),
            [2143, 793, 1143, 1122, 1300, 337, 664],
        )
        expected = {
            2143: -0.000102735306,
            793: 0.000139854925,
            1143: -0.071438538785,
            1122: -0.007575926487,
            1300: 0.159920363865,
            337: -0.128466775831,
            664: -0.02032064605,
        }
        observed = self.paired.set_index("gt_unit_id")["precision_change"]
        for unit_id, value in expected.items():
            self.assertAlmostEqual(observed.loc[unit_id], value)

    def test_markdown_describes_snr_and_contains_all_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "per_unit.md"
            _write_markdown(self.table, destination)
            text = destination.read_text()
        self.assertIn("pre-sort GT-template detectability metric", text)
        self.assertIn("| 1 | 2143 | 16.4340 |", text)
        self.assertIn("| 7 | 664 | 3.7236 |", text)
        self.assertEqual(sum(line.startswith("| ") for line in text.splitlines()), 64)

    def test_paired_markdown_labels_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "paired.md"
            _write_paired_markdown(self.paired, destination)
            text = destination.read_text()
        self.assertIn("raw precision (Th 9/8)", text)
        self.assertIn("omission1 precision (Th 9/10.75)", text)
        self.assertIn("| 5 | 1300 | 4.5785 | 5.7119 |", text)
        self.assertEqual(sum(line.startswith("| ") for line in text.splitlines()), 8)


if __name__ == "__main__":
    unittest.main()