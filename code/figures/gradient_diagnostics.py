#!/usr/bin/env python3
"""Collate and plot same-parameter microbatch gradient diagnostics.

Usage:
    python gradient_diagnostics.py <label-or-jsonl>

For a label, reads ``models/<label>/gradient_diagnostics.jsonl``. Writes a CSV
under ``results/tables`` and a four-panel figure under ``figures``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def resolve_input(value: str) -> tuple[str, Path]:
    path = Path(value)
    if path.exists():
        return path.stem.replace("_gradient_diagnostics", ""), path
    return value, REPO / "models" / value / "gradient_diagnostics.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="run label or path to gradient_diagnostics.jsonl")
    args = parser.parse_args()

    label, path = resolve_input(args.source)
    if not path.exists():
        raise FileNotFoundError(path)
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not records:
        raise ValueError(f"no diagnostic records in {path}")

    rows = []
    spectra = []
    records.sort(key=lambda record: record["micro_step"])
    for record in records:
        row = {key: value for key, value in record.items()
               if key != "covariance_eigenvalues"}
        rows.append(row)
        eigenvalues = np.asarray(record.get("covariance_eigenvalues", []), dtype=float)
        total = eigenvalues.sum()
        spectra.append(eigenvalues / total if total > 0 else eigenvalues)
    frame = pd.DataFrame(rows)
    if "gradient_signal_norm_sq" not in frame:
        frame["gradient_signal_norm_sq"] = frame["mean_gradient_norm"] ** 2
    frame["gpu_h"] = frame["elapsed_s"] / 3600.0

    tables = REPO / "results" / "tables"
    figures = REPO / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    table_path = tables / f"{label}_gradient_diagnostics.csv"
    figure_path = figures / f"{label}_gradient_diagnostics.png"
    frame.to_csv(table_path, index=False)

    x = frame["samples_seen"].clip(lower=1)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    ax = axes[0, 0]
    ax.plot(x, frame["gradient_noise_scale"], "o-", label="instantaneous")
    ax.plot(x, frame["gradient_noise_scale_ema"], "s--", label="log-EMA")
    physical_batch = float(frame["physical_batch"].iloc[0])
    ax.axhline(physical_batch, color="#2ca02c", ls=":",
               label=f"physical batch ({physical_batch:g})")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_ylabel("examples")
    ax.set_title("Gradient-noise scale relative to physical batch")
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    ax.plot(x, frame["gradient_signal_norm_sq"], "o-", label="mean gradient norm²")
    ax.plot(x, frame["gradient_covariance_trace"], "s-", label="covariance trace")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_title("Signal and stochastic variation")
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    ax.plot(x, frame["pairwise_cosine_mean"], "o-", label="mean")
    ax.fill_between(x, frame["pairwise_cosine_min"], frame["pairwise_cosine_max"],
                    alpha=0.2, label="min-max")
    ax.axhline(0, color="0.5", lw=1)
    ax.set_xscale("log")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title("Microbatch gradient alignment")
    ax.set_ylabel("pairwise cosine")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    for index, spectrum in enumerate(spectra):
        if len(spectrum):
            ax.plot(np.arange(1, len(spectrum) + 1), spectrum, "o-", alpha=0.7,
                    label=f"step {int(frame.iloc[index]['micro_step'])}")
    ax.set_yscale("log")
    ax.set_xlabel("sample-covariance component")
    ax.set_ylabel("fraction of covariance trace")
    ax.set_title("Gradient covariance spectrum")
    ax.legend(fontsize=7)

    for ax in axes.flat:
        ax.grid(alpha=0.3, which="both")
        if ax is not axes[1, 1]:
            ax.set_xlabel("training windows used for gradients")
    fig.suptitle(f"Gradient measurement diagnostics: {label}", fontweight="bold")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=150)
    print(frame.to_string(index=False))
    print(f"wrote {table_path}")
    print(f"wrote {figure_path}")


if __name__ == "__main__":
    main()