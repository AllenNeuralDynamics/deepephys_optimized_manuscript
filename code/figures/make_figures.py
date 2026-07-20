#!/usr/bin/env python3
"""Generate the manuscript figures from the in-band score CSVs.

Writes PNGs into ``../../figures/``. Reads ``results/scores/<label>_{dprime,diag}.csv``
and ``results/tables/<label>_trajectory.csv``. Configurations are seed-averaged; the
reference architecture (``base_channels=32``) is labelled ``base32`` (there is no
"champion" — every row is just one architecture among many).

Figures produced (data permitting):
    F1  combined original-screen + matched-R5 width/schedule/depth d' ranking
    F4  combined template-SNR change vs matched-filter Δd' comparison
  F5  amplitude vs unit quality (the shrinkage law)
  F6  per-unit amplitude heatmap (units × models)          [colored table]
  F7  per-unit Δd' heatmap (units × models)                [colored table]
  F8  d' & amplitude vs training updates (om0 vs om1)
"""
from __future__ import annotations

import csv
import glob
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from adjustText import adjust_text
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[2]
S = REPO / "results" / "scores"
T = REPO / "results" / "tables"
FIG = REPO / "figures"
FIG.mkdir(exist_ok=True)

# display name, seed-glob, loss  (single-seed Tier-2 rows use an exact label, no '*')
CFG = [
    # base32 body (Tier 1)
    ("base32", "ib_champion_s*", "charb"),
    ("base32_l2", "ib_champ_l2_s*", "L2"),
    ("omission0", "ib_omission0_s*", "charb"),
    ("omission0_l2", "ib_omission0_l2_s*", "L2"),
    # capacity
    ("base64", "ib_base64_s*", "charb"),
    ("base64_l2", "ib_base64_l2_s0", "L2"),
    ("base64_om0", "ib_base64_om0_s0", "charb"),
    ("arch", "ib_arch_s0", "charb"),
    ("arch_l2", "ib_arch_l2_s0", "L2"),
    ("arch_om0", "ib_arch_om0_s0", "charb"),
    ("arch_l2_om0", "ib_arch_l2_om0_s*", "L2"),   # Tier-3 champion body (arch + L2 + omission=0), 3 seeds
    # SUPPORT blind-spot wiring
    ("support_sd", "ib_support_sd_s0", "charb"),
    ("support_all", "ib_support_all_s0", "charb"),
    ("support_all_l2", "ib_support_all_l2_s0", "L2"),
    # fuse width
    ("fuse256", "ib_fuse256_s0", "charb"),
    ("fuse256_l2", "ib_fuse256_l2_s0", "L2"),
    ("fuse512", "ib_fuse512_s0", "charb"),
    # temporal / norm / blind-spot frames
    ("tmult8", "ib_tmult8_s0", "charb"),
    ("no_norm", "ib_no_norm_s0", "charb"),
    ("ho", "ib_ho_s0", "charb"),
    # published reference — the ORIGINAL DeepInterpolation ephys architecture (Lecoq 2021),
    # temporal-only, no spatial blind spot; highlighted distinctly in F1.
    ("origdi", "ib_origdi_s*", "orig"),
    # NOTE: the 3.30-M-update support_all runs (om0_scale / om1_scale) are deliberately
    # not ranked against the short-budget models here; they appear only in F8.
]


def labels(pat):
    if "*" in pat:
        return [Path(f).name[:-11] for f in sorted(glob.glob(str(S / (pat + "_dprime.csv"))))]
    return [pat] if (S / (pat + "_dprime.csv")).exists() else []


# Keep only configurations with at least one scored seed. Unscored runs appear automatically once
# their endpoint CSVs exist.
CFG = [c for c in CFG if labels(c[1])]
PATS = {c[0]: c[1] for c in CFG}
NAMES = [c[0] for c in CFG]

# Exact trainable parameter counts and configured omission routes, reconstructed from each
# checkpoint's embedded config and strict-loaded against the pinned inference implementation.
SCREEN_METADATA = {
    "base32": (850_216, 1),
    "base32_l2": (850_216, 1),
    "omission0": (848_680, 0),
    "omission0_l2": (848_680, 0),
    "base64": (3_151_240, 1),
    "base64_l2": (3_151_240, 1),
    "base64_om0": (3_149_704, 0),
    "arch": (12_585_672, 1),
    "arch_l2": (12_585_672, 1),
    "arch_om0": (12_582_600, 0),
    "arch_l2_om0": (12_582_600, 0),
    "support_sd": (851_372, 1),
    "support_all": (900_462, 1),
    "support_all_l2": (900_462, 1),
    "fuse256": (925_864, 1),
    "fuse256_l2": (925_864, 1),
    "fuse512": (1_141_416, 1),
    "tmult8": (852_932, 1),
    "no_norm": (847_400, 1),
    "ho": (848_680, 1),
    "origdi": (5_253_057, 1),
}
missing_metadata = set(NAMES) - set(SCREEN_METADATA)
if missing_metadata:
    raise ValueError(f"missing SNR/d-prime plot metadata: {sorted(missing_metadata)}")

FOLLOWUP = (
    {"key": "base64", "name": "base64 R5", "bar": "base64 R5\nom0",
     "label": "ib_r5_bs256", "nested": True, "omission": 0,
     "parameters": 3_149_704, "color": "#dd8452", "marker": "s"},
    {"key": "sqrt2_om0", "name": "sqrt2 om0", "bar": "sqrt2\nom0",
     "label": "ib_w96_gsqrt2_om0_s0", "nested": False, "omission": 0,
     "parameters": 1_830_896, "color": "#dd8452", "marker": "X"},
    {"key": "depth2_om0", "name": "depth2 om0", "bar": "depth2\nom0",
     "label": "ib_w96_d2_om0_s0", "nested": False, "omission": 0,
     "parameters": 1_796_200, "color": "#dd8452", "marker": "v"},
    {"key": "g15_om0", "name": "g1.5 om0", "bar": "g1.5\nom0",
     "label": "ib_w96_g15_om0_s0", "nested": False, "omission": 0,
     "parameters": 2_233_936, "color": "#dd8452", "marker": "o"},
    {"key": "cap384", "name": "cap384 om0", "bar": "cap384\nom0",
     "label": "ib_w96_cap384_om0_s0", "nested": False, "omission": 0,
     "parameters": 4_601_320, "color": "#dd8452", "marker": "D"},
    {"key": "full_om0", "name": "full96 om0", "bar": "full96\nom0",
     "label": "ib_w96_om0_s0", "nested": False, "omission": 0,
     "parameters": 6_962_152, "color": "#dd8452", "marker": "o"},
    {"key": "sqrt2_om1", "name": "sqrt2 om1", "bar": "sqrt2\nom1",
     "label": "ib_w96_gsqrt2_om1_s0", "nested": False, "omission": 1,
     "parameters": 1_832_432, "color": "#4c72b0", "marker": "^"},
    {"key": "depth2_om1", "name": "depth2 om1", "bar": "depth2\nom1",
     "label": "ib_w96_d2_om1_s0", "nested": False, "omission": 1,
     "parameters": 1_797_736, "color": "#4c72b0", "marker": "v"},
    {"key": "g15_om1", "name": "g1.5 om1", "bar": "g1.5\nom1",
     "label": "ib_w96_g15_om1_s0", "nested": False, "omission": 1,
     "parameters": 2_235_472, "color": "#4c72b0", "marker": "^"},
    {"key": "full_om1", "name": "full96 om1", "bar": "full96\nom1",
     "label": "ib_w96_om1_s0", "nested": False, "omission": 1,
     "parameters": 6_963_688, "color": "#4c72b0", "marker": "^"},
)
FOLLOWUP_NAMES = tuple(f"R5 {item['name']}" for item in FOLLOWUP)
FOLLOWUP_BY_NAME = dict(zip(FOLLOWUP_NAMES, FOLLOWUP))
COMPARISON_NAMES = [*NAMES, *FOLLOWUP_NAMES]


def load(lbl, kind):
    f = S / f"{lbl}_{kind}.csv"
    return {r["unit_id"]: r for r in csv.DictReader(open(f))} if f.exists() else {}


def load_followup(item, kind):
    if item["nested"]:
        f = S / item["label"] / f"{item['label']}_best_{kind}.csv"
    else:
        f = S / f"{item['label']}_{kind}.csv"
    data = {r["unit_id"]: r for r in csv.DictReader(open(f))}
    if len(data) != 10:
        raise ValueError(f"{item['label']}: expected 10 {kind} rows")
    return data


anchor = load("ib_champion_s0", "dprime")
baseD = {u: float(r["dprime_raw"]) for u, r in anchor.items()}
units = sorted(baseD, key=lambda u: -baseD[u])
RAW = st.mean(baseD.values())
RAW_SNR = st.mean(float(r["snr_raw"]) for r in anchor.values())


def per_seed(pat, kind, col):
    out = []
    for l in labels(pat):
        d = load(l, kind)
        out.append(st.mean(float(d[u][col]) for u in units if u in d))
    return out


def cfg_unit(pat, kind, col):
    labs = labels(pat)
    res = {}
    for u in units:
        v = [float(load(l, kind)[u][col]) for l in labs if u in load(l, kind)]
        res[u] = st.mean(v) if v else float("nan")
    return res


def comparison_unit(name, kind, col):
    if name in PATS:
        return cfg_unit(PATS[name], kind, col)
    data = load_followup(FOLLOWUP_BY_NAME[name], kind)
    return {unit: float(data[unit][col]) for unit in units}


# ---- F1: original d' ranking + matched-R5 follow-up ----
dmean = [st.mean(per_seed(p, "dprime", "dprime_deep")) for p in PATS.values()]
dsd = [(st.stdev(v) if len(v) > 1 else 0.0) for v in (per_seed(p, "dprime", "dprime_deep") for p in PATS.values())]
followup_dmean = [
    st.mean(float(row["dprime_deep"]) for row in load_followup(item, "dprime").values())
    for item in FOLLOWUP
]

def _bar_color(name):
    if name == "origdi":                     # published original-DI reference — highlighted
        return "#c44e52"
    if name == "base32":                     # our reference body
        return "#7f7f7f"
    return "#4c72b0"

combined_names = [*NAMES, *[f"R5 {item['bar']}" for item in FOLLOWUP]]
combined_means = [*dmean, *followup_dmean]
combined_sds = [*dsd, *([0.0] * len(FOLLOWUP))]
combined_colors = [*[_bar_color(name) for name in NAMES],
                   *(["#4c72b0"] * len(FOLLOWUP))]
combined_is_followup = [*([False] * len(NAMES)), *([True] * len(FOLLOWUP))]
combined_omission = [*([None] * len(NAMES)),
                     *[item["omission"] for item in FOLLOWUP]]
combined_order = np.argsort(combined_means)[::-1]

fig, ax = plt.subplots(figsize=(16.2, 6.2))
bars = ax.bar(
    range(len(combined_order)), [combined_means[i] for i in combined_order],
    yerr=[2 * combined_sds[i] for i in combined_order], capsize=3,
    color=[combined_colors[i] for i in combined_order],
)
for bar, item_index in zip(bars, combined_order):
    if combined_is_followup[item_index]:
        bar.set_edgecolor("#222222")
        bar.set_linewidth(1.1)
        if combined_omission[item_index] == 1:
            bar.set_hatch("///")
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.004,
            f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=7,
        )
    elif combined_names[item_index] == "origdi":
        bar.set_edgecolor("#222222")
        bar.set_linewidth(1.4)
ax.axhline(RAW, ls=":", c="k", label=f"raw ({RAW:.3f})")
ci = NAMES.index("base32")
ax.axhspan(dmean[ci] - 2 * dsd[ci], dmean[ci] + 2 * dsd[ci], color="gray", alpha=0.25,
           label="base32 ±2 seed SD (screening reference)")
if "origdi" in NAMES:                        # legend swatch for the highlighted reference
    ax.bar([0], [0], color="#c44e52", edgecolor="k", linewidth=1.4,
           label="original DI (published reference)")
ax.legend(handles=[
    *ax.get_legend_handles_labels()[0],
    Patch(facecolor="#F2F2F2", edgecolor="#222222", linewidth=1.1,
          label="matched R5 follow-up (outlined)"),
    Patch(facecolor="white", edgecolor="#222222", hatch="///", label="omission1"),
], fontsize=8, ncol=2, loc="upper right")
ax.set_xticks(range(len(combined_order)))
ax.set_xticklabels([combined_names[i] for i in combined_order], rotation=52, ha="right",
                   fontsize=8)
ax.set_ylabel("d′  (mean ± 2 seed SD where replicated)")
lower = min(combined_means) - 0.03
upper = max(RAW, max(dmean), max(followup_dmean)) + 0.03
ax.set_ylim(lower, upper)
ax.grid(axis="y", alpha=0.2)
ax.set_title("Detection d′ across the original screen and matched R5 follow-up",
             fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "f1_dprime_ranking.png", dpi=180); plt.close(fig)

# ---- F4: template SNR vs matched-filter d' across all endpoints ----
fig, ax = plt.subplots(figsize=(13.2, 8.2))
snr_x, detect_y, screen_coordinates = [], [], {}
for name, pat in PATS.items():
    d = st.mean(per_seed(pat, "dprime", "dprime_deep"))
    sn = st.mean(per_seed(pat, "dprime", "snr_deep"))
    coordinates = (sn - RAW_SNR, d - RAW)
    screen_coordinates[name] = coordinates
    snr_x.append(coordinates[0]); detect_y.append(coordinates[1])
ax.axhline(0, ls=":", c="k")
rho_all = float(spearmanr(snr_x, detect_y)[0])


def _followup_snr_dprime(selected_units):
    coordinates = {}
    for item in FOLLOWUP:
        data = load_followup(item, "dprime")
        rows = [data[unit] for unit in selected_units]
        coordinates[item["key"]] = (
            st.mean(float(row["snr_deep"]) - float(row["snr_raw"]) for row in rows),
            st.mean(float(row["dprime_deep"]) - float(row["dprime_raw"]) for row in rows),
        )
    return coordinates


followup_coordinates = _followup_snr_dprime(units)
followup_x, followup_y = zip(*followup_coordinates.values())
combined_rho = float(spearmanr([*snr_x, *followup_x], [*detect_y, *followup_y])[0])
followup_rho = float(spearmanr(followup_x, followup_y)[0])
weak_units = [unit for unit in units if baseD[unit] <= 2.2]
if len(weak_units) != 4:
    raise ValueError(f"expected four weak units, found {len(weak_units)}")
weak_coordinates = _followup_snr_dprime(weak_units)
weak_x, weak_y = zip(*weak_coordinates.values())
weak_rho = float(spearmanr(weak_x, weak_y)[0])

plot_points = [
    {
        "name": name,
        "x": screen_coordinates[name][0],
        "y": screen_coordinates[name][1],
        "parameters": SCREEN_METADATA[name][0],
        "omission": SCREEN_METADATA[name][1],
    }
    for name in NAMES
]
plot_points.extend(
    {
        "name": item["name"],
        "x": followup_coordinates[item["key"]][0],
        "y": followup_coordinates[item["key"]][1],
        "parameters": item["parameters"],
        "omission": item["omission"],
    }
    for item in FOLLOWUP
)
if len(plot_points) != len(COMPARISON_NAMES) or any(
        point["omission"] not in {0, 1} for point in plot_points):
    raise ValueError(
        f"SNR/d-prime plot requires {len(COMPARISON_NAMES)} entries with omission route 0 or 1"
    )

parameter_norm = LogNorm(
    vmin=min(point["parameters"] for point in plot_points),
    vmax=max(point["parameters"] for point in plot_points),
)
parameter_cmap = plt.get_cmap("viridis")
route_markers = {0: "o", 1: "^"}
for omission, marker in route_markers.items():
    route_points = [point for point in plot_points if point["omission"] == omission]
    ax.scatter(
        [point["x"] for point in route_points],
        [point["y"] for point in route_points],
        c=[point["parameters"] for point in route_points],
        cmap=parameter_cmap,
        norm=parameter_norm,
        marker=marker,
        s=82,
        edgecolor="#202020",
        linewidth=0.75,
        zorder=3,
    )

direct_labels = []
for point in plot_points:
    label = ax.text(
        point["x"], point["y"], point["name"], fontsize=7.4,
        color="#202020", ha="left", va="bottom", zorder=4,
    )
    label.set_path_effects([path_effects.withStroke(linewidth=2.5, foreground="white")])
    direct_labels.append(label)

stats_box = ax.text(
    0.02, 0.04,
    f"Spearman ρ = {rho_all:.2f} (original {len(NAMES)})\n"
    f"ρ = {combined_rho:.2f} (all {len(COMPARISON_NAMES)} entries)\n"
    f"matched R5: all-unit ρ = {followup_rho:.2f}; "
    f"weak-unit ρ = {weak_rho:.2f}",
    transform=ax.transAxes, fontsize=9, va="bottom",
    bbox=dict(fc="white", ec="0.8", alpha=0.9),
)
route_handles = [
    Line2D([0], [0], marker="o", linestyle="", markersize=7.5,
           markerfacecolor="#a0a0a0", markeredgecolor="#202020", label="omission0"),
    Line2D([0], [0], marker="^", linestyle="", markersize=7.5,
           markerfacecolor="#a0a0a0", markeredgecolor="#202020", label="omission1"),
]
ax.legend(handles=route_handles, frameon=False, fontsize=8.5, loc="upper left", ncol=2)

colorbar = fig.colorbar(
    matplotlib.cm.ScalarMappable(norm=parameter_norm, cmap=parameter_cmap),
    ax=ax, pad=0.018, fraction=0.045,
)
colorbar.set_label("Trainable parameters")
colorbar.set_ticks(np.array([1, 2, 4, 8, 12]) * 1_000_000)
colorbar.ax.yaxis.set_major_formatter(
    FuncFormatter(lambda value, _: f"{value / 1_000_000:g} M")
)
ax.set_xlabel("Change in peak-channel template SNR  (denoised − raw)")
ax.set_ylabel("Change in multichannel matched-filter d′  (denoised − raw)")
ax.set_title(
    "Template SNR does not provide a stable model ranking",
    fontweight="bold", pad=12,
)
ax.grid(alpha=0.2)
fig.tight_layout()
fig.canvas.draw()
adjust_text(
    direct_labels,
    x=[point["x"] for point in plot_points],
    y=[point["y"] for point in plot_points],
    objects=[stats_box],
    ax=ax,
    expand=(1.06, 1.16),
    force_text=(0.35, 0.55),
    force_static=(0.25, 0.4),
    force_pull=(0.015, 0.025),
    max_move=(18, 18),
    ensure_inside_axes=True,
)
fig.savefig(FIG / "f4_snr_vs_dprime.png", dpi=180)
plt.close(fig)

# ---- F5: amplitude vs unit quality, full screen + paired omission contrast ----
amp32 = cfg_unit("ib_champion_s*", "diag", "amp_ratio")
ampom = cfg_unit("ib_omission0_s*", "diag", "amp_ratio")
xs = [baseD[u] for u in units]
all_amp = {
    name: comparison_unit(name, "diag", "amp_ratio")
    for name in COMPARISON_NAMES
}
rho_by_config = [float(spearmanr(xs, [all_amp[name][u] for u in units])[0])
                 for name in COMPARISON_NAMES]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)

rng = np.random.default_rng(20260717)
for model_index, name in enumerate(COMPARISON_NAMES):
    jitter = np.exp(rng.normal(0, 0.014, len(units)))
    a1.scatter(np.asarray(xs) * jitter, [all_amp[name][u] for u in units],
               s=16, color="#a9a9a9", alpha=0.35, linewidth=0)
for u in units:
    values = np.asarray([all_amp[name][u] for name in COMPARISON_NAMES])
    a1.errorbar(baseD[u], np.median(values),
                yerr=[[np.median(values) - np.quantile(values, 0.1)],
                      [np.quantile(values, 0.9) - np.median(values)]],
                fmt="D", ms=4, color="#333333", capsize=2, zorder=3)
a1.axhline(1.0, ls=":", c="k")
a1.set_xscale("log")
a1.set_xlabel("raw matched-filter d′  (unit quality, log scale)")
a1.set_ylabel("denoised/raw empirical-template amplitude")
a1.set_title(f"A  All {len(COMPARISON_NAMES)} architecture-comparison entries")
a1.text(0.03, 0.04,
        f"Per-model Spearman ρ:\nmedian {np.median(rho_by_config):.2f} "
        f"(range {min(rho_by_config):.2f}–{max(rho_by_config):.2f})",
        transform=a1.transAxes, fontsize=8, va="bottom",
        bbox=dict(fc="white", ec="0.8", alpha=0.9))

for u in units:
    a2.plot([baseD[u], baseD[u]], [amp32[u], ampom[u]], c="lightgray", lw=0.8, zorder=1)
a2.scatter(xs, [amp32[u] for u in units], c="k", label="base32", zorder=2)
a2.scatter(xs, [ampom[u] for u in units], c="#dd8452", label="omission0", zorder=2)
a2.axhline(1.0, ls=":", c="k")
a2.set_xscale("log")
a2.set_xlabel("raw matched-filter d′  (unit quality, log scale)")
a2.set_title("B  Matched omission contrast")
a2.legend(fontsize=8)
fig.suptitle("Amplitude preservation depends on unit quality; omission0 lifts weak units",
             fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "f5_amp_vs_quality.png", dpi=150); plt.close(fig)

# ---- F6 / F7: per-unit heatmaps ----
def heatmap(kind, col, delta, fname, cmap, title, center=None):
    data = {}
    for cn in COMPARISON_NAMES:
        d = comparison_unit(cn, kind, col)
        if delta:
            raw = comparison_unit(cn, "dprime", "dprime_raw")
            d = {u: d[u] - raw[u] for u in units}
        data[cn] = d
    M = np.array([[data[cn][u] for cn in COMPARISON_NAMES] for u in units])
    fig, ax = plt.subplots(figsize=(16.5, 5.8))
    if center is not None:
        vmax = np.nanmax(np.abs(M - center))
        im = ax.imshow(M, cmap=cmap, vmin=center - vmax, vmax=center + vmax, aspect="auto")
    else:
        im = ax.imshow(M, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(COMPARISON_NAMES)))
    ax.set_xticklabels(COMPARISON_NAMES, rotation=50, ha="right", fontsize=7)
    ax.set_yticks(range(len(units))); ax.set_yticklabels([f"{u} ({baseD[u]:.1f})" for u in units])
    ax.set_ylabel("unit (baseline d′)")
    for i in range(len(units)):
        for j in range(len(COMPARISON_NAMES)):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title(title)
    fig.tight_layout(); fig.savefig(FIG / fname, dpi=150); plt.close(fig)


heatmap("diag", "amp_ratio", False, "f6_perunit_amp_heatmap.png", "RdYlGn",
    f"Per-unit amplitude preservation across {len(COMPARISON_NAMES)} architecture-comparison entries")
heatmap("dprime", "dprime_deep", True, "f7_perunit_dprime_delta_heatmap.png", "RdBu",
    f"Per-unit change in detectability Δd′ across {len(COMPARISON_NAMES)} architecture-comparison entries",
    center=0.0)

# ---- F8: trajectories ----
def traj(label):
    f = T / f"{label}_trajectory.csv"
    if not f.exists():
        return None
    rows = [r for r in csv.DictReader(open(f)) if r["tag"].startswith("s") and r["step"]]
    rows.sort(key=lambda r: float(r["step"]))
    return ([float(r["step"]) for r in rows],
            [float(r["dprime_deep"]) for r in rows],
            [float(r["amp_ratio"]) for r in rows])


fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
for lab, name, c in [("ib_om0_scale", "om0 (t±1 in temporal branch)", "#4c72b0"),
                     ("ib_om1_scale", "om1 (t±1 in spatial branch)", "#d55e00")]:
    tr = traj(lab)
    if tr:
        s, d, amp = tr
        a1.semilogx(s, d, "-o", c=c, label=name, ms=3)
        a2.semilogx(s, amp, "-o", c=c, label=name, ms=3)
a1.axhline(RAW, ls=":", c="k", label=f"raw ({RAW:.2f})")
a1.set_xlabel("training updates"); a1.set_ylabel("d′"); a1.set_title("Detection vs training"); a1.legend(fontsize=8)
a2.set_xlabel("training updates"); a2.set_ylabel("amp_ratio"); a2.set_title("Amplitude vs training"); a2.legend(fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "f8_trajectory.png", dpi=150); plt.close(fig)

print("wrote:", sorted(p.name for p in FIG.glob("f*.png")))
