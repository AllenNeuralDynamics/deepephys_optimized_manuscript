#!/usr/bin/env python3
"""Render Full96 residual distribution and whiteness diagnostics."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "results" / "residual_diagnostics"
FIGURES = REPO / "figures"
TABLES = REPO / "results" / "tables"
ROUTES = {
    "om0": {
        "label": "Full96 omission0",
        "color": "#B84D27",
        "checkpoint_sha256": "f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506",
    },
    "om1": {
        "label": "Full96 omission1",
        "color": "#23748F",
        "checkpoint_sha256": "90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a",
    },
}
RAW_COLOR = "#4F5965"


def _prefix(route: str) -> Path:
    return SOURCE / f"full96_{route}"


def _load() -> dict[str, dict]:
    loaded = {}
    for route, config in ROUTES.items():
        prefix = _prefix(route)
        paths = {
            "npz": prefix.with_suffix(".npz"),
            "channels": prefix.with_name(prefix.name + "_channels.csv"),
            "summary": prefix.with_name(prefix.name + "_summary.csv"),
            "metadata": prefix.with_name(prefix.name + "_metadata.json"),
        }
        missing = [path for path in paths.values() if not path.exists()]
        if missing:
            raise FileNotFoundError("missing residual artifacts: " + ", ".join(map(str, missing)))
        metadata = json.loads(paths["metadata"].read_text())
        if metadata["checkpoint_sha256"] != config["checkpoint_sha256"]:
            raise ValueError(f"{route} checkpoint hash differs from the selected endpoint")
        loaded[route] = {
            "arrays": np.load(paths["npz"]),
            "channels": pd.read_csv(paths["channels"]),
            "summary": pd.read_csv(paths["summary"]),
            "metadata": metadata,
        }
    return loaded


def _assert_shared_raw(data: dict[str, dict]) -> None:
    first = data["om0"]
    second = data["om1"]
    exact_keys = ("background_times", "spectral_starts", "channel_depth_order")
    numeric_keys = (
        "sampling_frequency",
        "channel_locations_um",
        "spatial_distance_um",
        "overview_start_frame",
        "overview_time_ms",
        "raw_overview_uV",
        "raw_autocorrelation",
        "raw_spatial_correlation",
        "raw_frequencies_hz",
        "raw_power",
        "raw_normal_quantiles",
        "raw_empirical_quantiles",
        "raw_histogram_edges",
        "raw_histogram_density",
    )
    for key in exact_keys:
        if not np.array_equal(first["arrays"][key], second["arrays"][key]):
            raise ValueError(f"route artifacts differ for {key}")
    for key in numeric_keys:
        if not np.allclose(first["arrays"][key], second["arrays"][key], rtol=0, atol=1e-6):
            raise ValueError(f"route artifacts differ for {key}")
    for key in ("raw_overview_sha256", "background_times_sha256"):
        if first["metadata"][key] != second["metadata"][key]:
            raise ValueError(f"route metadata differ for {key}")
    first_raw = first["channels"].query("domain == 'raw'").reset_index(drop=True)
    second_raw = second["channels"].query("domain == 'raw'").reset_index(drop=True)
    numeric = first_raw.select_dtypes(include=[np.number]).columns
    if not np.allclose(first_raw[numeric], second_raw[numeric], rtol=0, atol=1e-8):
        raise ValueError("route channel tables differ for the shared raw domain")


def _depth_ticks(axis, depths: np.ndarray, ylabel: str = "Probe depth (um)") -> None:
    selected = np.linspace(0, len(depths) - 1, 5).round().astype(int)
    axis.set_yticks(selected, [f"{depths[index]:.0f}" for index in selected])
    axis.set_ylabel(ylabel)


def plot_probe_overview(data: dict[str, dict]) -> None:
    reference = data["om0"]["arrays"]
    order = reference["channel_depth_order"]
    depths = reference["channel_locations_um"][order, 1]
    time = reference["overview_time_ms"]
    domains = (
        ("raw_overview_uV", "Raw AP band"),
        ("prediction_overview_uV", "Model prediction"),
        ("residual_overview_uV", "Residual: raw - prediction"),
    )
    centered_values = []
    for route in ROUTES:
        arrays = data[route]["arrays"]
        for key, _ in domains:
            values = arrays[key]
            centered_values.append(values - np.median(values, axis=1, keepdims=True))
    limit = float(
        np.quantile(np.abs(np.concatenate([values.ravel() for values in centered_values])), 0.997)
    )

    figure = plt.figure(figsize=(16.5, 10.5))
    grid = figure.add_gridspec(
        2, 4, width_ratios=(1, 1, 1, 0.035), hspace=0.28, wspace=0.18
    )
    axes = np.asarray(
        [[figure.add_subplot(grid[row, column]) for column in range(3)] for row in range(2)]
    )
    colorbar_axis = figure.add_subplot(grid[:, 3])
    image = None
    for row, (route, config) in enumerate(ROUTES.items()):
        arrays = data[route]["arrays"]
        for column, (key, title) in enumerate(domains):
            values = arrays[key]
            values = values - np.median(values, axis=1, keepdims=True)
            image = axes[row, column].imshow(
                values,
                aspect="auto",
                cmap="RdBu_r",
                vmin=-limit,
                vmax=limit,
                extent=(time[0], time[-1], len(depths) - 0.5, -0.5),
                interpolation="nearest",
            )
            if row == 0:
                axes[row, column].set_title(title, fontweight="bold")
            axes[row, column].set_xlabel("Time (ms)")
            if column == 0:
                _depth_ticks(axes[row, column], depths)
                axes[row, column].text(
                    -0.25,
                    1.04,
                    config["label"],
                    transform=axes[row, column].transAxes,
                    fontweight="bold",
                    color=config["color"],
                )
            else:
                axes[row, column].set_yticks([])
    colorbar = figure.colorbar(image, cax=colorbar_axis)
    colorbar.set_label("Voltage (uV; channel median removed)")
    figure.suptitle(
        "The same injected-GT-free interval decomposed into prediction and residual",
        fontweight="bold",
    )
    figure.subplots_adjust(top=0.91, bottom=0.08, left=0.07, right=0.94)
    figure.savefig(FIGURES / "residual_probe_overview.png", dpi=160)
    plt.close(figure)


def _diagnostic_domains(data: dict[str, dict]) -> list[tuple[str, str, str, dict]]:
    return [
        ("raw", "Raw AP", RAW_COLOR, data["om0"]),
        ("residual", "om0 residual", ROUTES["om0"]["color"], data["om0"]),
        ("residual", "om1 residual", ROUTES["om1"]["color"], data["om1"]),
    ]


def plot_distribution_temporal(data: dict[str, dict]) -> None:
    figure, axes = plt.subplots(2, 3, figsize=(16.5, 9.6))
    normal_grid = np.linspace(-6, 6, 600)
    normal_density = np.exp(-0.5 * normal_grid**2) / np.sqrt(2 * np.pi)
    axes[0, 0].plot(normal_grid, normal_density, "--", color="#111111", label="Normal")
    domains = _diagnostic_domains(data)
    labels = []
    metric_tables = []
    for domain, label, color, route_data in domains:
        arrays = route_data["arrays"]
        channels = route_data["channels"].query("domain == @domain").copy()
        summary = route_data["summary"].query("domain == @domain").iloc[0]
        labels.append(label)
        metric_tables.append(channels)

        edges = arrays[f"{domain}_histogram_edges"]
        centers = 0.5 * (edges[:-1] + edges[1:])
        axes[0, 0].plot(
            centers,
            arrays[f"{domain}_histogram_density"],
            color=color,
            lw=1.8,
            label=label,
        )

        normal_quantiles = arrays[f"{domain}_normal_quantiles"]
        empirical = arrays[f"{domain}_empirical_quantiles"]
        axes[0, 1].plot(
            normal_quantiles,
            np.median(empirical, axis=1),
            color=color,
            lw=1.8,
            label=label,
        )
        axes[0, 1].fill_between(
            normal_quantiles,
            np.quantile(empirical, 0.1, axis=1),
            np.quantile(empirical, 0.9, axis=1),
            color=color,
            alpha=0.12,
        )

        autocorrelation = arrays[f"{domain}_autocorrelation"]
        sampling_frequency = float(arrays["sampling_frequency"])
        lags_ms = np.arange(autocorrelation.shape[1]) / sampling_frequency * 1000
        axes[0, 2].plot(
            lags_ms[1:],
            np.median(autocorrelation[:, 1:], axis=0),
            color=color,
            lw=1.8,
            label=(
                f"{label} (nominal LB-FDR reject "
                f"{summary['ljung_box_fdr_reject_fraction']:.0%})"
            ),
        )
        axes[0, 2].fill_between(
            lags_ms[1:],
            np.quantile(autocorrelation[:, 1:], 0.1, axis=0),
            np.quantile(autocorrelation[:, 1:], 0.9, axis=0),
            color=color,
            alpha=0.12,
        )

        frequencies = arrays[f"{domain}_frequencies_hz"]
        power = arrays[f"{domain}_power"]
        keep = (frequencies >= 300) & (frequencies <= 7_500)
        normalized = power / np.mean(power[keep], axis=0, keepdims=True)
        normalized_db = 10 * np.log10(np.maximum(normalized, 1e-12))
        axes[1, 0].plot(
            frequencies[keep] / 1000,
            np.median(normalized_db[keep], axis=1),
            color=color,
            lw=1.8,
            label=label,
        )
        axes[1, 0].fill_between(
            frequencies[keep] / 1000,
            np.quantile(normalized_db[keep], 0.1, axis=1),
            np.quantile(normalized_db[keep], 0.9, axis=1),
            color=color,
            alpha=0.12,
        )

        axes[1, 2].scatter(
            channels["mean_abs_autocorrelation"],
            channels["spectral_flatness"],
            s=12,
            alpha=0.35,
            color=color,
            label=label,
        )

    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xlim(-6, 6)
    axes[0, 0].set_ylim(1e-5, 1)
    axes[0, 0].set_xlabel("Per-channel standardized voltage")
    axes[0, 0].set_ylabel("Density")
    axes[0, 0].set_title("A  Marginal distribution", loc="left", fontweight="bold")
    axes[0, 0].legend(frameon=False, fontsize=8)

    axes[0, 1].plot([-4, 4], [-4, 4], ":", color="#111111")
    axes[0, 1].set_xlim(-4, 4)
    axes[0, 1].set_ylim(-6, 6)
    axes[0, 1].set_xlabel("Normal quantile")
    axes[0, 1].set_ylabel("Empirical quantile")
    axes[0, 1].set_title("B  Channel QQ curves", loc="left", fontweight="bold")

    axes[0, 2].axhline(0, color="#AAB0B5", lw=0.7)
    axes[0, 2].set_xlabel("Lag (ms)")
    axes[0, 2].set_ylabel("Autocorrelation")
    axes[0, 2].set_title("C  Temporal dependence", loc="left", fontweight="bold")
    axes[0, 2].legend(frameon=False, fontsize=8)

    axes[1, 0].axhline(0, color="#AAB0B5", lw=0.7)
    axes[1, 0].set_xlabel("Frequency (kHz)")
    axes[1, 0].set_ylabel("Power relative to band mean (dB)")
    axes[1, 0].set_title("D  Spectral shape", loc="left", fontweight="bold")

    box_values = [table["excess_kurtosis"].to_numpy() for table in metric_tables]
    box = axes[1, 1].boxplot(box_values, tick_labels=labels, showfliers=False, patch_artist=True)
    for patch, (_, _, color, _) in zip(box["boxes"], domains):
        patch.set_facecolor(color)
        patch.set_alpha(0.45)
    for index, values in enumerate(box_values, start=1):
        axes[1, 1].text(
            index,
            np.median(values),
            f"  {np.median(values):.3f}",
            va="center",
            ha="left",
            fontsize=8,
            fontweight="bold",
        )
    axes[1, 1].axhline(0, color="#111111", ls=":")
    axes[1, 1].tick_params(axis="x", rotation=18)
    axes[1, 1].set_ylabel("Excess kurtosis")
    axes[1, 1].set_title("E  Heavy-tail effect size", loc="left", fontweight="bold")

    axes[1, 2].set_xlabel("Mean absolute ACF, lags 1-30")
    axes[1, 2].set_ylabel("Spectral flatness, 0.3-7.5 kHz")
    axes[1, 2].set_title("F  Whiteness effect sizes", loc="left", fontweight="bold")
    axes[1, 2].legend(frameon=False, fontsize=8)
    for axis in axes.ravel():
        axis.grid(alpha=0.18)
    figure.suptitle(
        "Residuals approach Gaussian margins but remain temporally colored",
        fontweight="bold",
    )
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    figure.savefig(FIGURES / "residual_distribution_temporal.png", dpi=170)
    plt.close(figure)


def _distance_curve(correlations: np.ndarray, distances: np.ndarray):
    triangle = np.triu(np.ones_like(correlations, dtype=bool), k=1)
    pair_distances = distances[triangle]
    pair_correlations = np.abs(correlations[triangle])
    edges = np.arange(0, 501, 20)
    centers = 0.5 * (edges[:-1] + edges[1:])
    medians = np.full(len(centers), np.nan)
    lower = np.full(len(centers), np.nan)
    upper = np.full(len(centers), np.nan)
    for index, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        selected = pair_correlations[
            (pair_distances >= left) & (pair_distances < right)
        ]
        if selected.size:
            medians[index] = np.median(selected)
            lower[index], upper[index] = np.quantile(selected, [0.1, 0.9])
    return centers, medians, lower, upper


def plot_spatial_whiteness(data: dict[str, dict]) -> None:
    reference = data["om0"]["arrays"]
    order = reference["channel_depth_order"]
    locations = reference["channel_locations_um"]
    depths = locations[order, 1]
    distances = reference["spatial_distance_um"]
    domains = _diagnostic_domains(data)
    matrices = [
        route_data["arrays"][f"{domain}_spatial_correlation"]
        for domain, _, _, route_data in domains
    ]
    off_diagonal = ~np.eye(matrices[0].shape[0], dtype=bool)
    limit = max(
        0.05,
        float(
            np.quantile(
                np.abs(np.concatenate([matrix[off_diagonal] for matrix in matrices])),
                0.995,
            )
        ),
    )
    limit = min(limit, 1.0)
    figure = plt.figure(figsize=(16.2, 10.2))
    grid = figure.add_gridspec(
        2, 4, width_ratios=(1, 1, 1, 0.035), hspace=0.34, wspace=0.24
    )
    axes = np.asarray(
        [[figure.add_subplot(grid[row, column]) for column in range(3)] for row in range(2)]
    )
    correlation_colorbar_axis = figure.add_subplot(grid[0, 3])
    ratio_colorbar_axis = figure.add_subplot(grid[1, 3])
    correlation_cmap = plt.get_cmap("RdBu_r").copy()
    correlation_cmap.set_bad("#F0F0F0")
    image = None
    for column, ((domain, label, _, route_data), matrix) in enumerate(zip(domains, matrices)):
        sorted_matrix = matrix[np.ix_(order, order)].copy()
        np.fill_diagonal(sorted_matrix, np.nan)
        image = axes[0, column].imshow(
            sorted_matrix,
            cmap=correlation_cmap,
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
            aspect="auto",
        )
        axes[0, column].set_title(label, fontweight="bold")
        axes[0, column].set_xlabel("Probe contact (depth sorted)")
        if column == 0:
            _depth_ticks(axes[0, column], depths, "Row depth (um)")
        else:
            axes[0, column].set_yticks([])
    colorbar = figure.colorbar(image, cax=correlation_colorbar_axis)
    colorbar.set_label("Zero-lag channel correlation")

    for (domain, label, color, route_data), matrix in zip(domains, matrices):
        centers, median, lower, upper = _distance_curve(matrix, distances)
        axes[1, 0].plot(centers, median, color=color, lw=1.8, label=label)
        axes[1, 0].fill_between(centers, lower, upper, color=color, alpha=0.12)
    axes[1, 0].set_xlim(0, 500)
    axes[1, 0].set_xlabel("Contact distance (um)")
    axes[1, 0].set_ylabel("Absolute correlation")
    axes[1, 0].set_title("D  Spatial dependence vs distance", loc="left", fontweight="bold")
    axes[1, 0].legend(frameon=False, fontsize=8)

    ratio_values = []
    for route in ROUTES:
        channels = data[route]["channels"]
        raw_std = channels.query("domain == 'raw'").set_index("channel_index")["std"]
        residual = channels.query("domain == 'residual'").set_index("channel_index")
        ratio_values.append((residual["std"] / raw_std).to_numpy())
    ratio_limit = np.quantile(np.concatenate(ratio_values), [0.02, 0.98])
    scatter = None
    for column, (route, config, ratios) in enumerate(
        zip(ROUTES, ROUTES.values(), ratio_values), start=1
    ):
        scatter = axes[1, column].scatter(
            locations[:, 0],
            locations[:, 1],
            c=ratios,
            s=22,
            marker="s",
            cmap="viridis",
            vmin=ratio_limit[0],
            vmax=ratio_limit[1],
        )
        axes[1, column].set_title(
            f"{'E' if column == 1 else 'F'}  {config['label']} residual scale",
            loc="left",
            fontweight="bold",
        )
        axes[1, column].set_xlabel("Lateral position (um)")
        if column == 1:
            axes[1, column].set_ylabel("Probe depth (um)")
        else:
            axes[1, column].set_yticklabels([])
    ratio_colorbar = figure.colorbar(scatter, cax=ratio_colorbar_axis)
    ratio_colorbar.set_label("Residual SD / raw SD")
    axes[1, 0].grid(alpha=0.18)
    figure.suptitle(
        "Residual spatial correlation and variance across the NP1 probe",
        fontweight="bold",
    )
    figure.subplots_adjust(top=0.91, bottom=0.08, left=0.07, right=0.94)
    figure.savefig(FIGURES / "residual_spatial_whiteness.png", dpi=170)
    plt.close(figure)


def write_summary_table(data: dict[str, dict]) -> None:
    rows = []
    raw_added = False
    for route, config in ROUTES.items():
        summary = data[route]["summary"].copy()
        for _, row in summary.iterrows():
            if row["domain"] == "raw":
                if raw_added:
                    continue
                row = row.copy()
                row["model_label"] = "shared_raw"
                raw_added = True
            rows.append(row)
    combined = pd.DataFrame(rows)
    path = TABLES / "residual_diagnostics_summary.csv"
    combined.to_csv(path, index=False)
    raw = combined.query("model_label == 'shared_raw' and domain == 'raw'").iloc[0]
    omission0 = combined.query(
        "model_label == 'ib_w96_om0_scale' and domain == 'residual'"
    ).iloc[0]
    omission1 = combined.query(
        "model_label == 'ib_w96_om1_scale' and domain == 'residual'"
    ).iloc[0]

    def decimal(column: str, reference: str) -> list[str]:
        return [
            f"{raw[column]:.4f}",
            f"{omission0[column]:.4f}",
            f"{omission1[column]:.4f}",
            reference,
        ]

    def percent(column: str) -> list[str]:
        return [
            f"{raw[column]:.1%}",
            f"{omission0[column]:.1%}",
            f"{omission1[column]:.1%}",
            "no systematic rejection",
        ]

    compact_rows = []
    specifications = (
        ("Median variance / raw variance", "median_variance_ratio_to_raw", "n/a", decimal),
        ("Median absolute skewness", "median_abs_skewness", "0", decimal),
        ("Median excess kurtosis", "median_excess_kurtosis", "0", decimal),
        ("Median normal-QQ RMSE", "median_normal_quantile_rmse", "0", decimal),
        ("Median fraction absolute z > 3", "median_fraction_abs_gt_3", "0.0027", decimal),
        ("Nominal Jarque-Bera FDR-reject channels", "jarque_bera_fdr_reject_fraction", "", percent),
        ("Median mean absolute ACF", "median_mean_abs_autocorrelation", "0", decimal),
        ("Median max absolute ACF", "median_max_abs_autocorrelation", "0", decimal),
        ("Nominal Ljung-Box FDR-reject channels", "ljung_box_fdr_reject_fraction", "", percent),
        ("Median spectral flatness", "median_spectral_flatness", "1", decimal),
        ("Median near-contact absolute correlation", "median_abs_near_correlation", "0", decimal),
        ("Median far-contact absolute correlation", "median_abs_far_correlation", "0", decimal),
    )
    for diagnostic, column, reference, formatter in specifications:
        values = formatter(column, reference) if formatter is decimal else formatter(column)
        compact_rows.append(
            {
                "diagnostic": diagnostic,
                "raw AP": values[0],
                "om0 residual": values[1],
                "om1 residual": values[2],
                "Gaussian-white reference": values[3],
            }
        )
    compact = pd.DataFrame(compact_rows)
    path.with_suffix(".md").write_text(compact.to_markdown(index=False) + "\n")


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    data = _load()
    try:
        _assert_shared_raw(data)
        plot_probe_overview(data)
        plot_distribution_temporal(data)
        plot_spatial_whiteness(data)
        write_summary_table(data)
    finally:
        for route_data in data.values():
            route_data["arrays"].close()
    print("wrote three residual-diagnostic figures and summary table")


if __name__ == "__main__":
    main()