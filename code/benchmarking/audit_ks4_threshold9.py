#!/usr/bin/env python3
"""Audit the full-recording Full96 omission1 Kilosort threshold-9 result."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from codeocean import CodeOcean

import audit_ks4_results as common


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO / "results" / "benchmarking" / "ks4_full_threshold9"
BASELINE_COMPUTATION_ID = "2ad21011-a937-44dc-a370-5280049621ef"
THRESHOLD9_COMPUTATION_ID = "748787df-c7f1-4d45-9d51-9f9b5fd9cedc"
PIPELINE_ID = "5a096db9-3fd7-4984-b5a3-f409b4c8b6ee"
THRESHOLD9_CAPSULE_ID = "eb0a6d2f-2418-4a0a-9765-beaa973745db"
THRESHOLD9_CAPSULE_COMMIT = "ff43f0d"


def load_run(client: CodeOcean, computation_id: str) -> dict:
    computation = client.computations.get_computation(computation_id)
    if computation.exit_code != 0 or not computation.has_results:
        raise RuntimeError(
            f"computation {computation_id} is not successful: "
            f"exit={computation.exit_code}, results={computation.has_results}"
        )
    return {
        "computation": computation,
        "performances": common._load_csv(
            client, computation_id, common.PERFORMANCES
        ),
        "unit_counts": common._load_csv(
            client, computation_id, common.UNIT_COUNTS
        ),
        "run_times": common._load_csv(
            client, computation_id, common.RUN_TIMES
        ),
        "spike_counts": common._sorting_spike_counts(client, computation_id),
    }


def sorter_params(
    client: CodeOcean, computation_id: str, sorting_case: str
) -> dict:
    root = f"gt_studies/{common.SESSION}/results"
    folder = client.computations.list_computation_results(computation_id, root)
    candidates = [
        item.path
        for item in folder.items
        if item.type == "folder" and item.name.startswith(f"{sorting_case}_")
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected one {sorting_case} result, found {candidates}"
        )
    provenance = json.loads(
        common._download(
            client,
            computation_id,
            f"{candidates[0]}/sorting/provenance.json",
        )
    )
    return provenance["annotations"]["__sorting_info__"]["params"][
        "sorter_params"
    ]


def deep_sorter_params(client: CodeOcean, computation_id: str) -> dict:
    return sorter_params(client, computation_id, "deepks4")


def raw_sorter_params(client: CodeOcean, computation_id: str) -> dict:
    return sorter_params(client, computation_id, "ks4")


def controlled_parameter_changes(baseline: dict, candidate: dict) -> dict:
    keys = sorted(set(baseline) | set(candidate))
    changes = {
        key: {"baseline": baseline.get(key), "candidate": candidate.get(key)}
        for key in keys
        if baseline.get(key) != candidate.get(key)
    }
    if changes != {"Th_learned": {"baseline": 8, "candidate": 9}}:
        raise ValueError(f"unexpected sorter parameter changes: {changes}")
    return changes


def paired_comparison(
    baseline: pd.DataFrame, candidate: pd.DataFrame
) -> pd.DataFrame:
    fields = [
        "gt_unit_id",
        "accuracy",
        "precision",
        "recall",
        "true_positive_injected_spikes",
        "false_positive_spikes_in_matched_cluster",
    ]
    merged = baseline[fields].merge(
        candidate[fields], on="gt_unit_id", suffixes=("_8", "_9"), validate="1:1"
    )
    for metric in fields[1:]:
        merged[f"delta_{metric}"] = merged[f"{metric}_9"] - merged[f"{metric}_8"]
    return merged


def paired_accuracy_bootstrap(
    comparison: pd.DataFrame, draws: int = 200_000
) -> dict[str, float | int]:
    differences = comparison["delta_accuracy"].to_numpy()
    rng = np.random.default_rng(0)
    indices = rng.integers(0, len(differences), size=(draws, len(differences)))
    bootstrap = differences[indices].mean(axis=1)
    low, high = np.quantile(bootstrap, [0.025, 0.975])
    return {
        "draws": draws,
        "seed": 0,
        "mean_difference": float(differences.mean()),
        "median_difference": float(np.median(differences)),
        "interval_95_low": float(low),
        "interval_95_high": float(high),
        "probability_mean_difference_gt_0": float((bootstrap > 0).mean()),
        "units_improved": int((differences > 0).sum()),
        "units_worsened": int((differences < 0).sum()),
        "units_unchanged": int((differences == 0).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    client = CodeOcean(
        domain=os.environ["CODEOCEAN_DOMAIN"], token=os.environ["CODEOCEAN_TOKEN"]
    )

    baseline = load_run(client, BASELINE_COMPUTATION_ID)
    candidate = load_run(client, THRESHOLD9_COMPUTATION_ID)
    common._assert_raw_identity({"om0": baseline, "om1": candidate})
    parameter_changes = controlled_parameter_changes(
        deep_sorter_params(client, BASELINE_COMPUTATION_ID),
        deep_sorter_params(client, THRESHOLD9_COMPUTATION_ID),
    )
    gt_counts = common._gt_spike_counts(client, BASELINE_COMPUTATION_ID)

    raw_performance = baseline["performances"].query("sorting_case == 'ks4'")
    raw_per_unit = common._event_accounting("raw AP", raw_performance, gt_counts)
    raw_per_unit.insert(1, "Th_learned", 8)
    raw_summary = common._summary_row(
        "raw AP",
        f"{BASELINE_COMPUTATION_ID};{THRESHOLD9_COMPUTATION_ID}",
        raw_performance,
        baseline["unit_counts"].query("sorting_case == 'ks4'").iloc[0],
        baseline["run_times"].query("sorting_case == 'ks4'").iloc[0],
        baseline["spike_counts"]["ks4"],
        raw_per_unit,
    )
    raw_summary["Th_learned"] = 8
    summary_rows = [raw_summary]
    per_unit_frames = [raw_per_unit]
    denoised_per_unit = {}
    for threshold, computation_id, run in (
        (8, BASELINE_COMPUTATION_ID, baseline),
        (9, THRESHOLD9_COMPUTATION_ID, candidate),
    ):
        performance = run["performances"].query("sorting_case == 'deepks4'")
        per_unit = common._event_accounting(
            f"Full96 omission1 Th_learned={threshold}", performance, gt_counts
        )
        per_unit.insert(1, "Th_learned", threshold)
        per_unit_frames.append(per_unit)
        denoised_per_unit[threshold] = per_unit
        summary = common._summary_row(
            f"Full96 omission1 Th_learned={threshold}",
            computation_id,
            performance,
            run["unit_counts"].query("sorting_case == 'deepks4'").iloc[0],
            run["run_times"].query("sorting_case == 'deepks4'").iloc[0],
            run["spike_counts"]["deepks4"],
            per_unit,
        )
        summary["Th_learned"] = threshold
        summary_rows.append(summary)

    summary = pd.DataFrame(summary_rows)
    summary.insert(1, "Th_learned", summary.pop("Th_learned"))
    per_unit = pd.concat(per_unit_frames, ignore_index=True)
    comparison = paired_comparison(
        denoised_per_unit[8], denoised_per_unit[9]
    )
    bootstrap = paired_accuracy_bootstrap(comparison)

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output / "summary.csv", index=False, float_format="%.12g")
    per_unit.to_csv(output / "per_unit.csv", index=False, float_format="%.12g")
    comparison.to_csv(
        output / "threshold8_vs9_per_unit.csv", index=False, float_format="%.12g"
    )
    manifest = {
        "pipeline_id": PIPELINE_ID,
        "baseline_computation_id": BASELINE_COMPUTATION_ID,
        "threshold9_computation_id": THRESHOLD9_COMPUTATION_ID,
        "threshold9_capsule_id": THRESHOLD9_CAPSULE_ID,
        "threshold9_capsule_commit": THRESHOLD9_CAPSULE_COMMIT,
        "duration_s": common.DURATION_S,
        "raw_arm_identity": "exact",
        "controlled_sorter_parameter_changes": parameter_changes,
        "paired_unit_accuracy_bootstrap": bootstrap,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote full threshold-9 audit to {output}")


if __name__ == "__main__":
    main()