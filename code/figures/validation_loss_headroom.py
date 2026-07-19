#!/usr/bin/env python3
"""Calibrate spike-reconstruction headroom against observed validation-loss changes."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "figures"
MODELS = REPO / "models"
R5_LABELS = ("ib_r5_bs256", "ib_r5_s1", "ib_r5_s2")
METHOD_LABELS = ("ib_r9_adaptive", "ib_r10_importance", "ib_r11_batchonly",
                 "ib_r12_fixed256")


def final_loss(label: str) -> float:
    metrics = json.loads((MODELS / label / "metrics.json").read_text())
    return float(metrics["final_val_loss_norm"])


def build_summary() -> tuple[pd.DataFrame, pd.Series]:
    raw = pd.read_csv(TABLES / "validation_loss_headroom_raw.csv").iloc[0]
    meaningful = float(raw["meaningful_loss_drop"])
    zero_upper = float(raw["zero_residual_loss_drop_upper"])
    r5_losses = np.array([final_loss(label) for label in R5_LABELS])
    naf_delta = abs(final_loss("ib_r13_naf58") - final_loss("ib_r5_bs256"))
    method_losses = np.array([final_loss(label) for label in METHOD_LABELS])

    rows = [
        ("meaningful spike headroom", meaningful,
         "spike-support residual reduced to same-channel off-spike floor"),
        ("zero-residual upper bound", zero_upper,
         "all spike-support residual removed, including unpredictable target noise"),
        ("R5 three-seed SD", float(r5_losses.std(ddof=1)),
         "run-to-run variation under the matched recipe"),
        ("R13 NAF - R5 seed 0", naf_delta,
         "capacity-matched architecture loss difference"),
        ("R9-R12 method range", float(method_losses.max() - method_losses.min()),
         "range across adaptive, sampling, and batch controls"),
    ]
    summary = pd.DataFrame(rows, columns=["quantity", "absolute_loss_change", "interpretation"])
    summary["relative_to_meaningful_headroom"] = summary["absolute_loss_change"] / meaningful
    summary["percent_of_r5_validation_loss"] = (
        100.0 * summary["absolute_loss_change"] / float(raw["validation_loss"])
    )
    return summary, raw


def plot(summary: pd.DataFrame, raw: pd.Series) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    figure.suptitle("How much can meaningful spike reconstruction move validation loss?",
                    fontsize=15, fontweight="bold")

    axis = axes[0]
    background = float(raw["matched_background_loss_mean"])
    support_loss = float(raw["support_loss_mean"])
    values = [0.0, support_loss - background]
    bars = axis.bar(["same-channel\noff-spike", "GT spike support"], values,
                    color=["#6B7378", "#C75A31"], width=0.62)
    axis.set_ylabel("excess elementwise loss above off-spike floor")
    axis.set_title("A  Spike elements have little excess loss")
    axis.set_ylim(0, max(values) * 1.35)
    labels = ["reference", f"{values[1]:.5f}"]
    for bar, value, label in zip(bars, values, labels):
        axis.text(bar.get_x() + bar.get_width() / 2,
                  value + max(values) * 0.035, label,
                  ha="center", va="bottom", fontsize=9)
    axis.text(0.03, 0.05,
              f"raw means: {background:.4f} off-spike, {support_loss:.4f} support\n"
              f"support = {100 * float(raw['support_fraction']):.4f}% of elements\n"
              f"meaningful dL = {float(raw['meaningful_loss_drop']):.2e}",
              transform=axis.transAxes, fontsize=9,
              bbox={"boxstyle": "round,pad=0.35", "facecolor": "white",
                    "edgecolor": "#C9CDD0"})

    axis = axes[1]
    order = [
        "R13 NAF - R5 seed 0", "R5 three-seed SD", "meaningful spike headroom",
        "zero-residual upper bound", "R9-R12 method range",
    ]
    frame = summary.set_index("quantity").loc[order].reset_index()
    colors = ["#956800", "#6B7378", "#168578", "#4C78A8", "#7B5EA7"]
    axis.barh(frame["quantity"], frame["absolute_loss_change"], color=colors)
    axis.set_xscale("log")
    axis.invert_yaxis()
    axis.set_xlabel("absolute validation-loss change (log scale)")
    axis.set_title("B  Observed deltas versus spike headroom")
    for y, value in enumerate(frame["absolute_loss_change"]):
        axis.text(value * 1.08, y, f"{value:.2e}", va="center", fontsize=8)
    axis.margins(x=0.22)

    figure.tight_layout(rect=(0, 0, 1, 0.94))
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURES / "validation_loss_headroom.png", dpi=180)
    plt.close(figure)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    summary, raw = build_summary()
    summary.to_csv(TABLES / "validation_loss_scale.csv", index=False)
    try:
        markdown = summary.to_markdown(index=False, floatfmt=".6g")
    except ImportError:
        markdown = summary.to_csv(index=False)
    (TABLES / "validation_loss_scale.md").write_text(markdown.rstrip() + "\n")
    recovery = np.array([0.10, 0.25, 0.50, 1.00])
    scenarios = pd.DataFrame({
        "recoverable_spike_excess_removed": recovery,
        "validation_loss_drop": recovery * float(raw["meaningful_loss_drop"]),
        "projected_validation_loss": (
            float(raw["validation_loss"])
            - recovery * float(raw["meaningful_loss_drop"])
        ),
    })
    scenarios.to_csv(TABLES / "validation_loss_reconstruction_scenarios.csv", index=False)
    try:
        scenario_markdown = scenarios.to_markdown(index=False, floatfmt=".8g")
    except ImportError:
        scenario_markdown = scenarios.to_csv(index=False)
    (TABLES / "validation_loss_reconstruction_scenarios.md").write_text(
        scenario_markdown.rstrip() + "\n"
    )
    plot(summary, raw)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()