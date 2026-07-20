#!/usr/bin/env python3
"""Summarize the matched R5 width, depth, and temporal channel-schedule follow-up."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SCORES = REPO / "results" / "scores"
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "figures"
BOOTSTRAP_SEED = 20260719
BOOTSTRAP_SAMPLES = 200_000
RAW_DPRIME = 4.496968895228467
WEAK_UNITS = (94, 664, 720, 1129)
OMISSION_COLORS = {0: "#dd8452", 1: "#4c72b0"}
MARKERS = {
    "base64_om0": "s",
    "sqrt2_om0": "X",
    "depth2_om0": "v",
    "growth15_om0": "o",
    "cap384_om0": "D",
    "full96_om0": "P",
    "sqrt2_om1": "X",
    "depth2_om1": "v",
    "growth15_om1": "o",
    "full96_om1": "P",
}


@dataclass(frozen=True)
class Configuration:
    key: str
    label: str
    display: str
    schedule: str
    omission: int
    parameters: int
    code_ocean_runtime_s: int
    nested_endpoint: bool
    color: str


CONFIGURATIONS = (
    Configuration(
        "base64_om0", "ib_r5_bs256", "base64 2x", "64-128-256-512", 0,
        3_149_704, 9_554, True, OMISSION_COLORS[0],
    ),
    Configuration(
        "sqrt2_om0", "ib_w96_gsqrt2_om0_s0", "base96 growth sqrt2",
        "96-136-192-272", 0, 1_830_896, 9_553, False, OMISSION_COLORS[0],
    ),
    Configuration(
        "depth2_om0", "ib_w96_d2_om0_s0", "base96 depth 2",
        "96-192-384", 0, 1_796_200, 9_596, False, OMISSION_COLORS[0],
    ),
    Configuration(
        "growth15_om0", "ib_w96_g15_om0_s0", "base96 growth 1.5x",
        "96-144-216-324", 0, 2_233_936, 9_915, False, OMISSION_COLORS[0],
    ),
    Configuration(
        "cap384_om0", "ib_w96_cap384_om0_s0", "base96 cap 384",
        "96-192-384-384", 0, 4_601_320, 14_281, False, OMISSION_COLORS[0],
    ),
    Configuration(
        "full96_om0", "ib_w96_om0_s0", "base96 full 2x",
        "96-192-384-768", 0, 6_962_152, 16_672, False, OMISSION_COLORS[0],
    ),
    Configuration(
        "sqrt2_om1", "ib_w96_gsqrt2_om1_s0", "base96 growth sqrt2",
        "96-136-192-272", 1, 1_832_432, 9_654, False, OMISSION_COLORS[1],
    ),
    Configuration(
        "depth2_om1", "ib_w96_d2_om1_s0", "base96 depth 2",
        "96-192-384", 1, 1_797_736, 9_800, False, OMISSION_COLORS[1],
    ),
    Configuration(
        "growth15_om1", "ib_w96_g15_om1_s0", "base96 growth 1.5x",
        "96-144-216-324", 1, 2_235_472, 10_249, False, OMISSION_COLORS[1],
    ),
    Configuration(
        "full96_om1", "ib_w96_om1_s0", "base96 full 2x",
        "96-192-384-768", 1, 6_963_688, 16_610, False, OMISSION_COLORS[1],
    ),
)
CONFIG_BY_KEY = {configuration.key: configuration for configuration in CONFIGURATIONS}


def endpoint_paths(configuration: Configuration) -> tuple[Path, Path]:
    if configuration.nested_endpoint:
        prefix = SCORES / configuration.label / f"{configuration.label}_best"
    else:
        prefix = SCORES / configuration.label
    return Path(f"{prefix}_dprime.csv"), Path(f"{prefix}_diag.csv")


def load_endpoint(configuration: Configuration) -> pd.DataFrame:
    dprime_path, diag_path = endpoint_paths(configuration)
    dprime = pd.read_csv(dprime_path)
    diag = pd.read_csv(diag_path)
    if len(dprime) != 10 or len(diag) != 10:
        raise ValueError(f"{configuration.label}: expected 10 d-prime and diagnostic rows")
    if dprime["unit_id"].nunique() != 10 or diag["unit_id"].nunique() != 10:
        raise ValueError(f"{configuration.label}: unit IDs are not unique")
    metrics = dprime[[
        "unit_id", "dprime_deep", "dprime_deep_fixed", "dprime_raw", "snr_deep",
    ]].merge(
        diag[[
            "unit_id", "amp_ratio", "fwhm_ratio", "temporal_cos", "spatial_cos",
        ]],
        on="unit_id",
        how="inner",
        validate="one_to_one",
    )
    if len(metrics) != 10 or not np.isfinite(metrics.drop(columns="unit_id")).all().all():
        raise ValueError(f"{configuration.label}: incomplete or non-finite endpoint metrics")
    return metrics.set_index("unit_id").sort_index()


def validate_provenance() -> None:
    with (REPO / "results" / "runs.csv").open(newline="") as handle:
        ledger = {row["label"]: row for row in csv.DictReader(handle)}
    for configuration in CONFIGURATIONS:
        if configuration.nested_endpoint:
            continue
        row = ledger[configuration.label]
        if (row["state"], row["ckpt_downloaded"], row["scored"]) != (
                "completed", "yes", "yes"):
            raise ValueError(f"{configuration.label}: ledger is not complete")
        parameter_match = re.search(r"(\d+) params", row["notes"])
        runtime_match = re.search(r"CO succeeded in (\d+) s", row["notes"])
        if parameter_match is None or int(parameter_match.group(1)) != configuration.parameters:
            raise ValueError(f"{configuration.label}: parameter provenance mismatch")
        if runtime_match is None or int(runtime_match.group(1)) != configuration.code_ocean_runtime_s:
            raise ValueError(f"{configuration.label}: runtime provenance mismatch")

    naf_summary = pd.read_csv(TABLES / "naf_control_summary.csv")
    base64 = naf_summary.loc[naf_summary["label"] == "ib_r5_bs256"].iloc[0]
    if int(base64["model_params"]) != CONFIG_BY_KEY["base64_om0"].parameters:
        raise ValueError("base64 R5 parameter provenance mismatch")


def paired_effect(
        frames: dict[str, pd.DataFrame], left: str, right: str, seed_offset: int,
) -> dict[str, float | int | str]:
    delta = (
        frames[left]["dprime_deep"] - frames[right]["dprime_deep"]
    ).to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    indices = rng.integers(0, len(delta), size=(BOOTSTRAP_SAMPLES, len(delta)))
    bootstrap = delta[indices].mean(axis=1)
    low, high = np.quantile(bootstrap, (0.025, 0.975))
    return {
        "comparison": f"{left}_minus_{right}",
        "left": left,
        "right": right,
        "mean_dprime_delta": float(delta.mean()),
        "units_positive": int(np.count_nonzero(delta > 0)),
        "units_total": int(len(delta)),
        "paired_unit_bootstrap_95_low": float(low),
        "paired_unit_bootstrap_95_high": float(high),
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED + seed_offset,
    }


def markdown_table(frame: pd.DataFrame, digits: int) -> str:
    def render(value) -> str:
        if pd.isna(value):
            return "—"
        if isinstance(value, (float, np.floating)):
            return f"{value:.{digits}f}"
        return str(value)

    header = "| " + " | ".join(str(column) for column in frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = [
        "| " + " | ".join(render(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    ]
    return "\n".join((header, rule, *rows)) + "\n"


def build_tables() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    validate_provenance()
    frames = {
        configuration.key: load_endpoint(configuration)
        for configuration in CONFIGURATIONS
    }
    baseline = frames["base64_om0"]
    full_runtime = CONFIG_BY_KEY["full96_om0"].code_ocean_runtime_s
    rows = []
    for configuration in CONFIGURATIONS:
        endpoint = frames[configuration.key]
        row = {
            "key": configuration.key,
            "label": configuration.label,
            "display": configuration.display,
            "schedule": configuration.schedule,
            "omission": configuration.omission,
            "parameters": configuration.parameters,
            "code_ocean_runtime_s": configuration.code_ocean_runtime_s,
            "code_ocean_runtime_h": configuration.code_ocean_runtime_s / 3600,
            "runtime_reduction_vs_full96_om0": (
                1 - configuration.code_ocean_runtime_s / full_runtime
                if configuration.omission == 0 else np.nan
            ),
        }
        for metric in (
                "dprime_deep", "dprime_deep_fixed", "dprime_raw", "snr_deep",
                "amp_ratio", "fwhm_ratio", "temporal_cos", "spatial_cos"):
            row[metric] = float(endpoint[metric].mean())
        weak_mask = endpoint.index.isin(WEAK_UNITS)
        if int(weak_mask.sum()) != len(WEAK_UNITS):
            raise ValueError(f"{configuration.label}: weak-unit subgroup is incomplete")
        row["weak_unit_dprime"] = float(endpoint.loc[weak_mask, "dprime_deep"].mean())
        row["other_six_dprime"] = float(endpoint.loc[~weak_mask, "dprime_deep"].mean())
        delta = endpoint["dprime_deep"] - baseline["dprime_deep"]
        row["dprime_delta_vs_base64"] = float(delta.mean())
        row["dprime_percent_vs_base64"] = (
            100 * float(delta.mean()) / float(baseline["dprime_deep"].mean())
        )
        row["weak_dprime_delta_vs_base64"] = float(delta.loc[weak_mask].mean())
        row["other_six_dprime_delta_vs_base64"] = float(delta.loc[~weak_mask].mean())
        rows.append(row)
    summary = pd.DataFrame(rows)

    comparisons = (
        ("sqrt2_om0", "base64_om0"),
        ("depth2_om0", "base64_om0"),
        ("growth15_om0", "base64_om0"),
        ("cap384_om0", "base64_om0"),
        ("full96_om0", "base64_om0"),
        ("growth15_om0", "sqrt2_om0"),
        ("cap384_om0", "growth15_om0"),
        ("full96_om0", "cap384_om0"),
        ("depth2_om0", "sqrt2_om0"),
        ("sqrt2_om1", "sqrt2_om0"),
        ("depth2_om1", "depth2_om0"),
        ("growth15_om1", "growth15_om0"),
        ("full96_om1", "full96_om0"),
        ("depth2_om1", "sqrt2_om1"),
        ("growth15_om1", "sqrt2_om1"),
        ("full96_om1", "growth15_om1"),
    )
    effects = pd.DataFrame([
        paired_effect(frames, left, right, seed_offset)
        for seed_offset, (left, right) in enumerate(comparisons)
    ])
    return summary, effects, frames


def plot(summary: pd.DataFrame, effects: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(13.2, 8.8))

    omission0 = summary.loc[summary["omission"] == 0].set_index("key")
    order = (
        "base64_om0", "sqrt2_om0", "depth2_om0", "growth15_om0", "cap384_om0",
        "full96_om0",
    )
    axis = axes[0, 0]
    for key in order:
        row = omission0.loc[key]
        configuration = CONFIG_BY_KEY[key]
        axis.scatter(
            row["code_ocean_runtime_h"], row["dprime_deep"],
            s=55 + configuration.parameters / 55_000,
            color=configuration.color, marker=MARKERS[key], edgecolor="white",
            linewidth=0.8, zorder=3,
        )
        offsets = {
            "base64_om0": (-70, 14),
            "sqrt2_om0": (7, -15),
            "depth2_om0": (8, -8),
            "growth15_om0": (7, 5),
            "cap384_om0": (7, 5),
            "full96_om0": (-91, 7),
        }
        axis.annotate(
            configuration.display, (row["code_ocean_runtime_h"], row["dprime_deep"]),
            xytext=offsets[key], textcoords="offset points", fontsize=8,
        )
    axis.plot(
        omission0.loc[[
            "base64_om0", "sqrt2_om0", "growth15_om0", "cap384_om0",
            "full96_om0",
        ], "code_ocean_runtime_h"],
        omission0.loc[[
            "base64_om0", "sqrt2_om0", "growth15_om0", "cap384_om0",
            "full96_om0",
        ], "dprime_deep"],
        color="#9AA0A3", lw=1.0, zorder=1,
    )
    axis.axhline(RAW_DPRIME, color="#333333", ls=":", lw=1.1, label="raw data")
    axis.set_xlabel("Code Ocean end-to-end runtime (hours)")
    axis.set_ylabel("mean benchmark d′")
    axis.set_title("A  Depth and channel schedule change cost and d′")
    axis.set_ylim(omission0["dprime_deep"].min() - 0.018, RAW_DPRIME + 0.01)
    axis.legend(frameon=False, fontsize=8, loc="upper left")

    axis = axes[0, 1]
    comparison_keys = (
        "sqrt2_om0_minus_base64_om0",
        "depth2_om0_minus_base64_om0",
        "growth15_om0_minus_base64_om0",
        "cap384_om0_minus_base64_om0",
        "full96_om0_minus_base64_om0",
    )
    effect_index = effects.set_index("comparison")
    labels = ("growth sqrt2", "depth 2", "growth 1.5x", "cap 384", "full 2x")
    colors = (OMISSION_COLORS[0],) * len(labels)
    for position, (comparison, color) in enumerate(zip(comparison_keys, colors)):
        row = effect_index.loc[comparison]
        mean = row["mean_dprime_delta"]
        axis.errorbar(
            position, mean,
            yerr=[[mean - row["paired_unit_bootstrap_95_low"]],
                  [row["paired_unit_bootstrap_95_high"] - mean]],
            fmt="o", color=color, capsize=5, ms=7, lw=1.7,
        )
        axis.text(position, mean + 0.006, f"{mean:+.3f}", ha="center", fontsize=8)
    axis.axhline(0, color="#555555", lw=1)
    axis.set_xticks(range(len(labels)), labels)
    axis.set_ylabel("paired mean Δd′ versus base64 R5")
    axis.set_title("B  Paired effects versus base64 R5")
    axis.text(
        0.02, 0.04, "95% paired-unit bootstrap intervals\n10 fixed units; not biological replicates",
        transform=axis.transAxes, fontsize=8, va="bottom",
        bbox={"facecolor": "white", "edgecolor": "0.85", "alpha": 0.9},
    )

    axis = axes[1, 0]
    for schedule, keys in (
            ("growth sqrt2", ("sqrt2_om0", "sqrt2_om1")),
            ("depth 2", ("depth2_om0", "depth2_om1")),
            ("growth 1.5x", ("growth15_om0", "growth15_om1")),
            ("full 2x", ("full96_om0", "full96_om1"))):
        rows = summary.set_index("key").loc[list(keys)]
        marker = MARKERS[keys[0]]
        axis.plot((0, 1), rows["dprime_deep"], color="#777777", lw=1.5)
        axis.scatter((0, 1), rows["dprime_deep"], marker=marker, s=55,
                     color=(OMISSION_COLORS[0], OMISSION_COLORS[1]), zorder=3)
    axis.set_xticks((0, 1), ("omission0", "omission1"))
    axis.set_ylabel("mean benchmark d′")
    axis.set_title("C  Omission1 raises the all-unit d′ mean")
    axis.legend(handles=[
         Line2D([], [], marker="X", color="none", markerfacecolor="#777777",
             label="growth sqrt2"),
        Line2D([], [], marker="v", color="none", markerfacecolor="#777777",
               label="depth 2"),
        Line2D([], [], marker="o", color="none", markerfacecolor="#777777",
               label="growth 1.5x"),
        Line2D([], [], marker="P", color="none", markerfacecolor="#777777",
               label="full 2x"),
    ], frameon=False, fontsize=8)

    axis = axes[1, 1]
    for schedule, keys in (
            ("growth sqrt2", ("sqrt2_om0", "sqrt2_om1")),
            ("depth 2", ("depth2_om0", "depth2_om1")),
            ("growth 1.5x", ("growth15_om0", "growth15_om1")),
            ("full 2x", ("full96_om0", "full96_om1"))):
        rows = summary.set_index("key").loc[list(keys)]
        marker = MARKERS[keys[0]]
        axis.plot((0, 1), rows["weak_unit_dprime"], color="#777777", lw=1.5)
        axis.scatter((0, 1), rows["weak_unit_dprime"], marker=marker, s=55,
                     color=(OMISSION_COLORS[0], OMISSION_COLORS[1]), zorder=3)
    axis.set_xticks((0, 1), ("omission0", "omission1"))
    axis.set_ylabel("mean d′ for four weak units")
    axis.set_title("D  Omission1 lowers weak-unit d′")
    axis.legend(handles=[
         Line2D([], [], marker="X", color="none", markerfacecolor="#777777",
             label="growth sqrt2"),
        Line2D([], [], marker="v", color="none", markerfacecolor="#777777",
               label="depth 2"),
        Line2D([], [], marker="o", color="none", markerfacecolor="#777777",
               label="growth 1.5x"),
        Line2D([], [], marker="P", color="none", markerfacecolor="#777777",
               label="full 2x"),
    ], frameon=False, fontsize=8)

    for axis in axes.flat:
        axis.grid(alpha=0.22)
    figure.suptitle("Matched R5 width, depth, and channel-schedule follow-up", fontweight="bold")
    figure.tight_layout()
    figure.savefig(FIGURES / "width_schedule_followup.png", dpi=180)
    plt.close(figure)


def write_tables(
    summary: pd.DataFrame, effects: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
) -> None:
    summary.to_csv(TABLES / "width_schedule_summary.csv", index=False)
    effects.to_csv(TABLES / "width_schedule_paired_effects.csv", index=False)
    presentation = summary[[
        "display", "schedule", "omission", "parameters", "code_ocean_runtime_h",
        "dprime_deep", "dprime_deep_fixed", "dprime_delta_vs_base64", "amp_ratio",
        "weak_unit_dprime", "weak_dprime_delta_vs_base64", "fwhm_ratio",
        "temporal_cos", "spatial_cos",
    ]]
    summary_markdown = markdown_table(presentation, 4)
    effects_markdown = markdown_table(effects, 5)
    (TABLES / "width_schedule_summary.md").write_text(summary_markdown)
    (TABLES / "width_schedule_paired_effects.md").write_text(
        effects_markdown
    )

    display = {
        "base64_om0": "base64 R5 om0",
        "sqrt2_om0": "sqrt2 om0",
        "depth2_om0": "depth2 om0",
        "growth15_om0": "g1.5 om0",
        "cap384_om0": "cap384 om0",
        "full96_om0": "full96 om0",
        "sqrt2_om1": "sqrt2 om1",
        "depth2_om1": "depth2 om1",
        "growth15_om1": "g1.5 om1",
        "full96_om1": "full96 om1",
    }
    unit_order = frames["base64_om0"]["dprime_raw"].sort_values(ascending=False).index

    def per_unit(metric: str, delta_from_raw: bool, stem: str) -> None:
        matrix = pd.DataFrame({
            "unit_id": unit_order,
            "raw dprime": frames["base64_om0"].loc[unit_order, "dprime_raw"].to_numpy(),
        })
        for key, name in display.items():
            values = frames[key].loc[unit_order, metric]
            if delta_from_raw:
                values = values - frames[key].loc[unit_order, "dprime_raw"]
            matrix[name] = values.to_numpy()
        mean_row = {"unit_id": "mean", "raw dprime": np.nan}
        mean_row.update({name: float(matrix[name].mean()) for name in display.values()})
        matrix = pd.concat([matrix, pd.DataFrame([mean_row])], ignore_index=True)
        matrix.to_csv(TABLES / f"{stem}.csv", index=False)
        (TABLES / f"{stem}.md").write_text(markdown_table(matrix, 3))

    per_unit("amp_ratio", False, "width_schedule_perunit_amp")
    per_unit("dprime_deep", True, "width_schedule_perunit_dprime_delta")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    summary, effects, frames = build_tables()
    write_tables(summary, effects, frames)
    plot(summary, effects)
    print(summary.to_string(index=False))
    print(effects.to_string(index=False))
    print(f"wrote {FIGURES / 'width_schedule_followup.png'}")


if __name__ == "__main__":
    main()