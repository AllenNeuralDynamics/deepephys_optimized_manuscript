#!/usr/bin/env python3
"""Plot final matched-cluster false positives across Kilosort peels."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO / "results" / "benchmarking" / "ks4_event_lineage"
SOURCE = SOURCE_DIR / "event_lineage_score_summary.csv"
DERIVED = SOURCE_DIR / "fp_by_peel.csv"
FIGURES = REPO / "figures"

THRESHOLD = 10.75
STAGE = "duplicate_removal"
STATUSES = ("tp", "fp_matched_cluster")
PEEL_BIN_WIDTH = 5
MIN_BIN_EVENTS = 100
EXPECTED_TOTALS = {
    "raw": {"tp_events": 100_597, "fp_events": 56_509, "peel0_fp": 39},
    "denoised": {"tp_events": 110_783, "fp_events": 30_931, "peel0_fp": 45},
}
DOMAIN_STYLE = {
    "raw": {"label": "Raw AP", "color": "#4F5965"},
    "denoised": {"label": "Full96 denoised", "color": "#23748F"},
}


def build_table(source: Path = SOURCE) -> pd.DataFrame:
    if not source.exists():
        raise FileNotFoundError(f"missing lineage score summary: {source}")
    frame = pd.read_csv(source)
    required = {"domain", "Th_learned", "stage", "status", "peel", "events"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"lineage score summary is missing columns: {sorted(missing)}")

    selected = frame.loc[
        frame["Th_learned"].eq(THRESHOLD)
        & frame["stage"].eq(STAGE)
        & frame["status"].isin(STATUSES),
        ["domain", "peel", "status", "events"],
    ].copy()
    domains = set(selected["domain"])
    if domains != set(DOMAIN_STYLE):
        raise ValueError(f"unexpected domains: {sorted(domains)}")

    wide = (
        selected.pivot_table(
            index=["domain", "peel"],
            columns="status",
            values="events",
            aggfunc="sum",
            fill_value=0,
        )
        .rename(
            columns={
                "tp": "tp_events",
                "fp_matched_cluster": "fp_events",
            }
        )
        .reset_index()
    )
    for domain in DOMAIN_STYLE:
        maximum = int(wide.loc[wide["domain"].eq(domain), "peel"].max())
        complete = pd.DataFrame({"domain": domain, "peel": np.arange(maximum + 1)})
        domain_rows = complete.merge(
            wide.loc[wide["domain"].eq(domain)],
            on=["domain", "peel"],
            how="left",
        ).fillna(0)
        wide = pd.concat(
            [wide.loc[~wide["domain"].eq(domain)], domain_rows], ignore_index=True
        )

    wide[["peel", "tp_events", "fp_events"]] = wide[
        ["peel", "tp_events", "fp_events"]
    ].astype(np.int64)
    wide["matched_events"] = wide["tp_events"] + wide["fp_events"]
    wide["fp_fraction"] = np.divide(
        wide["fp_events"],
        wide["matched_events"],
        out=np.zeros(len(wide), dtype=float),
        where=wide["matched_events"].gt(0),
    )
    wide = wide.sort_values(["domain", "peel"]).reset_index(drop=True)
    wide["fp_share"] = wide.groupby("domain")["fp_events"].transform(
        lambda values: values / values.sum()
    )
    wide["fp_cumulative"] = wide.groupby("domain")["fp_share"].cumsum()

    for domain, expected in EXPECTED_TOTALS.items():
        rows = wide.loc[wide["domain"].eq(domain)]
        observed = {
            "tp_events": int(rows["tp_events"].sum()),
            "fp_events": int(rows["fp_events"].sum()),
            "peel0_fp": int(rows.loc[rows["peel"].eq(0), "fp_events"].iloc[0]),
        }
        if observed != expected:
            raise ValueError(f"{domain} lineage totals differ: {observed} != {expected}")
        if not np.isclose(rows["fp_share"].sum(), 1.0):
            raise ValueError(f"{domain} FP shares do not sum to one")
        if not np.isclose(rows["fp_cumulative"].iloc[-1], 1.0):
            raise ValueError(f"{domain} cumulative FP proportion does not end at one")
    return wide


def quantile_peel(rows: pd.DataFrame, quantile: float) -> int:
    index = np.searchsorted(rows["fp_cumulative"].to_numpy(), quantile)
    return int(rows.iloc[min(index, len(rows) - 1)]["peel"])


def plot(table: pd.DataFrame) -> None:
    FIGURES.mkdir(exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(13.2, 5.4))
    fraction_axis, cumulative_axis = axes

    for domain, style in DOMAIN_STYLE.items():
        rows = table.loc[table["domain"].eq(domain)].sort_values("peel")
        binned = (
            rows.assign(
                bin_start=(rows["peel"] // PEEL_BIN_WIDTH) * PEEL_BIN_WIDTH
            )
            .groupby("bin_start", as_index=False)
            .agg(fp_events=("fp_events", "sum"), matched_events=("matched_events", "sum"))
        )
        binned["peel_center"] = binned["bin_start"] + (PEEL_BIN_WIDTH - 1) / 2
        binned["fp_fraction"] = binned["fp_events"] / binned["matched_events"]
        supported = binned.loc[binned["matched_events"].ge(MIN_BIN_EVENTS)]
        fraction_axis.plot(
            supported["peel_center"],
            supported["fp_fraction"],
            color=style["color"],
            lw=2.2,
            marker="o",
            markersize=4.2,
            label=style["label"],
        )
        cumulative_axis.plot(
            rows["peel"],
            rows["fp_cumulative"],
            color=style["color"],
            lw=2.2,
            label=style["label"],
        )
        median_peel = quantile_peel(rows, 0.5)
        cumulative_axis.scatter(
            [median_peel],
            [rows.loc[rows["peel"].eq(median_peel), "fp_cumulative"].iloc[0]],
            s=48,
            color=style["color"],
            edgecolor="white",
            linewidth=0.9,
            zorder=4,
        )
        cumulative_axis.annotate(
            f"50% by peel {median_peel}",
            xy=(median_peel, 0.5),
            xytext=(8, 10 if domain == "raw" else -18),
            textcoords="offset points",
            color=style["color"],
            fontsize=9,
            fontweight="bold",
        )

    fraction_axis.axhline(0.5, color="#A9AFB5", lw=1, ls="--", zorder=0)
    cumulative_axis.axhline(0.5, color="#A9AFB5", lw=1, ls="--", zorder=0)
    for axis in axes:
        axis.set_ylim(0, 1.02)
        axis.set_xlabel("Matching-pursuit peel")
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.grid(axis="y", color="#D9DDE0", lw=0.7, alpha=0.65)
        axis.spines[["top", "right"]].set_visible(False)

    fraction_axis.set_xlim(0, 60)
    cumulative_axis.set_xlim(0, int(table["peel"].max()))
    fraction_axis.set_ylabel("False positives among GT-matched events")
    fraction_axis.set_title(
        "A  FP fraction rises with peel depth", loc="left", fontweight="bold"
    )
    cumulative_axis.set_ylabel("Cumulative share of all false positives")
    cumulative_axis.set_title("B  Most FPs accumulate after early peels", loc="left", fontweight="bold")
    fraction_axis.legend(frameon=False, loc="lower right")
    fraction_axis.text(
        0.03,
        0.95,
        "Weighted 5-peel bins\nBins with >=100 matched events",
        transform=fraction_axis.transAxes,
        va="top",
        fontsize=8.5,
        color="#6A737B",
    )

    figure.suptitle(
        "Kilosort4 matched-cluster false positives across subtraction peels",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.925,
        "Fixed denoised templates, final duplicate-removal stage, "
        r"$Th_{learned}=10.75$",
        ha="center",
        fontsize=10,
        color="#4F5965",
    )
    figure.subplots_adjust(left=0.075, right=0.98, bottom=0.13, top=0.82, wspace=0.22)
    figure.savefig(FIGURES / "kilosort4_fp_by_peel.png", dpi=180)
    figure.savefig(FIGURES / "kilosort4_fp_by_peel.pdf")
    plt.close(figure)


def main() -> None:
    table = build_table()
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(DERIVED, index=False)
    plot(table)
    for domain in DOMAIN_STYLE:
        rows = table.loc[table["domain"].eq(domain)]
        print(
            f"{domain}|fp={int(rows.fp_events.sum())}|"
            f"peel0={int(rows.loc[rows.peel.eq(0), 'fp_events'].iloc[0])}|"
            f"median_peel={quantile_peel(rows, 0.5)}|"
            f"q90_peel={quantile_peel(rows, 0.9)}"
        )


if __name__ == "__main__":
    main()