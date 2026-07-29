import sys
import unittest
from pathlib import Path


FIGURE_CODE = Path(__file__).resolve().parents[1] / "figures"
sys.path.insert(0, str(FIGURE_CODE))

from kilosort4_target_decoy import EXPECTED, load_data


REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "benchmarking" / "ks4_target_decoy"


class KilosortTargetDecoyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.comparison, cls.gate, cls.trajectory = load_data()

    def test_final_counts_are_exact(self):
        for domain, expected in EXPECTED.items():
            row = self.comparison.loc[self.comparison["domain"].eq(domain)].iloc[0]
            self.assertEqual({key: int(row[key]) for key in expected}, expected)

    def test_exact_candidate_fdr_never_exceeds_five_percent(self):
        accepted = self.gate.loc[self.gate["accepted_events"].gt(0)]
        self.assertFalse(accepted.empty)
        self.assertLessEqual(accepted["exact_fdr"].max(), 0.05)
        self.assertTrue(
            accepted["selected_target_count"].astype(int).eq(
                accepted["accepted_events"].astype(int)
            ).all()
        )

    def test_gate_is_stricter_than_kilosort_floor(self):
        accepted = self.gate.loc[self.gate["accepted_events"].gt(0)]
        self.assertGreater(accepted["selected_threshold"].median(), 8.0)
        self.assertGreater(accepted["selected_threshold"].min(), 8.0)

    def test_gate_loses_units_and_true_positive_events(self):
        for _, row in self.comparison.iterrows():
            self.assertLess(
                row["matched_gt_units_target_decoy"],
                row["matched_gt_units_baseline"],
            )
            self.assertLess(row["tp_target_decoy"], row["tp_baseline"])
            self.assertLess(
                row["fp_in_matched_clusters_target_decoy"],
                row["fp_in_matched_clusters_baseline"],
            )

    def test_only_high_snr_reference_units_survive(self):
        units = __import__("pandas").read_csv(RESULTS / "target_decoy_unit_summary.csv")
        final = units.query("stage == 'duplicate_removal' and cluster_id >= 0")
        observed = {
            domain: set(group["gt_unit_id"].astype(int))
            for domain, group in final.groupby("domain")
        }
        self.assertEqual(observed["raw_native_fdr"], {793, 2143})
        self.assertEqual(observed["denoised_native_fdr"], {793, 2143})

    def test_threshold_and_stopping_trajectories_cover_both_domains(self):
        self.assertEqual(
            set(self.trajectory["domain"]),
            {"raw_native_fdr", "denoised_native_fdr"},
        )
        accepted = self.trajectory.loc[self.trajectory["accepting_batches"].gt(0)]
        self.assertTrue(accepted["threshold_median"].notna().all())
        for _, rows in self.trajectory.groupby("domain"):
            self.assertLess(rows["accepting_batch_fraction"].iloc[-1], 0.5)


if __name__ == "__main__":
    unittest.main()
