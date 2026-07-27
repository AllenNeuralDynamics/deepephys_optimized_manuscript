#!/usr/bin/env python3
"""Build the full-recording Kilosort comparison ordered by GT template SNR."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_ks4_all_runs_table import COMMON_GT_UNITS


REPO = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = REPO / "results" / "benchmarking"
BASELINE_PER_UNIT = "kilosort4_per_unit.csv"
MATRIX_PER_UNIT = "ks4_full_threshold_matrix/per_unit.csv"
SNR_SPECS = {
    "Full96 omission0": {
        "stem": "ib_w96_om0_scale_s00210923_examples",
        "checkpoint_sha256":
            "f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506",
    },
    "Full96 omission1": {
        "stem": "ib_w96_om1_scale_s00210923_examples",
        "checkpoint_sha256":
            "90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a",
    },
}
CONDITION_ORDER = {
    ("raw AP", 9.0, 8.0): 0,
    ("raw AP", 9.0, 10.75): 1,
    ("Full96 omission0", 9.0, 8.0): 2,
    ("Full96 omission0", 9.0, 10.75): 3,
    ("Full96 omission1", 9.0, 8.0): 4,
    ("Full96 omission1", 9.0, 9.0): 5,
    ("Full96 omission1", 9.0, 10.0): 6,
    ("Full96 omission1", 9.0, 10.75): 7,
    ("Full96 omission1", 10.0, 9.0): 8,
}
OUTPUT_COLUMNS = [
    "raw_snr_rank",
    "gt_unit_id",
    "raw_template_snr",
    "input_template_snr",
    "input_template_snr_change_from_raw",
    "input",
    "Th_universal",
    "Th_learned",
    "accuracy",
    "precision",
    "recall",
    "true_positive_injected_spikes",
    "false_negative_injected_spikes",
    "false_positive_spikes_in_matched_cluster",
]
PAIRED_COLUMNS = [
    "raw_snr_rank",
    "gt_unit_id",
    "raw_template_snr",
    "omission1_template_snr",
    "template_snr_change",
    "raw_precision_th_9_8",
    "omission1_precision_th_9_10_75",
    "precision_change",
]


def _load_snr(repo: Path) -> dict[str, pd.DataFrame]:
    root = repo / "results" / "qualitative" / "learning_stages"
    output = {}
    raw_reference = None
    expected_units = set(COMMON_GT_UNITS)
    for route, spec in SNR_SPECS.items():
        csv_path = root / f"{spec['stem']}.csv"
        metadata_path = root / f"{spec['stem']}_metadata.json"
        metadata = json.loads(metadata_path.read_text())
        if metadata["checkpoint_sha256"] != spec["checkpoint_sha256"]:
            raise ValueError(f"{route} SNR artifact has unexpected checkpoint")
        frame = pd.read_csv(csv_path).set_index("unit_id")
        if not expected_units.issubset(frame.index):
            raise ValueError(f"{route} SNR artifact is missing common GT units")
        raw = frame.loc[list(COMMON_GT_UNITS), "snr_raw"].sort_index()
        if raw_reference is None:
            raw_reference = raw
        elif not np.array_equal(raw_reference.to_numpy(), raw.to_numpy()):
            raise ValueError("raw template SNR differs between route artifacts")
        output[route] = frame
    return output


def _load_sorter_rows(results: Path) -> pd.DataFrame:
    baseline = pd.read_csv(results / BASELINE_PER_UNIT)
    matrix = pd.read_csv(results / MATRIX_PER_UNIT)

    raw = matrix.loc[matrix["input"].str.startswith("raw AP ")].copy()
    raw["input"] = "raw AP"
    omission0 = baseline.loc[baseline["input"].eq("Full96 omission0")].copy()
    omission0["Th_universal"] = 9.0
    omission0["Th_learned"] = 8.0
    omission0_10_75 = matrix.loc[
        matrix["input"].eq("Full96 omission0 9/10.75")
    ].copy()
    omission0_10_75["input"] = "Full96 omission0"
    omission1 = matrix.loc[
        matrix["input"].str.startswith("Full96 omission1 ")
    ].copy()
    omission1["input"] = "Full96 omission1"

    rows = pd.concat(
        [raw, omission0, omission0_10_75, omission1], ignore_index=True
    )
    rows = rows.loc[rows["gt_unit_id"].isin(COMMON_GT_UNITS)].copy()
    if len(rows) != len(COMMON_GT_UNITS) * len(CONDITION_ORDER):
        raise ValueError(f"expected 63 reference-unit rows, found {len(rows)}")
    observed = set(
        zip(rows["input"], rows["Th_universal"], rows["Th_learned"])
    )
    if observed != set(CONDITION_ORDER):
        raise ValueError(f"unexpected sorter conditions: {observed}")
    return rows


def build_table(results: Path, repo: Path = REPO) -> pd.DataFrame:
    """Return common-unit sorter metrics ordered by baseline raw template SNR."""
    snr = _load_snr(repo)
    rows = _load_sorter_rows(results)
    raw_snr = snr["Full96 omission1"]["snr_raw"]
    omission0_snr = snr["Full96 omission0"]["snr_deep"]
    omission1_snr = snr["Full96 omission1"]["snr_deep"]

    rows["raw_template_snr"] = rows["gt_unit_id"].map(raw_snr)
    rows["input_template_snr"] = rows["raw_template_snr"]
    rows.loc[rows["input"].eq("Full96 omission0"), "input_template_snr"] = (
        rows.loc[rows["input"].eq("Full96 omission0"), "gt_unit_id"].map(
            omission0_snr
        )
    )
    rows.loc[rows["input"].eq("Full96 omission1"), "input_template_snr"] = (
        rows.loc[rows["input"].eq("Full96 omission1"), "gt_unit_id"].map(
            omission1_snr
        )
    )
    if rows[["raw_template_snr", "input_template_snr"]].isna().any().any():
        raise ValueError("failed to join template SNR to sorter rows")
    rows["input_template_snr_change_from_raw"] = (
        rows["input_template_snr"] - rows["raw_template_snr"]
    )
    rows["false_negative_injected_spikes"] = (
        rows["gt_spike_events"] - rows["true_positive_injected_spikes"]
    )

    unit_order = (
        raw_snr.loc[list(COMMON_GT_UNITS)]
        .sort_values(ascending=False)
        .index.astype(int)
        .tolist()
    )
    rank = {unit_id: index + 1 for index, unit_id in enumerate(unit_order)}
    rows["raw_snr_rank"] = rows["gt_unit_id"].map(rank)
    rows["condition_order"] = [
        CONDITION_ORDER[(label, float(th_universal), float(th_learned))]
        for label, th_universal, th_learned in zip(
            rows["input"], rows["Th_universal"], rows["Th_learned"]
        )
    ]
    rows = rows.sort_values(["raw_snr_rank", "condition_order"])
    return rows[OUTPUT_COLUMNS].reset_index(drop=True)


def build_raw_vs_10_75(table: pd.DataFrame) -> pd.DataFrame:
    """Return the SNR-ordered raw versus omission1 9/10.75 precision pairing."""
    raw = table.loc[
        table["input"].eq("raw AP")
        & table["Th_universal"].eq(9)
        & table["Th_learned"].eq(8)
    ].set_index("gt_unit_id")
    candidate = table.loc[
        table["input"].eq("Full96 omission1")
        & table["Th_universal"].eq(9)
        & table["Th_learned"].eq(10.75)
    ].set_index("gt_unit_id")
    if not raw.index.is_unique or not candidate.index.is_unique:
        raise ValueError("raw or omission1 9/10.75 contains duplicate GT units")
    if set(raw.index) != set(candidate.index) or len(raw) != len(COMMON_GT_UNITS):
        raise ValueError("raw and omission1 9/10.75 GT units do not match")

    paired = pd.DataFrame(
        {
            "raw_snr_rank": raw["raw_snr_rank"],
            "gt_unit_id": raw.index,
            "raw_template_snr": raw["raw_template_snr"],
            "omission1_template_snr": candidate["input_template_snr"],
            "template_snr_change": candidate[
                "input_template_snr_change_from_raw"
            ],
            "raw_precision_th_9_8": raw["precision"],
            "omission1_precision_th_9_10_75": candidate["precision"],
        }
    )
    paired["precision_change"] = (
        paired["omission1_precision_th_9_10_75"]
        - paired["raw_precision_th_9_8"]
    )
    return paired.sort_values("raw_snr_rank")[PAIRED_COLUMNS].reset_index(drop=True)


def _write_markdown(table: pd.DataFrame, destination: Path) -> None:
    display = table.copy()
    display.columns = [
        "raw SNR rank",
        "GT unit",
        "raw template SNR",
        "input template SNR",
        "input SNR change",
        "input",
        "Th universal",
        "Th learned",
        "accuracy",
        "precision",
        "recall",
        "TP",
        "FN",
        "FP in matched cluster",
    ]
    for column in (
        "raw template SNR",
        "input template SNR",
        "input SNR change",
        "accuracy",
        "precision",
        "recall",
    ):
        display[column] = display[column].map(lambda value: f"{value:.4f}")
    for column in ("Th universal", "Th learned"):
        display[column] = display[column].map(lambda value: f"{value:g}")
    for column in ("TP", "FN", "FP in matched cluster"):
        display[column] = display[column].map(lambda value: f"{value:,.0f}")

    preamble = (
        "# Full-recording Kilosort4 per-unit comparison by template SNR\n\n"
        "Rows are ordered by descending raw template SNR, then by sorter "
        "condition. SNR is the peak-to-peak average GT template on its raw "
        "peak channel divided by background noise SD, estimated from 100 GT "
        "spikes and 200 background windows. This is a pre-sort GT-template "
        "detectability metric, not Kilosort's post-sort quality-metric SNR. "
        "Raw and denoised SNR values come from the exact scheduled-step "
        "checkpoints used in the full Kilosort benchmark.\n\n"
    )
    header = "| " + " | ".join(display.columns) + " |"
    separator = "|" + "|".join("---" for _ in display.columns) + "|"
    body = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in display.itertuples(index=False, name=None)
    ]
    destination.write_text(preamble + "\n".join([header, separator, *body]) + "\n")


def _write_paired_markdown(table: pd.DataFrame, destination: Path) -> None:
    display = table.copy()
    display.columns = [
        "raw SNR rank",
        "GT unit",
        "raw template SNR",
        "omission1 template SNR",
        "SNR change",
        "raw precision (Th 9/8)",
        "omission1 precision (Th 9/10.75)",
        "precision change",
    ]
    for column in display.columns[2:]:
        display[column] = display[column].map(lambda value: f"{value:.4f}")
    preamble = (
        "# Raw versus Full96 omission1 9/10.75 by template SNR\n\n"
        "The seven common matched GT units are ordered by descending raw "
        "template SNR. Precision is compared between raw Kilosort "
        "(`Th_universal=9`, `Th_learned=8`) and Full96 omission1 Kilosort "
        "(`Th_universal=9`, `Th_learned=10.75`).\n\n"
    )
    header = "| " + " | ".join(display.columns) + " |"
    separator = "|" + "|".join("---" for _ in display.columns) + "|"
    body = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in display.itertuples(index=False, name=None)
    ]
    destination.write_text(preamble + "\n".join([header, separator, *body]) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    results = args.results_dir.resolve()
    table = build_table(results)
    paired = build_raw_vs_10_75(table)
    table.to_csv(
        results / "kilosort4_full_per_unit_by_snr.csv",
        index=False,
        float_format="%.12g",
    )
    _write_markdown(table, results / "kilosort4_full_per_unit_by_snr.md")
    paired.to_csv(
        results / "kilosort4_raw_vs_10p75_by_snr.csv",
        index=False,
        float_format="%.12g",
    )
    _write_paired_markdown(
        paired, results / "kilosort4_raw_vs_10p75_by_snr.md"
    )
    print(
        f"wrote {len(table)} per-unit rows and {len(paired)} paired rows to {results}"
    )


if __name__ == "__main__":
    main()