#!/usr/bin/env python3
"""Plot the target-decoy FDR experiment against native Kilosort baselines."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "benchmarking" / "ks4_target_decoy"
FIGURES = REPO / "figures"
COMPARISON = RESULTS / "target_decoy_vs_native_baseline.csv"
GATE = RESULTS / "target_decoy_gate_by_batch_peel.csv"

DOMAIN_STYLE = {
    "raw_native": {"label": "Raw-native", "color": "#4F5965"},
    "denoised": {"label": "Full96 denoised-native", "color": "#23748F"},
}
EXPECTED = {
    "raw_native": {
        "matched_gt_units_baseline": 7,
        "matched_gt_units_target_decoy": 2,
        "tp_baseline": 97677,
        "tp_target_decoy": 30920,
        "fp_in_matched_clusters_baseline": 31012,
        "fp_in_matched_clusters_target_decoy": 18,
    },
    "denoised": {
        "matched_gt_units_baseline": 8,
        "matched_gt_units_target_decoy": 2,
        "tp_baseline": 125183,
        "tp_target_decoy": 35082,
        "fp_in_matched_clusters_baseline": 80624,
        "fp_in_matched_clusters_target_decoy": 4,
    },
}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not COMPARISON.exists() or not GATE.exists():
        raise FileNotFoundError("missing audited target-decoy result tables")
    comparison = pd.read_csv(COMPARISON)
    gate = pd.read_csv(GATE)
    if set(comparison["domain"]) != set(DOMAIN_STYLE):
        raise ValueError(f"unexpected comparison domains: {comparison['domain'].tolist()}")
    for domain, expected in EXPECTED.items():
        row = comparison.loc[comparison["domain"].eq(domain)].iloc[0]
        observed = {key: int(row[key]) for key in expected}
        if observed != expected:
            raise ValueError(f"{domain} result differs: {observed} != {expected}")
    required_gate = {
        "domain",
        "batch",
        "peel",
        "selected_threshold",
        "accepted_events",
        "exact_fdr",
        "negative_to_positive_floor_ratio",
    }
    missing = required_gate - set(gate.columns)
    if missing:
        raise ValueError(f"gate table is missing columns: {sorted(missing)}")
    if gate["exact_fdr"].dropna().gt(0.05).any():
        raise ValueError("accepted target-decoy row exceeds exact 5% FDR")

    accepted = gate.loc[gate["accepted_events"].gt(0)].copy()
    trajectory = (
        gate.groupby(["domain", "peel"], as_index=False)
        .agg(total_batches=("batch", "size"))
        .merge(
            accepted.groupby(["domain", "peel"], as_index=False).agg(
                accepting_batches=("batch", "size"),
                accepted_events=("accepted_events", "sum"),
                threshold_median=("selected_threshold", "median"),
                threshold_q10=("selected_threshold", lambda values: values.quantile(0.1)),
                threshold_q90=("selected_threshold", lambda values: values.quantile(0.9)),
                exact_fdr_max=("exact_fdr", "max"),
            ),
            on=["domain", "peel"],
            how="left",
        )
        .fillna({"accepting_batches": 0, "accepted_events": 0})
    )
    trajectory["accepting_batch_fraction"] = (
        trajectory["accepting_batches"] / trajectory["total_batches"]
    )
    return comparison, gate, trajectory


def plot(comparison: pd.DataFrame, trajectory: pd.DataFrame) -> None:
    FIGURES.mkdir(exist_ok=True)
    figure, axes = plt.subplots(2, 2, figsize=(13.6, 9.2))
    units_axis, event_axis, threshold_axis, batch_axis = axes.flat
    domains = list(DOMAIN_STYLE)
    x = np.arange(len(domains))
    width = 0.34

    baseline_units = [
        comparison.loc[comparison["domain"].eq(domain), "matched_gt_units_baseline"].iloc[0]
        for domain in domains
    ]
    adaptive_units = [
        comparison.loc[
            comparison["domain"].eq(domain), "matched_gt_units_target_decoy"
        ].iloc[0]
        for domain in domains
    ]
    units_axis.bar(x - width / 2, baseline_units, width, color="#A9AFB5", label="Native 9/8")
    units_axis.bar(x + width / 2, adaptive_units, width, color="#B84D27", label="Target-decoy q=5%")
    units_axis.set_xticks(x, [DOMAIN_STYLE[domain]["label"] for domain in domains])
    units_axis.set_ylim(0, 10)
    units_axis.set_ylabel("GT units matched (of 10)")
    units_axis.set_title("A  Candidate-level FDR loses most GT units", loc="left", fontweight="bold")
    units_axis.legend(frameon=False)

    event_x = np.arange(4)
    labels = []
    baseline_values = []
    adaptive_values = []
    colors = []
    for domain in domains:
        row = comparison.loc[comparison["domain"].eq(domain)].iloc[0]
        for metric, short, color in (
            ("tp", "TP", "#23748F"),
            ("fp_in_matched_clusters", "FP", "#B84D27"),
        ):
            compact_domain = "Raw" if domain == "raw_native" else "Denoised"
            labels.append(f"{compact_domain}\n{short}")
            baseline_values.append(row[f"{metric}_baseline"])
            adaptive_values.append(row[f"{metric}_target_decoy"])
            colors.append(color)
    event_axis.bar(event_x - width / 2, baseline_values, width, color="#A9AFB5", label="Native 9/8")
    bars = event_axis.bar(event_x + width / 2, adaptive_values, width, color=colors, label="Target-decoy q=5%")
    event_axis.set_xticks(event_x, labels)
    event_axis.set_yscale("log")
    event_axis.set_ylim(1, 300000)
    event_axis.set_ylabel("Events (log scale)")
    event_axis.set_title("B  FP removal comes with severe TP loss", loc="left", fontweight="bold")
    for bar, value in zip(bars, adaptive_values):
        event_axis.text(bar.get_x() + bar.get_width() / 2, value * 1.2, f"{int(value):,}", ha="center", va="bottom", fontsize=8)

    for domain, style in DOMAIN_STYLE.items():
        gate_domain = {
            "raw_native": "raw_native_fdr",
            "denoised": "denoised_native_fdr",
        }[domain]
        rows = trajectory.loc[
            trajectory["domain"].eq(gate_domain)
            & trajectory["accepting_batches"].gt(0)
        ].sort_values("peel")
        threshold_axis.fill_between(
            rows["peel"], rows["threshold_q10"], rows["threshold_q90"],
            color=style["color"], alpha=0.15, linewidth=0,
        )
        threshold_axis.plot(
            rows["peel"], rows["threshold_median"], color=style["color"], lw=2.2,
            label=style["label"],
        )
        batch_axis.plot(
            rows["peel"], rows["accepting_batch_fraction"], color=style["color"],
            lw=2.2, label=style["label"],
        )
    threshold_axis.axhline(8, color="#A9AFB5", lw=1, ls="--", label="Kilosort floor")
    threshold_axis.set_ylabel("Selected score threshold")
    threshold_axis.set_xlabel("Matching-pursuit peel")
    threshold_axis.set_xlim(0, 20)
    threshold_axis.set_ylim(8, 55)
    threshold_axis.set_title("C  The sign-decoy gate is extremely stringent", loc="left", fontweight="bold")
    threshold_axis.legend(frameon=False, fontsize=8.5)

    batch_axis.set_xlim(0, 20)
    batch_axis.set_ylim(0, 1.02)
    batch_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    batch_axis.set_ylabel("Batches accepting at least one event")
    batch_axis.set_xlabel("Matching-pursuit peel")
    batch_axis.set_title("D  Most batches stop by peel 10–15", loc="left", fontweight="bold")

    for axis in axes.flat:
        axis.grid(axis="y", color="#D9DDE0", lw=0.7, alpha=0.65)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle(
        "A 5% sign-decoy candidate FDR is not a useful Kilosort operating point",
        fontsize=14, fontweight="bold",
    )
    figure.text(
        0.5, 0.935,
        "Native raw and denoised transforms, matched 1,200-second interval; no GT used for decisions",
        ha="center", fontsize=9.5, color="#4F5965",
    )
    figure.subplots_adjust(left=0.08, right=0.98, bottom=0.08, top=0.88, hspace=0.28, wspace=0.2)
    figure.savefig(FIGURES / "kilosort4_target_decoy_result.png", dpi=180)
    figure.savefig(FIGURES / "kilosort4_target_decoy_result.pdf")
    plt.close(figure)


def main() -> None:
    comparison, _, trajectory = load_data()
    trajectory.to_csv(RESULTS / "target_decoy_gate_trajectory.csv", index=False)
    plot(comparison, trajectory)
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
