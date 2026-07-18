#!/usr/bin/env python3
"""Analyze the completed three-seed R0, R1, and R5 recipe replications.

The recipes are paired by training seed and evaluated on the same frozen ten-unit
benchmark. This script keeps seed-level replication separate from paired unit-level
effects and compares convergence by windows seen, not optimizer updates.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SCORES = REPO / "results" / "scores"
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "figures"

RECIPES = [
    ("R0", "baseline", ["ib_r0_base", "ib_r0_s1", "ib_r0_s2"], 64, "#262626"),
    ("R1", "+warmup", ["ib_r1_warmup", "ib_r1_s1", "ib_r1_s2"], 64, "#2878a4"),
    ("R5", "batch 256", ["ib_r5_bs256", "ib_r5_s1", "ib_r5_s2"], 256, "#c65d32"),
]
TARGETS = (4.20, 4.30, 4.35)
BUDGETS = ((1_000_000, "1m"), (5_000_000, "5m"),
           (10_000_000, "10m"), (17_900_000, "17_9m"))


def target_key(target: float) -> str:
    return f"{target:.2f}".replace(".", "_")


def trajectory(label: str, batch_size: int) -> tuple[pd.DataFrame, str]:
    path = TABLES / f"{label}_trajectory.csv"
    frame = pd.read_csv(path).dropna(subset=["step"]).sort_values("step").copy()
    if "samples_seen" in frame and frame["samples_seen"].notna().all():
        frame["samples"] = frame["samples_seen"]
        source = "measured"
    else:
        frame["samples"] = frame["step"] * batch_size
        source = "step_x_batch"
    if not frame["samples"].is_monotonic_increasing:
        raise ValueError(f"non-monotonic sample telemetry: {label}")
    return frame, source


def first_crossing(frame: pd.DataFrame, target: float) -> float:
    x = frame["samples"].to_numpy(dtype=float)
    y = frame["dprime_deep"].to_numpy(dtype=float)
    for index, value in enumerate(y):
        if value < target:
            continue
        if index == 0:
            return float(x[index])
        x0, x1 = x[index - 1:index + 1]
        y0, y1 = y[index - 1:index + 1]
        if y1 == y0:
            return float(x1)
        return float(x0 + (x1 - x0) * (target - y0) / (y1 - y0))
    return float("nan")


def endpoint(label: str) -> dict[str, float]:
    dprime = pd.read_csv(SCORES / label / f"{label}_best_dprime.csv")
    diag = pd.read_csv(SCORES / label / f"{label}_best_diag.csv")
    return {
        "endpoint_dprime": float(dprime["dprime_deep"].mean()),
        "endpoint_dprime_fixed": float(dprime["dprime_deep_fixed"].mean()),
        "endpoint_snr": float(dprime["snr_deep"].mean()),
        "endpoint_amp_ratio": float(diag["amp_ratio"].mean()),
        "endpoint_fwhm_ratio": float(diag["fwhm_ratio"].mean()),
        "endpoint_temporal_cos": float(diag["temporal_cos"].mean()),
        "endpoint_spatial_cos": float(diag["spatial_cos"].mean()),
    }


def exact_signflip_p(differences: np.ndarray) -> float:
    observed = abs(float(differences.mean()))
    null = [abs(float((differences * signs).mean()))
            for signs in itertools.product((-1, 1), repeat=len(differences))]
    return float(np.mean(np.asarray(null) >= observed - 1e-15))


def build_run_table() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    rows = []
    trajectories = {}
    for recipe, name, labels, batch_size, _color in RECIPES:
        for seed, label in enumerate(labels):
            frame, samples_source = trajectory(label, batch_size)
            trajectories[label] = frame
            row = {
                "recipe": recipe,
                "recipe_name": name,
                "seed": seed,
                "label": label,
                "batch_size": batch_size,
                "samples_source": samples_source,
                **endpoint(label),
            }
            for target in TARGETS:
                row[f"samples_to_dprime_{target_key(target)}"] = first_crossing(frame, target)
            for budget, key in BUDGETS:
                row[f"dprime_at_{key}"] = float(np.interp(
                    budget, frame["samples"], frame["dprime_deep"]
                ))
            rows.append(row)
    return pd.DataFrame(rows), trajectories


def build_pairwise(run_table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    baseline = run_table[run_table["recipe"] == "R0"].set_index("seed")
    for recipe in ("R1", "R5"):
        candidate = run_table[run_table["recipe"] == recipe].set_index("seed")
        for seed in baseline.index:
            left, right = candidate.loc[seed], baseline.loc[seed]
            row = {
                "comparison": f"{recipe}-R0",
                "seed": int(seed),
                "candidate_label": left["label"],
                "baseline_label": right["label"],
            }
            for metric in ("endpoint_dprime", "endpoint_dprime_fixed",
                           "endpoint_amp_ratio", "endpoint_temporal_cos",
                           "endpoint_spatial_cos"):
                row[f"{metric}_delta"] = float(left[metric] - right[metric])
            row["endpoint_fwhm_abs_error_delta"] = float(
                abs(left["endpoint_fwhm_ratio"] - 1)
                - abs(right["endpoint_fwhm_ratio"] - 1)
            )
            for target in TARGETS:
                key = f"samples_to_dprime_{target_key(target)}"
                row[f"{key}_delta"] = float(left[key] - right[key])
            rows.append(row)
    return pd.DataFrame(rows)


def build_summary(run_table: pd.DataFrame, pairwise: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for recipe, name, _labels, _batch_size, _color in RECIPES:
        group = run_table[run_table["recipe"] == recipe]
        row = {
            "recipe": recipe,
            "recipe_name": name,
            "n_seeds": len(group),
            "endpoint_dprime_mean": group["endpoint_dprime"].mean(),
            "endpoint_dprime_sd": group["endpoint_dprime"].std(ddof=1),
            "endpoint_dprime_fixed_mean": group["endpoint_dprime_fixed"].mean(),
            "endpoint_amp_ratio_mean": group["endpoint_amp_ratio"].mean(),
            "endpoint_fwhm_ratio_mean": group["endpoint_fwhm_ratio"].mean(),
            "endpoint_temporal_cos_mean": group["endpoint_temporal_cos"].mean(),
            "endpoint_spatial_cos_mean": group["endpoint_spatial_cos"].mean(),
        }
        for target in TARGETS:
            key = f"samples_to_dprime_{target_key(target)}"
            reached = group[key].dropna()
            row[f"reached_dprime_{target_key(target)}"] = f"{len(reached)}/{len(group)}"
            row[f"median_samples_to_dprime_{target_key(target)}"] = (
                float(reached.median()) if len(reached) else float("nan")
            )
        for _budget, key in BUDGETS:
            row[f"dprime_at_{key}_mean"] = group[f"dprime_at_{key}"].mean()
        if recipe != "R0":
            differences = pairwise.loc[
                pairwise["comparison"] == f"{recipe}-R0", "endpoint_dprime_delta"
            ].to_numpy()
            row["paired_dprime_delta_vs_r0"] = float(differences.mean())
            row["seeds_improved_vs_r0"] = f"{int((differences > 0).sum())}/{len(differences)}"
            row["paired_signflip_p"] = exact_signflip_p(differences)
        rows.append(row)
    return pd.DataFrame(rows)


def build_unit_effects() -> pd.DataFrame:
    rows = []
    recipe_labels = {recipe: labels for recipe, _name, labels, _batch, _color in RECIPES}
    for recipe in ("R1", "R5"):
        seed_differences = []
        for seed, (candidate_label, baseline_label) in enumerate(zip(
                recipe_labels[recipe], recipe_labels["R0"])):
            candidate = pd.read_csv(
                SCORES / candidate_label / f"{candidate_label}_best_dprime.csv"
            ).set_index("unit_id")["dprime_deep"]
            baseline = pd.read_csv(
                SCORES / baseline_label / f"{baseline_label}_best_dprime.csv"
            ).set_index("unit_id")["dprime_deep"]
            difference = candidate.subtract(baseline).rename(f"seed_{seed}_delta")
            seed_differences.append(difference)
        effects = pd.concat(seed_differences, axis=1)
        for unit_id, values in effects.iterrows():
            rows.append({
                "comparison": f"{recipe}-R0",
                "unit_id": int(unit_id),
                **values.to_dict(),
                "mean_dprime_delta": float(values.mean()),
                "seeds_improved": int((values > 0).sum()),
            })
    return pd.DataFrame(rows)


def plot(run_table: pd.DataFrame, trajectories: dict[str, pd.DataFrame]) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.5, 5.1))
    common_samples = np.geomspace(100_000, 17_900_000, 240)

    for recipe, name, labels, _batch_size, color in RECIPES:
        interpolated = []
        for label in labels:
            frame = trajectories[label]
            visible = frame[frame["samples"] >= 100_000]
            axes[0].plot(visible["samples"] / 1e6, visible["dprime_deep"],
                         color=color, alpha=0.25, lw=1)
            interpolated.append(np.interp(
                common_samples, frame["samples"], frame["dprime_deep"]
            ))
        axes[0].plot(common_samples / 1e6, np.mean(interpolated, axis=0),
                     color=color, lw=2.4, label=f"{recipe} {name}")
    axes[0].axhline(4.35, color="0.55", ls=":", lw=1.2)
    axes[0].set_xscale("log")
    axes[0].set_xlim(0.1, 18.5)
    axes[0].set_ylim(4.05, 4.40)
    axes[0].set_xlabel("training windows seen (millions)")
    axes[0].set_ylabel("mean benchmark d-prime")
    axes[0].set_title("Convergence across matched seeds")
    axes[0].legend(frameon=False, fontsize=9)

    x = np.arange(len(RECIPES))
    for seed in range(3):
        values = [float(run_table.loc[
            (run_table["recipe"] == recipe) & (run_table["seed"] == seed),
            "endpoint_dprime"
        ].iloc[0]) for recipe, *_rest in RECIPES]
        axes[1].plot(x, values, color="0.72", lw=1.2, zorder=1)
    for index, (recipe, name, _labels, _batch_size, color) in enumerate(RECIPES):
        values = run_table.loc[run_table["recipe"] == recipe, "endpoint_dprime"]
        axes[1].scatter(np.full(len(values), index), values, color=color, s=42, zorder=3)
        axes[1].errorbar(index, values.mean(), yerr=values.std(ddof=1), color=color,
                         marker="D", ms=6, capsize=4, lw=1.5, zorder=4)
    axes[1].set_xticks(x, [f"{recipe}\n{name}" for recipe, name, *_rest in RECIPES])
    axes[1].set_ylabel("best-checkpoint mean d-prime")
    axes[1].set_title("Endpoint effect is small relative to seed spread")

    for axis in axes:
        axis.grid(alpha=0.22)
    figure.suptitle("Recipe replication on the frozen hybrid benchmark", fontweight="bold")
    figure.tight_layout()
    figure.savefig(FIGURES / "recipe_replication.png", dpi=180)
    plt.close(figure)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    run_table, trajectories = build_run_table()
    pairwise = build_pairwise(run_table)
    summary = build_summary(run_table, pairwise)
    unit_effects = build_unit_effects()

    run_table.to_csv(TABLES / "recipe_replication_runs.csv", index=False)
    pairwise.to_csv(TABLES / "recipe_replication_pairwise.csv", index=False)
    summary.to_csv(TABLES / "recipe_replication_summary.csv", index=False)
    unit_effects.to_csv(TABLES / "recipe_replication_unit_effects.csv", index=False)
    try:
        markdown = summary.to_markdown(index=False, floatfmt=".4f")
    except Exception:
        markdown = summary.to_csv(index=False)
    (TABLES / "recipe_replication_summary.md").write_text(markdown.rstrip() + "\n")
    plot(run_table, trajectories)

    print(summary.to_string(index=False))
    print(f"wrote {TABLES / 'recipe_replication_summary.csv'}")
    print(f"wrote {FIGURES / 'recipe_replication.png'}")


if __name__ == "__main__":
    main()