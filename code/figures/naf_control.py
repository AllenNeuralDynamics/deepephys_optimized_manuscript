#!/usr/bin/env python3
"""Analyze the capacity-matched NAF temporal-block control against R5."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SCORES = REPO / "results" / "scores"
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "figures"
R5_LABELS = ("ib_r5_bs256", "ib_r5_s1", "ib_r5_s2")
R13 = "ib_r13_naf58"
COLORS = {"R5": "#C75A31", "R13": "#956800", "seed": "#9AA0A3"}


def endpoint(label: str) -> tuple[pd.DataFrame, dict[str, float]]:
    dprime = pd.read_csv(SCORES / label / f"{label}_best_dprime.csv")
    diag = pd.read_csv(SCORES / label / f"{label}_best_diag.csv")
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


def trajectory(label: str) -> pd.DataFrame:
    frame = pd.read_csv(TABLES / f"{label}_trajectory.csv")
    frame = frame.dropna(subset=["step"]).sort_values("step").copy()
    if "samples_seen" not in frame or not frame["samples_seen"].notna().all():
        frame["samples_seen"] = frame["step"] * 256
    return frame


def loss_curve(label: str) -> pd.DataFrame:
    rows = [json.loads(line) for line in (
        REPO / "models" / label / "losses.jsonl"
    ).read_text().splitlines() if line.strip()]
    unique = {int(row["step"]): row for row in rows}
    frame = pd.DataFrame([unique[step] for step in sorted(unique)])
    if "samples_seen" not in frame:
        frame["samples_seen"] = frame["step"] * 256
    return frame


def build_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    frames = {}
    for seed, label in enumerate((*R5_LABELS, R13)):
        endpoint_frame, values = endpoint(label)
        frames[label] = endpoint_frame
        metrics = json.loads((REPO / "models" / label / "metrics.json").read_text())
        rows.append({
            "method": "R13 NAF58" if label == R13 else "R5 DoubleConv64",
            "seed": 0 if label == R13 else seed,
            "label": label,
            "model_params": metrics["model_params"],
            "final_val_loss_norm": metrics["final_val_loss_norm"],
            "runtime_s": metrics["runtime_s"],
            **values,
        })
    summary = pd.DataFrame(rows)

    paired = pd.concat([
        frames[R13]["dprime_deep"],
        frames[R5_LABELS[0]]["dprime_deep"],
    ], axis=1, keys=("r13_dprime", "r5_seed0_dprime"), join="inner").dropna()
    effects = paired.reset_index()
    effects["dprime_delta"] = effects["r13_dprime"] - effects["r5_seed0_dprime"]
    return summary, effects


def plot(summary: pd.DataFrame, effects: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(13.2, 9.3))

    axis = axes[0, 0]
    for label in R5_LABELS[1:]:
        frame = trajectory(label)
        axis.plot(frame["samples_seen"] / 1e6, frame["dprime_deep"],
                  color=COLORS["seed"], alpha=0.35, lw=1.1)
    for label, name, color in (
            (R5_LABELS[0], "R5 seed 0, DoubleConv64", COLORS["R5"]),
            (R13, "R13 seed 0, NAF58", COLORS["R13"])):
        frame = trajectory(label)
        axis.plot(frame["samples_seen"] / 1e6, frame["dprime_deep"], "-o",
                  color=color, lw=2.0, ms=3.2, label=name)
    axis.set_xscale("log")
    axis.set_xlim(0.1, 19)
    axis.set_ylim(4.05, 4.40)
    axis.set_xlabel("training windows seen (millions)")
    axis.set_ylabel("mean benchmark d-prime")
    axis.set_title("A  NAF does not improve d-prime convergence")
    axis.legend(frameon=False, fontsize=8)

    axis = axes[0, 1]
    r5 = summary[summary["method"] == "R5 DoubleConv64"]
    r13 = summary[summary["method"] == "R13 NAF58"].iloc[0]
    axis.scatter(np.zeros(len(r5)), r5["dprime_deep"], color=COLORS["R5"], s=48)
    axis.errorbar(0, r5["dprime_deep"].mean(), yerr=r5["dprime_deep"].std(ddof=1),
                  color=COLORS["R5"], marker="D", ms=6, capsize=4)
    axis.scatter([1], [r13["dprime_deep"]], color=COLORS["R13"], marker="D", s=72)
    axis.axhspan(r5["dprime_deep"].min(), r5["dprime_deep"].max(),
                 color=COLORS["seed"], alpha=0.12)
    axis.set_xticks([0, 1], ["R5\n3 seeds", "R13 NAF\n1 seed"])
    axis.set_ylabel("best-checkpoint mean d-prime")
    axis.set_title("B  NAF is below the observed R5 seed range")

    axis = axes[1, 0]
    ordered = effects.sort_values("r5_seed0_dprime")
    axis.bar(np.arange(len(ordered)), ordered["dprime_delta"], color=COLORS["R13"])
    axis.axhline(0, color="#555555", lw=1)
    axis.set_xticks(np.arange(len(ordered)), ordered["unit_id"].astype(str), rotation=45)
    axis.set_xlabel("GT unit (ordered by R5 seed-0 d-prime)")
    axis.set_ylabel("R13 - R5 seed-0 d-prime")
    axis.set_title("C  Paired unit effects")

    axis = axes[1, 1]
    for label, name, color in (
            (R5_LABELS[0], "R5 seed 0", COLORS["R5"]),
            (R13, "R13 NAF", COLORS["R13"])):
        frame = loss_curve(label)
        axis.plot(frame["samples_seen"] / 1e6, frame["val_loss"],
                  color=color, lw=2.0, label=name)
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlim(0.01, 19)
    axis.set_xlabel("training windows seen (millions)")
    axis.set_ylabel("held-out Charbonnier loss")
    axis.set_title("D  Similar final loss, slower NAF runtime")
    axis.legend(frameon=False, fontsize=8)
    axis.text(0.02, 0.05,
              f"R5: {float(r5.iloc[0].runtime_s)/3600:.2f} h\n"
              f"R13: {float(r13.runtime_s)/3600:.2f} h",
              transform=axis.transAxes, ha="left", va="bottom", fontsize=8,
              bbox={"boxstyle": "round,pad=0.3", "facecolor": "white",
                    "edgecolor": "none", "alpha": 0.9})

    for axis in axes.flat:
        axis.grid(alpha=0.22, which="both")
    figure.suptitle("Capacity-matched NAF temporal-block control", fontweight="bold")
    figure.tight_layout()
    figure.savefig(FIGURES / "naf_control.png", dpi=180)
    plt.close(figure)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    summary, effects = build_tables()
    summary.to_csv(TABLES / "naf_control_summary.csv", index=False)
    effects.to_csv(TABLES / "naf_control_unit_effects.csv", index=False)
    try:
        markdown = summary.to_markdown(index=False, floatfmt=".4f")
    except Exception:
        markdown = summary.to_csv(index=False)
    (TABLES / "naf_control_summary.md").write_text(markdown.rstrip() + "\n")
    plot(summary, effects)
    print(summary.to_string(index=False))
    print(f"wrote {FIGURES / 'naf_control.png'}")


if __name__ == "__main__":
    main()