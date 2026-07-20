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
DATA = REPO / "results" / "qualitative" / "full96_om0_examples.npz"
METADATA = DATA.with_name("full96_om0_examples_metadata.json")
FIGURES = REPO / "figures"
UNITS = (2143, 1143, 720, 1129)
RAW_COLOR = "#4F5965"
DENOISED_COLOR = "#D26A3A"
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


def plot_probe_overview(data) -> None:
    raw_probe = _center_channels(data["raw_probe_uV"])
    denoised_probe = _center_channels(data["denoised_probe_uV"])
    raw_local = _center_channels(data["raw_local_uV"])
    denoised_local = _center_channels(data["denoised_local_uV"])
    overview_time = data["overview_time_ms"]
    local_time = data["local_time_ms"]
    probe_depth = data["probe_depth_um"]
    local_depth = data["local_depth_um"]
    peak_index = int(_scalar(data, "local_peak_index"))
    exemplar_unit = int(_scalar(data, "exemplar_unit"))

    figure = plt.figure(figsize=(14.2, 8.6))
    grid = figure.add_gridspec(2, 1, height_ratios=(1.05, 0.9), hspace=0.34)
    overview_grid = grid[0].subgridspec(1, 3, width_ratios=(1, 1, 0.035), wspace=0.2)
    detail_grid = grid[1].subgridspec(1, 4, width_ratios=(1, 1, 0.045, 1.08), wspace=0.45)
    axes = {
        "raw_probe": figure.add_subplot(overview_grid[0, 0]),
        "denoised_probe": figure.add_subplot(overview_grid[0, 1]),
        "overview_colorbar": figure.add_subplot(overview_grid[0, 2]),
        "raw_local": figure.add_subplot(detail_grid[0, 0]),
        "denoised_local": figure.add_subplot(detail_grid[0, 1]),
        "local_colorbar": figure.add_subplot(detail_grid[0, 2]),
        "trace": figure.add_subplot(detail_grid[0, 3]),
    }
    overview_limit = np.quantile(np.abs(np.concatenate([raw_probe.ravel(), denoised_probe.ravel()])), 0.995)
    local_limit = np.quantile(np.abs(np.concatenate([raw_local.ravel(), denoised_local.ravel()])), 0.995)
    for name, values, title in (
        ("raw_probe", raw_probe, "A  Raw AP-band recording"),
        ("denoised_probe", denoised_probe, "B  Full96 omission0 output"),
    ):
        image = axes[name].imshow(
            values,
            aspect="auto",
            cmap="RdBu_r",
            vmin=-overview_limit,
            vmax=overview_limit,
            extent=(overview_time[0], overview_time[-1], len(probe_depth) - 0.5, -0.5),
            interpolation="nearest",
        )
        axes[name].axvline(0, color="#111111", lw=0.9, ls=":")
        axes[name].set_title(title, loc="left", fontweight="bold")
        axes[name].set_xlabel("Time from exemplar GT event (ms)")
        _depth_ticks(axes[name], probe_depth)
    colorbar = figure.colorbar(image, cax=axes["overview_colorbar"])
    colorbar.set_label("Voltage (µV; channel median removed)")

    for name, values, title in (
        ("raw_local", raw_local, f"C  Raw close-up, GT unit {exemplar_unit}"),
        ("denoised_local", denoised_local, "D  Denoised close-up, same event"),
    ):
        local_image = axes[name].imshow(
            values,
            aspect="auto",
            cmap="RdBu_r",
            vmin=-local_limit,
            vmax=local_limit,
            extent=(local_time[0], local_time[-1], len(local_depth) - 0.5, -0.5),
            interpolation="nearest",
        )
        axes[name].axvline(0, color="#111111", lw=0.9, ls=":")
        axes[name].set_title(title, loc="left", fontweight="bold")
        axes[name].set_xlabel("Time from GT event (ms)")
        _depth_ticks(axes[name], local_depth)
    local_colorbar = figure.colorbar(local_image, cax=axes["local_colorbar"])
    local_colorbar.ax.set_title("µV", pad=6)

    raw_trace = raw_local[peak_index] - np.median(raw_local[peak_index, :10])
    denoised_trace = denoised_local[peak_index] - np.median(denoised_local[peak_index, :10])
    axes["trace"].plot(local_time, raw_trace, color=RAW_COLOR, lw=1.4, label="raw")
    axes["trace"].plot(local_time, denoised_trace, color=DENOISED_COLOR, lw=1.7, label="denoised")
    axes["trace"].axvline(0, color="#111111", lw=0.9, ls=":")
    axes["trace"].axhline(0, color="#B7BDC2", lw=0.7)
    axes["trace"].set_title("E  Peak-channel voltage", loc="left", fontweight="bold")
    axes["trace"].set_xlabel("Time from GT event (ms)")
    axes["trace"].set_ylabel("Voltage (µV)")
    axes["trace"].legend(frameon=False)
    axes["trace"].grid(alpha=0.2)
    figure.suptitle(
        "The frozen hybrid benchmark before and after DeepInterpolation",
        fontweight="bold",
        y=0.99,
    )
    figure.subplots_adjust(top=0.92, right=0.96, left=0.07, bottom=0.08)
    figure.savefig(FIGURES / "benchmark_raw_denoised_example.png", dpi=140)
    plt.close(figure)


def plot_unit_attenuation(data) -> None:
    time = (np.arange(120) - 45) / 30.0
    figure, axes = plt.subplots(len(UNITS), 3, figsize=(12.8, 10.6), squeeze=False)
    for row_index, unit_id in enumerate(UNITS):
        raw = _center_template(data[f"unit_{unit_id}_raw_template_uV"])
        denoised = _center_template(data[f"unit_{unit_id}_denoised_template_uV"])
        depths = data[f"unit_{unit_id}_depth_um"]
        peak_index = int(_scalar(data, f"unit_{unit_id}_peak_index"))
        raw, denoised, depths, peak_index = _local_template_contacts(
            raw, denoised, depths, peak_index
        )
        limit = np.max(np.abs(raw))
        for column, values, title in (
            (0, raw, "Raw empirical template"),
            (1, denoised, "Denoised empirical template"),
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
            axes[row_index, column].set_xlabel("Time (ms)")
            _depth_ticks(axes[row_index, column], depths, "Contact depth (µm)")
        figure.colorbar(image, ax=axes[row_index, :2], pad=0.008, fraction=0.018).set_label("µV")

        raw_trace = raw[:, peak_index]
        denoised_trace = denoised[:, peak_index]
        axes[row_index, 2].plot(time, raw_trace, color=RAW_COLOR, lw=1.35, label="raw")
        axes[row_index, 2].plot(time, denoised_trace, color=DENOISED_COLOR, lw=1.65, label="denoised")
        axes[row_index, 2].axvline(0, color="#111111", lw=0.7, ls=":")
        axes[row_index, 2].axhline(0, color="#B7BDC2", lw=0.7)
        raw_dprime = float(_scalar(data, f"unit_{unit_id}_dprime_raw"))
        deep_dprime = float(_scalar(data, f"unit_{unit_id}_dprime_deep"))
        amplitude_ratio = np.ptp(denoised_trace) / max(np.ptp(raw_trace), 1e-9)
        axes[row_index, 2].text(
            0.98,
            0.05,
            f"raw d′ {raw_dprime:.2f} → {deep_dprime:.2f}\namp ratio {amplitude_ratio:.2f}",
            transform=axes[row_index, 2].transAxes,
            ha="right",
            va="bottom",
            fontsize=8.5,
            bbox={"facecolor": "white", "edgecolor": "0.85", "alpha": 0.9},
        )
        axes[row_index, 2].set_title(
            f"Unit {unit_id}  |  peak-channel template",
            loc="left",
            fontweight="bold",
        )
        axes[row_index, 2].set_xlabel("Time (ms)")
        axes[row_index, 2].set_ylabel("Voltage (µV)")
        axes[row_index, 2].grid(alpha=0.2)
    axes[0, 2].legend(frameon=False, loc="upper right")
    figure.suptitle(
        "Weak GT units are attenuated more than strong units",
        fontweight="bold",
        y=0.995,
    )
    figure.subplots_adjust(top=0.95, hspace=0.5, wspace=0.48, right=0.95)
    figure.savefig(FIGURES / "unit_attenuation_examples.png", dpi=190)
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
    if not DATA.exists() or not METADATA.exists():
        raise FileNotFoundError(
            "qualitative source data are missing; run code/scoring/export_qualitative_examples.py"
        )
    with np.load(DATA) as data:
        plot_probe_overview(data)
        plot_unit_attenuation(data)
        plot_dprime_explainer(data)
    metadata = json.loads(METADATA.read_text())
    print(
        "wrote qualitative figures from",
        metadata["model_label"],
        metadata["checkpoint_sha256"][:12],
    )


if __name__ == "__main__":
    main()