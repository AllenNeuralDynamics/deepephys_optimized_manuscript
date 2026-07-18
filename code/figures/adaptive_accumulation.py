#!/usr/bin/env python3
"""Plot the measured gradient statistics and decisions of adaptive accumulation.

Usage:
    python adaptive_accumulation.py [label]

Reads ``models/<label>/gradient_diagnostics.jsonl`` and writes a controller
table under ``results/tables`` plus a four-panel figure under ``figures``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label", nargs="?", default="ib_r9_adaptive")
    args = parser.parse_args()

    source = REPO / "models" / args.label / "gradient_diagnostics.jsonl"
    if not source.exists():
        raise FileNotFoundError(source)
    records = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    if not records:
        raise ValueError(f"no diagnostic records in {source}")

    frame = pd.DataFrame(records).sort_values("samples_seen", ignore_index=True)
    frame["active_effective_batch"] = (
        frame["physical_batch"] * frame["accumulation_target"]
    )
    frame["proposed_effective_batch"] = (
        frame["physical_batch"] * frame["proposed_accumulation"]
    )
    frame["resolved"] = frame["gradient_noise_scale"].notna()

    tables = REPO / "results" / "tables"
    figures = REPO / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    table_path = tables / f"{args.label}_controller.csv"
    figure_path = figures / f"{args.label}_controller.png"
    columns = [
        "micro_step", "optimizer_step", "samples_seen", "elapsed_s",
        "gradient_noise_scale", "gradient_noise_scale_ema", "resolved",
        "pairwise_cosine_mean", "pairwise_cosine_min", "pairwise_cosine_max",
        "physical_batch", "accumulation_target", "proposed_accumulation",
        "active_effective_batch", "proposed_effective_batch", "lr",
    ]
    frame[[column for column in columns if column in frame]].to_csv(table_path, index=False)

    x = frame["samples_seen"].clip(lower=1)
    physical_batch = float(frame["physical_batch"].iloc[0])
    unresolved = ~frame["resolved"]
    colors = {
        "instant": "#d95f02",
        "ema": "#1b6ca8",
        "active": "#276749",
        "proposed": "#8c2d62",
        "reference": "#5f6368",
    }

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5), sharex=True)

    ax = axes[0, 0]
    ax.plot(x, frame["gradient_noise_scale"], "o-", color=colors["instant"],
            label="instantaneous estimate")
    ax.plot(x, frame["gradient_noise_scale_ema"], "s--", color=colors["ema"],
            label="log-EMA used by controller")
    if unresolved.any():
        ax.scatter(x[unresolved], frame.loc[unresolved, "gradient_noise_scale_ema"],
                   marker="x", s=70, color="black", label="unresolved; EMA held")
    ax.axhline(physical_batch, color=colors["reference"], ls=":",
               label=f"physical batch ({physical_batch:g})")
    ax.set_yscale("log")
    ax.set_ylabel("gradient-noise scale (examples)")
    ax.set_title("A  Measured stochastic-gradient scale")
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    ax.step(x, frame["active_effective_batch"], where="post", lw=2.2,
            color=colors["active"], label="active at measurement")
    ax.step(x, frame["proposed_effective_batch"], where="post", lw=1.8, ls="--",
            color=colors["proposed"], label="controller proposal")
    ax.axhline(physical_batch, color=colors["reference"], ls=":")
    changes = frame["proposed_accumulation"].ne(frame["proposed_accumulation"].shift())
    for _, row in frame.loc[changes & (frame["proposed_accumulation"] > 1)].iterrows():
        ax.annotate(
            f"{int(row['proposed_accumulation'])} observations",
            (max(1, row["samples_seen"]), row["proposed_effective_batch"]),
            xytext=(5, 7), textcoords="offset points", fontsize=8,
        )
    ax.set_yscale("log", base=2)
    batch_ticks = [physical_batch * factor for factor in (1, 2, 4, 8)]
    ax.set_yticks(batch_ticks, labels=[f"{value:g}" for value in batch_ticks])
    ax.set_ylim(0.9 * physical_batch, 10 * physical_batch)
    ax.set_ylabel("effective batch (examples)")
    ax.set_title("B  Integration horizon selected online")
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    ax.plot(x, frame["pairwise_cosine_mean"], "o-", color=colors["ema"],
            label="mean pairwise cosine")
    ax.fill_between(
        x, frame["pairwise_cosine_min"], frame["pairwise_cosine_max"],
        color=colors["ema"], alpha=0.18, label="microbatch min-max",
    )
    ax.axhline(0, color=colors["reference"], lw=1)
    ax.set_ylim(-1.05, 1.05)
    ax.set_ylabel("gradient cosine")
    ax.set_title("C  Agreement collapses late in training")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    optimizer_steps = frame["optimizer_step"].clip(lower=1)
    ax.plot(x, optimizer_steps, "o-", lw=2.2, color=colors["active"],
            label="adaptive updates")
    ax.plot(x, (frame["samples_seen"] / physical_batch).clip(lower=1), ls=":",
            color=colors["reference"], label=f"always batch {physical_batch:g}")
    ax.plot(x, (frame["samples_seen"] / (4 * physical_batch)).clip(lower=1), ls="--",
            color=colors["proposed"], label=f"always batch {4 * physical_batch:g}")
    ax.set_yscale("log")
    ax.set_ylabel("cumulative optimizer updates")
    ax.set_title("D  Adaptive integration reduces late updates")
    ax.legend(fontsize=8)

    for ax in axes.flat:
        ax.set_xscale("log")
        ax.set_xlabel("training windows seen")
        ax.grid(alpha=0.25, which="both")
    fig.suptitle("Objective-preserving adaptive gradient integration", fontweight="bold")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    print(frame[columns].to_string(index=False))
    print(f"wrote {table_path}")
    print(f"wrote {figure_path}")


if __name__ == "__main__":
    main()