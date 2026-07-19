#!/usr/bin/env python3
"""Compare integration and objective-preserving sampling controls with R1."""
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

CONTROLS = [
    ("R1", "ib_r1_warmup", "R1 warmup, batch 64", 64, "#303437"),
    ("R9", "ib_r9_adaptive", "R9 adaptive accumulation", 64, "#168578"),
    ("R10", "ib_r10_importance", "R10 importance sampling", 64, "#7B5EA7"),
    ("R11", "ib_r11_batchonly", "R11 physical batch 256", 256, "#C75A31"),
    ("R12", "ib_r12_fixed256", "R12 accumulated batch 256", 64, "#C7932F"),
]
R1_REPLICATES = ["ib_r1_warmup", "ib_r1_s1", "ib_r1_s2"]
TARGETS = (4.20, 4.30, 4.35)
BUDGETS = ((1_000_000, "1m"), (5_000_000, "5m"),
           (10_000_000, "10m"), (17_900_000, "17_9m"))
CO_RUNTIME_S = {
    "ib_r1_warmup": 10_061,
    "ib_r9_adaptive": 9_716,
    "ib_r10_importance": 22_059,
    "ib_r11_batchonly": 8_845,
    "ib_r12_fixed256": 9_565,
}
BASELINE_UPDATES = 281_244


def load_trajectory(label: str, batch_size: int) -> pd.DataFrame:
    frame = pd.read_csv(TABLES / f"{label}_trajectory.csv")
    frame = frame.dropna(subset=["step"]).sort_values("step").copy()
    inferred = frame["step"] * batch_size
    if "samples_seen" in frame and frame["samples_seen"].notna().all():
        frame["samples"] = frame["samples_seen"]
        frame["samples_source"] = "measured"
    else:
        frame["samples"] = inferred
        frame["samples_source"] = "step_x_batch"
    return frame


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


def sustained_scored_crossing(frame: pd.DataFrame, target: float) -> float:
    values = frame["dprime_deep"].to_numpy(dtype=float)
    for index in range(len(values)):
        if np.all(values[index:] >= target):
            return float(frame.iloc[index]["samples"])
    return float("nan")


def controller_phases() -> pd.DataFrame:
    controller = pd.read_csv(TABLES / "ib_r9_adaptive_controller.csv")
    final_samples = int(json.loads(
        (REPO / "models" / "ib_r9_adaptive" / "metrics.json").read_text()
    )["samples_seen"])
    starts = [(0, 64, "initial")]
    current = 64
    for row in controller.itertuples():
        proposed = int(row.proposed_effective_batch)
        if proposed != current:
            starts.append((int(row.samples_seen), proposed,
                           "resolved" if bool(row.resolved) else "held"))
            current = proposed
    rows = []
    for index, (start, batch, decision) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else final_samples
        rows.append({
            "start_samples": start,
            "end_samples": end,
            "effective_batch": batch,
            "decision": decision,
        })
    return pd.DataFrame(rows)


def build_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame,
                            dict[str, pd.DataFrame]]:
    trajectories = {}
    endpoints = {}
    endpoint_frames = {}
    rows = []
    for short, label, name, batch_size, _color in CONTROLS:
        trajectory = load_trajectory(label, batch_size)
        trajectories[label] = trajectory
        endpoint_frame, metrics = endpoint(label)
        endpoint_frames[label] = endpoint_frame
        endpoints[label] = metrics

        model_metrics_path = REPO / "models" / label / "metrics.json"
        if model_metrics_path.exists():
            model_metrics = json.loads(model_metrics_path.read_text())
            updates = int(model_metrics["optimizer_steps"])
            training_s = float(model_metrics["training_elapsed_s"])
        else:
            updates = BASELINE_UPDATES
            training_s = float("nan")
        row = {
            "method": short,
            "label": label,
            "display_name": name,
            "physical_batch": batch_size,
            "optimizer_updates": updates,
            "update_reduction_vs_r1": 1 - updates / BASELINE_UPDATES,
            "training_elapsed_s": training_s,
            "code_ocean_runtime_s": CO_RUNTIME_S[label],
            **metrics,
        }
        for target in TARGETS:
            key = f"{target:.2f}".replace(".", "_")
            row[f"first_samples_to_dprime_{key}"] = first_crossing(trajectory, target)
            row[f"sustained_scored_samples_to_dprime_{key}"] = (
                sustained_scored_crossing(trajectory, target)
            )
        for budget, key in BUDGETS:
            row[f"dprime_at_{key}"] = float(np.interp(
                budget, trajectory["samples"], trajectory["dprime_deep"]
            ))
        rows.append(row)
    summary = pd.DataFrame(rows)

    r1 = summary.loc[summary["method"] == "R1"].iloc[0]
    deltas = []
    for method in ("R9", "R10", "R11", "R12"):
        candidate = summary.loc[summary["method"] == method].iloc[0]
        row = {"comparison": f"{method}-R1"}
        for metric in ("dprime_deep", "dprime_deep_fixed", "snr_deep", "amp_ratio",
                       "fwhm_ratio", "temporal_cos", "spatial_cos"):
            row[f"{metric}_delta"] = float(candidate[metric] - r1[metric])
        deltas.append(row)
    comparison = pd.DataFrame(deltas)

    unit_rows = []
    pairs = (
        ("R9-R1", "ib_r9_adaptive", "ib_r1_warmup"),
        ("R10-R1", "ib_r10_importance", "ib_r1_warmup"),
        ("R11-R1", "ib_r11_batchonly", "ib_r1_warmup"),
        ("R12-R1", "ib_r12_fixed256", "ib_r1_warmup"),
        ("R9-R11", "ib_r9_adaptive", "ib_r11_batchonly"),
        ("R12-R11", "ib_r12_fixed256", "ib_r11_batchonly"),
    )
    for name, candidate, baseline in pairs:
        paired = pd.concat([
            endpoint_frames[candidate]["dprime_deep"],
            endpoint_frames[baseline]["dprime_deep"],
        ], axis=1, keys=("candidate", "baseline"), join="inner").dropna()
        for unit_id, values in paired.iterrows():
            unit_rows.append({
                "comparison": name,
                "unit_id": int(unit_id),
                "candidate_dprime": float(values["candidate"]),
                "baseline_dprime": float(values["baseline"]),
                "dprime_delta": float(values["candidate"] - values["baseline"]),
            })
    unit_effects = pd.DataFrame(unit_rows)
    phases = controller_phases()
    return summary, comparison, unit_effects, phases, trajectories


def plot(summary: pd.DataFrame, unit_effects: pd.DataFrame,
         phases: pd.DataFrame, trajectories: dict[str, pd.DataFrame]) -> None:
    colors = {short: color for short, _label, _name, _batch, color in CONTROLS}
    figure, axes = plt.subplots(2, 2, figsize=(13.5, 9.5))

    axis = axes[0, 0]
    for label in R1_REPLICATES:
        frame = load_trajectory(label, 64)
        axis.plot(frame["samples"] / 1e6, frame["dprime_deep"],
                  color="#8D9498", alpha=0.35, lw=1.1)
    for short, label, name, _batch, color in CONTROLS:
        frame = trajectories[label]
        axis.plot(frame["samples"] / 1e6, frame["dprime_deep"], "-o",
                  color=color, lw=2.0, ms=3.3, label=name)
    axis.set_xscale("log")
    axis.set_xlim(0.1, 19)
    axis.set_ylim(4.05, 4.40)
    axis.set_xlabel("training windows seen (millions)")
    axis.set_ylabel("mean benchmark d-prime")
    axis.set_title("A  Detection versus equal data budget")
    axis.legend(frameon=False, fontsize=8, loc="lower right")

    axis = axes[0, 1]
    r1_values = []
    for label in R1_REPLICATES:
        _frame, values = endpoint(label)
        r1_values.append(values["dprime_deep"])
    methods = ("R1", "R9", "R10", "R11", "R12")
    for x, method in enumerate(methods):
        if method == "R1":
            values = np.asarray(r1_values)
            axis.scatter(np.full(len(values), x), values, color=colors[method], s=45)
            axis.errorbar(x, values.mean(), yerr=values.std(ddof=1), color=colors[method],
                          marker="D", ms=6, capsize=4, lw=1.4)
        else:
            value = float(summary.loc[summary["method"] == method, "dprime_deep"].iloc[0])
            axis.scatter([x], [value], color=colors[method], s=70, marker="D")
    axis.axhspan(min(r1_values), max(r1_values), color="#8D9498", alpha=0.12,
                 label="R1 observed seed range")
    axis.set_xticks(range(len(methods)),
                    ["R1\n3 seeds", "R9", "R10", "R11", "R12"])
    axis.set_ylabel("best-checkpoint mean d-prime")
    axis.set_title("B  All controls lie within R1 seed spread")
    axis.legend(frameon=False, fontsize=8, loc="lower left")

    axis = axes[1, 0]
    comparisons = ("R9-R1", "R10-R1", "R11-R1", "R12-R1")
    selected = unit_effects[unit_effects["comparison"].isin(comparisons)]
    order = (selected[selected["comparison"] == "R9-R1"]
             .sort_values("baseline_dprime")["unit_id"].tolist())
    positions = np.arange(len(order))
    for offset, comparison, color in (
            (-0.30, "R9-R1", colors["R9"]),
            (-0.10, "R10-R1", colors["R10"]),
            (0.10, "R11-R1", colors["R11"]),
            (0.30, "R12-R1", colors["R12"])):
        frame = selected[selected["comparison"] == comparison].set_index("unit_id").loc[order]
        axis.bar(positions + offset, frame["dprime_delta"], width=0.19,
                 color=color, label=comparison)
    axis.axhline(0, color="#555555", lw=1)
    axis.set_xticks(positions, [str(unit_id) for unit_id in order], rotation=45)
    axis.set_xlabel("GT unit (ordered by R1 d-prime)")
    axis.set_ylabel("paired endpoint d-prime delta")
    axis.set_title("C  Mean effects hide opposing unit changes")
    axis.legend(frameon=False, fontsize=8)

    axis = axes[1, 1]
    for row in summary.itertuples():
        runtime_h = row.code_ocean_runtime_s / 3600
        axis.scatter(runtime_h, row.dprime_deep, s=75, color=colors[row.method],
                     marker="D" if row.method != "R1" else "o", zorder=3)
        offset = (-28, 4) if row.method == "R10" else (5, 4)
        axis.annotate(row.method, (runtime_h, row.dprime_deep), xytext=offset,
                      textcoords="offset points", fontsize=8, color=colors[row.method])
    r1_seed_values = []
    for label in R1_REPLICATES:
        _frame, values = endpoint(label)
        r1_seed_values.append(values["dprime_deep"])
    axis.axhspan(min(r1_seed_values), max(r1_seed_values),
                 color="#8D9498", alpha=0.12)
    axis.set_xlabel("Code Ocean runtime (hours)")
    axis.set_ylabel("best-checkpoint mean d-prime")
    axis.set_title("D  Runtime versus endpoint detection")
    axis.set_xlim(2.2, 6.5)

    for axis in axes.flat:
        axis.grid(alpha=0.22, which="both")
    figure.suptitle("Integration and objective-preserving sampling controls",
                     fontweight="bold")
    figure.tight_layout()
    figure.savefig(FIGURES / "integration_controls.png", dpi=180)
    plt.close(figure)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    summary, comparison, unit_effects, phases, trajectories = build_tables()
    summary.to_csv(TABLES / "integration_controls_summary.csv", index=False)
    comparison.to_csv(TABLES / "integration_controls_comparison.csv", index=False)
    unit_effects.to_csv(TABLES / "integration_controls_unit_effects.csv", index=False)
    phases.to_csv(TABLES / "integration_controls_phases.csv", index=False)
    try:
        markdown = summary.to_markdown(index=False, floatfmt=".4f")
    except Exception:
        markdown = summary.to_csv(index=False)
    (TABLES / "integration_controls_summary.md").write_text(markdown.rstrip() + "\n")
    plot(summary, unit_effects, phases, trajectories)
    print(summary.to_string(index=False))
    print(f"wrote {FIGURES / 'integration_controls.png'}")


if __name__ == "__main__":
    main()