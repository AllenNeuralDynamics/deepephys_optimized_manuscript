#!/usr/bin/env python3
"""Audit the full-recording Kilosort threshold matrix and recovery provenance."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from codeocean import CodeOcean

import audit_ks4_results as common
import audit_ks4_threshold9 as threshold9


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO / "results" / "benchmarking" / "ks4_full_threshold_matrix"
BASELINE_ID = "2ad21011-a937-44dc-a370-5280049621ef"
OMISSION0_BASELINE_ID = "db76c533-9f39-46e6-98fe-e83adf56ea51"
LEARNED9_ID = "748787df-c7f1-4d45-9d51-9f9b5fd9cedc"
LEARNED10_FAILED_ID = "9c4dd3bf-f773-49f8-b332-683aa17947d3"
LEARNED10_RECOVERY_ID = "07338f3d-31b2-43d3-bc78-62b3a1852858"
LEARNED10_SORTER_ASSET_ID = "07a54bd7-f145-41c8-b19e-1d8e05c060b2"
LEARNED10_75_ID = "418f3a7b-1e3a-4d11-a85d-191fd05a37da"
OMISSION0_LEARNED10_75_ID = "a2ccfc54-5109-44ef-9968-b3c1435fcffc"
RAW_LEARNED10_75_ID = "fab61c02-f1d5-4d26-965b-2cdb47aad29b"
UNIVERSAL10_ID = "a7a8065f-b4b2-43a4-acf6-b87e7ff02201"
PIPELINE_ID = "5a096db9-3fd7-4984-b5a3-f409b4c8b6ee"
SORTER_CAPSULE_ID = "eb0a6d2f-2418-4a0a-9765-beaa973745db"
SORTER_COMMITS = {
    "raw 9/10.75": "4826f2e",
    "omission0 9/10.75": "4826f2e",
    "9/9": "ff43f0d",
    "9/10": "1f7d371",
    "9/10.75": "4826f2e",
    "10/9": "43b46d9",
}


def assert_case_identity(first: dict, second: dict, sorting_case: str) -> None:
    """Require exact evaluator, unit-count, runtime, and event-count identity."""
    left = (
        first["performances"]
        .query("sorting_case == @sorting_case")
        .sort_values("gt_unit_id")
        .reset_index(drop=True)
    )
    right = (
        second["performances"]
        .query("sorting_case == @sorting_case")
        .sort_values("gt_unit_id")
        .reset_index(drop=True)
    )
    for column in ("gt_unit_id", "accuracy", "precision", "recall"):
        if not np.array_equal(left[column].to_numpy(), right[column].to_numpy()):
            raise ValueError(f"{sorting_case} performance differs for {column}")
    if first["spike_counts"][sorting_case] != second["spike_counts"][sorting_case]:
        raise ValueError(f"{sorting_case} total spike-event count differs")
    for table, column in (("unit_counts", "num_sorter"), ("run_times", "run_times")):
        left_value = first[table].query("sorting_case == @sorting_case").iloc[0][column]
        right_value = second[table].query("sorting_case == @sorting_case").iloc[0][column]
        if left_value != right_value:
            raise ValueError(
                f"{sorting_case} {column} differs: {left_value} != {right_value}"
            )


def parameter_changes(
    baseline: dict, candidate: dict, expected: dict
) -> dict:
    keys = sorted(set(baseline) | set(candidate))
    changes = {
        key: {"baseline": baseline.get(key), "candidate": candidate.get(key)}
        for key in keys
        if baseline.get(key) != candidate.get(key)
    }
    if changes != expected:
        raise ValueError(f"unexpected sorter parameter changes: {changes}")
    return changes


def standard_case(
    label: str,
    th_universal: float,
    th_learned: float,
    computation_id: str,
    run: dict,
    gt_counts: dict[int, int],
) -> tuple[dict, pd.DataFrame]:
    performance = run["performances"].query("sorting_case == 'deepks4'")
    per_unit = common._event_accounting(label, performance, gt_counts)
    per_unit.insert(1, "Th_universal", th_universal)
    per_unit.insert(2, "Th_learned", th_learned)
    summary = common._summary_row(
        label,
        computation_id,
        performance,
        run["unit_counts"].query("sorting_case == 'deepks4'").iloc[0],
        run["run_times"].query("sorting_case == 'deepks4'").iloc[0],
        run["spike_counts"]["deepks4"],
        per_unit,
    )
    summary.update(Th_universal=th_universal, Th_learned=th_learned)
    return summary, per_unit


def recovered_case(
    client: CodeOcean, gt_counts: dict[int, int]
) -> tuple[dict, pd.DataFrame, dict]:
    computation = client.computations.get_computation(LEARNED10_RECOVERY_ID)
    if computation.exit_code != 0 or not computation.has_results:
        raise RuntimeError(
            f"recovery computation is not successful: exit={computation.exit_code}, "
            f"results={computation.has_results}"
        )
    summary = common._load_csv(
        client, LEARNED10_RECOVERY_ID, "recovered_threshold10_summary.csv"
    ).iloc[0]
    raw = common._load_csv(
        client, LEARNED10_RECOVERY_ID, "recovered_threshold10_per_unit.csv"
    )
    manifest = json.loads(
        common._download(
            client, LEARNED10_RECOVERY_ID, "recovered_threshold10_manifest.json"
        )
    )
    if manifest["gt_events"] != sum(gt_counts.values()):
        raise ValueError("recovered result used unexpected GT event count")
    per_unit = pd.DataFrame(
        {
            "input": "Full96 omission1 9/10",
            "Th_universal": 9,
            "Th_learned": 10,
            "gt_unit_id": raw["gt_unit_id"],
            "gt_spike_events": raw["num_gt"].astype(int),
            "accuracy": raw["accuracy"],
            "precision": raw["precision"],
            "recall": raw["recall"],
            "true_positive_injected_spikes": raw["tp"].astype(int),
            "matched_cluster_spikes": (raw["tp"] + raw["fp"]).astype(int),
            "false_positive_spikes_in_matched_cluster": raw["fp"].astype(int),
        }
    )
    matched = per_unit[per_unit["accuracy"] > 0]
    summary_row = {
        "input": "Full96 omission1 9/10",
        "source_computation_id": LEARNED10_RECOVERY_ID,
        "Th_universal": 9,
        "Th_learned": 10,
        "mean_accuracy": float(summary["mean_accuracy"]),
        "mean_precision": float(summary["mean_precision"]),
        "mean_recall": float(summary["mean_recall"]),
        "gt_units_detected": int(summary["gt_units_detected"]),
        "gt_units_above_0_8_accuracy": int(summary["gt_units_above_0_8_accuracy"]),
        "sorter_units": int(summary["sorter_units"]),
        "sorted_spike_events": int(summary["sorted_spike_events"]),
        "sorted_spike_events_per_s": float(summary["sorted_spike_events_per_s"]),
        "sorted_spike_events_per_sorter_unit": int(summary["sorted_spike_events"])
        / int(summary["sorter_units"]),
        "sorter_run_time_s": float(summary["sorter_run_time_s"]),
        "gt_units_matched": len(matched),
        "injected_spikes_in_matched_gt_units": int(matched["gt_spike_events"].sum()),
        "true_positive_injected_spikes": int(summary["true_positive_injected_spikes"]),
        "matched_cluster_spikes": int(
            summary["true_positive_injected_spikes"]
            + summary["false_positive_spikes_in_gt_matched_clusters"]
        ),
        "false_positive_spikes_in_matched_clusters": int(
            summary["false_positive_spikes_in_gt_matched_clusters"]
        ),
    }
    return summary_row, per_unit, manifest["sorter_parameters"]


def followup_comparison(
    reference: pd.DataFrame, candidates: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    metrics = [
        "accuracy",
        "precision",
        "recall",
        "true_positive_injected_spikes",
        "false_positive_spikes_in_matched_cluster",
    ]
    frames = []
    reference = reference.set_index("gt_unit_id")
    for label, candidate in candidates.items():
        candidate = candidate.set_index("gt_unit_id").reindex(reference.index)
        if candidate.index.has_duplicates or candidate[metrics].isna().any().any():
            raise ValueError(f"candidate {label} does not match reference GT units")
        frame = pd.DataFrame({"gt_unit_id": reference.index, "candidate": label})
        for metric in metrics:
            frame[f"reference_{metric}"] = reference[metric].to_numpy()
            frame[f"candidate_{metric}"] = candidate[metric].to_numpy()
            frame[f"delta_{metric}"] = (
                candidate[metric] - reference[metric]
            ).to_numpy()
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    client = CodeOcean(
        domain=os.environ["CODEOCEAN_DOMAIN"], token=os.environ["CODEOCEAN_TOKEN"]
    )

    baseline = threshold9.load_run(client, BASELINE_ID)
    omission0_baseline = threshold9.load_run(client, OMISSION0_BASELINE_ID)
    omission0_learned10_75 = threshold9.load_run(
        client, OMISSION0_LEARNED10_75_ID
    )
    raw_learned10_75 = threshold9.load_run(client, RAW_LEARNED10_75_ID)
    learned9 = threshold9.load_run(client, LEARNED9_ID)
    learned10_75 = threshold9.load_run(client, LEARNED10_75_ID)
    universal10 = threshold9.load_run(client, UNIVERSAL10_ID)
    common._assert_raw_identity({"om0": baseline, "om1": omission0_baseline})
    common._assert_raw_identity(
        {"om0": omission0_baseline, "om1": omission0_learned10_75}
    )
    assert_case_identity(omission0_learned10_75, raw_learned10_75, "deepks4")
    common._assert_raw_identity({"om0": baseline, "om1": learned9})
    common._assert_raw_identity({"om0": learned9, "om1": learned10_75})
    common._assert_raw_identity({"om0": learned9, "om1": universal10})
    gt_counts = common._gt_spike_counts(client, BASELINE_ID)

    params_9_8 = threshold9.deep_sorter_params(client, BASELINE_ID)
    params_omission0_9_8 = threshold9.deep_sorter_params(
        client, OMISSION0_BASELINE_ID
    )
    params_omission0_9_10_75 = threshold9.deep_sorter_params(
        client, OMISSION0_LEARNED10_75_ID
    )
    params_raw_9_8 = threshold9.raw_sorter_params(
        client, OMISSION0_BASELINE_ID
    )
    params_raw_9_10_75 = threshold9.raw_sorter_params(
        client, RAW_LEARNED10_75_ID
    )
    params_9_9 = threshold9.deep_sorter_params(client, LEARNED9_ID)
    params_9_10_75 = threshold9.deep_sorter_params(client, LEARNED10_75_ID)
    params_10_9 = threshold9.deep_sorter_params(client, UNIVERSAL10_ID)
    learned10_summary, learned10_units, params_9_10 = recovered_case(
        client, gt_counts
    )
    changes = {
        "raw_9/8_to_9/10.75": parameter_changes(
            params_raw_9_8,
            params_raw_9_10_75,
            {"Th_learned": {"baseline": 8, "candidate": 10.75}},
        ),
        "omission0_9/8_to_9/10.75": parameter_changes(
            params_omission0_9_8,
            params_omission0_9_10_75,
            {"Th_learned": {"baseline": 8, "candidate": 10.75}},
        ),
        "9/8_to_9/9": parameter_changes(
            params_9_8,
            params_9_9,
            {"Th_learned": {"baseline": 8, "candidate": 9}},
        ),
        "9/9_to_9/10": parameter_changes(
            params_9_9,
            params_9_10,
            {"Th_learned": {"baseline": 9, "candidate": 10}},
        ),
        "9/10_to_9/10.75": parameter_changes(
            params_9_10,
            params_9_10_75,
            {"Th_learned": {"baseline": 10, "candidate": 10.75}},
        ),
        "9/9_to_10/9": parameter_changes(
            params_9_9,
            params_10_9,
            {"Th_universal": {"baseline": 9, "candidate": 10}},
        ),
    }

    raw_performance = baseline["performances"].query("sorting_case == 'ks4'")
    raw_units = common._event_accounting("raw AP 9/8", raw_performance, gt_counts)
    raw_units.insert(1, "Th_universal", 9)
    raw_units.insert(2, "Th_learned", 8)
    raw_summary = common._summary_row(
        "raw AP 9/8",
        (
            f"{BASELINE_ID};{OMISSION0_BASELINE_ID};"
            f"{OMISSION0_LEARNED10_75_ID};{LEARNED9_ID};"
            f"{LEARNED10_75_ID};{UNIVERSAL10_ID}"
        ),
        raw_performance,
        baseline["unit_counts"].query("sorting_case == 'ks4'").iloc[0],
        baseline["run_times"].query("sorting_case == 'ks4'").iloc[0],
        baseline["spike_counts"]["ks4"],
        raw_units,
    )
    raw_summary.update(Th_universal=9, Th_learned=8)

    raw_10_75_performance = raw_learned10_75["performances"].query(
        "sorting_case == 'ks4'"
    )
    raw_10_75_units = common._event_accounting(
        "raw AP 9/10.75", raw_10_75_performance, gt_counts
    )
    raw_10_75_units.insert(1, "Th_universal", 9)
    raw_10_75_units.insert(2, "Th_learned", 10.75)
    raw_10_75_summary = common._summary_row(
        "raw AP 9/10.75",
        RAW_LEARNED10_75_ID,
        raw_10_75_performance,
        raw_learned10_75["unit_counts"].query("sorting_case == 'ks4'").iloc[0],
        raw_learned10_75["run_times"].query("sorting_case == 'ks4'").iloc[0],
        raw_learned10_75["spike_counts"]["ks4"],
        raw_10_75_units,
    )
    raw_10_75_summary.update(Th_universal=9, Th_learned=10.75)

    case_specs = (
        ("Full96 omission1 9/8", 9, 8, BASELINE_ID, baseline),
        ("Full96 omission1 9/9", 9, 9, LEARNED9_ID, learned9),
        ("Full96 omission1 9/10.75", 9, 10.75, LEARNED10_75_ID, learned10_75),
        ("Full96 omission1 10/9", 10, 9, UNIVERSAL10_ID, universal10),
        (
            "Full96 omission0 9/10.75",
            9,
            10.75,
            OMISSION0_LEARNED10_75_ID,
            omission0_learned10_75,
        ),
    )
    summaries = [raw_summary, raw_10_75_summary]
    per_unit_frames = [raw_units, raw_10_75_units]
    units_by_label = {}
    for spec in case_specs:
        summary, per_unit = standard_case(*spec, gt_counts)
        summaries.append(summary)
        per_unit_frames.append(per_unit)
        if spec[0].startswith("Full96 omission1 "):
            units_by_label[spec[0].rsplit(" ", 1)[-1]] = per_unit
    summaries.insert(3, learned10_summary)
    per_unit_frames.insert(3, learned10_units)
    units_by_label["9/10"] = learned10_units

    summary = pd.DataFrame(summaries)
    threshold_columns = ["Th_universal", "Th_learned"]
    for offset, column in enumerate(threshold_columns, start=1):
        summary.insert(offset, column, summary.pop(column))
    per_unit = pd.concat(per_unit_frames, ignore_index=True)
    followups = followup_comparison(
        units_by_label["9/9"],
        {
            "9/10": units_by_label["9/10"],
            "9/10.75": units_by_label["9/10.75"],
            "10/9": units_by_label["10/9"],
        },
    )
    bootstraps = {}
    for label in ("9/10", "9/10.75", "10/9"):
        frame = followups.query("candidate == @label")
        bootstraps[label] = threshold9.paired_accuracy_bootstrap(frame)

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output / "summary.csv", index=False, float_format="%.12g")
    per_unit.to_csv(output / "per_unit.csv", index=False, float_format="%.12g")
    followups.to_csv(
        output / "followups_vs_9_9_per_unit.csv", index=False, float_format="%.12g"
    )
    manifest = {
        "pipeline_id": PIPELINE_ID,
        "computation_ids": {
            "raw 9/10.75": RAW_LEARNED10_75_ID,
            "omission0 9/8": OMISSION0_BASELINE_ID,
            "omission0 9/10.75": OMISSION0_LEARNED10_75_ID,
            "9/8": BASELINE_ID,
            "9/9": LEARNED9_ID,
            "9/10_failed_pipeline": LEARNED10_FAILED_ID,
            "9/10_recovery_evaluation": LEARNED10_RECOVERY_ID,
            "9/10.75": LEARNED10_75_ID,
            "10/9": UNIVERSAL10_ID,
        },
        "sorter_capsule_id": SORTER_CAPSULE_ID,
        "sorter_commits": SORTER_COMMITS,
        "learned10_recovered_sorter_asset_id": LEARNED10_SORTER_ASSET_ID,
        "duration_s": common.DURATION_S,
        "raw_baseline_identity": (
            "exact across all computations that retained raw Th_learned=8"
        ),
        "raw_control_identity": (
            "raw 9/10.75 intentionally differs only at Th_learned; the "
            "denoised omission0 9/10.75 arm is exact versus its resume source"
        ),
        "controlled_sorter_parameter_changes": changes,
        "paired_unit_accuracy_bootstraps_vs_9_9": bootstraps,
        "learned10_recovery_reason": (
            "Pipeline evaluation failed only in optional SNR binned plotting; "
            "the completed sorter task was captured and evaluated directly."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote full threshold matrix audit to {output}")


if __name__ == "__main__":
    main()