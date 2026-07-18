#!/usr/bin/env python3
"""Render the current denoiser topology and its tested architectural evolution."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / "figures" / "architecture_evolution.png"

COLORS = {
    "ink": "#202427",
    "muted": "#5F676C",
    "line": "#4D565B",
    "neutral": "#E9ECEE",
    "grid": "#D9E6EA",
    "temporal": "#CDE8E2",
    "temporal_edge": "#24786D",
    "spatial": "#F5D3C1",
    "spatial_edge": "#B54E2D",
    "fuse": "#DEE8C9",
    "fuse_edge": "#657F32",
    "naf": "#F2D58A",
    "naf_edge": "#956800",
    "original": "#E3E5E7",
    "base": "#D4E1EE",
}


def setup(axis) -> None:
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")


def box(axis, x, y, width, height, text, face, edge, fontsize=8.5,
        weight="normal", linewidth=1.25, linestyle="-") -> None:
    axis.add_patch(FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=face, edgecolor=edge, linewidth=linewidth,
        linestyle=linestyle, zorder=3,
    ))
    axis.text(
        x + width / 2, y + height / 2, text,
        ha="center", va="center", fontsize=fontsize,
        fontweight=weight, color=COLORS["ink"], linespacing=1.25, zorder=4,
    )


def arrow(axis, start, end, color=None, linewidth=1.45, label=None,
          label_offset=(0, 0.035), connection="arc3,rad=0") -> None:
    color = color or COLORS["line"]
    axis.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=11,
        linewidth=linewidth, color=color, shrinkA=2, shrinkB=2,
        connectionstyle=connection, zorder=2,
    ))
    if label:
        midpoint = ((start[0] + end[0]) / 2 + label_offset[0],
                    (start[1] + end[1]) / 2 + label_offset[1])
        axis.text(*midpoint, label, ha="center", va="center",
                  fontsize=7.2, color=color, zorder=5)


def panel_heading(axis, letter, title, subtitle=None) -> None:
    axis.text(0.0, 1.035, letter, ha="left", va="bottom", fontsize=15,
              fontweight="bold", color=COLORS["ink"], transform=axis.transAxes)
    axis.text(0.04, 1.035, title, ha="left", va="bottom", fontsize=11.5,
              fontweight="bold", color=COLORS["ink"], transform=axis.transAxes)
    if subtitle:
        axis.text(0.04, 0.99, subtitle, ha="left", va="top", fontsize=8.3,
                  color=COLORS["muted"], transform=axis.transAxes)


def topology_panel(axis) -> None:
    setup(axis)
    panel_heading(
        axis, "A", "Shared R5 / R13 denoiser topology",
        "Only the temporal stage family changes in R13; the self-supervised blind spot is unchanged.",
    )

    box(axis, 0.01, 0.35, 0.12, 0.27,
        "input\n(B, 61, 384)\n\n60 neighbors\n+ center t",
        COLORS["neutral"], COLORS["line"], fontsize=8.2, weight="bold")
    box(axis, 0.17, 0.39, 0.12, 0.19,
        "NP1 scatter\n192 x 4 grid",
        COLORS["grid"], "#527985", fontsize=8.5, weight="bold")
    arrow(axis, (0.13, 0.485), (0.17, 0.485))

    box(axis, 0.34, 0.64, 0.12, 0.17,
        "fold neighbors\n(B, 240, 192)",
        COLORS["temporal"], COLORS["temporal_edge"], fontsize=8.0)
    box(axis, 0.50, 0.61, 0.18, 0.23,
        "temporal U-Net\n3 scales + skips\n\nR5: DoubleConv, width 64\nR13: NAF, width 58",
        COLORS["temporal"], COLORS["temporal_edge"], fontsize=8.1, weight="bold")
    box(axis, 0.72, 0.66, 0.07, 0.13,
        "u\n4 x 192", COLORS["temporal"], COLORS["temporal_edge"], fontsize=7.7)

    box(axis, 0.34, 0.18, 0.12, 0.17,
        "fold center t\n(B, 4, 192)",
        COLORS["spatial"], COLORS["spatial_edge"], fontsize=8.0)
    box(axis, 0.50, 0.13, 0.18, 0.27,
        "5 x ConvHole1D\ndilations 1, 2, 4, 8, 16\n\nown depth row excluded\n64 features",
        COLORS["spatial"], COLORS["spatial_edge"], fontsize=8.0, weight="bold")
    box(axis, 0.72, 0.20, 0.07, 0.13,
        "b\n64 x 192", COLORS["spatial"], COLORS["spatial_edge"], fontsize=7.7)

    arrow(axis, (0.29, 0.50), (0.34, 0.725), COLORS["temporal_edge"],
          label="t-30...t-1, t+1...t+30", label_offset=(0.02, 0.00),
          connection="arc3,rad=-0.12")
    arrow(axis, (0.29, 0.46), (0.34, 0.265), COLORS["spatial_edge"],
          label="center t", label_offset=(0.005, -0.02), connection="arc3,rad=0.12")
    arrow(axis, (0.46, 0.725), (0.50, 0.725), COLORS["temporal_edge"])
    arrow(axis, (0.68, 0.725), (0.72, 0.725), COLORS["temporal_edge"])
    arrow(axis, (0.46, 0.265), (0.50, 0.265), COLORS["spatial_edge"])
    arrow(axis, (0.68, 0.265), (0.72, 0.265), COLORS["spatial_edge"])

    box(axis, 0.82, 0.34, 0.09, 0.29,
        "pointwise fuse\n\nconcat 4 + 64\n1 x 1 convs\n68 -> 64 -> 64 -> 4",
        COLORS["fuse"], COLORS["fuse_edge"], fontsize=7.8, weight="bold")
    arrow(axis, (0.79, 0.725), (0.82, 0.56), COLORS["temporal_edge"],
          connection="arc3,rad=0.10")
    arrow(axis, (0.79, 0.265), (0.82, 0.41), COLORS["spatial_edge"],
          connection="arc3,rad=-0.10")
    box(axis, 0.925, 0.39, 0.055, 0.19,
        "output\n\n(B, 1,\n384)", COLORS["neutral"], COLORS["line"], fontsize=7.2)
    arrow(axis, (0.91, 0.485), (0.925, 0.485), COLORS["fuse_edge"])

    axis.text(
        0.50, 0.015,
        "Prediction at (t, channel c) never receives the noisy sample at (t, c): "
        "time excludes t, ConvHole excludes c, and fusion is pointwise.",
        ha="center", va="bottom", fontsize=8.2, fontweight="bold",
        color="#8C3523",
    )


def evolution_panel(axis) -> None:
    setup(axis)
    panel_heading(axis, "B", "Architectural evolution",
                  "The diagram separates representation changes from the later training-recipe changes.")

    box(axis, 0.02, 0.29, 0.26, 0.42,
        "Original DeepInterpolation\n(2021 control)\n\n2-D temporal-only U-Net\ncenter frame absent\nno spatial blind-spot branch",
        COLORS["original"], COLORS["line"], fontsize=8.4, weight="bold")
    box(axis, 0.37, 0.29, 0.26, 0.42,
        "base32 reference\n\nfold columns into features\n1-D U-Net along probe depth\nresidual GroupNorm / GELU blocks\n+ center-frame ConvHole branch",
        COLORS["base"], "#476F97", fontsize=8.2, weight="bold")
    box(axis, 0.72, 0.29, 0.26, 0.42,
        "replicated R5 body\n\nbase width 32 -> 64\nomission 1 -> 0\nt+/-1 move into temporal path\n3 center frames -> center t only\n3.15 M parameters",
        COLORS["temporal"], COLORS["temporal_edge"], fontsize=8.2, weight="bold")

    arrow(axis, (0.28, 0.50), (0.37, 0.50))
    arrow(axis, (0.63, 0.50), (0.72, 0.50))
    axis.text(0.325, 0.78, "geometry + blind spot", ha="center", va="center",
              fontsize=7.4, color=COLORS["muted"])
    axis.text(0.675, 0.78, "capacity + frame routing", ha="center", va="center",
              fontsize=7.4, color=COLORS["muted"])
    axis.text(0.5, 0.12,
              "Batch 256, learning rate, warmup, accumulation, and sampling are training controls, not architecture.",
              ha="center", va="center", fontsize=8.0, color=COLORS["muted"],
              fontstyle="italic")


def block_comparison_panel(axis) -> None:
    setup(axis)
    panel_heading(axis, "C", "Local temporal-stage substitution",
                  "R13 is capacity matched (+0.42% parameters); results are pending.")

    axis.text(0.23, 0.83, "R5: DoubleConv1d", ha="center", va="center",
              fontsize=9.2, fontweight="bold", color=COLORS["temporal_edge"])
    box(axis, 0.04, 0.57, 0.38, 0.19,
        "Conv k3 -> GroupNorm -> GELU\nConv k3 -> GroupNorm",
        COLORS["temporal"], COLORS["temporal_edge"], fontsize=8.0)
    box(axis, 0.09, 0.35, 0.28, 0.12,
        "+ residual projection -> GELU",
        COLORS["neutral"], COLORS["line"], fontsize=7.8)
    arrow(axis, (0.23, 0.57), (0.23, 0.47), COLORS["temporal_edge"])

    axis.text(0.73, 0.83, "R13: NAFStage1d", ha="center", va="center",
              fontsize=9.2, fontweight="bold", color=COLORS["naf_edge"])
    box(axis, 0.52, 0.60, 0.42, 0.16,
        "width projection -> LayerNorm\n1 x 1 expansion -> depthwise Conv k3",
        COLORS["naf"], COLORS["naf_edge"], fontsize=7.8)
    box(axis, 0.52, 0.40, 0.42, 0.14,
        "SimpleGate (split x multiply) -> channel attention\n1 x 1 projection -> beta-scaled residual",
        COLORS["naf"], COLORS["naf_edge"], fontsize=7.7)
    box(axis, 0.52, 0.21, 0.42, 0.13,
        "LayerNorm -> gated feed-forward\n-> gamma-scaled residual",
        COLORS["naf"], COLORS["naf_edge"], fontsize=7.7)
    arrow(axis, (0.73, 0.60), (0.73, 0.54), COLORS["naf_edge"])
    arrow(axis, (0.73, 0.40), (0.73, 0.34), COLORS["naf_edge"])
    axis.text(0.73, 0.13,
              "No GELU / ReLU; multiplicative gates provide nonlinearity.\n"
              "beta = gamma = 0 at initialization.",
              ha="center", va="center", fontsize=7.8, color=COLORS["muted"])

    axis.text(
        0.5, 0.015,
        "Unchanged in R13: temporal window, U-Net scales and skips, ConvHole branch,\n"
        "pointwise fuse, noisy target, and Charbonnier loss.",
        ha="center", va="bottom", fontsize=7.3, fontweight="bold", color="#8C3523",
    )


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure(figsize=(16, 10.2), facecolor="#FAFAF8")
    grid = figure.add_gridspec(
        2, 2, height_ratios=(1.12, 1.0), width_ratios=(1.0, 1.05),
        left=0.035, right=0.985, top=0.94, bottom=0.045,
        hspace=0.24, wspace=0.08,
    )
    topology_panel(figure.add_subplot(grid[0, :]))
    evolution_panel(figure.add_subplot(grid[1, 0]))
    block_comparison_panel(figure.add_subplot(grid[1, 1]))
    figure.suptitle(
        "DeepInterpolation ephys: current topology and architectural evolution",
        x=0.035, y=0.985, ha="left", fontsize=15, fontweight="bold",
        color=COLORS["ink"],
    )
    figure.savefig(OUTPUT, dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()