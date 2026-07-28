import sys
import unittest
from pathlib import Path

import numpy as np


FIGURE_CODE = Path(__file__).resolve().parents[1] / "figures"
sys.path.insert(0, str(FIGURE_CODE))

from kilosort4_fp_by_peel import build_table
from kilosort4_score_margin_by_peel import EXPECTED_EVENTS, load_analysis


class KilosortEventLineageFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fp_table = build_table()
        cls.margin_table, cls.margin_summary = load_analysis()

    def test_fp_totals_and_shares(self):
        expected = {"raw": 56509, "denoised": 30931}
        for domain, total in expected.items():
            rows = self.fp_table.loc[self.fp_table["domain"].eq(domain)]
            self.assertEqual(int(rows["fp_events"].sum()), total)
            self.assertAlmostEqual(rows["fp_share"].sum(), 1.0)
            self.assertAlmostEqual(rows["fp_cumulative"].iloc[-1], 1.0)

    def test_every_condition_status_total_is_exact(self):
        for (domain, threshold), expected in EXPECTED_EVENTS.items():
            observed = self.margin_summary.loc[
                self.margin_summary["domain"].eq(domain)
                & self.margin_summary["Th_learned"].eq(threshold)
            ].set_index("status")["events"]
            self.assertEqual(observed.to_dict(), expected)

    def test_all_accepted_score_statistics_exceed_threshold(self):
        margin_columns = [
            "score_margin_mean",
            "score_margin_q10",
            "score_margin_median",
            "score_margin_q90",
        ]
        self.assertTrue(self.margin_table[margin_columns].ge(0).all().all())

    def test_per_peel_quantiles_are_ordered(self):
        self.assertTrue(
            self.margin_table["score_margin_q10"]
            .le(self.margin_table["score_margin_median"])
            .all()
        )
        self.assertTrue(
            self.margin_table["score_margin_median"]
            .le(self.margin_table["score_margin_q90"])
            .all()
        )

    def test_matched_cluster_fp_events_occur_later_and_closer_to_threshold(self):
        summary = self.margin_summary.set_index(
            ["domain", "Th_learned", "status"]
        )
        for domain in ("raw", "denoised"):
            tp = summary.loc[(domain, 10.75, "tp")]
            fp = summary.loc[(domain, 10.75, "fp_matched_cluster")]
            self.assertGreater(fp["median_peel"], tp["median_peel"])
            self.assertLess(
                fp["weighted_mean_score_margin"],
                tp["weighted_mean_score_margin"],
            )

    def test_raw_eight_zero_fp_is_not_zero_event_output(self):
        summary = self.margin_summary.set_index(
            ["domain", "Th_learned", "status"]
        )
        self.assertEqual(summary.loc[("raw", 8.0, "fp_matched_cluster"), "events"], 0)
        self.assertEqual(
            summary.loc[("raw", 8.0, "unmatched_cluster"), "events"],
            21112308,
        )
        self.assertTrue(
            np.isnan(
                summary.loc[
                    ("raw", 8.0, "fp_matched_cluster"),
                    "weighted_mean_score_margin",
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()