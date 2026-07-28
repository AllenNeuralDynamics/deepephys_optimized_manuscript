#!/usr/bin/env python3
"""Compare raw-native and denoised-native Kilosort default 9/8 lineage."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "benchmarking"
RAW_DIR = RESULTS / "ks4_native_baseline"
DENOISED_DIR = RESULTS / "ks4_event_lineage"
FIGURES = REPO / "figures"

RAW_SCORE = RAW_DIR / "raw_native_event_lineage_score_summary.csv"
RAW_STAGE = RAW_DIR / "raw_native_event_lineage_stage_summary.csv"
DENOISED_SCORE = DENOISED_DIR / "event_lineage_score_summary.csv"
DENOISED_STAGE = DENOISED_DIR / "event_lineage_stage_summary.csv"

PEEL_TABLE = RAW_DIR / "native_baseline_by_peel.csv"
SUMMARY_TABLE = RAW_DIR / "native_baseline_summary.csv"
STAGE_TABLE = RAW_DIR / "native_baseline_stage_summary.csv"

THRESHOLD = 8.0
STAGE = "duplicate_removal"
PEEL_BIN_WIDTH = 5
MIN_EVENTS = 100
DOMAIN_STYLE = {
    "raw_native": {"label": "Raw-native", "color": "#4F5965"},
    "denoised": {"label": "Full96 denoised-native", "color": "#23748F"},
}
STATUS_STYLE = {
    "tp": {"label": "TP", "color": "#23748F"},
    "fp_matched_cluster": {
        "label": "FP in GT-matched cluster",
        "color": "#B84D27",
    },
}
EXPECTED_STAGE = {
    "raw_native": {
        "events_present": 4_273_542,
        "clusters": 567,
        "matched_gt_units": 7,
        "tp": 97_677,
        "fn": 81_689,
        "fp_in_matched_clusters": 31_012,
        "events_in_unmatched_clusters": 4_144_853,
    },
    "denoised": {
        "events_present": 10_184_212,
        "clusters": 649,
        "matched_gt_units": 8,
        "tp": 125_183,
        "fn": 54_183,
        "fp_in_matched_clusters": 80_624,
        "events_in_unmatched_clusters": 9_978_405,
    },
}
EXPECTED_STATUS_EVENTS = {
    "raw_native": {
        "tp": 97_677,
        "fp_matched_cluster": 31_012,
        "unmatched_cluster": 4_144_853,
    },
    "denoised": {
        "tp": 125_183,
        "fp_matched_cluster": 80_624,
        "unmatched_cluster": 9_978_405,
    },
}


def quantile_peel(rows: pd.DataFrame, quantile: float, column: str = "events") -> int:
    ordered = rows.sort_values("peel")
    cumulative = ordered[column].cumsum().to_numpy()
    target = ordered[column].sum() * quantile
    index = min(int(np.searchsorted(cumulative, target)), len(ordered) - 1)
    return int(ordered.iloc[index]["peel"])


def load_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [
        path
        for path in (RAW_SCORE, RAW_STAGE, DENOISED_SCORE, DENOISED_STAGE)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("missing native baseline inputs: " + ", ".join(map(str, missing)))

    raw_scores = pd.read_csv(RAW_SCORE)
    denoised_scores = pd.read_csv(DENOISED_SCORE).query(
        "domain == 'denoised' and Th_learned == @THRESHOLD"
    )
    scores = pd.concat([raw_scores, denoised_scores], ignore_index=True)
    scores = scores.query(
        "Th_learned == @THRESHOLD and stage == @STAGE and "
        "status in ['tp', 'fp_matched_cluster', 'unmatched_cluster']"
    ).copy()

    raw_stage = pd.read_csv(RAW_STAGE)
    denoised_stage = pd.read_csv(DENOISED_STAGE).query(
        "domain == 'denoised' and Th_learned == @THRESHOLD"
    )
    stages = pd.concat([raw_stage, denoised_stage], ignore_index=True)
    stages = stages.query("Th_learned == @THRESHOLD").copy()
    return scores, stages


def build_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scores, stages = load_sources()
    if set(scores["domain"]) != set(DOMAIN_STYLE):
        raise ValueError(f"unexpected native baseline domains: {sorted(scores['domain'].unique())}")

    for statistic in ("mean", "q10", "median", "q90"):
        scores[f"score_margin_{statistic}"] = scores[f"score_{statistic}"] - THRESHOLD
        if scores[f"score_margin_{statistic}"].lt(0).any():
            raise ValueError(f"accepted {statistic} score fell below threshold")
    scores["supported"] = scores["events"].ge(MIN_EVENTS)
    scores = scores.sort_values(["domain", "status", "peel"]).reset_index(drop=True)

    summary_rows = []
    peel_rows = []
    for domain in DOMAIN_STYLE:
        condition = scores.loc[scores["domain"].eq(domain)]
        for status, expected in EXPECTED_STATUS_EVENTS[domain].items():
            rows = condition.loc[condition["status"].eq(status)].sort_values("peel")
            events = int(rows["events"].sum())
            if events != expected:
                raise ValueError(f"{domain} {status} events differ: {events} != {expected}")
            weighted_score = float((rows["score_mean"] * rows["events"]).sum() / events)
            summary_rows.append(
                {
                    "domain": domain,
                    "status": status,
                    "events": events,
                    "peel0_events": int(rows.loc[rows["peel"].eq(0), "events"].sum()),
                    "peel0_fraction": float(
                        rows.loc[rows["peel"].eq(0), "events"].sum() / events
                    ),
                    "mean_peel": float((rows["peel"] * rows["events"]).sum() / events),
                    "median_peel": quantile_peel(rows, 0.5),
                    "q90_peel": quantile_peel(rows, 0.9),
                    "weighted_mean_score": weighted_score,
                    "weighted_mean_score_margin": weighted_score - THRESHOLD,
                }
            )

        tp = condition.loc[condition["status"].eq("tp"), ["peel", "events"]].rename(
            columns={"events": "tp_events"}
        )
        fp = condition.loc[
            condition["status"].eq("fp_matched_cluster"), ["peel", "events"]
        ].rename(columns={"events": "fp_events"})
        maximum = int(max(tp["peel"].max(), fp["peel"].max()))
        complete = pd.DataFrame({"peel": np.arange(maximum + 1)})
        per_peel = complete.merge(tp, on="peel", how="left").merge(
            fp, on="peel", how="left"
        ).fillna(0)
        per_peel[["peel", "tp_events", "fp_events"]] = per_peel[
            ["peel", "tp_events", "fp_events"]
        ].astype(np.int64)
        per_peel.insert(0, "domain", domain)
        per_peel["matched_events"] = per_peel["tp_events"] + per_peel["fp_events"]
        per_peel["fp_fraction"] = np.divide(
            per_peel["fp_events"],
            per_peel["matched_events"],
            out=np.zeros(len(per_peel), dtype=float),
            where=per_peel["matched_events"].gt(0),
        )
        per_peel["fp_share"] = per_peel["fp_events"] / per_peel["fp_events"].sum()
        per_peel["fp_cumulative"] = per_peel["fp_share"].cumsum()
        if not np.isclose(per_peel["fp_share"].sum(), 1.0):
            raise ValueError(f"{domain} FP shares do not sum to one")
        peel_rows.append(per_peel)

    final = stages.query("stage == @STAGE").set_index("domain")
    for domain, expected in EXPECTED_STAGE.items():
        observed = {key: int(final.at[domain, key]) for key in expected}
        if observed != expected:
            raise ValueError(f"{domain} final stage differs: {observed} != {expected}")
    stage_columns = [
        "domain",
        "Th_learned",
        "stage",
        "events_present",
        "events_removed",
        "clusters",
        "matched_gt_units",
        "tp",
        "fn",
        "fp_in_matched_clusters",
        "events_in_unmatched_clusters",
        "pooled_precision",
        "pooled_recall",
        "template_learning_sort_identity",
    ]
    return (
        scores,
        pd.DataFrame(summary_rows),
        stages[stage_columns].sort_values(["domain", "stage"]).reset_index(drop=True),
    ), pd.concat(peel_rows, ignore_index=True), final.reset_index()


def plot(scores: pd.DataFrame, summary: pd.DataFrame, peels: pd.DataFrame) -> None:
    FIGURES.mkdir(exist_ok=True)
    figure, axes = plt.subplots(2, 2, figsize=(13.8, 9.2))
    fraction_axis, cumulative_axis, raw_axis, denoised_axis = axes.flat

    for domain, style in DOMAIN_STYLE.items():
        rows = peels.loc[peels["domain"].eq(domain)].sort_values("peel")
        binned = (
            rows.assign(bin_start=(rows["peel"] // PEEL_BIN_WIDTH) * PEEL_BIN_WIDTH)
            .groupby("bin_start", as_index=False)
            .agg(fp_events=("fp_events", "sum"), matched_events=("matched_events", "sum"))
        )
        binned["peel_center"] = binned["bin_start"] + (PEEL_BIN_WIDTH - 1) / 2
        binned["fp_fraction"] = binned["fp_events"] / binned["matched_events"]
        supported = binned.loc[binned["matched_events"].ge(MIN_EVENTS)]
        fraction_axis.plot(
            supported["peel_center"],
            supported["fp_fraction"],
            color=style["color"],
            lw=2.2,
            marker="o",
            markersize=4,
            label=style["label"],
        )
        cumulative_axis.plot(
            rows["peel"], rows["fp_cumulative"], color=style["color"], lw=2.2,
            label=style["label"],
        )
        median = int(
            summary.loc[
                summary["domain"].eq(domain)
                & summary["status"].eq("fp_matched_cluster"),
                "median_peel",
            ].iloc[0]
        )
        cumulative_axis.scatter(
            [median],
            [rows.loc[rows["peel"].eq(median), "fp_cumulative"].iloc[0]],
            color=style["color"], edgecolor="white", linewidth=0.8, s=45, zorder=4,
        )

    for domain, axis in (("raw_native", raw_axis), ("denoised", denoised_axis)):
        condition = scores.loc[
            scores["domain"].eq(domain)
            & scores["status"].isin(STATUS_STYLE)
            & scores["supported"]
        ]
        for status, style in STATUS_STYLE.items():
            rows = condition.loc[condition["status"].eq(status)].sort_values("peel")
            axis.fill_between(
                rows["peel"], rows["score_margin_q10"], rows["score_margin_q90"],
                color=style["color"], alpha=0.14, linewidth=0,
            )
            axis.plot(
                rows["peel"], rows["score_margin_median"], color=style["color"],
                lw=2, label=style["label"],
            )
        condition_summary = summary.loc[summary["domain"].eq(domain)].set_index("status")
        axis.text(
            0.97, 0.95,
            f"TP: {int(condition_summary.at['tp', 'events']):,}\n"
            f"FP: {int(condition_summary.at['fp_matched_cluster', 'events']):,}",
            transform=axis.transAxes, ha="right", va="top", fontsize=9,
            color="#4F5965",
        )
        axis.set_yscale("log")
        axis.set_xlim(0, 100)
        axis.set_ylim(1e-3, 100)
        axis.set_xlabel("Matching-pursuit peel")
        axis.grid(axis="y", which="major", color="#D9DDE0", lw=0.7, alpha=0.65)
        axis.spines[["top", "right"]].set_visible(False)

    fraction_axis.axhline(0.5, color="#A9AFB5", lw=1, ls="--")
    fraction_axis.set_xlim(0, 60)
    fraction_axis.set_ylim(0, 1.02)
    fraction_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    fraction_axis.set_ylabel("FP among GT-matched events")
    fraction_axis.set_xlabel("Matching-pursuit peel (weighted 5-peel bins)")
    fraction_axis.set_title("A  FP fraction rises across peels", loc="left", fontweight="bold")
    fraction_axis.legend(frameon=False, loc="lower right")

    cumulative_axis.axhline(0.5, color="#A9AFB5", lw=1, ls="--")
    cumulative_axis.set_xlim(0, int(peels["peel"].max()))
    cumulative_axis.set_ylim(0, 1.02)
    cumulative_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    cumulative_axis.set_ylabel("Cumulative share of matched-cluster FP")
    cumulative_axis.set_xlabel("Matching-pursuit peel")
    cumulative_axis.set_title("B  Denoised FP burden extends later", loc="left", fontweight="bold")

    raw_axis.set_ylabel(r"Accepted score margin $s - Th_{learned}$")
    denoised_axis.set_ylabel(r"Accepted score margin $s - Th_{learned}$")
    raw_axis.set_title("C  Raw-native default 9/8", loc="left", fontweight="bold")
    denoised_axis.set_title("D  Denoised-native default 9/8", loc="left", fontweight="bold")
    raw_axis.legend(frameon=False, loc="lower left")

    for axis in (fraction_axis, cumulative_axis):
        axis.grid(axis="y", color="#D9DDE0", lw=0.7, alpha=0.65)
        axis.spines[["top", "right"]].set_visible(False)

    figure.suptitle(
        "Native Kilosort4 default baseline on matched 1,200-second inputs",
        fontsize=14, fontweight="bold",
    )
    figure.text(
        0.5, 0.935,
        r"Each domain learns its own preprocessing, drift, whitening, and templates; "
        r"$Th_{universal}=9$, $Th_{learned}=8$",
        ha="center", fontsize=9.5, color="#4F5965",
    )
    figure.subplots_adjust(left=0.08, right=0.98, bottom=0.08, top=0.88, hspace=0.28, wspace=0.2)
    figure.savefig(FIGURES / "kilosort4_native_baseline_by_peel.png", dpi=180)
    figure.savefig(FIGURES / "kilosort4_native_baseline_by_peel.pdf")
    plt.close(figure)


def main() -> None:
    (scores, summary, stages), peels, _ = build_tables()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    scores.to_csv(RAW_DIR / "native_baseline_score_margin_by_peel.csv", index=False)
    summary.to_csv(SUMMARY_TABLE, index=False)
    stages.to_csv(STAGE_TABLE, index=False)
    peels.to_csv(PEEL_TABLE, index=False)
    plot(scores, summary, peels)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
