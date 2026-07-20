#!/usr/bin/env python3
"""Render qualitative benchmark, attenuation, and d-prime explanation figures."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
QUALITATIVE = REPO / "results" / "qualitative"
ARTIFACTS = {
    "om0": QUALITATIVE / "full96_om0_examples.npz",
    "om1": QUALITATIVE / "full96_om1_examples.npz",
    "origdi": QUALITATIVE / "origdi_s0_examples.npz",
}
METADATA = {
    key: path.with_name(f"{path.stem}_metadata.json")
    for key, path in ARTIFACTS.items()
}
FIGURES = REPO / "figures"
UNITS = (2143, 1143, 720, 1129)
RAW_COLOR = "#4F5965"
MODEL_COLORS = {
    "om0": "#D26A3A",
    "om1": "#2A7F9E",
    "origdi": "#6F5A8A",
}
MODEL_LABELS = {
    "om0": "Full96 omission0",
    "om1": "Full96 omission1",
    "origdi": "Original DI",
}
HIT_COLOR = "#C84A44"
BACKGROUND_COLOR = "#8D969F"


def _scalar(data, key):
    return np.asarray(data[key]).item()


def _center_channels(values: np.ndarray) -> np.ndarray:
    return values - np.median(values, axis=1, keepdims=True)


def _center_template(values: np.ndarray) -> np.ndarray:
    baseline = np.median(values[:10], axis=0, keepdims=True)
    return values - baseline


def _depth_ticks(axis, depths: np.ndarray, label: str = "Probe depth (µm)") -> None:
    unique_depths = np.unique(depths)
    if depths[0] > depths[-1]:
        unique_depths = unique_depths[::-1]
    selected = np.linspace(0, len(unique_depths) - 1, min(4, len(unique_depths))).round().astype(int)
    tick_depths = unique_depths[selected]
    positions = [np.flatnonzero(depths == depth).mean() for depth in tick_depths]
    axis.set_yticks(positions, [f"{depth:.0f}" for depth in tick_depths])
    axis.set_ylabel(label)


def _local_template_contacts(raw, denoised, depths, peak_index, radius_um=120.0):
    keep = np.flatnonzero(np.abs(depths - depths[peak_index]) <= radius_um)
    order = np.argsort(-depths[keep], kind="stable")
    indices = keep[order]
    local_peak_index = int(np.flatnonzero(indices == peak_index)[0])
    return raw[:, indices], denoised[:, indices], depths[indices], local_peak_index


def _assert_shared_domain(data_by_model) -> None:
    reference = data_by_model["om0"]
    exact_keys = (
        "exemplar_unit",
        "event_frame",
        "event_isolation_frames",
        "local_channels",
        "local_peak_index",
    )
    numeric_keys = (
        "sampling_frequency",
        "overview_time_ms",
        "probe_depth_um",
        "local_time_ms",
        "local_depth_um",
        "raw_probe_uV",
        "raw_local_uV",
    )
    for model_key, data in data_by_model.items():
        if model_key == "om0":
            continue
        for key in exact_keys:
            if not np.array_equal(reference[key], data[key]):
                raise ValueError(f"{model_key} differs from omission0 for {key}")
        for key in numeric_keys:
            if not np.allclose(reference[key], data[key], rtol=0, atol=1e-6):
                raise ValueError(f"{model_key} differs from omission0 for {key}")
        for unit_id in UNITS:
            for suffix in ("channels", "depth_um", "peak_index", "raw_template_uV"):
                key = f"unit_{unit_id}_{suffix}"
                if not np.allclose(reference[key], data[key], rtol=0, atol=1e-6):
                    raise ValueError(f"{model_key} differs from omission0 for {key}")


def plot_probe_overview(data_by_model) -> None:
    reference = data_by_model["om0"]
    raw_probe = _center_channels(reference["raw_probe_uV"])
    raw_local = _center_channels(reference["raw_local_uV"])
    probes = {"raw": raw_probe}
    locals_ = {"raw": raw_local}
    for model_key, data in data_by_model.items():
        probes[model_key] = _center_channels(data["denoised_probe_uV"])
        locals_[model_key] = _center_channels(data["denoised_local_uV"])
    overview_time = reference["overview_time_ms"]
    local_time = reference["local_time_ms"]
    probe_depth = reference["probe_depth_um"]
    local_depth = reference["local_depth_um"]
    peak_index = int(_scalar(reference, "local_peak_index"))
    exemplar_unit = int(_scalar(reference, "exemplar_unit"))

    figure = plt.figure(figsize=(16.8, 11.2))
    grid = figure.add_gridspec(3, 1, height_ratios=(1.0, 0.88, 0.58), hspace=0.38)
    overview_grid = grid[0].subgridspec(1, 5, width_ratios=(1, 1, 1, 1, 0.035), wspace=0.22)
    detail_grid = grid[1].subgridspec(1, 5, width_ratios=(1, 1, 1, 1, 0.035), wspace=0.22)
    overview_axes = [figure.add_subplot(overview_grid[0, index]) for index in range(4)]
    detail_axes = [figure.add_subplot(detail_grid[0, index]) for index in range(4)]
    overview_colorbar = figure.add_subplot(overview_grid[0, 4])
    local_colorbar = figure.add_subplot(detail_grid[0, 4])
    trace_axis = figure.add_subplot(grid[2, 0])
    overview_limit = np.quantile(
        np.abs(np.concatenate([values.ravel() for values in probes.values()])), 0.995
    )
    local_limit = np.quantile(
        np.abs(np.concatenate([values.ravel() for values in locals_.values()])), 0.995
    )
    display_columns = (
        ("raw", "A", "Raw AP-band"),
        ("om0", "B", MODEL_LABELS["om0"]),
        ("om1", "C", MODEL_LABELS["om1"]),
        ("origdi", "D", MODEL_LABELS["origdi"]),
    )
    for axis, (model_key, panel, title) in zip(overview_axes, display_columns):
        image = axis.imshow(
            probes[model_key],
            aspect="auto",
            cmap="RdBu_r",
            vmin=-overview_limit,
            vmax=overview_limit,
            extent=(overview_time[0], overview_time[-1], len(probe_depth) - 0.5, -0.5),
            interpolation="nearest",
        )
        axis.axvline(0, color="#111111", lw=0.9, ls=":")
        axis.set_title(f"{panel}  {title}", loc="left", fontweight="bold")
        axis.set_xlabel("Time from GT event (ms)")
        _depth_ticks(axis, probe_depth, "Probe depth (µm)" if model_key == "raw" else "")
    colorbar = figure.colorbar(image, cax=overview_colorbar)
    colorbar.set_label("Voltage (µV; channel median removed)")

    for axis, (model_key, panel, title) in zip(
        detail_axes,
        (
            ("raw", "E", f"Raw close-up, unit {exemplar_unit}"),
            ("om0", "F", "Full96 omission0"),
            ("om1", "G", "Full96 omission1"),
            ("origdi", "H", "Original DI"),
        ),
    ):
        local_image = axis.imshow(
            locals_[model_key],
            aspect="auto",
            cmap="RdBu_r",
            vmin=-local_limit,
            vmax=local_limit,
            extent=(local_time[0], local_time[-1], len(local_depth) - 0.5, -0.5),
            interpolation="nearest",
        )
        axis.axvline(0, color="#111111", lw=0.9, ls=":")
        axis.set_title(f"{panel}  {title}", loc="left", fontweight="bold")
        axis.set_xlabel("Time from GT event (ms)")
        _depth_ticks(axis, local_depth, "Contact depth (µm)" if model_key == "raw" else "")
    local_scale = figure.colorbar(local_image, cax=local_colorbar)
    local_scale.ax.set_title("µV", pad=6)

    raw_trace = raw_local[peak_index] - np.median(raw_local[peak_index, :10])
    trace_axis.plot(local_time, raw_trace, color=RAW_COLOR, lw=1.4, label="Raw")
    for model_key, data in data_by_model.items():
        trace = locals_[model_key][peak_index]
        trace = trace - np.median(trace[:10])
        trace_axis.plot(
            local_time, trace, color=MODEL_COLORS[model_key], lw=1.6,
            label=MODEL_LABELS[model_key],
        )
    trace_axis.axvline(0, color="#111111", lw=0.9, ls=":")
    trace_axis.axhline(0, color="#B7BDC2", lw=0.7)
    trace_axis.set_title("I  Peak-channel voltage for the same event", loc="left", fontweight="bold")
    trace_axis.set_xlabel("Time from GT event (ms)")
    trace_axis.set_ylabel("Voltage (µV)")
    trace_axis.legend(frameon=False, ncol=4, loc="upper right")
    trace_axis.grid(alpha=0.2)
    figure.suptitle(
        "The frozen hybrid benchmark before and after DeepInterpolation",
        fontweight="bold",
        y=0.99,
    )
    figure.subplots_adjust(top=0.94, right=0.96, left=0.065, bottom=0.07)
    figure.savefig(FIGURES / "benchmark_raw_denoised_example.png", dpi=110)
    plt.close(figure)


def plot_unit_attenuation(data_by_model) -> None:
    time = (np.arange(120) - 45) / 30.0
    figure = plt.figure(figsize=(18.6, 11.8))
    grid = figure.add_gridspec(
        len(UNITS), 7,
        width_ratios=(1, 1, 1, 1, 0.035, 0.08, 1.25),
        hspace=0.65,
        wspace=0.42,
    )
    axes = np.empty((len(UNITS), 5), dtype=object)
    colorbar_axes = []
    for row_index in range(len(UNITS)):
        for column in range(4):
            axes[row_index, column] = figure.add_subplot(grid[row_index, column])
        colorbar_axes.append(figure.add_subplot(grid[row_index, 4]))
        axes[row_index, 4] = figure.add_subplot(grid[row_index, 6])
    reference = data_by_model["om0"]
    for row_index, unit_id in enumerate(UNITS):
        raw = _center_template(reference[f"unit_{unit_id}_raw_template_uV"])
        templates = {
            model_key: _center_template(data[f"unit_{unit_id}_denoised_template_uV"])
            for model_key, data in data_by_model.items()
        }
        depths = reference[f"unit_{unit_id}_depth_um"]
        peak_index = int(_scalar(reference, f"unit_{unit_id}_peak_index"))
        raw, om0, depths, peak_index = _local_template_contacts(
            raw, templates["om0"], depths, peak_index
        )
        keep_depths = depths.copy()
        templates["om0"] = om0
        for model_key in ("om1", "origdi"):
            _, local_template, model_depths, model_peak = _local_template_contacts(
                _center_template(reference[f"unit_{unit_id}_raw_template_uV"]),
                templates[model_key],
                reference[f"unit_{unit_id}_depth_um"],
                int(_scalar(reference, f"unit_{unit_id}_peak_index")),
            )
            if not np.array_equal(model_depths, keep_depths) or model_peak != peak_index:
                raise ValueError(f"local contact mismatch for unit {unit_id}, {model_key}")
            templates[model_key] = local_template
        raw_trace = raw[:, peak_index]
        raw_dprime = float(_scalar(reference, f"unit_{unit_id}_dprime_raw"))
        metric_labels = {0: f"raw d′ {raw_dprime:.2f}"}
        for column, model_key in enumerate(("om0", "om1", "origdi"), start=1):
            trace = templates[model_key][:, peak_index]
            deep_dprime = float(
                _scalar(data_by_model[model_key], f"unit_{unit_id}_dprime_deep")
            )
            amplitude_ratio = np.ptp(trace) / max(np.ptp(raw_trace), 1e-9)
            metric_labels[column] = f"d′ {deep_dprime:.2f} | amp {amplitude_ratio:.2f}"
        limit = np.max(np.abs(raw))
        for column, values, title in (
            (0, raw, "Raw"),
            (1, templates["om0"], "Full96 omission0"),
            (2, templates["om1"], "Full96 omission1"),
            (3, templates["origdi"], "Original DI"),
        ):
            image = axes[row_index, column].imshow(
                values.T,
                aspect="auto",
                cmap="RdBu_r",
                vmin=-limit,
                vmax=limit,
                extent=(time[0], time[-1], len(depths) - 0.5, -0.5),
                interpolation="nearest",
            )
            axes[row_index, column].axvline(0, color="#111111", lw=0.7, ls=":")
            if row_index == 0:
                axes[row_index, column].set_title(title, fontweight="bold")
            axes[row_index, column].set_xlabel(
                f"Time (ms)\n{metric_labels[column]}", fontsize=8.5
            )
            _depth_ticks(
                axes[row_index, column], depths,
                "Contact depth (µm)" if column == 0 else "",
            )
        scale = figure.colorbar(image, cax=colorbar_axes[row_index])
        scale.ax.set_title("µV", pad=5, fontsize=8)

        trace_axis = axes[row_index, 4]
        trace_axis.plot(time, raw_trace, color=RAW_COLOR, lw=1.25, label="Raw")
        for model_key, data in data_by_model.items():
            trace = templates[model_key][:, peak_index]
            trace_axis.plot(
                time, trace, color=MODEL_COLORS[model_key], lw=1.5,
                label=MODEL_LABELS[model_key],
            )
        trace_axis.axvline(0, color="#111111", lw=0.7, ls=":")
        trace_axis.axhline(0, color="#B7BDC2", lw=0.7)
        trace_axis.set_title(
            f"Unit {unit_id}  |  peak-channel templates",
            loc="left",
            fontweight="bold",
        )
        trace_axis.set_xlabel("Time (ms)")
        trace_axis.set_ylabel("Voltage (µV)")
        trace_axis.grid(alpha=0.2)
    axes[0, 4].legend(frameon=False, loc="upper right", fontsize=8)
    figure.suptitle(
        "Weak GT units are attenuated more than strong units",
        fontweight="bold",
        y=0.995,
    )
    figure.subplots_adjust(top=0.94, right=0.97, left=0.06, bottom=0.06)
    figure.savefig(FIGURES / "unit_attenuation_examples.png", dpi=170)
    plt.close(figure)


def _normalized_scores(hit: np.ndarray, background: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    pooled = np.sqrt(0.5 * (hit.var() + background.var()))
    pooled = max(float(pooled), 1e-9)
    return (hit - background.mean()) / pooled, (background - background.mean()) / pooled, pooled


def plot_dprime_explainer(data) -> None:
    units = (2143, 1129)
    figure, axes = plt.subplots(2, 2, figsize=(12.4, 7.8), sharey=False)
    for row_index, unit_id in enumerate(units):
        domain_values = []
        for domain in ("raw", "denoised"):
            hits = data[f"unit_{unit_id}_{domain}_hit_scores"]
            background = data[f"unit_{unit_id}_{domain}_background_scores"]
            domain_values.append(_normalized_scores(hits, background)[:2])
        low = min(np.quantile(values, 0.005) for pair in domain_values for values in pair)
        high = max(np.quantile(values, 0.995) for pair in domain_values for values in pair)
        bins = np.linspace(low, high, 34)
        for column, (domain, title) in enumerate(
            (("raw", "Raw"), ("denoised", "Denoised"))
        ):
            hit, background = domain_values[column]
            axis = axes[row_index, column]
            axis.hist(background, bins=bins, density=True, color=BACKGROUND_COLOR, alpha=0.62, label="background")
            axis.hist(hit, bins=bins, density=True, color=HIT_COLOR, alpha=0.58, label="GT events")
            axis.axvline(background.mean(), color="#555555", lw=1.2)
            axis.axvline(hit.mean(), color="#A52A2A", lw=1.3)
            dprime = float(_scalar(data, f"unit_{unit_id}_{'dprime_raw' if domain == 'raw' else 'dprime_deep'}"))
            axis.text(
                0.97,
                0.9,
                f"d′ = {dprime:.2f}",
                transform=axis.transAxes,
                ha="right",
                va="top",
                fontweight="bold",
                bbox={"facecolor": "white", "edgecolor": "0.85", "alpha": 0.9},
            )
            axis.set_title(f"{'ABCD'[row_index * 2 + column]}  Unit {unit_id}, {title}", loc="left", fontweight="bold")
            axis.set_xlabel("Matched-filter score (pooled-SD units)")
            axis.set_ylabel("Density")
            axis.grid(alpha=0.18)
    axes[0, 0].legend(frameon=False)
    figure.text(
        0.5,
        0.955,
        r"$d'=(\mu_{GT}-\mu_{bg})/\sqrt{(\sigma^2_{GT}+\sigma^2_{bg})/2}$",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.015,
        "All 100 GT-event scores and 200 spike-excluded background scores enter through their means and variances; no threshold, peak count, or extreme-value statistic is used.",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    figure.subplots_adjust(top=0.9, bottom=0.1, hspace=0.38, wspace=0.28)
    figure.savefig(FIGURES / "dprime_score_distributions.png", dpi=190)
    plt.close(figure)


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    missing = [path for path in (*ARTIFACTS.values(), *METADATA.values()) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "qualitative source data are missing: " + ", ".join(str(path) for path in missing)
        )
    loaded = {key: np.load(path) for key, path in ARTIFACTS.items()}
    try:
        _assert_shared_domain(loaded)
        plot_probe_overview(loaded)
        plot_unit_attenuation(loaded)
        plot_dprime_explainer(loaded["om0"])
    finally:
        for data in loaded.values():
            data.close()
    metadata = {key: json.loads(path.read_text()) for key, path in METADATA.items()}
    print(
        "wrote qualitative figures from",
        ", ".join(metadata[key]["model_label"] for key in ARTIFACTS),
    )


if __name__ == "__main__":
    main()