#!/usr/bin/env python3
"""Export compact raw/denoised examples from the frozen hybrid benchmark.

This GPU/S3 step is run once for a selected checkpoint. It uses the same event
selection, background sampling, empirical templates, matched filters, and seed
as the endpoint scorer, validates against the committed endpoint CSV, and writes
a compact NPZ consumed by ``code/figures/qualitative_examples.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCORING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCORING_DIR))

from detection_metrics import compute_surrogate


def _native_to_microvolts(recording, traces: np.ndarray, channels=None) -> np.ndarray:
    num_channels = recording.get_num_channels()
    try:
        gains = np.asarray(recording.get_channel_gains(), dtype=np.float32)
        offsets = np.asarray(recording.get_channel_offsets(), dtype=np.float32)
    except Exception:
        gains = np.ones(num_channels, dtype=np.float32)
        offsets = np.zeros(num_channels, dtype=np.float32)
    if channels is not None:
        gains = gains[np.asarray(channels, dtype=int)]
        offsets = offsets[np.asarray(channels, dtype=int)]
    return np.asarray(traces, dtype=np.float32) * gains + offsets


def _nearest_other_event_distance(all_times: np.ndarray, time: int) -> int:
    matches = np.flatnonzero(all_times == time)
    if matches.size > 1:
        return 0
    insertion = int(np.searchsorted(all_times, time))
    distances = []
    if insertion > 0:
        distances.append(time - int(all_times[insertion - 1]))
    next_index = insertion + 1 if insertion < len(all_times) and all_times[insertion] == time else insertion
    if next_index < len(all_times):
        distances.append(int(all_times[next_index]) - time)
    return min(distances) if distances else 1 << 30


def _select_exemplar_time(sorting, unit_id: int, num_samples: int, sampling_frequency: float) -> tuple[int, int]:
    all_times = np.sort(
        np.concatenate(
            [
                np.asarray(sorting.get_unit_spike_train(unit, segment_index=0))
                for unit in sorting.unit_ids
            ]
        )
    )
    candidates = np.asarray(
        sorting.get_unit_spike_train(unit_id, segment_index=0), dtype=np.int64
    )
    margin = int(round(0.05 * sampling_frequency))
    candidates = candidates[(candidates > margin) & (candidates < num_samples - margin)]
    if not candidates.size:
        raise ValueError(f"unit {unit_id} has no spike with sufficient recording margin")
    distances = np.asarray(
        [_nearest_other_event_distance(all_times, int(time)) for time in candidates]
    )
    minimum_gap = int(round(0.010 * sampling_frequency))
    isolated = candidates[distances >= minimum_gap]
    if isolated.size:
        selected = isolated[np.argmin(np.abs(isolated - num_samples // 2))]
    else:
        selected = candidates[np.argmax(distances)]
    distance = _nearest_other_event_distance(all_times, int(selected))
    return int(selected), int(distance)


def _validate_against_reference(frame: pd.DataFrame, reference_path: Path) -> None:
    reference = pd.read_csv(reference_path)
    columns = [
        "unit_id",
        "snr_raw",
        "snr_deep",
        "dprime_raw",
        "dprime_deep",
        "dprime_deep_fixed",
    ]
    comparison = frame[columns].merge(
        reference[columns], on="unit_id", suffixes=("_new", "_reference"),
        validate="one_to_one",
    )
    for column in columns[1:]:
        error = np.max(
            np.abs(
                comparison[f"{column}_new"].to_numpy()
                - comparison[f"{column}_reference"].to_numpy()
            )
        )
        if error > 1e-6:
            raise ValueError(f"{column} differs from frozen endpoint by {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rec-url", required=True)
    parser.add_argument("--gt-url", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--inference-code", required=True)
    parser.add_argument("--reference-scores", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--model-label", default="ib_w96_om0_s0")
    parser.add_argument("--units", default="2143,1143,720,1129")
    parser.add_argument("--exemplar-unit", type=int, default=1143)
    parser.add_argument("--overview-ms", type=float, default=30.0)
    parser.add_argument("--local-ms", type=float, default=4.0)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(args.inference_code).resolve()))
    import spikeinterface as si
    from di_ephys.inference import deepinterpolate

    detail_units = [int(value) for value in args.units.split(",")]
    if args.exemplar_unit not in detail_units:
        detail_units.append(args.exemplar_unit)
    recording = si.read_zarr(args.rec_url, storage_options={"anon": True})
    sorting = si.read_zarr(args.gt_url, storage_options={"anon": True})
    denoised = deepinterpolate(
        recording,
        args.checkpoint,
        device=args.device,
        batch_size=args.batch_size,
    )

    metrics, details = compute_surrogate(
        recording,
        denoised,
        sorting,
        n_spikes=100,
        n_background=200,
        seed=0,
        detail_units=detail_units,
    )
    _validate_against_reference(metrics, Path(args.reference_scores))

    sampling_frequency = float(recording.get_sampling_frequency())
    num_samples = int(recording.get_num_samples(segment_index=0))
    event_time, isolation_frames = _select_exemplar_time(
        sorting, args.exemplar_unit, num_samples, sampling_frequency
    )
    overview_frames = int(round(args.overview_ms * sampling_frequency / 1000.0))
    overview_start = event_time - overview_frames // 2
    overview_end = overview_start + overview_frames
    raw_overview = recording.get_traces(
        segment_index=0, start_frame=overview_start, end_frame=overview_end
    )
    denoised_overview = denoised.get_traces(
        segment_index=0, start_frame=overview_start, end_frame=overview_end
    )
    raw_overview = _native_to_microvolts(recording, raw_overview)
    denoised_overview = _native_to_microvolts(recording, denoised_overview)

    locations = np.asarray(recording.get_channel_locations(), dtype=np.float32)
    peak_channel = int(details[args.exemplar_unit]["peak_channel"])
    distances = np.linalg.norm(locations - locations[peak_channel], axis=1)
    local_channels = np.argsort(distances)[:24]
    local_channels = local_channels[
        np.lexsort((locations[local_channels, 0], locations[local_channels, 1]))
    ][::-1]
    local_frames = int(round(args.local_ms * sampling_frequency / 1000.0))
    local_start = event_time - local_frames // 2
    local_end = local_start + local_frames
    raw_local = recording.get_traces(
        segment_index=0, start_frame=local_start, end_frame=local_end,
        channel_ids=recording.channel_ids[local_channels],
    )
    denoised_local = denoised.get_traces(
        segment_index=0, start_frame=local_start, end_frame=local_end,
        channel_ids=recording.channel_ids[local_channels],
    )
    raw_local = _native_to_microvolts(recording, raw_local, local_channels)
    denoised_local = _native_to_microvolts(
        recording, denoised_local, local_channels
    )

    depth_order = np.lexsort((locations[:, 0], locations[:, 1]))[::-1]
    payload: dict[str, np.ndarray] = {
        "sampling_frequency": np.asarray(sampling_frequency),
        "exemplar_unit": np.asarray(args.exemplar_unit),
        "event_frame": np.asarray(event_time),
        "event_isolation_frames": np.asarray(isolation_frames),
        "overview_time_ms": (
            np.arange(overview_frames) + overview_start - event_time
        ).astype(np.float32) / sampling_frequency * 1000.0,
        "raw_probe_uV": raw_overview[:, depth_order].T.astype(np.float32),
        "denoised_probe_uV": denoised_overview[:, depth_order].T.astype(np.float32),
        "probe_depth_um": locations[depth_order, 1].astype(np.float32),
        "local_time_ms": (
            np.arange(local_frames) + local_start - event_time
        ).astype(np.float32) / sampling_frequency * 1000.0,
        "raw_local_uV": raw_local.T.astype(np.float32),
        "denoised_local_uV": denoised_local.T.astype(np.float32),
        "local_channels": local_channels.astype(np.int64),
        "local_depth_um": locations[local_channels, 1].astype(np.float32),
        "local_peak_index": np.asarray(
            int(np.where(local_channels == peak_channel)[0][0])
        ),
    }
    metrics_by_unit = metrics.set_index("unit_id")
    for unit_id in detail_units:
        detail = details[unit_id]
        channels = np.asarray(detail["channels"], dtype=np.int64)
        order = np.lexsort((locations[channels, 0], locations[channels, 1]))[::-1]
        channels = channels[order]
        peak_channel = int(detail["peak_channel"])
        peak_index = int(np.where(channels == peak_channel)[0][0])
        raw_template = np.asarray(detail["raw_template"])[:, order]
        denoised_template = np.asarray(detail["denoised_template"])[:, order]
        payload[f"unit_{unit_id}_channels"] = channels
        payload[f"unit_{unit_id}_depth_um"] = locations[channels, 1]
        payload[f"unit_{unit_id}_peak_index"] = np.asarray(peak_index)
        payload[f"unit_{unit_id}_raw_template_uV"] = _native_to_microvolts(
            recording, raw_template, channels
        )
        payload[f"unit_{unit_id}_denoised_template_uV"] = _native_to_microvolts(
            recording, denoised_template, channels
        )
        for key in (
            "raw_hit_scores",
            "raw_background_scores",
            "denoised_hit_scores",
            "denoised_background_scores",
        ):
            payload[f"unit_{unit_id}_{key}"] = np.asarray(detail[key])
        for key in (
            "dprime_raw",
            "dprime_deep",
            "dprime_deep_fixed",
            "snr_raw",
            "snr_deep",
        ):
            payload[f"unit_{unit_id}_{key}"] = np.asarray(
                metrics_by_unit.loc[unit_id, key]
            )

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **payload)
    metrics.to_csv(output_path.with_suffix(".csv"), index=False)
    checkpoint_hash = hashlib.sha256(Path(args.checkpoint).read_bytes()).hexdigest()
    metadata = {
        "recording_url": args.rec_url,
        "sorting_url": args.gt_url,
        "model_label": args.model_label,
        "checkpoint_sha256": checkpoint_hash,
        "inference_commit": "808d7fa",
        "scoring_seed": 0,
        "n_spikes_per_unit": 100,
        "n_background_events": 200,
        "detail_units": detail_units,
        "exemplar_unit": args.exemplar_unit,
        "exemplar_event_frame": event_time,
        "exemplar_isolation_ms": isolation_frames / sampling_frequency * 1000.0,
        "overview_ms": args.overview_ms,
        "local_ms": args.local_ms,
        "voltage_unit": "uV",
        "reference_scores": str(args.reference_scores),
    }
    Path(args.metadata).write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"wrote {output_path} and {args.metadata}")


if __name__ == "__main__":
    main()