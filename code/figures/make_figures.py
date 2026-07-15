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

# display name, seed-glob, loss
CFG = [
    ("base32", "ib_champion_s*", "charb"),
    ("omission0", "ib_omission0_s*", "charb"),
    ("champ_l2", "ib_champ_l2_s*", "L2"),
    ("omission0_l2", "ib_omission0_l2_s*", "L2"),
    ("base64", "ib_base64_s*", "charb"),
    ("om0_scale", "ib_om0_scale", "L2"),
    ("om1_scale", "ib_om1_scale", "L2"),
]
PATS = {c[0]: c[1] for c in CFG}
NAMES = [c[0] for c in CFG]


def labels(pat):
    if "*" in pat:
        return [Path(f).name[:-11] for f in sorted(glob.glob(str(S / (pat + "_dprime.csv"))))]
    return [pat] if (S / (pat + "_dprime.csv")).exists() else []


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
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.bar(range(len(order)), [dmean[i] for i in order], yerr=[2 * dsd[i] for i in order],
       capsize=4, color=["#d55e00" if NAMES[i] == "base64" else "#4c72b0" for i in order])
ax.axhline(RAW, ls=":", c="k", label=f"raw ({RAW:.3f})")
ci = NAMES.index("base32")
ax.axhspan(dmean[ci] - 2 * dsd[ci], dmean[ci] + 2 * dsd[ci], color="gray", alpha=0.25,
           label="base32 ±2σ (noise floor)")
ax.set_xticks(range(len(order)))
ax.set_xticklabels([NAMES[i] for i in order], rotation=45, ha="right")
ax.set_ylabel("d′  (mean ± 2σ over seeds)")
ax.set_ylim(4.2, 4.55)
ax.set_title("Detection d′ across architectures (in-band)")
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "f1_dprime_ranking.png", dpi=150); plt.close(fig)

# ---- F4: SNR gain vs Δd' ----
fig, ax = plt.subplots(figsize=(6, 4.5))
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
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
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

print("wrote:", sorted(p.name for p in FIG.glob("f*.png")))
