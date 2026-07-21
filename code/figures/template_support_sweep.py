#!/usr/bin/env python3
"""Summarize temporal/spatial support sweeps for three representative models."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "template_support"
FIGURES = REPO / "figures"
MODELS = (
    ("ib_w96_om0_s0", "Full96 omission0"),
    ("ib_w96_om1_s0", "Full96 omission1"),
    ("ib_origdi_s0", "Original DI, seed 0"),
)
EVALUATIONS = (
    ("in_sample", "In-sample", "#4F5965", "o"),
    ("crossfit", "Cross-fitted", "#D26A3A", "s"),
)
TOP_SUPPORTS = ("top1", "top2", "top4", "top8", "top16", "top24")
WEAK_UNITS = (94, 664, 720, 1129)
PRESPECIFIED_CELLS = (
    ("frozen_endpoint", 4.0, "endpoint"),
    ("top2_4ms", 4.0, "top2"),
    ("top2_2ms", 2.0, "top2"),
    ("top2_1ms", 1.0, "top2"),
    ("top2_0.5ms", 0.5, "top2"),
    ("top1_1ms", 1.0, "top1"),
)


def load_results() -> pd.DataFrame:
    frames = []
    for label, _ in MODELS:
        source = RESULTS / f"{label}_per_unit.csv"
        if not source.exists():
            raise FileNotFoundError(f"missing support sweep: {source}")
        frame = pd.read_csv(source)
        if set(frame["evaluation"]) != {"in_sample", "crossfit"}:
            raise ValueError(f"unexpected evaluations in {source}")
        if frame["unit_id"].nunique() != 10:
            raise ValueError(f"expected 10 units in {source}")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _mean_interval(frame: pd.DataFrame, x_column: str) -> pd.DataFrame:
    return (
        frame.groupby(x_column)["ddprime"]
        .agg(
            mean="mean",
            low=lambda values: np.quantile(values, 0.1),
            high=lambda values: np.quantile(values, 0.9),
        )
        .reset_index()
        .sort_values(x_column)
    )


def make_figure(frame: pd.DataFrame) -> None:
    figure, axes = plt.subplots(
        3, 3, figsize=(14.8, 10.8), sharey="row", squeeze=False
    )
    for column, (model_label, title) in enumerate(MODELS):
        model = frame[frame["model_label"] == model_label]
        temporal_axis = axes[0, column]
        spatial_axis = axes[1, column]
        for evaluation, legend, color, marker in EVALUATIONS:
            selected = model[
                (model["evaluation"] == evaluation)
                & (model["spatial_support"] == "top2")
            ]
            temporal = _mean_interval(selected, "temporal_ms")
            temporal_axis.plot(
                temporal["temporal_ms"],
                temporal["mean"],
                color=color,
                marker=marker,
                lw=1.8,
                label=legend,
            )
            temporal_axis.fill_between(
                temporal["temporal_ms"],
                temporal["low"],
                temporal["high"],
                color=color,
                alpha=0.12,
                linewidth=0,
            )

            selected = model[
                (model["evaluation"] == evaluation)
                & (model["temporal_ms"] == 1.0)
                & (model["spatial_support"].isin(TOP_SUPPORTS))
            ].copy()
            selected["requested_channels"] = selected["spatial_support"].str[3:].astype(int)
            spatial = _mean_interval(selected, "requested_channels")
            spatial_axis.plot(
                spatial["requested_channels"],
                spatial["mean"],
                color=color,
                marker=marker,
                lw=1.8,
                label=legend,
            )
            spatial_axis.fill_between(
                spatial["requested_channels"],
                spatial["low"],
                spatial["high"],
                color=color,
                alpha=0.12,
                linewidth=0,
            )
            endpoint = model[
                (model["evaluation"] == evaluation)
                & (model["temporal_ms"] == 4.0)
                & (model["spatial_support"] == "endpoint")
            ]
            temporal_axis.scatter(
                4.0,
                endpoint["ddprime"].mean(),
                marker="*",
                s=105,
                facecolor=color,
                edgecolor="white",
                linewidth=0.7,
                zorder=5,
            )
            spatial_axis.scatter(
                endpoint["n_channels"].mean(),
                endpoint["ddprime"].mean(),
                marker="*",
                s=105,
                facecolor=color,
                edgecolor="white",
                linewidth=0.7,
                zorder=5,
            )

        for axis in (temporal_axis, spatial_axis):
            axis.axhline(0, color="#222222", lw=0.9, ls=":")
            axis.grid(alpha=0.18)
        temporal_axis.set_title(title, fontweight="bold")
        temporal_axis.set_xlabel("Template duration (ms); top 2 channels")
        spatial_axis.set_xlabel("Top raw-template channels; 1-ms window")
        spatial_axis.set_xscale("log", base=2)
        spatial_axis.set_xticks((1, 2, 4, 8, 16, 24), ("1", "2", "4", "8", "16", "24"))
        if column == 0:
            temporal_axis.set_ylabel("Denoised − raw d′")
            spatial_axis.set_ylabel("Denoised − raw d′")

        subgroup_axis = axes[2, column]
        crossfit = model[model["evaluation"] == "crossfit"]
        endpoint = crossfit[
            (crossfit["temporal_ms"] == 4.0)
            & (crossfit["spatial_support"] == "endpoint")
        ]
        compact = crossfit[
            (crossfit["temporal_ms"] == 1.0)
            & (crossfit["spatial_support"] == "top2")
        ]
        groups = (
            ("All 10", lambda values: values),
            ("Weak 4", lambda values: values[values["unit_id"].isin(WEAK_UNITS)]),
            ("Other 6", lambda values: values[~values["unit_id"].isin(WEAK_UNITS)]),
        )
        centers = np.arange(len(groups))
        width = 0.34
        endpoint_values = [selector(endpoint)["ddprime"].mean() for _, selector in groups]
        compact_values = [selector(compact)["ddprime"].mean() for _, selector in groups]
        subgroup_axis.bar(
            centers - width / 2,
            endpoint_values,
            width,
            color="#8D969F",
            label="Frozen 4-ms endpoint",
        )
        subgroup_axis.bar(
            centers + width / 2,
            compact_values,
            width,
            color="#D26A3A",
            label="1 ms, top 2",
        )
        subgroup_axis.axhline(0, color="#222222", lw=0.9, ls=":")
        subgroup_axis.set_xticks(centers, [name for name, _ in groups])
        subgroup_axis.set_xlabel("Cross-fitted unit aggregation")
        subgroup_axis.grid(axis="y", alpha=0.18)
        if column == 0:
            subgroup_axis.set_ylabel("Denoised − raw d′")
    axes[0, 0].legend(frameon=False, loc="best")
    axes[2, 0].legend(frameon=False, loc="lower right", fontsize=8)
    figure.text(
        0.5,
        0.012,
        "Top: duration at fixed top-2 raw-ranked channels. Middle: channel count at fixed 1 ms. Bottom: cross-fitted aggregate gaps.\nBands show the 10th–90th percentile across 10 fixed GT units; stars mark the frozen 4-ms/50%-amplitude endpoint. Negative means lower denoised separability.",
        ha="center",
        fontsize=8.2,
    )
    figure.suptitle(
        "Does reducing temporal or spatial template support remove the d′ deficit?",
        fontweight="bold",
        y=0.995,
    )
    figure.subplots_adjust(top=0.94, bottom=0.09, hspace=0.42, wspace=0.22)
    FIGURES.mkdir(exist_ok=True)
    figure.savefig(FIGURES / "template_support_sweep.png", dpi=180)
    plt.close(figure)


def prespecified_results(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model_label, _ in MODELS:
        for evaluation, _, _, _ in EVALUATIONS:
            selected = frame[
                (frame["model_label"] == model_label)
                & (frame["evaluation"] == evaluation)
            ]
            for name, duration_ms, spatial_support in PRESPECIFIED_CELLS:
                cell = selected[
                    (selected["temporal_ms"] == duration_ms)
                    & (selected["spatial_support"] == spatial_support)
                ]
                weak = cell[cell["unit_id"].isin(WEAK_UNITS)]
                other = cell[~cell["unit_id"].isin(WEAK_UNITS)]
                rows.append(
                    {
                        "model_label": model_label,
                        "evaluation": evaluation,
                        "cell": name,
                        "temporal_ms": duration_ms,
                        "spatial_support": spatial_support,
                        "mean_n_channels": cell["n_channels"].mean(),
                        "dprime_raw": cell["dprime_raw"].mean(),
                        "dprime_deep": cell["dprime_deep"].mean(),
                        "ddprime": cell["ddprime"].mean(),
                        "units_improved": int((cell["ddprime"] > 0).sum()),
                        "weak4_ddprime": weak["ddprime"].mean(),
                        "other6_ddprime": other["ddprime"].mean(),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    frame = load_results()
    make_figure(frame)
    results = prespecified_results(frame)
    results.to_csv(
        RESULTS / "template_support_prespecified_results.csv", index=False
    )
    print(results.round(4).to_string(index=False))


if __name__ == "__main__":
    main()