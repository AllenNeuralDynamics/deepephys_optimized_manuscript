#!/usr/bin/env python3
"""Render same-domain voltage and unit-template evolution over Full96 training."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "results" / "qualitative" / "learning_stages"
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "figures"
UNITS = (2143, 1143, 720, 1129)
STAGES = (
    (135, 34_560, "34.6k"),
    (459, 117_504, "117.5k"),
    (1_565, 400_640, "400.6k"),
    (61_903, 15_847_168, "15.85M"),
    (210_923, 53_996_288, "54.0M"),
)
ROUTES = {
    "om0": {
        "label": "Full96 omission0",
        "run": "ib_w96_om0_scale",
        "colors": ("#F0C5B2", "#E89B78", "#D97346", "#B84D27", "#7F2E18"),
    },
    "om1": {
        "label": "Full96 omission1",
        "run": "ib_w96_om1_scale",
        "colors": ("#B8DDE8", "#82BED0", "#4598B3", "#23748F", "#125064"),
    },
}
RAW_COLOR = "#4F5965"


def _scalar(data: np.lib.npyio.NpzFile, key: str) -> float:
    return float(np.asarray(data[key]).item())


def _artifact_path(run: str, step: int) -> Path:
    return SOURCE / f"{run}_s{step:08d}_examples.npz"


def _center_channels(values: np.ndarray) -> np.ndarray:
    return values - np.median(values, axis=1, keepdims=True)


def _center_template(values: np.ndarray) -> np.ndarray:
    return values - np.median(values[:10], axis=0, keepdims=True)


def _depth_ticks(axis, depths: np.ndarray, ylabel: str) -> None:
    unique_depths = np.unique(depths)
    if depths[0] > depths[-1]:
        unique_depths = unique_depths[::-1]
    selected = np.linspace(0, len(unique_depths) - 1, min(4, len(unique_depths))).round().astype(int)
    tick_depths = unique_depths[selected]
    positions = [np.flatnonzero(depths == depth).mean() for depth in tick_depths]
    axis.set_yticks(positions, [f"{depth:.0f}" for depth in tick_depths])
    axis.set_ylabel(ylabel)


def _local_template_contacts(values: np.ndarray, depths: np.ndarray, peak_index: int) -> tuple[np.ndarray, np.ndarray, int]:
    keep = np.flatnonzero(np.abs(depths - depths[peak_index]) <= 120.0)
    indices = keep[np.argsort(-depths[keep], kind="stable")]
    local_peak = int(np.flatnonzero(indices == peak_index)[0])
    return values[:, indices], depths[indices], local_peak


def _plot_stage_trace_bands(
    axis,
    time: np.ndarray,
    raw_trace: np.ndarray,
    stage_traces: list[np.ndarray],
    colors: tuple[str, ...],
    ylabel: str | None = "Training windows\n(stage p-p / raw p-p)",
) -> None:
    raw_scale = max(float(np.ptp(raw_trace)), 1e-9)
    offsets = np.arange(len(stage_traces) - 1, -1, -1, dtype=float) * 1.35
    labels = []
    for offset, trace, color, (_, _, stage_label) in zip(offsets, stage_traces, colors, STAGES):
        amplitude_ratio = float(np.ptp(trace) / raw_scale)
        axis.axhline(offset, color="#D8DCDF", lw=0.6, zorder=0)
        axis.plot(time, raw_trace / raw_scale + offset, color=RAW_COLOR, lw=0.9, alpha=0.35)
        axis.plot(time, trace / raw_scale + offset, color=color, lw=1.5)
        labels.append(f"{stage_label}  ({amplitude_ratio:.2f}x)")
    axis.axvline(0, color="#111111", lw=0.8, ls=":")
    axis.set_yticks(offsets, labels)
    axis.set_ylim(offsets[-1] - 0.85, offsets[0] + 0.85)
    axis.set_xlabel("Time from GT event (ms)")
    if ylabel:
        axis.set_ylabel(ylabel)
    else:
        axis.tick_params(axis="y", labelsize=8.5, pad=3)
    axis.grid(axis="x", alpha=0.2)


def _load() -> tuple[dict[str, list[np.lib.npyio.NpzFile]], dict[str, pd.DataFrame]]:
    paths = {
        route: [_artifact_path(config["run"], step) for step, _, _ in STAGES]
        for route, config in ROUTES.items()
    }
    missing = [path for route_paths in paths.values() for path in route_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("missing learning-stage artifacts: " + ", ".join(map(str, missing)))
    data = {route: [np.load(path) for path in route_paths] for route, route_paths in paths.items()}
    tables = {
        route: pd.read_csv(TABLES / f"{config['run']}_trajectory.csv")
        for route, config in ROUTES.items()
    }
    return data, tables


def _assert_shared_domain(data: dict[str, list[np.lib.npyio.NpzFile]], tables: dict[str, pd.DataFrame]) -> None:
    reference = data["om0"][0]
    exact_keys = ("exemplar_unit", "event_frame", "event_isolation_frames", "local_channels", "local_peak_index")
    numeric_keys = (
        "sampling_frequency", "overview_time_ms", "probe_depth_um", "local_time_ms",
        "local_depth_um", "raw_probe_uV", "raw_local_uV",
    )
    for route, stages in data.items():
        run = ROUTES[route]["run"]
        trajectory = tables[route].set_index("step")
        for (step, expected_windows, _), artifact in zip(STAGES, stages):
            for key in exact_keys:
                if not np.array_equal(reference[key], artifact[key]):
                    raise ValueError(f"{run} step {step} differs for {key}")
            for key in numeric_keys:
                if not np.allclose(reference[key], artifact[key], rtol=0, atol=1e-6):
                    raise ValueError(f"{run} step {step} differs for {key}")
            for unit_id in UNITS:
                for suffix in ("channels", "depth_um", "peak_index", "raw_template_uV"):
                    key = f"unit_{unit_id}_{suffix}"
                    if not np.allclose(reference[key], artifact[key], rtol=0, atol=1e-6):
                        raise ValueError(f"{run} step {step} differs for {key}")
            row = trajectory.loc[float(step)]
            metrics = pd.read_csv(_artifact_path(run, step).with_suffix(".csv"))
            if int(row["samples_seen"]) != expected_windows:
                raise ValueError(f"{run} step {step} has unexpected sample exposure")
            if not np.isclose(metrics["dprime_deep"].mean(), row["dprime_deep"], rtol=0, atol=1e-6):
                raise ValueError(f"{run} step {step} does not reproduce trajectory d-prime")


def plot_voltage_evolution(data: dict[str, list[np.lib.npyio.NpzFile]]) -> None:
    reference = data["om0"][0]
    raw_probe = _center_channels(reference["raw_probe_uV"])
    raw_local = _center_channels(reference["raw_local_uV"])
    probe_time = reference["overview_time_ms"]
    local_time = reference["local_time_ms"]
    probe_depth = reference["probe_depth_um"]
    local_depth = reference["local_depth_um"]
    peak_index = int(_scalar(reference, "local_peak_index"))
    probe_values = [raw_probe] + [
        _center_channels(artifact["denoised_probe_uV"])
        for stages in data.values() for artifact in stages
    ]
    local_values = [raw_local] + [
        _center_channels(artifact["denoised_local_uV"])
        for stages in data.values() for artifact in stages
    ]
    probe_limit = float(np.quantile(np.abs(np.concatenate([value.ravel() for value in probe_values])), 0.995))
    local_limit = float(np.quantile(np.abs(np.concatenate([value.ravel() for value in local_values])), 0.995))

    figure = plt.figure(figsize=(20.5, 15.5))
    outer = figure.add_gridspec(2, 1, hspace=0.34)
    column_titles = ("Raw",) + tuple(label for _, _, label in STAGES)
    for route_index, (route, config) in enumerate(ROUTES.items()):
        grid = outer[route_index].subgridspec(
            3, 7, width_ratios=(1, 1, 1, 1, 1, 1, 0.035),
            height_ratios=(1.0, 0.8, 0.62), hspace=0.42, wspace=0.22,
        )
        stage_probe = [raw_probe] + [_center_channels(artifact["denoised_probe_uV"]) for artifact in data[route]]
        stage_local = [raw_local] + [_center_channels(artifact["denoised_local_uV"]) for artifact in data[route]]
        probe_axes = [figure.add_subplot(grid[0, column]) for column in range(6)]
        local_axes = [figure.add_subplot(grid[1, column]) for column in range(6)]
        probe_colorbar = figure.add_subplot(grid[0, 6])
        local_colorbar = figure.add_subplot(grid[1, 6])
        trace_axis = figure.add_subplot(grid[2, :6])
        for column, (axis, values, title) in enumerate(zip(probe_axes, stage_probe, column_titles)):
            image = axis.imshow(
                values, aspect="auto", cmap="RdBu_r", vmin=-probe_limit, vmax=probe_limit,
                extent=(probe_time[0], probe_time[-1], len(probe_depth) - 0.5, -0.5),
                interpolation="nearest",
            )
            axis.axvline(0, color="#111111", lw=0.7, ls=":")
            axis.set_title(title if column == 0 else f"{title} windows", fontweight="bold", fontsize=10)
            axis.set_xlabel("Time from GT event (ms)")
            _depth_ticks(axis, probe_depth, "Probe depth (µm)" if column == 0 else "")
        figure.colorbar(image, cax=probe_colorbar, label="Voltage (µV; channel median removed)")
        for column, (axis, values) in enumerate(zip(local_axes, stage_local)):
            local_image = axis.imshow(
                values, aspect="auto", cmap="RdBu_r", vmin=-local_limit, vmax=local_limit,
                extent=(local_time[0], local_time[-1], len(local_depth) - 0.5, -0.5),
                interpolation="nearest",
            )
            axis.axvline(0, color="#111111", lw=0.7, ls=":")
            axis.set_xlabel("Time from GT event (ms)")
            _depth_ticks(axis, local_depth, "Contact depth (µm)" if column == 0 else "")
        figure.colorbar(local_image, cax=local_colorbar, label="Voltage (µV)")

        raw_trace = raw_local[peak_index] - np.median(raw_local[peak_index, :10])
        stage_traces = []
        for artifact in data[route]:
            values = _center_channels(artifact["denoised_local_uV"])[peak_index]
            values = values - np.median(values[:10])
            stage_traces.append(values)
        _plot_stage_trace_bands(
            trace_axis, local_time, raw_trace, stage_traces, config["colors"]
        )
        trace_axis.set_title(
            "Peak-channel stages over the same raw trace (gray)", loc="left", fontsize=10,
        )
        probe_axes[0].text(
            -0.28, 1.22, config["label"], transform=probe_axes[0].transAxes,
            fontsize=13, fontweight="bold", va="bottom",
        )
    figure.suptitle(
        "Same-event voltage evolves from a collapsed output to a structured spike estimate",
        fontweight="bold", y=0.995,
    )
    figure.subplots_adjust(top=0.96, bottom=0.055, left=0.055, right=0.95)
    figure.savefig(FIGURES / "learning_voltage_evolution.png", dpi=150)
    plt.close(figure)


def plot_unit_profile_evolution(data: dict[str, list[np.lib.npyio.NpzFile]]) -> None:
    reference = data["om0"][0]
    time = (np.arange(120) - 45) / 30.0
    column_titles = ("Raw",) + tuple(f"{label} windows" for _, _, label in STAGES)
    for route, config in ROUTES.items():
        figure = plt.figure(figsize=(21.5, 12.8))
        grid = figure.add_gridspec(
            len(UNITS), 8,
            width_ratios=(1, 1, 1, 1, 1, 1, 0.45, 1.4),
            hspace=0.68,
            wspace=0.3,
        )
        for row_index, unit_id in enumerate(UNITS):
            raw_full = _center_template(reference[f"unit_{unit_id}_raw_template_uV"])
            depths_full = reference[f"unit_{unit_id}_depth_um"]
            raw_peak = int(_scalar(reference, f"unit_{unit_id}_peak_index"))
            raw, depths, peak_index = _local_template_contacts(raw_full, depths_full, raw_peak)
            stage_templates = []
            for artifact in data[route]:
                template = _center_template(artifact[f"unit_{unit_id}_denoised_template_uV"])
                local, model_depths, model_peak = _local_template_contacts(template, depths_full, raw_peak)
                if not np.array_equal(depths, model_depths) or peak_index != model_peak:
                    raise ValueError(f"local contact mismatch for {route}, unit {unit_id}")
                stage_templates.append(local)
            raw_trace = raw[:, peak_index]
            limit = float(np.max(np.abs(raw)))
            heatmaps = [raw] + stage_templates
            raw_dprime = _scalar(reference, f"unit_{unit_id}_dprime_raw")
            for column, (values, title) in enumerate(zip(heatmaps, column_titles)):
                axis = figure.add_subplot(grid[row_index, column])
                axis.imshow(
                    values.T, aspect="auto", cmap="RdBu_r", vmin=-limit, vmax=limit,
                    extent=(time[0], time[-1], len(depths) - 0.5, -0.5), interpolation="nearest",
                )
                axis.axvline(0, color="#111111", lw=0.7, ls=":")
                if row_index == 0:
                    axis.set_title(title, fontweight="bold", fontsize=10)
                if column == 0:
                    metric = f"raw d′ {raw_dprime:.2f}"
                else:
                    artifact = data[route][column - 1]
                    dprime = _scalar(artifact, f"unit_{unit_id}_dprime_deep")
                    amplitude = np.ptp(values[:, peak_index]) / max(np.ptp(raw_trace), 1e-9)
                    metric = f"d′ {dprime:.2f} | amp {amplitude:.2f}"
                axis.set_xlabel(f"Time (ms)\n{metric}", fontsize=8.2)
                _depth_ticks(axis, depths, f"Unit {unit_id}\nDepth (µm)" if column == 0 else "")
            trace_axis = figure.add_subplot(grid[row_index, 7])
            _plot_stage_trace_bands(
                trace_axis,
                time,
                raw_trace,
                [values[:, peak_index] for values in stage_templates],
                config["colors"],
                ylabel=None,
            )
            if row_index == 0:
                trace_axis.set_title(
                    "Stage profiles over raw (gray)\nwindows (stage p-p / raw p-p)",
                    fontweight="bold",
                    fontsize=9.2,
                )
        figure.suptitle(
            f"{config['label']}: GT-unit templates emerge at different rates across unit strengths",
            fontweight="bold", y=0.995,
        )
        figure.subplots_adjust(top=0.95, bottom=0.065, left=0.07, right=0.98)
        figure.savefig(FIGURES / f"learning_unit_profile_evolution_{route}.png", dpi=150)
        plt.close(figure)


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    data, tables = _load()
    try:
        _assert_shared_domain(data, tables)
        plot_voltage_evolution(data)
        plot_unit_profile_evolution(data)
    finally:
        for stages in data.values():
            for artifact in stages:
                artifact.close()
    metadata = [
        json.loads(_artifact_path(config["run"], step).with_name(
            f"{config['run']}_s{step:08d}_examples_metadata.json"
        ).read_text())
        for config in ROUTES.values() for step, _, _ in STAGES
    ]
    print(f"wrote learning-evolution figures from {len(metadata)} validated artifacts")


if __name__ == "__main__":
    main()