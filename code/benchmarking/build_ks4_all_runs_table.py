#!/usr/bin/env python3
"""Combine all audited raw and denoised Kilosort4 runs into one table."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = REPO / "results" / "benchmarking"
FULL_DURATION_S = 7144.262
FULL_MATRIX = "ks4_full_threshold_matrix/summary.csv"
FULL_MATRIX_PER_UNIT = "ks4_full_threshold_matrix/per_unit.csv"
BASELINE_SUMMARY = "kilosort4_summary.csv"
BASELINE_PER_UNIT = "kilosort4_per_unit.csv"
COMMON_GT_UNITS = (337, 664, 793, 1122, 1143, 1300, 2143)
COMMON_ACCURACY_COLUMN = "mean_accuracy_common_7_gt_units"
COMMON_PRECISION_COLUMN = "mean_precision_common_7_gt_units"
COMMON_RECALL_COLUMN = "mean_recall_common_7_gt_units"
COMMON_TP_COLUMN = "true_positive_injected_spikes_in_common_7_gt_units"
COMMON_FN_COLUMN = "false_negative_injected_spikes_in_common_7_gt_units"
COMMON_FP_COLUMN = "false_positive_spikes_in_common_7_gt_matched_clusters"
COMMON_COLUMNS = (
    COMMON_ACCURACY_COLUMN,
    COMMON_PRECISION_COLUMN,
    COMMON_RECALL_COLUMN,
    COMMON_TP_COLUMN,
    COMMON_FN_COLUMN,
    COMMON_FP_COLUMN,
)
CLIP_RUNS = (
    (
        "20 min clip",
        1200.0,
        "ks4_threshold_confirmation/threshold_sweep_summary.csv",
        "ks4_threshold_confirmation/threshold_sweep_per_unit.csv",
        "c474cfbf-d8ff-4548-93b6-7df282523473",
    ),
    (
        "5 min clip",
        300.0,
        "ks4_threshold_sweep/threshold_sweep_summary.csv",
        "ks4_threshold_sweep/threshold_sweep_per_unit.csv",
        "93d1865b-a451-45df-90b2-dbcf554544cb",
    ),
)
METRICS = [
    "mean_accuracy",
    "mean_precision",
    "mean_recall",
    "gt_units_detected",
    "gt_units_above_0_8_accuracy",
    "sorter_units",
    "sorted_spike_events",
    "sorted_spike_events_per_s",
    "true_positive_injected_spikes",
    "false_positive_spikes_in_matched_clusters",
    "sorter_run_time_s",
]
OUTPUT_COLUMNS = [
    "scope",
    "duration_s",
    "input",
    "Th_universal",
    "Th_learned",
    "source_computation_id",
    *METRICS,
    *COMMON_COLUMNS,
]


def _assert_matching_row(
    baseline: pd.DataFrame,
    baseline_label: str,
    matrix: pd.DataFrame,
    matrix_label: str,
) -> None:
    left = baseline.loc[baseline["input"].eq(baseline_label), METRICS]
    right = matrix.loc[matrix["input"].eq(matrix_label), METRICS]
    if len(left) != 1 or len(right) != 1:
        raise ValueError(f"missing overlap row: {baseline_label}, {matrix_label}")
    pd.testing.assert_frame_equal(
        left.reset_index(drop=True),
        right.reset_index(drop=True),
        check_exact=False,
        rtol=0,
        atol=1e-9,
    )


def _full_recording_rows(results: Path) -> pd.DataFrame:
    baseline = pd.read_csv(results / BASELINE_SUMMARY)
    matrix = pd.read_csv(results / FULL_MATRIX)
    baseline_units = pd.read_csv(results / BASELINE_PER_UNIT)
    matrix_units = pd.read_csv(results / FULL_MATRIX_PER_UNIT)
    _assert_matching_row(baseline, "raw AP", matrix, "raw AP 9/8")
    _assert_matching_row(
        baseline,
        "Full96 omission1",
        matrix,
        "Full96 omission1 9/8",
    )
    baseline_counts = _common_event_counts_by_input(baseline_units)
    matrix_counts = _common_event_counts_by_input(matrix_units)

    raw = matrix.loc[matrix["input"].str.startswith("raw AP ")].copy()
    for column in COMMON_COLUMNS:
        raw[column] = raw["input"].map(
            {label: counts[column] for label, counts in matrix_counts.items()}
        )
    raw["input"] = "raw AP"
    omission0 = baseline.loc[baseline["input"].eq("Full96 omission0")].copy()
    omission0["Th_universal"] = 9.0
    omission0["Th_learned"] = 8.0
    for column, value in baseline_counts["Full96 omission0"].items():
        omission0[column] = value
    omission0_10_75_label = "Full96 omission0 9/10.75"
    omission0_10_75 = matrix.loc[
        matrix["input"].eq(omission0_10_75_label)
    ].copy()
    for column, value in matrix_counts[omission0_10_75_label].items():
        omission0_10_75[column] = value
    omission0_10_75["input"] = "Full96 omission0"
    omission1 = matrix.loc[
        matrix["input"].str.startswith("Full96 omission1 ")
    ].copy()
    for column in COMMON_COLUMNS:
        omission1[column] = omission1["input"].map(
            {label: counts[column] for label, counts in matrix_counts.items()}
        )
    omission1["input"] = "Full96 omission1"

    combined = pd.concat(
        [raw, omission0, omission0_10_75, omission1], ignore_index=True
    )
    combined.insert(0, "duration_s", FULL_DURATION_S)
    combined.insert(0, "scope", "full recording")
    return combined[OUTPUT_COLUMNS]


def _clip_rows(
    results: Path,
    scope: str,
    duration_s: float,
    relative_path: str,
    per_unit_path: str,
    computation_id: str,
) -> pd.DataFrame:
    frame = pd.read_csv(results / relative_path).rename(
        columns={
            "false_positive_spikes_in_gt_matched_clusters":
                "false_positive_spikes_in_matched_clusters"
        }
    )
    per_unit = pd.read_csv(results / per_unit_path)
    selected = per_unit.loc[per_unit["gt_unit_id"].isin(COMMON_GT_UNITS)]
    counts = selected.groupby("Th_learned")["gt_unit_id"].nunique()
    if len(counts) != len(frame) or not counts.eq(len(COMMON_GT_UNITS)).all():
        raise ValueError(f"clip is missing common GT units: {per_unit_path}")
    if selected["accuracy"].le(0).any():
        raise ValueError(f"common GT unit is unmatched in clip: {per_unit_path}")
    grouped = selected.groupby("Th_learned")
    common_values = {
        COMMON_ACCURACY_COLUMN: grouped["accuracy"].mean(),
        COMMON_PRECISION_COLUMN: grouped["precision"].mean(),
        COMMON_RECALL_COLUMN: grouped["recall"].mean(),
        COMMON_TP_COLUMN: grouped["tp"].sum().astype(int),
        COMMON_FN_COLUMN: grouped["fn"].sum().astype(int),
        COMMON_FP_COLUMN: grouped["fp"].sum().astype(int),
    }
    for column, values in common_values.items():
        frame[column] = frame["Th_learned"].map(values)
    if frame[list(COMMON_COLUMNS)].isna().any().any():
        raise ValueError(f"clip thresholds do not match per-unit rows: {per_unit_path}")
    frame.insert(0, "source_computation_id", computation_id)
    frame.insert(0, "Th_universal", 9.0)
    frame.insert(0, "input", "Full96 omission1")
    frame.insert(0, "duration_s", duration_s)
    frame.insert(0, "scope", scope)
    return frame[OUTPUT_COLUMNS]


def _common_event_counts_by_input(
    per_unit: pd.DataFrame,
) -> dict[str, dict[str, float | int]]:
    expected = set(COMMON_GT_UNITS)
    output = {}
    for label, frame in per_unit.groupby("input", sort=False):
        matched = set(frame.loc[frame["accuracy"].gt(0), "gt_unit_id"].astype(int))
        if not matched.issubset(expected):
            raise ValueError(
                f"{label} matched units fall outside reference seven: {sorted(matched)}"
            )
        selected = frame.loc[frame["gt_unit_id"].isin(COMMON_GT_UNITS)]
        true_positive = selected["true_positive_injected_spikes"]
        output[label] = {
            COMMON_ACCURACY_COLUMN: float(selected["accuracy"].mean()),
            COMMON_PRECISION_COLUMN: float(selected["precision"].mean()),
            COMMON_RECALL_COLUMN: float(selected["recall"].mean()),
            COMMON_TP_COLUMN: int(true_positive.sum()),
            COMMON_FN_COLUMN: int((selected["gt_spike_events"] - true_positive).sum()),
            COMMON_FP_COLUMN: int(
                selected["false_positive_spikes_in_matched_cluster"].sum()
            ),
        }
    return output


def build_table(results: Path) -> pd.DataFrame:
    """Return all audited Kilosort runs in a common schema."""
    frames = [_full_recording_rows(results)]
    frames.extend(_clip_rows(results, *spec) for spec in CLIP_RUNS)
    table = pd.concat(frames, ignore_index=True)
    if len(table) != 15:
        raise ValueError(f"expected 15 Kilosort runs, found {len(table)}")
    keys = ["scope", "input", "Th_universal", "Th_learned"]
    if table.duplicated(keys).any():
        duplicates = table.loc[table.duplicated(keys, keep=False), keys]
        raise ValueError(f"duplicate Kilosort configurations:\n{duplicates}")
    return table


def _write_markdown(table: pd.DataFrame, destination: Path) -> None:
    display = table[
        [
            "scope",
            "input",
            "Th_universal",
            "Th_learned",
            "mean_accuracy",
            "mean_precision",
            "mean_recall",
            COMMON_ACCURACY_COLUMN,
            COMMON_PRECISION_COLUMN,
            COMMON_RECALL_COLUMN,
            "gt_units_detected",
            "gt_units_above_0_8_accuracy",
            "sorter_units",
            "sorted_spike_events_per_s",
            COMMON_TP_COLUMN,
            COMMON_FN_COLUMN,
            COMMON_FP_COLUMN,
        ]
    ].copy()
    display.columns = [
        "scope",
        "input",
        "Th universal",
        "Th learned",
        "accuracy (all 10)",
        "precision (all 10)",
        "recall (all 10)",
        "accuracy (fixed 7)",
        "precision (fixed 7)",
        "recall (fixed 7)",
        "GT detected",
        "GT >0.8",
        "sorter units",
        "events/s",
        "TP spikes in fixed 7 GT units",
        "FN spikes in fixed 7 GT units",
        "FP spikes in fixed 7 GT-matched clusters",
    ]
    for column in ("Th universal", "Th learned"):
        display[column] = display[column].map(lambda value: f"{value:g}")
    for column in (
        "accuracy (all 10)",
        "precision (all 10)",
        "recall (all 10)",
        "accuracy (fixed 7)",
        "precision (fixed 7)",
        "recall (fixed 7)",
    ):
        display[column] = display[column].map(lambda value: f"{value:.4f}")
    for column in ("GT detected", "GT >0.8"):
        display[column] = display[column].map(lambda value: f"{value}/10")
    for column in (
        "sorter units",
        "events/s",
        "TP spikes in fixed 7 GT units",
        "FN spikes in fixed 7 GT units",
        "FP spikes in fixed 7 GT-matched clusters",
    ):
        display[column] = display[column].map(lambda value: f"{value:,.0f}")

    preamble = (
        "# All raw and denoised Kilosort4 runs\n\n"
        "All rows use the exact 681532 ProbeC `recording1_3` hybrid case. "
        "Compare performance within a scope: the 5-minute and 20-minute "
        "intervals are nested calibration clips, and recording duration "
        "changes Kilosort template learning, clustering, and drift behavior. "
        "The fixed-7 metrics and TP/FN/FP columns are restricted to GT units "
        "337, 664, 793, 1122, 1143, 1300, and 2143, the units matched by raw "
        "9/8 and all denoised full-recording conditions. A stricter condition "
        "that loses one of these units retains its zero metrics and full FN "
        "count; units 94, 720, and 1129 are excluded.\n\n"
    )
    header = "| " + " | ".join(display.columns) + " |"
    separator = "|" + "|".join("---" for _ in display.columns) + "|"
    rows = [
        "| "
        + " | ".join(str(value).replace("|", "\\|") for value in row)
        + " |"
        for row in display.itertuples(index=False, name=None)
    ]
    destination.write_text(
        preamble + "\n".join([header, separator, *rows]) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    results = args.results_dir.resolve()
    table = build_table(results)
    table.to_csv(
        results / "kilosort4_all_runs.csv", index=False, float_format="%.12g"
    )
    _write_markdown(table, results / "kilosort4_all_runs.md")
    print(f"wrote {len(table)} Kilosort4 runs to {results}")


if __name__ == "__main__":
    main()