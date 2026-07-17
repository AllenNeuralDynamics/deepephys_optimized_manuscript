#!/usr/bin/env python3
"""Cross-recipe convergence analysis for the training-efficiency sweep.

Overlays the d'-vs-training-budget trajectories of the six recipe runs (R0-R5),
all sharing the base64_om0 body but differing in optimizer / LR schedule, and
quantifies how fast each reaches a target detection performance.

Reads ``results/tables/ib_r*_trajectory.csv`` (produced by collate_trajectory.py).
Because the recipes use different batch sizes, three budget axes are computed:

* updates      -- optimizer steps (the raw checkpoint step).
* samples seen -- updates x batch size (apples-to-apples: all recipes cover the
                  same ~18 M windows, so this is the fair convergence axis).
* GPU-hours    -- measured wall-clock, apportioned across the run in proportion
                  to the checkpoint step (constant time/update within a run).

Emits ``figures/recipe_convergence.png`` (d' vs samples-seen and vs GPU-hours)
and ``results/tables/recipe_convergence_summary.{csv,md}`` (final/peak d' and the
budget each recipe needs to first cross a set of target d' thresholds).

Usage:
    python recipe_convergence.py [--targets 4.20 4.30 4.35]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "results" / "tables"
FIGS = REPO / "figures"

# label, batch_size, measured CO run_time (min, 2026-07-16), display name, colour.
# base64_om0 (Tier-2 anchor) final best_model d' = 4.359 -- R0 should reproduce it.
RECIPES = [
    ("ib_r0_base",     64, 164, "R0 baseline adamw/cosine",   "#444444"),
    ("ib_r1_warmup",   64, 168, "R1 +warmup",                 "#1f77b4"),
    ("ib_r2_onecycle", 64, 165, "R2 one-cycle",               "#2ca02c"),
    ("ib_r3_adamw2e3", 64, 163, "R3 adamw lr2e-3 tuned",      "#ff7f0e"),
    ("ib_r4_lion",     64, 169, "R4 lion",                    "#d62728"),
    ("ib_r5_bs256",   256, 159, "R5 batch256",                "#9467bd"),
]
ANCHOR = 4.359  # base64_om0 best_model d' (sanity reference for R0)
METRIC = "dprime_deep"


def load(label: str, batch: int, run_min: float) -> pd.DataFrame | None:
    path = TABLES / f"{label}_trajectory.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["step"].notna()].copy()
    if df.empty:
        return None
    df["step"] = df["step"].astype(int)
    df = df.sort_values("step", ignore_index=True)
    df["samples"] = df["step"] * batch
    df["gpu_h"] = (run_min / 60.0) * df["step"] / df["step"].max()
    return df


def cross(df: pd.DataFrame, xcol: str, target: float) -> float | None:
    """Smallest x at which METRIC first reaches ``target`` (linear interp)."""
    y = df[METRIC].to_numpy()
    x = df[xcol].to_numpy()
    for i in range(len(y)):
        if y[i] >= target:
            if i == 0:
                return float(x[i])
            x0, x1, y0, y1 = x[i - 1], x[i], y[i - 1], y[i]
            if y1 == y0:
                return float(x1)
            return float(x0 + (x1 - x0) * (target - y0) / (y1 - y0))
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--targets", nargs="+", type=float, default=[4.20, 4.30, 4.35])
    args = ap.parse_args()

    data = [(lab, bat, rm, name, col, load(lab, bat, rm))
            for lab, bat, rm, name, col in RECIPES]
    data = [d for d in data if d[-1] is not None]
    if not data:
        print("no trajectory tables found yet under results/tables/ib_r*_trajectory.csv")
        return

    # ---- figure: d' vs samples-seen and vs GPU-hours -------------------------
    FIGS.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    for _lab, _bat, _rm, name, col, df in data:
        for ax, xcol in zip(axes, ("samples", "gpu_h")):
            ax.plot(df[xcol], df[METRIC], "-o", ms=4, lw=1.6, color=col, label=name)
    for ax, xcol, xlabel in zip(axes, ("samples", "gpu_h"),
                                ("windows seen (updates x batch)", "GPU-hours")):
        ax.axhline(ANCHOR, ls="--", lw=1, color="grey", alpha=0.7,
                   label=f"base64_om0 anchor {ANCHOR:.3f}")
        ax.set_xscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("d' (deep, mean over GT units)")
        ax.grid(alpha=0.3, which="both")
    axes[0].set_title("Detection vs data seen")
    axes[1].set_title("Detection vs wall-clock")
    axes[0].legend(fontsize=8, loc="lower right")
    fig.suptitle("Training-efficiency recipe sweep (base64_om0 body)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGS / "recipe_convergence.png", dpi=150)
    print(f"wrote {FIGS / 'recipe_convergence.png'}")

    # ---- summary table: final / peak d' + budget-to-target -------------------
    rows = []
    for lab, _bat, rm, name, _col, df in data:
        final = df.iloc[-1]
        row = {
            "recipe": name,
            "label": lab,
            "run_min": rm,
            "final_step": int(final["step"]),
            "final_dprime": round(float(final[METRIC]), 4),
            "peak_dprime": round(float(df[METRIC].max()), 4),
        }
        for t in args.targets:
            s = cross(df, "samples", t)
            g = cross(df, "gpu_h", t)
            row[f"samples@{t:.2f}"] = None if s is None else f"{s/1e6:.2f}M"
            row[f"gpu_h@{t:.2f}"] = None if g is None else round(g, 2)
        rows.append(row)
    summ = pd.DataFrame(rows)

    out = TABLES / "recipe_convergence_summary"
    summ.to_csv(out.with_suffix(".csv"), index=False)
    try:
        md = summ.to_markdown(index=False)
    except Exception:
        md = summ.to_csv(index=False)
    out.with_suffix(".md").write_text(md + "\n")
    print(summ.to_string(index=False))
    print(f"\nwrote {out.with_suffix('.csv')}")


if __name__ == "__main__":
    main()
