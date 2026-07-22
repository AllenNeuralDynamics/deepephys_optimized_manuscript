#!/usr/bin/env python3
"""Collate in-band scores into the manuscript tables.

Reads
-----
results/runs.csv                      run manifest (label, config, seed, loss, ...)
results/scores/<label>_dprime.csv     per-unit d' (unit_id, dprime_deep, dprime_deep_fixed,
                                       dprime_raw, snr_deep, ...)
results/scores/<label>_diag.csv       per-unit waveform (unit_id, amp_ratio, fwhm_ratio,
                                       temporal_cos, spatial_cos, ...)
results/scores/<label>/<label>_best_* equivalent endpoint layout for trajectory/control runs

Writes (results/tables/, both .csv and .md)
-------------------------------------------
master_table            one row per run: config, loss, mean-over-units of every metric
perunit_amp             amp_ratio,      units (rows, by baseline d') x models (cols)
perunit_dprime          dprime_deep,    units x models
perunit_dprime_delta    dprime_deep - dprime_raw, units x models
noise_floor             sigma of d'/amp over seed replicates, per config
model_family_summary    run/config counts and d' range by experiment family and budget
table_coverage          one row per ledger entry: endpoint layout, inclusion, and exclusion reason

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


def _write(df: pd.DataFrame, stem: str, index: bool = False) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / f"{stem}.csv", index=index)
    try:
        md = df.to_markdown(index=index, floatfmt=".3f")
    except Exception:  # tabulate not installed
        md = df.to_csv(index=index)
    (TABLES / f"{stem}.md").write_text(md.rstrip() + "\n")


def endpoint_paths(label: str) -> tuple[str, Path, Path] | None:
    """Resolve one complete endpoint pair without treating checkpoints as independent runs."""
    candidates = (
        ("root", SCORES / f"{label}_dprime.csv", SCORES / f"{label}_diag.csv"),
        ("nested_best", SCORES / label / f"{label}_best_dprime.csv",
         SCORES / label / f"{label}_best_diag.csv"),
    )
    for layout, dprime_path, diag_path in candidates:
        if dprime_path.exists() and diag_path.exists():
            return layout, dprime_path, diag_path

    partial = [str(path.relative_to(REPO)) for _, dp, dg in candidates
               for path in (dp, dg) if path.exists()]
    if partial:
        raise FileNotFoundError(
            f"incomplete endpoint pair for {label}: found {', '.join(partial)}"
        )
    return None


def experiment_family(run: pd.Series) -> str:
    tier = str(run["tier"])
    config = str(run["config"])
    if tier in {"scale", "full96_duration"}:
        return "duration_diagnostic"
    if tier in {"opt4_width", "opt5_schedule", "opt6_depth"}:
        return "width_schedule_followup"
    if tier == "recipe":
        return "recipe_screen"
    if tier == "opt2_rep":
        return "recipe_replication"
    if tier == "opt2_diag":
        return "gradient_diagnostic"
    if tier == "opt2_method":
        return "integration_control"
    if tier == "opt3_arch":
        return "naf_control"
    if tier == "weight2":
        return "corrected_weighting"
    if any(token in config for token in ("_w3", "_w10", "_w30", "_g100", "_g300",
                                          "_g1000")):
        return "legacy_weighting_screen"
    return "architecture_screen"


def budget_group(run: pd.Series) -> str:
    if str(run["tier"]) == "scale":
        return "long_211.5M_windows"
    if str(run["tier"]) == "full96_duration":
        return "duration_54.0M_windows"
    if str(run["train_chunks"]) == "4":
        return "short_~18M_windows"
    return f"train_chunks_{run['train_chunks']}"


def load_run(label: str) -> tuple[pd.DataFrame, str, Path, Path] | None:
    """Merge a run's per-unit d' and diagnostic CSVs on unit_id; return per-unit rows."""
    resolved = endpoint_paths(label)
    if resolved is None:
        return None
    layout, dprime_path, diag_path = resolved
    dp = pd.read_csv(dprime_path)
    dg = pd.read_csv(diag_path)
    per_unit = dp.merge(dg, on="unit_id", how="outer")
    per_unit.insert(0, "model", label)
    return per_unit, layout, dprime_path, diag_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=str(REPO / "results" / "runs.csv"))
    args = ap.parse_args()

    manifest = pd.read_csv(args.manifest, keep_default_na=False)
    all_metrics = [m for m in DPRIME_METRICS + DIAG_METRICS]

    master_rows, per_unit_frames, scored, pending, coverage_rows = [], [], [], [], []
    for _, run in manifest.iterrows():
        label = run["label"]
        loaded = load_run(label)
        if loaded is None:
            pending.append(label)
            state = str(run["state"]).lower()
            if state in {"running", "initializing"}:
                reason = "training_in_progress"
            elif state == "aborted":
                reason = "aborted"
            else:
                reason = "no_endpoint_scores"
            coverage_rows.append({
                "label": label, "experiment_family": experiment_family(run),
                "budget_group": budget_group(run), "included": False,
                "endpoint_layout": "", "dprime_path": "", "diag_path": "",
                "reason": reason,
            })
            if str(run["scored"]).lower() == "yes":
                raise FileNotFoundError(f"ledger marks {label} scored, but endpoint files are missing")
            continue
        per_unit, layout, dprime_path, diag_path = loaded
        scored.append(label)
        per_unit_frames.append(per_unit)
        coverage_rows.append({
            "label": label, "experiment_family": experiment_family(run),
            "budget_group": budget_group(run), "included": True,
            "endpoint_layout": layout,
            "dprime_path": str(dprime_path.relative_to(REPO)),
            "diag_path": str(diag_path.relative_to(REPO)), "reason": "",
        })
        row = {"label": label, "experiment_family": experiment_family(run),
               "budget_group": budget_group(run), "config": run["config"],
               "seed": run["seed"], "loss": run["loss"], "tier": run["tier"],
               "train_chunks": run["train_chunks"]}
        for m in all_metrics:
            row[m] = per_unit[m].mean() if m in per_unit else pd.NA
        master_rows.append(row)

    print(f"scored: {len(scored)}/{len(manifest)}   pending: {len(pending)}")
    if not master_rows:
        print("No scored runs yet — nothing written. (Drop CSVs in results/scores/ and re-run.)")
        return

    master = pd.DataFrame(master_rows).sort_values("dprime_deep", ascending=False,
                                                   ignore_index=True)
    _write(master, "master_table")
    family_summary = (master.groupby(["experiment_family", "budget_group"], as_index=False)
                      .agg(runs=("label", "size"),
                           configurations=("config", "nunique"),
                           dprime_min=("dprime_deep", "min"),
                           dprime_max=("dprime_deep", "max"))
                      .sort_values(["budget_group", "experiment_family"], ignore_index=True))
    _write(family_summary, "model_family_summary")
    _write(pd.DataFrame(coverage_rows), "table_coverage")

    # Descriptive training-seed variability for each replicated config.
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
