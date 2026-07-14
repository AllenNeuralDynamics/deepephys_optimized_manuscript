#!/usr/bin/env python3
"""Collate a trajectory run's per-checkpoint scores into a metric-vs-step table.

Reads ``results/scores/<label>/<label>_<tag>_{dprime,diag}.csv`` where ``<tag>`` is
``best`` (validation-loss-selected checkpoint) or ``s<step>`` (the 12 log-spaced
checkpoints), averages each metric over the GT units, and writes
``results/tables/<label>_trajectory.{csv,md}`` sorted by training step.

Usage:
    python collate_trajectory.py <label>          # e.g. ib_om0_scale
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

DPRIME = ["dprime_deep", "dprime_deep_fixed", "dprime_raw", "ddprime", "snr_deep"]
DIAG = ["amp_ratio", "fwhm_ratio", "temporal_cos", "spatial_cos"]
REPO = Path(__file__).resolve().parents[2]


def means(path: Path, cols: list[str]) -> dict:
    df = pd.read_csv(path)
    return {c: float(df[c].mean()) for c in cols if c in df.columns}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("label", help="trajectory run label, e.g. ib_om0_scale")
    args = ap.parse_args()

    sdir = REPO / "results" / "scores" / args.label
    rows = []
    for dp in sorted(sdir.glob(f"{args.label}_*_dprime.csv")):
        tag = re.sub(rf"^{re.escape(args.label)}_(.*)_dprime\.csv$", r"\1", dp.name)
        step = int(tag[1:]) if tag.startswith("s") and tag[1:].isdigit() else None
        row = {"label": args.label, "tag": tag, "step": step}
        row.update(means(dp, DPRIME))
        diag = sdir / f"{args.label}_{tag}_diag.csv"
        if diag.exists():
            row.update(means(diag, DIAG))
        rows.append(row)

    if not rows:
        print(f"no score CSVs found under {sdir}")
        return

    df = pd.DataFrame(rows).sort_values(by="step", na_position="last", ignore_index=True)
    df = df[[c for c in ["label", "tag", "step", *DPRIME, *DIAG] if c in df.columns]]

    out = REPO / "results" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"{args.label}_trajectory.csv", index=False)
    try:
        md = df.to_markdown(index=False, floatfmt=".4f")
    except Exception:  # tabulate not installed
        md = df.to_csv(index=False)
    (out / f"{args.label}_trajectory.md").write_text(md + "\n")

    print(df.to_string(index=False))
    print(f"\nwrote {len(df)} rows -> {out / (args.label + '_trajectory.csv')}")


if __name__ == "__main__":
    main()
