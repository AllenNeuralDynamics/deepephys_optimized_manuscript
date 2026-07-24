#!/usr/bin/env python3
"""Audit completed Full96 Kilosort4 results and write compact tables."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from codeocean import CodeOcean

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO / "results" / "benchmarking"
COMPUTATIONS = {
    "om0": "db76c533-9f39-46e6-98fe-e83adf56ea51",
    "om1": "2ad21011-a937-44dc-a370-5280049621ef",
}
SESSION = "ecephys_681532_2023-10-18_13-01-15"
STREAM = "experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3"
DURATION_S = 7144.262
PERFORMANCES = "aggregated/dataframes/performances.csv"
UNIT_COUNTS = "aggregated/dataframes/unit_counts.csv"
RUN_TIMES = "aggregated/dataframes/run_times.csv"


def _download(
    client: CodeOcean,
    computation_id: str,
    path: str,
    byte_range: str | None = None,
) -> bytes:
    urls = client.computations.get_result_file_urls(computation_id, path)
    url = getattr(urls, "download_url", None) or getattr(urls, "url", None)
    if not url:
        raise RuntimeError(f"Code Ocean returned no download URL for {path}")
    headers = {"Range": byte_range} if byte_range else None
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    if byte_range and response.status_code != requests.codes.partial_content:
        raise RuntimeError(
            f"server ignored byte range for {path}: HTTP {response.status_code}"
        )
    return response.content


def _load_csv(client: CodeOcean, computation_id: str, path: str) -> pd.DataFrame:
    frame = pd.read_csv(io.BytesIO(_download(client, computation_id, path)))
    return frame.loc[:, ~frame.columns.str.startswith("Unnamed")]


def _npy_shape(
    client: CodeOcean, computation_id: str, path: str
) -> tuple[tuple[int, ...], np.dtype]:
    stream = io.BytesIO(
        _download(client, computation_id, path, byte_range="bytes=0-4095")
    )
    version = np.lib.format.read_magic(stream)
    if version == (1, 0):
        shape, _, dtype = np.lib.format.read_array_header_1_0(stream)
    elif version in ((2, 0), (3, 0)):
        shape, _, dtype = np.lib.format.read_array_header_2_0(stream)
    else:
        raise ValueError(f"unsupported NPY version {version} for {path}")
    return shape, dtype


def _sorting_spike_counts(
    client: CodeOcean, computation_id: str
) -> dict[str, int]:
    root = f"gt_studies/{SESSION}/results"
    folder = client.computations.list_computation_results(computation_id, root)
    counts: dict[str, int] = {}
    for item in folder.items:
        if item.type != "folder":
            continue
        if item.name.startswith("deepks4_"):
            case = "deepks4"
        elif item.name.startswith("ks4_"):
            case = "ks4"
        else:
            continue
        path = f"{item.path}/sorting/spikes.npy"
        shape, dtype = _npy_shape(client, computation_id, path)
        expected_fields = {"sample_index", "unit_index", "segment_index"}
        if len(shape) != 1 or set(dtype.names or ()) != expected_fields:
            raise ValueError(f"unexpected sorting spike array at {path}: {shape}, {dtype}")
        counts[case] = int(shape[0])
    if set(counts) != {"ks4", "deepks4"}:
        raise ValueError(f"missing sorting spike arrays: {counts}")
    return counts


def _gt_spike_counts(client: CodeOcean, computation_id: str) -> dict[int, int]:
    root = f"gt_studies/{SESSION}/sorting_analyzer/{STREAM}/sorting"
    info = json.loads(
        _download(client, computation_id, f"{root}/numpysorting_info.json")
    )
    spikes = np.load(
        io.BytesIO(_download(client, computation_id, f"{root}/spikes.npy")),
        allow_pickle=False,
    )
    indices, counts = np.unique(spikes["unit_index"], return_counts=True)
    unit_ids = np.asarray(info["unit_ids"])
    if not np.array_equal(indices, np.arange(len(unit_ids))):
        raise ValueError("GT sorting unit indices are not contiguous")
    output = {
        int(unit_ids[index]): int(count) for index, count in zip(indices, counts)
    }
    if sum(output.values()) != 1_070_127:
        raise ValueError(f"unexpected injected GT event count: {sum(output.values())}")
    return output


def _assert_raw_identity(route_data: dict[str, dict]) -> None:
    first = route_data["om0"]
    second = route_data["om1"]
    raw_first = (
        first["performances"]
        .query("sorting_case == 'ks4'")
        .sort_values("gt_unit_id")
        .reset_index(drop=True)
    )
    raw_second = (
        second["performances"]
        .query("sorting_case == 'ks4'")
        .sort_values("gt_unit_id")
        .reset_index(drop=True)
    )
    for column in ("gt_unit_id", "accuracy", "precision", "recall"):
        if not np.array_equal(raw_first[column].to_numpy(), raw_second[column].to_numpy()):
            raise ValueError(f"route raw performance differs for {column}")
    if first["spike_counts"]["ks4"] != second["spike_counts"]["ks4"]:
        raise ValueError("route raw total spike-event counts differ")
    for table, column in (("unit_counts", "num_sorter"), ("run_times", "run_times")):
        left = first[table].query("sorting_case == 'ks4'").iloc[0][column]
        right = second[table].query("sorting_case == 'ks4'").iloc[0][column]
        if left != right:
            raise ValueError(f"route raw {column} differs: {left} != {right}")


def _event_accounting(
    label: str, performances: pd.DataFrame, gt_counts: dict[int, int]
) -> pd.DataFrame:
    frame = performances.sort_values("gt_unit_id").copy()
    frame.insert(0, "input", label)
    frame["gt_spike_events"] = frame["gt_unit_id"].map(gt_counts).astype(int)
    matched = frame["accuracy"] > 0
    frame["true_positive_injected_spikes"] = 0
    frame["matched_cluster_spikes"] = 0
    frame.loc[matched, "true_positive_injected_spikes"] = np.rint(
        frame.loc[matched, "recall"] * frame.loc[matched, "gt_spike_events"]
    ).astype(int)
    frame.loc[matched, "matched_cluster_spikes"] = np.rint(
        frame.loc[matched, "true_positive_injected_spikes"]
        / frame.loc[matched, "precision"]
    ).astype(int)
    frame["evaluator_unmatched_spikes_in_matched_cluster"] = (
        frame["matched_cluster_spikes"] - frame["true_positive_injected_spikes"]
    )
    reconstructed = {
        "recall": (
            frame.loc[matched, "true_positive_injected_spikes"]
            / frame.loc[matched, "gt_spike_events"]
        ),
        "precision": (
            frame.loc[matched, "true_positive_injected_spikes"]
            / frame.loc[matched, "matched_cluster_spikes"]
        ),
        "accuracy": (
            frame.loc[matched, "true_positive_injected_spikes"]
            / (
                frame.loc[matched, "gt_spike_events"]
                + frame.loc[matched, "matched_cluster_spikes"]
                - frame.loc[matched, "true_positive_injected_spikes"]
            )
        ),
    }
    for metric, values in reconstructed.items():
        if not np.allclose(frame.loc[matched, metric], values, rtol=0, atol=1e-9):
            raise ValueError(f"integer event counts do not reconstruct {metric}")
    return frame[
        [
            "input",
            "gt_unit_id",
            "gt_spike_events",
            "accuracy",
            "precision",
            "recall",
            "true_positive_injected_spikes",
            "matched_cluster_spikes",
            "evaluator_unmatched_spikes_in_matched_cluster",
        ]
    ]


def _summary_row(
    label: str,
    source_id: str,
    performances: pd.DataFrame,
    unit_counts: pd.DataFrame,
    run_times: pd.DataFrame,
    spike_events: int,
    per_unit: pd.DataFrame,
) -> dict[str, float | int | str]:
    matched = per_unit[per_unit["accuracy"] > 0]
    return {
        "input": label,
        "source_computation_id": source_id,
        "mean_accuracy": float(performances["accuracy"].mean()),
        "mean_precision": float(performances["precision"].mean()),
        "mean_recall": float(performances["recall"].mean()),
        "gt_units_detected": int((performances["accuracy"] > 0).sum()),
        "gt_units_above_0_8_accuracy": int((performances["accuracy"] > 0.8).sum()),
        "sorter_units": int(unit_counts["num_sorter"]),
        "sorted_spike_events": spike_events,
        "sorted_spike_events_per_s": spike_events / DURATION_S,
        "sorted_spike_events_per_sorter_unit": spike_events / unit_counts["num_sorter"],
        "sorter_run_time_s": float(run_times["run_times"]),
        "gt_units_matched": len(matched),
        "injected_spikes_in_matched_gt_units": int(matched["gt_spike_events"].sum()),
        "true_positive_injected_spikes": int(
            matched["true_positive_injected_spikes"].sum()
        ),
        "matched_cluster_spikes": int(matched["matched_cluster_spikes"].sum()),
        "evaluator_unmatched_spikes_in_matched_clusters": int(
            matched["evaluator_unmatched_spikes_in_matched_cluster"].sum()
        ),
    }


def _write_markdown(summary: pd.DataFrame, output: Path) -> None:
    display = summary[
        [
            "input",
            "mean_accuracy",
            "mean_precision",
            "mean_recall",
            "gt_units_detected",
            "gt_units_above_0_8_accuracy",
            "sorter_units",
            "sorted_spike_events",
            "sorted_spike_events_per_s",
            "sorter_run_time_s",
        ]
    ].copy()
    display.columns = [
        "input",
        "mean accuracy",
        "mean precision",
        "mean recall",
        "GT detected",
        "GT >0.8",
        "sorter units",
        "sorted spike events",
        "spike events/s",
        "sorter runtime (h)",
    ]
    for column in ("mean accuracy", "mean precision", "mean recall"):
        display[column] = display[column].map(lambda value: f"{value:.4f}")
    for column in ("GT detected", "GT >0.8"):
        display[column] = display[column].map(lambda value: f"{value}/10")
    for column in ("sorter units", "sorted spike events"):
        display[column] = display[column].map(lambda value: f"{value:,.0f}")
    display["spike events/s"] = display["spike events/s"].map(
        lambda value: f"{value:,.1f}"
    )
    display["sorter runtime (h)"] = display["sorter runtime (h)"].map(
        lambda value: f"{value / 3600:.2f}"
    )
    (output / "kilosort4_summary.md").write_text(
        display.to_markdown(index=False) + "\n"
    )

    accounting = summary[
        [
            "input",
            "sorted_spike_events_per_sorter_unit",
            "true_positive_injected_spikes",
            "evaluator_unmatched_spikes_in_matched_clusters",
            "matched_cluster_spikes",
        ]
    ].copy()
    accounting.columns = [
        "input",
        "spike events / sorter unit",
        "TP injected spikes",
        "evaluator-unmatched spikes in matched clusters",
        "all spikes in matched clusters",
    ]
    for column in accounting.columns[1:]:
        accounting[column] = accounting[column].map(lambda value: f"{value:,.0f}")
    (output / "kilosort4_event_accounting.md").write_text(
        accounting.to_markdown(index=False) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    client = CodeOcean(
        domain=os.environ["CODEOCEAN_DOMAIN"], token=os.environ["CODEOCEAN_TOKEN"]
    )

    route_data: dict[str, dict] = {}
    for route, computation_id in COMPUTATIONS.items():
        computation = client.computations.get_computation(computation_id)
        if computation.exit_code != 0 or not computation.has_results:
            raise RuntimeError(
                f"{route} computation is not successful: "
                f"exit_code={computation.exit_code}, has_results={computation.has_results}"
            )
        route_data[route] = {
            "performances": _load_csv(client, computation_id, PERFORMANCES),
            "unit_counts": _load_csv(client, computation_id, UNIT_COUNTS),
            "run_times": _load_csv(client, computation_id, RUN_TIMES),
            "spike_counts": _sorting_spike_counts(client, computation_id),
        }
    _assert_raw_identity(route_data)
    gt_counts = _gt_spike_counts(client, COMPUTATIONS["om0"])

    raw_performance = route_data["om0"]["performances"].query("sorting_case == 'ks4'")
    per_unit_frames = [_event_accounting("raw AP", raw_performance, gt_counts)]
    summary_rows = []
    raw_counts = route_data["om0"]["unit_counts"].query("sorting_case == 'ks4'").iloc[0]
    raw_time = route_data["om0"]["run_times"].query("sorting_case == 'ks4'").iloc[0]
    summary_rows.append(
        _summary_row(
            "raw AP",
            ";".join(COMPUTATIONS.values()),
            raw_performance,
            raw_counts,
            raw_time,
            route_data["om0"]["spike_counts"]["ks4"],
            per_unit_frames[0],
        )
    )
    for route in ("om0", "om1"):
        label = f"Full96 omission{route[-1]}"
        performance = route_data[route]["performances"].query(
            "sorting_case == 'deepks4'"
        )
        per_unit = _event_accounting(label, performance, gt_counts)
        per_unit_frames.append(per_unit)
        counts = route_data[route]["unit_counts"].query(
            "sorting_case == 'deepks4'"
        ).iloc[0]
        run_time = route_data[route]["run_times"].query(
            "sorting_case == 'deepks4'"
        ).iloc[0]
        summary_rows.append(
            _summary_row(
                label,
                COMPUTATIONS[route],
                performance,
                counts,
                run_time,
                route_data[route]["spike_counts"]["deepks4"],
                per_unit,
            )
        )

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(summary_rows)
    summary["sorted_spike_event_ratio_to_raw"] = (
        summary["sorted_spike_events"] / summary.loc[0, "sorted_spike_events"]
    )
    per_unit = pd.concat(per_unit_frames, ignore_index=True)
    summary.to_csv(output / "kilosort4_summary.csv", index=False, float_format="%.12g")
    per_unit.to_csv(output / "kilosort4_per_unit.csv", index=False, float_format="%.12g")
    _write_markdown(summary, output)
    print(f"wrote Kilosort4 audit tables to {output}")


if __name__ == "__main__":
    main()