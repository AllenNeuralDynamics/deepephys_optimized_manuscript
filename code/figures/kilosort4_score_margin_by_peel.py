#!/usr/bin/env python3
"""Analyze accepted Kilosort scores relative to threshold across peels."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO / "results" / "benchmarking" / "ks4_event_lineage"
SOURCE = SOURCE_DIR / "event_lineage_score_summary.csv"
DERIVED = SOURCE_DIR / "accepted_score_margin_by_peel.csv"
SUMMARY = SOURCE_DIR / "accepted_score_margin_summary.csv"
FIGURES = REPO / "figures"

STAGE = "duplicate_removal"
THRESHOLDS = (8.0, 10.75)
MIN_EVENTS = 100
STATUS_STYLE = {
    "tp": {"label": "TP", "color": "#23748F", "zorder": 3},
    "fp_matched_cluster": {
        "label": "FP in GT-matched cluster",
        "color": "#B84D27",
        "zorder": 4,
    },
    "unmatched_cluster": {
        "label": "Event in unmatched cluster",
        "color": "#747C83",
        "zorder": 2,
    },
}
PANEL_ORDER = (
    ("raw", 8.0),
    ("raw", 10.75),
    ("denoised", 8.0),
    ("denoised", 10.75),
)
PANEL_LABELS = {
    "raw": "Raw voltage",
    "denoised": "Full96 denoised voltage",
}
EXPECTED_EVENTS = {
    ("raw", 8.0): {
        "tp": 36_050,
        "fp_matched_cluster": 0,
        "unmatched_cluster": 21_112_308,
    },
    ("raw", 10.75): {
        "tp": 100_597,
        "fp_matched_cluster": 56_509,
        "unmatched_cluster": 7_934_203,
    },
    ("denoised", 8.0): {
        "tp": 125_183,
        "fp_matched_cluster": 80_624,
        "unmatched_cluster": 9_978_405,
    },
    ("denoised", 10.75): {
        "tp": 110_783,
        "fp_matched_cluster": 30_931,
        "unmatched_cluster": 4_281_150,
    },
}


def event_quantile_peel(rows: pd.DataFrame, quantile: float) -> int:
    ordered = rows.sort_values("peel")
    cumulative = ordered["events"].cumsum().to_numpy()
    target = ordered["events"].sum() * quantile
    index = min(int(np.searchsorted(cumulative, target)), len(ordered) - 1)
    return int(ordered.iloc[index]["peel"])


def load_analysis(source: Path = SOURCE) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not source.exists():
        raise FileNotFoundError(f"missing lineage score summary: {source}")
    frame = pd.read_csv(source)
    required = {
        "domain",
        "Th_learned",
        "stage",
        "status",
        "peel",
        "events",
        "score_mean",
        "score_q10",
        "score_median",
        "score_q90",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"lineage score summary is missing columns: {sorted(missing)}")

    selected = frame.loc[
        frame["stage"].eq(STAGE)
        & frame["Th_learned"].isin(THRESHOLDS)
        & frame["status"].isin(STATUS_STYLE),
        sorted(required),
    ].copy()
    selected["peel"] = selected["peel"].astype(np.int64)
    selected["events"] = selected["events"].astype(np.int64)
    for statistic in ("mean", "q10", "median", "q90"):
        selected[f"score_margin_{statistic}"] = (
            selected[f"score_{statistic}"] - selected["Th_learned"]
        )
        if selected[f"score_margin_{statistic}"].lt(0).any():
            raise ValueError(f"accepted {statistic} score fell below threshold")
    selected["supported"] = selected["events"].ge(MIN_EVENTS)
    selected = selected.sort_values(
        ["domain", "Th_learned", "status", "peel"]
    ).reset_index(drop=True)

    summary_rows = []
    for domain, threshold in PANEL_ORDER:
        condition = selected.loc[
            selected["domain"].eq(domain)
            & selected["Th_learned"].eq(threshold)
        ]
        expected = EXPECTED_EVENTS[(domain, threshold)]
        for status in STATUS_STYLE:
            rows = condition.loc[condition["status"].eq(status)]
            events = int(rows["events"].sum())
            if events != expected[status]:
                raise ValueError(
                    f"{domain} Th={threshold:g} {status} events differ: "
                    f"{events} != {expected[status]}"
                )
            if events == 0:
                summary_rows.append(
                    {
                        "domain": domain,
                        "Th_learned": threshold,
                        "status": status,
                        "events": 0,
                        "peel0_events": 0,
                        "peel0_fraction": np.nan,
                        "mean_peel": np.nan,
                        "median_peel": np.nan,
                        "q90_peel": np.nan,
                        "weighted_mean_score": np.nan,
                        "weighted_mean_score_margin": np.nan,
                        "supported_max_peel": np.nan,
                    }
                )
                continue
            peel0 = int(rows.loc[rows["peel"].eq(0), "events"].sum())
            weighted_mean_score = float(
                (rows["score_mean"] * rows["events"]).sum() / events
            )
            supported = rows.loc[rows["supported"]]
            summary_rows.append(
                {
                    "domain": domain,
                    "Th_learned": threshold,
                    "status": status,
                    "events": events,
                    "peel0_events": peel0,
                    "peel0_fraction": peel0 / events,
                    "mean_peel": float((rows["peel"] * rows["events"]).sum() / events),
                    "median_peel": event_quantile_peel(rows, 0.5),
                    "q90_peel": event_quantile_peel(rows, 0.9),
                    "weighted_mean_score": weighted_mean_score,
                    "weighted_mean_score_margin": weighted_mean_score - threshold,
                    "supported_max_peel": int(supported["peel"].max()),
                }
            )

    summary = pd.DataFrame(summary_rows)
    if len(summary) != len(PANEL_ORDER) * len(STATUS_STYLE):
        raise RuntimeError("accepted-score summary has unexpected row count")
    return selected, summary


def plot(per_peel: pd.DataFrame, summary: pd.DataFrame) -> None:
    FIGURES.mkdir(exist_ok=True)
    figure, axes = plt.subplots(2, 2, figsize=(13.6, 9.2), sharex=True, sharey=True)

    for panel_index, ((domain, threshold), axis) in enumerate(
        zip(PANEL_ORDER, axes.flat)
    ):
        condition = per_peel.loc[
            per_peel["domain"].eq(domain)
            & per_peel["Th_learned"].eq(threshold)
            & per_peel["supported"]
        ]
        for status, style in STATUS_STYLE.items():
            rows = condition.loc[condition["status"].eq(status)].sort_values("peel")
            if rows.empty:
                continue
            axis.fill_between(
                rows["peel"],
                rows["score_margin_q10"],
                rows["score_margin_q90"],
                color=style["color"],
                alpha=0.12,
                linewidth=0,
                zorder=style["zorder"] - 1,
            )
            axis.plot(
                rows["peel"],
                rows["score_margin_median"],
                color=style["color"],
                lw=2.0,
                label=style["label"],
                zorder=style["zorder"],
            )

        condition_summary = summary.loc[
            summary["domain"].eq(domain)
            & summary["Th_learned"].eq(threshold)
        ]
        fp_events = int(
            condition_summary.loc[
                condition_summary["status"].eq("fp_matched_cluster"), "events"
            ].iloc[0]
        )
        unmatched_events = int(
            condition_summary.loc[
                condition_summary["status"].eq("unmatched_cluster"), "events"
            ].iloc[0]
        )
        axis.set_title(
            f"{'ABCD'[panel_index]}  {PANEL_LABELS[domain]}, "
            rf"$Th_{{learned}}={threshold:g}$",
            loc="left",
            fontweight="bold",
        )
        axis.text(
            0.97,
            0.95,
            f"matched-cluster FP: {fp_events:,}\n"
            f"unmatched events: {unmatched_events:,}",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=8.5,
            color="#4F5965",
        )
        if fp_events == 0:
            axis.text(
                0.97,
                0.77,
                "No FP curve: only two GT units matched",
                transform=axis.transAxes,
                ha="right",
                va="top",
                fontsize=8.5,
                color=STATUS_STYLE["fp_matched_cluster"]["color"],
                fontweight="bold",
            )
        axis.set_yscale("log")
        axis.set_xlim(0, 100)
        axis.set_ylim(1e-3, 100)
        axis.grid(axis="y", which="major", color="#D9DDE0", lw=0.7, alpha=0.65)
        axis.spines[["top", "right"]].set_visible(False)

    for axis in axes[-1, :]:
        axis.set_xlabel("Matching-pursuit peel")
    for axis in axes[:, 0]:
        axis.set_ylabel(r"Accepted score margin $s - Th_{learned}$")
    axes[0, 0].legend(frameon=False, loc="lower left", fontsize=8.5)

    figure.suptitle(
        "Accepted Kilosort4 scores approach threshold during repeated subtraction",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.935,
        "Lines: median; bands: 10th–90th percentile; "
        f"shown where each status has at least {MIN_EVENTS} events per peel",
        ha="center",
        fontsize=9.5,
        color="#4F5965",
    )
    figure.text(
        0.5,
        0.02,
        "Controlled diagnostic uses denoised-learned templates for both domains; "
        "raw-native production behavior requires a separate lineage run.",
        ha="center",
        fontsize=8.5,
        color="#6A737B",
    )
    figure.subplots_adjust(left=0.08, right=0.98, bottom=0.09, top=0.88, hspace=0.25, wspace=0.12)
    figure.savefig(FIGURES / "kilosort4_score_margin_by_peel.png", dpi=180)
    figure.savefig(FIGURES / "kilosort4_score_margin_by_peel.pdf")
    plt.close(figure)


def main() -> None:
    per_peel, summary = load_analysis()
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    per_peel.to_csv(DERIVED, index=False)
    summary.to_csv(SUMMARY, index=False)
    plot(per_peel, summary)
    print(
        summary[
            [
                "domain",
                "Th_learned",
                "status",
                "events",
                "mean_peel",
                "median_peel",
                "q90_peel",
                "weighted_mean_score_margin",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()