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
* GPU-hours    -- exact checkpoint elapsed time for telemetry-enabled runs;
                  otherwise a clearly marked step-proportional estimate.

Emits ``figures/recipe_convergence.png`` (d' vs samples-seen and vs GPU-hours)
and ``results/tables/recipe_convergence_summary.{csv,md}`` (final/peak d' and the
budget each recipe needs to first cross a set of target d' thresholds).

Usage:
    python recipe_convergence.py [--targets 4.20 4.30 4.35]
"""
from __future__ import annotations

import argparse
import itertools
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


def endpoint_units(label: str) -> pd.Series | None:
    path = REPO / "results" / "scores" / label / f"{label}_best_dprime.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    if "unit_id" not in frame or METRIC not in frame:
        return None
    return frame.set_index("unit_id")[METRIC]


def paired_endpoint_bootstrap(labels: list[tuple[str, str]]) -> pd.DataFrame:
    rng = np.random.default_rng(20260717)
    units = {label: endpoint_units(label) for label, _ in labels}
    rows = []
    for (label_a, name_a), (label_b, name_b) in itertools.combinations(labels, 2):
        if units[label_a] is None or units[label_b] is None:
            continue
        paired = pd.concat([units[label_a], units[label_b]], axis=1, join="inner").dropna()
        difference = (paired.iloc[:, 0] - paired.iloc[:, 1]).to_numpy()
        if not len(difference):
            continue
        draws = difference[rng.integers(0, len(difference), size=(100_000, len(difference)))]
        bootstrap_mean = draws.mean(axis=1)
        low, high = np.quantile(bootstrap_mean, [0.025, 0.975])
        rows.append({
            "recipe_a": name_a, "recipe_b": name_b,
            "mean_dprime_difference": float(difference.mean()),
            "unit_bootstrap_95_low": float(low),
            "unit_bootstrap_95_high": float(high),
            "n_paired_units": int(len(difference)),
        })
    return pd.DataFrame(rows)


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
    inferred_samples = df["step"] * batch
    if "samples_seen" in df and df["samples_seen"].notna().any():
        df["samples"] = df["samples_seen"].fillna(inferred_samples)
    else:
        df["samples"] = inferred_samples
    inferred_gpu_h = (run_min / 60.0) * df["step"] / df["step"].max()
    if "elapsed_s" in df and df["elapsed_s"].notna().any():
        df["gpu_h"] = (df["elapsed_s"] / 3600.0).fillna(inferred_gpu_h)
        df["time_source"] = np.where(df["elapsed_s"].notna(), "measured", "inferred")
    else:
        df["gpu_h"] = inferred_gpu_h
        df["time_source"] = "inferred"
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

    # ---- raw d′ = first non-NaN dprime_raw value across all recipes ----------
    raw_dp = 4.497  # frozen AP-band reference
    MIN_DEFICIT = 1e-3  # floor for log(deficit) to handle near-raw values

    FIGS.mkdir(parents=True, exist_ok=True)

    # ---- Figure 1: linear-y (d' vs samples-seen and vs GPU-hours) ------------
    fig1, axes1 = plt.subplots(1, 2, figsize=(13, 5.2))
    for _lab, _bat, _rm, name, col, df in data:
        for ax, xcol in zip(axes1, ("samples", "gpu_h")):
            ax.plot(df[xcol], df[METRIC], "-o", ms=4, lw=1.6, color=col, label=name)
    for ax, xcol, xlabel in zip(axes1, ("samples", "gpu_h"),
                                ("windows seen", "GPU-hours (estimated for R0–R5)")):
        ax.axhline(ANCHOR, ls="--", lw=1, color="grey", alpha=0.7,
                   label=f"base64_om0 anchor {ANCHOR:.3f}")
        ax.set_xscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("d′ (deep, mean over GT units)")
        ax.grid(alpha=0.3, which="both")
    axes1[0].set_title("Detection vs data seen")
    axes1[1].set_title("Detection vs wall-clock")
    axes1[0].legend(fontsize=8, loc="lower right")
    fig1.suptitle("Training-efficiency recipe sweep (base64_om0 body)", fontweight="bold")
    fig1.tight_layout()
    fig1.savefig(FIGS / "recipe_convergence.png", dpi=150)
    print(f"wrote {FIGS / 'recipe_convergence.png'}")

    # ---- Figure 2: log-log — detection DEFICIT vs GPU-hours ------------------
    # deficit = raw_dp - d'_deep  (always positive, lower = better)
    # y-axis: NOT inverted — deficit decreases going DOWN = improving, natural reading
    fig2, axes2 = plt.subplots(1, 2, figsize=(13, 5.2))

    for _lab, _bat, _rm, name, col, df in data:
        deficit = (raw_dp - df[METRIC]).clip(lower=MIN_DEFICIT)
        for ax, xcol in zip(axes2, ("samples", "gpu_h")):
            ax.plot(df[xcol], deficit, "-o", ms=4, lw=1.6, color=col, label=name)

    for ax, xcol, xlabel in zip(axes2, ("samples", "gpu_h"),
                                ("windows seen", "GPU-hours (estimated for R0–R5)")):
        for t in args.targets:
            tdef = raw_dp - t
            ax.axhline(tdef, ls=":", lw=1.2, color="grey", alpha=0.7)
            # label at 5 % from left edge using axes-fraction x-coord
            ax.text(0.02, tdef, f"d′={t:.2f}", transform=ax.get_yaxis_transform(),
                    fontsize=7, color="dimgrey", va="center", ha="left",
                    bbox=dict(fc="white", ec="none", pad=1))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("detection deficit  (raw d′ − d′_deep)   ↓ = better")
        ax.grid(alpha=0.3, which="both")

    axes2[0].set_title("Deficit vs data seen  (log–log)")
    axes2[1].set_title("Deficit vs wall-clock  (log–log)")
    axes2[0].legend(fontsize=8, loc="upper right")
    fig2.suptitle("Training-efficiency recipe sweep — log–log deficit (base64_om0 body)",
                  fontweight="bold")
    fig2.tight_layout()
    fig2.savefig(FIGS / "recipe_convergence_loglog.png", dpi=150)
    print(f"wrote {FIGS / 'recipe_convergence_loglog.png'}")

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
            "time_source": "measured" if (df["time_source"] == "measured").all() else "inferred",
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

    endpoint = paired_endpoint_bootstrap([(lab, name) for lab, _, _, name, _, _ in data])
    endpoint_path = TABLES / "recipe_endpoint_pairwise.csv"
    endpoint.to_csv(endpoint_path, index=False)
    print(f"wrote {endpoint_path}")


if __name__ == "__main__":
    main()
