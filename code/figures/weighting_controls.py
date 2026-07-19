#!/usr/bin/env python3
"""Analyze the corrected matched-L2 spike-weighting endpoint screen."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SCORES = REPO / "results" / "scores"
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "figures"
ANCHOR_LABELS = ("ib_arch_l2_om0_s0", "ib_arch_l2_om0_s1", "ib_arch_l2_om0_s2")
ARMS = [
    ("unweighted", "Unweighted", "none", 0),
    ("ib_w2_soft3", "Soft 3", "magnitude", 3),
    ("ib_w2_soft10", "Soft 10", "magnitude", 10),
    ("ib_w2_soft30", "Soft 30", "magnitude", 30),
    ("ib_w2_gate100", "Gate 100", "soft gate", 100),
    ("ib_w2_gate300", "Gate 300", "soft gate", 300),
    ("ib_w2_gate1000", "Gate 1000", "soft gate", 1000),
    ("ib_w2_hard1000", "Hard 1000", "hard gate", 1000),
]


def paths(label: str) -> tuple[Path, Path]:
    if label == "unweighted":
        return (SCORES / "ib_arch_l2_om0_s0_dprime.csv",
                SCORES / "ib_arch_l2_om0_s0_diag.csv")
    directory = SCORES / label
    return (directory / f"{label}_best_dprime.csv",
            directory / f"{label}_best_diag.csv")


def endpoint(label: str) -> tuple[pd.DataFrame, dict[str, float]]:
    dprime_path, diag_path = paths(label)
    dprime = pd.read_csv(dprime_path)
    diag = pd.read_csv(diag_path)
    values = {
        "dprime_deep": float(dprime["dprime_deep"].mean()),
        "dprime_deep_fixed": float(dprime["dprime_deep_fixed"].mean()),
        "snr_deep": float(dprime["snr_deep"].mean()),
        "amp_ratio": float(diag["amp_ratio"].mean()),
        "fwhm_ratio": float(diag["fwhm_ratio"].mean()),
        "temporal_cos": float(diag["temporal_cos"].mean()),
        "spatial_cos": float(diag["spatial_cos"].mean()),
    }
    return dprime.set_index("unit_id"), values


def anchor_seed_metrics() -> pd.DataFrame:
    rows = []
    for seed, label in enumerate(ANCHOR_LABELS):
        dprime = pd.read_csv(SCORES / f"{label}_dprime.csv")
        diag = pd.read_csv(SCORES / f"{label}_diag.csv")
        rows.append({
            "seed": seed,
            "dprime_deep": dprime["dprime_deep"].mean(),
            "amp_ratio": diag["amp_ratio"].mean(),
            "temporal_cos": diag["temporal_cos"].mean(),
            "spatial_cos": diag["spatial_cos"].mean(),
        })
    return pd.DataFrame(rows)


def build_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    endpoint_frames = {}
    rows = []
    for label, name, mode, strength in ARMS:
        frame, values = endpoint(label)
        endpoint_frames[label] = frame
        rows.append({
            "label": label,
            "display_name": name,
            "weight_mode": mode,
            "weight_strength": strength,
            **values,
        })
    summary = pd.DataFrame(rows)
    anchor = summary.iloc[0]
    for metric in ("dprime_deep", "dprime_deep_fixed", "snr_deep", "amp_ratio",
                   "fwhm_ratio", "temporal_cos", "spatial_cos"):
        summary[f"{metric}_delta_vs_unweighted_s0"] = summary[metric] - anchor[metric]

    unit_rows = []
    anchor_units = endpoint_frames["unweighted"]["dprime_deep"]
    for label, name, _mode, _strength in ARMS[1:]:
        paired = pd.concat([
            endpoint_frames[label]["dprime_deep"], anchor_units,
        ], axis=1, keys=("weighted_dprime", "unweighted_dprime"), join="inner").dropna()
        for unit_id, values in paired.iterrows():
            unit_rows.append({
                "label": label,
                "display_name": name,
                "unit_id": int(unit_id),
                "weighted_dprime": float(values["weighted_dprime"]),
                "unweighted_dprime": float(values["unweighted_dprime"]),
                "dprime_delta": float(values["weighted_dprime"] - values["unweighted_dprime"]),
            })
    return summary, pd.DataFrame(unit_rows), anchor_seed_metrics()


def plot(summary: pd.DataFrame, effects: pd.DataFrame,
         seed_context: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(14.0, 9.6))
    positions = np.arange(len(summary))
    colors = ["#55595C", "#4D9B72", "#78AE75", "#A6BC78",
              "#D9A441", "#D47732", "#B84C3D", "#763A63"]

    axis = axes[0, 0]
    axis.bar(positions, summary["dprime_deep"], color=colors)
    axis.axhspan(seed_context["dprime_deep"].min(), seed_context["dprime_deep"].max(),
                 color="#7F878B", alpha=0.14, label="unweighted 3-seed range")
    axis.set_ylim(4.0, 4.40)
    axis.set_ylabel("best-checkpoint mean d-prime")
    axis.set_title("A  Only soft weight 3 is a plausible endpoint lead")
    axis.legend(frameon=False, fontsize=8)

    axis = axes[0, 1]
    axis.bar(positions, summary["amp_ratio"], color=colors)
    axis.axhspan(seed_context["amp_ratio"].min(), seed_context["amp_ratio"].max(),
                 color="#7F878B", alpha=0.14)
    axis.set_ylim(0.90, 0.955)
    axis.set_ylabel("empirical-template amplitude ratio")
    axis.set_title("B  Small amplitude gains do not predict detection")

    axis = axes[1, 0]
    axis.plot(positions, summary["temporal_cos"], "o-", color="#2878A4",
              label="temporal cosine")
    axis.plot(positions, summary["spatial_cos"], "s-", color="#8A5B2D",
              label="spatial cosine")
    axis.set_ylim(0.85, 1.005)
    axis.set_ylabel("template cosine")
    axis.set_title("C  High soft gates distort temporal and spatial shape")
    axis.legend(frameon=False, fontsize=8)

    axis = axes[1, 1]
    arm_names = [item[1] for item in ARMS[1:]]
    order = (effects[effects["label"] == ARMS[1][0]]
             .sort_values("unweighted_dprime")["unit_id"].tolist())
    matrix = np.vstack([
        effects[effects["label"] == label].set_index("unit_id").loc[order, "dprime_delta"]
        for label, _name, _mode, _strength in ARMS[1:]
    ])
    limit = max(0.1, float(np.nanpercentile(np.abs(matrix), 95)))
    image = axis.imshow(matrix, aspect="auto", cmap="RdBu", vmin=-limit, vmax=limit)
    axis.set_yticks(np.arange(len(arm_names)), arm_names)
    axis.set_xticks(np.arange(len(order)), [str(unit_id) for unit_id in order], rotation=45)
    axis.set_xlabel("GT unit (ordered by unweighted d-prime)")
    axis.set_title("D  Unit-level d-prime delta versus unweighted seed 0")
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04, label="d-prime delta")

    labels = summary["display_name"].tolist()
    for axis in axes.flat[:3]:
        axis.set_xticks(positions, labels, rotation=35, ha="right")
        axis.grid(alpha=0.22, axis="y")
    figure.suptitle("Corrected matched-L2 spike-weighting endpoint screen",
                     fontweight="bold")
    figure.tight_layout()
    figure.savefig(FIGURES / "weighting_controls.png", dpi=180)
    plt.close(figure)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    summary, effects, seed_context = build_tables()
    summary.to_csv(TABLES / "weighting_controls_summary.csv", index=False)
    effects.to_csv(TABLES / "weighting_controls_unit_effects.csv", index=False)
    seed_context.to_csv(TABLES / "weighting_controls_seed_context.csv", index=False)
    try:
        markdown = summary.to_markdown(index=False, floatfmt=".4f")
    except Exception:
        markdown = summary.to_csv(index=False)
    (TABLES / "weighting_controls_summary.md").write_text(markdown.rstrip() + "\n")
    plot(summary, effects, seed_context)
    print(summary.to_string(index=False))
    print(f"wrote {FIGURES / 'weighting_controls.png'}")


if __name__ == "__main__":
    main()