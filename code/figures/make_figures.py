#!/usr/bin/env python3
"""Generate the manuscript figures from the in-band score CSVs.

Writes PNGs into ``../../figures/``. Reads ``results/scores/<label>_{dprime,diag}.csv``
and ``results/tables/<label>_trajectory.csv``. Configurations are seed-averaged; the
reference architecture (``base_channels=32``) is labelled ``base32`` (there is no
"champion" — every row is just one architecture among many).

Figures produced (data permitting):
  F1  d' ranking with base32 ±2σ variability band + raw line
  F4  SNR-gain vs Δd' ("the SNR trap")
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
import numpy as np

REPO = Path(__file__).resolve().parents[2]
S = REPO / "results" / "scores"
T = REPO / "results" / "tables"
FIG = REPO / "figures"
FIG.mkdir(exist_ok=True)

# display name, seed-glob, loss  (single-seed Tier-2 rows use an exact label, no '*')
CFG = [
    # base32 body (Tier 1)
    ("base32", "ib_champion_s*", "charb"),
    ("champ_l2", "ib_champ_l2_s*", "L2"),
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
    # NOTE: the SUPPORT-scale runs (om0_scale / om1_scale) are trained ~7x longer and are
    # deliberately NOT ranked against the short-budget models here — they appear only in F8,
    # the training-length comparison.
]


def labels(pat):
    if "*" in pat:
        return [Path(f).name[:-11] for f in sorted(glob.glob(str(S / (pat + "_dprime.csv"))))]
    return [pat] if (S / (pat + "_dprime.csv")).exists() else []


# Keep only configurations with at least one scored seed, so runs still training (e.g. origdi
# before it lands) don't break the plots — they appear automatically once their CSVs exist.
CFG = [c for c in CFG if labels(c[1])]
PATS = {c[0]: c[1] for c in CFG}
NAMES = [c[0] for c in CFG]


def load(lbl, kind):
    f = S / f"{lbl}_{kind}.csv"
    return {r["unit_id"]: r for r in csv.DictReader(open(f))} if f.exists() else {}


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


# ---- F1: d' ranking + variability band ----
dmean = [st.mean(per_seed(p, "dprime", "dprime_deep")) for p in PATS.values()]
dsd = [(st.stdev(v) if len(v) > 1 else 0.0) for v in (per_seed(p, "dprime", "dprime_deep") for p in PATS.values())]
order = np.argsort(dmean)[::-1]

def _bar_color(name):
    if name == "origdi":                     # published original-DI reference — highlighted
        return "#c44e52"
    if name == "base32":                     # our reference body
        return "#7f7f7f"
    return "#4c72b0"

fig, ax = plt.subplots(figsize=(10, 4.6))
ax.bar(range(len(order)), [dmean[i] for i in order], yerr=[2 * dsd[i] for i in order],
       capsize=3, color=[_bar_color(NAMES[i]) for i in order],
       edgecolor=["k" if NAMES[i] == "origdi" else "none" for i in order],
       linewidth=[1.4 if NAMES[i] == "origdi" else 0.0 for i in order])
ax.axhline(RAW, ls=":", c="k", label=f"raw ({RAW:.3f})")
ci = NAMES.index("base32")
ax.axhspan(dmean[ci] - 2 * dsd[ci], dmean[ci] + 2 * dsd[ci], color="gray", alpha=0.25,
           label="base32 ±2σ (noise floor)")
if "origdi" in NAMES:                        # legend swatch for the highlighted reference
    ax.bar([0], [0], color="#c44e52", edgecolor="k", linewidth=1.4,
           label="original DI (published reference)")
ax.set_xticks(range(len(order)))
ax.set_xticklabels([NAMES[i] for i in order], rotation=45, ha="right")
ax.set_ylabel("d′  (mean ± 2σ over seeds)")
ax.set_ylim(min(dmean) - 0.03, max(RAW, max(dmean)) + 0.03)
ax.set_title("Detection d′ across architectures (in-band)")
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "f1_dprime_ranking.png", dpi=150); plt.close(fig)

# ---- F4: SNR gain vs Δd' ----
fig, ax = plt.subplots(figsize=(8.5, 6))
for name, pat in PATS.items():
    d = st.mean(per_seed(pat, "dprime", "dprime_deep"))
    sn = st.mean(per_seed(pat, "dprime", "snr_deep"))
    ax.scatter(sn - RAW_SNR, d - RAW, s=70, color="#4c72b0")
    ax.annotate(name, (sn - RAW_SNR, d - RAW), fontsize=8, xytext=(4, 3), textcoords="offset points")
ax.axhline(0, ls=":", c="k")
ax.set_xlabel("SNR gain  (snr_deep − snr_raw)")
ax.set_ylabel("Δd′  (d′_deep − d′_raw)")
ax.set_title("The SNR trap: more denoising ≠ better detection")
fig.tight_layout(); fig.savefig(FIG / "f4_snr_vs_dprime.png", dpi=150); plt.close(fig)

# ---- F5: amplitude vs unit quality ----
amp32 = cfg_unit("ib_champion_s*", "diag", "amp_ratio")
ampom = cfg_unit("ib_omission0_s*", "diag", "amp_ratio")
fig, ax = plt.subplots(figsize=(6, 4.5))
xs = [baseD[u] for u in units]
for u in units:
    ax.plot([baseD[u], baseD[u]], [amp32[u], ampom[u]], c="lightgray", lw=0.8, zorder=1)
ax.scatter(xs, [amp32[u] for u in units], c="k", label="base32", zorder=2)
ax.scatter(xs, [ampom[u] for u in units], c="#4c72b0", label="omission0", zorder=2)
ax.axhline(1.0, ls=":", c="k")
ax.set_xscale("log")
ax.set_xlabel("baseline d′  (unit quality, log scale)")
ax.set_ylabel("amp_ratio")
ax.set_title("Amplitude preservation follows unit quality (Spearman 0.94)")
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "f5_amp_vs_quality.png", dpi=150); plt.close(fig)

# ---- F6 / F7: per-unit heatmaps ----
def heatmap(kind, col, delta, fname, cmap, title, center=None):
    data = {}
    for cn in NAMES:
        d = cfg_unit(PATS[cn], kind, col)
        if delta:
            raw = cfg_unit(PATS[cn], "dprime", "dprime_raw")
            d = {u: d[u] - raw[u] for u in units}
        data[cn] = d
    M = np.array([[data[cn][u] for cn in NAMES] for u in units])
    fig, ax = plt.subplots(figsize=(13, 5.5))
    if center is not None:
        vmax = np.nanmax(np.abs(M - center))
        im = ax.imshow(M, cmap=cmap, vmin=center - vmax, vmax=center + vmax, aspect="auto")
    else:
        im = ax.imshow(M, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(NAMES))); ax.set_xticklabels(NAMES, rotation=45, ha="right")
    ax.set_yticks(range(len(units))); ax.set_yticklabels([f"{u} ({baseD[u]:.1f})" for u in units])
    ax.set_ylabel("unit (baseline d′)")
    for i in range(len(units)):
        for j in range(len(NAMES)):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title(title)
    fig.tight_layout(); fig.savefig(FIG / fname, dpi=150); plt.close(fig)


heatmap("diag", "amp_ratio", False, "f6_perunit_amp_heatmap.png", "RdYlGn",
        "Per-unit amplitude preservation (units × models)")
heatmap("dprime", "dprime_deep", True, "f7_perunit_dprime_delta_heatmap.png", "RdBu",
        "Per-unit change in detectability Δd′ (units × models)", center=0.0)

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
for lab, name, c in [("ib_om0_scale", "om0 (t±1 visible)", "#4c72b0"),
                     ("ib_om1_scale", "om1 (t±1 hidden)", "#d55e00")]:
    tr = traj(lab)
    if tr:
        s, d, amp = tr
        a1.semilogx(s, d, "-o", c=c, label=name, ms=3)
        a2.semilogx(s, amp, "-o", c=c, label=name, ms=3)
a1.axhline(RAW, ls=":", c="k", label=f"raw ({RAW:.2f})")
a1.set_xlabel("training updates"); a1.set_ylabel("d′"); a1.set_title("Detection vs training"); a1.legend(fontsize=8)
a2.set_xlabel("training updates"); a2.set_ylabel("amp_ratio"); a2.set_title("Amplitude vs training"); a2.legend(fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "f8_trajectory.png", dpi=150); plt.close(fig)

# ---- F9: spike-aware loss dose-response (arch_l2_om0 body) ----
def _meand(label):
    d = load(label, "dprime")
    return st.mean(float(d[u]["dprime_deep"]) for u in units if u in d) if d else None

_base = [_meand(l) for l in labels("ib_arch_l2_om0_s*")]
if _base and all(v is not None for v in _base):
    b = st.mean(_base); bsd = st.stdev(_base) if len(_base) > 1 else 0.0
    soft = [(w, _meand(f"ib_arch_l2_om0_w{w}_s0")) for w in (3, 10, 30)]
    gate = [(w, _meand(f"ib_arch_l2_om0_g{w}_s0")) for w in (100, 300, 1000)]
    focal = (10, _meand("ib_arch_l2_om0_w10g2_s0"))
    hard = (1000, _meand("ib_arch_l2_om0_g1000h_s0"))
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.axhspan(b - 2 * bsd, b + 2 * bsd, color="gray", alpha=0.25, label="baseline ±2σ")
    ax.axhline(b, color="#7f7f7f", lw=1, label=f"arch_l2_om0 baseline ({b:.3f})")
    ax.axhline(RAW, ls=":", c="k", label=f"raw ({RAW:.3f})")
    xs, ys = zip(*[(w, d) for w, d in soft if d]); ax.plot(xs, ys, "-o", color="#4c72b0", label="soft  1 + λ·|nbr|")
    xs, ys = zip(*[(w, d) for w, d in gate if d]); ax.plot(xs, ys, "-s", color="#dd8452", label="saturating gate")
    if focal[1]:
        ax.plot([focal[0]], [focal[1]], "X", color="#c44e52", ms=12, label="focal γ=2")
    if hard[1]:
        ax.plot([hard[0]], [hard[1]], "D", color="#8172b3", ms=8, label="hard gate")
    ax.set_xscale("log"); ax.set_xlabel("spike weight  λ  (log)"); ax.set_ylabel("d′")
    ax.set_title("Spike-aware loss: detection vs weight (arch_l2_om0 body)")
    ax.legend(fontsize=7.5, loc="upper right", framealpha=0.9)
    fig.tight_layout(); fig.savefig(FIG / "f9_spike_weight.png", dpi=150); plt.close(fig)

print("wrote:", sorted(p.name for p in FIG.glob("f*.png")))
