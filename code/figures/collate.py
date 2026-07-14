#!/usr/bin/env python3
"""Collate in-band scores into the manuscript tables.

Reads
-----
results/runs.csv                      run manifest (label, config, seed, loss, ...)
results/scores/<label>_dprime.csv     per-unit d' (unit_id, dprime_deep, dprime_deep_fixed,
                                       dprime_raw, snr_deep, ...)
results/scores/<label>_diag.csv       per-unit waveform (unit_id, amp_ratio, fwhm_ratio,
                                       temporal_cos, spatial_cos, ...)

Writes (results/tables/, both .csv and .md)
-------------------------------------------
master_table            one row per run: config, loss, mean-over-units of every metric
perunit_amp             amp_ratio,      units (rows, by baseline d') x models (cols)
perunit_dprime          dprime_deep,    units x models
perunit_dprime_delta    dprime_deep - dprime_raw, units x models
noise_floor             sigma of d'/amp over seed replicates, per config

Runs without score files yet are reported as pending and skipped, so this is safe to run at any
time. No results are invented.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DPRIME_METRICS = ["dprime_deep", "dprime_deep_fixed", "dprime_raw", "snr_deep"]
DIAG_METRICS = ["amp_ratio", "fwhm_ratio", "temporal_cos", "spatial_cos"]

REPO = Path(__file__).resolve().parents[2]
SCORES = REPO / "results" / "scores"
TABLES = REPO / "results" / "tables"


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _write(df: pd.DataFrame, stem: str, index: bool = False) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / f"{stem}.csv", index=index)
    try:
        md = df.to_markdown(index=index, floatfmt=".3f")
    except Exception:  # tabulate not installed
        md = df.to_csv(index=index)
    (TABLES / f"{stem}.md").write_text(md + "\n")


def load_run(label: str) -> pd.DataFrame | None:
    """Merge a run's per-unit d' and diagnostic CSVs on unit_id; return per-unit rows."""
    dp = _read(SCORES / f"{label}_dprime.csv")
    dg = _read(SCORES / f"{label}_diag.csv")
    if dp is None and dg is None:
        return None
    if dp is None:
        dp = pd.DataFrame({"unit_id": dg["unit_id"]})
    if dg is None:
        dg = pd.DataFrame({"unit_id": dp["unit_id"]})
    per_unit = dp.merge(dg, on="unit_id", how="outer")
    per_unit.insert(0, "model", label)
    return per_unit


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=str(REPO / "results" / "runs.csv"))
    args = ap.parse_args()

    manifest = pd.read_csv(args.manifest)
    all_metrics = [m for m in DPRIME_METRICS + DIAG_METRICS]

    master_rows, per_unit_frames, scored, pending = [], [], [], []
    for _, run in manifest.iterrows():
        label = run["label"]
        per_unit = load_run(label)
        if per_unit is None:
            pending.append(label)
            continue
        scored.append(label)
        per_unit_frames.append(per_unit)
        row = {"label": label, "config": run["config"], "seed": run["seed"],
               "loss": run["loss"], "tier": run["tier"]}
        for m in all_metrics:
            row[m] = per_unit[m].mean() if m in per_unit else pd.NA
        master_rows.append(row)

    print(f"scored: {len(scored)}/{len(manifest)}   pending: {len(pending)}")
    if not master_rows:
        print("No scored runs yet — nothing written. (Drop CSVs in results/scores/ and re-run.)")
        return

    master = pd.DataFrame(master_rows).sort_values("dprime_deep", ascending=False, ignore_index=True)
    _write(master, "master_table")

    # Noise floor: sigma over seed replicates of each config.
    nf = (master.groupby("config")
                .agg(n=("seed", "count"),
                     dprime_deep_sd=("dprime_deep", "std"),
                     amp_ratio_sd=("amp_ratio", "std"))
                .reset_index())
    _write(nf, "noise_floor")

    # Per-unit matrices: units (rows, sorted by baseline d') x models (cols).
    per_unit_all = pd.concat(per_unit_frames, ignore_index=True)
    unit_order = None
    if "dprime_raw" in per_unit_all:
        unit_order = (per_unit_all.groupby("unit_id")["dprime_raw"].mean()
                      .sort_values(ascending=False).index)

    def matrix(value: str, stem: str, extra: pd.Series | None = None) -> None:
        if value not in per_unit_all:
            return
        src = per_unit_all if extra is None else per_unit_all.assign(**{value: extra})
        mat = src.pivot_table(index="unit_id", columns="model", values=value)
        if unit_order is not None:
            mat = mat.reindex(unit_order)
        mat.loc["mean"] = mat.mean()
        _write(mat.reset_index(), stem, index=False)

    matrix("amp_ratio", "perunit_amp")
    matrix("dprime_deep", "perunit_dprime")
    if {"dprime_deep", "dprime_raw"}.issubset(per_unit_all.columns):
        matrix("dprime_deep", "perunit_dprime_delta",
               extra=per_unit_all["dprime_deep"] - per_unit_all["dprime_raw"])

    print(f"wrote tables to {TABLES}")
    if pending:
        print("pending runs:", ", ".join(pending))


if __name__ == "__main__":
    main()
