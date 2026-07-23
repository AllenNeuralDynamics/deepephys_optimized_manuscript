#!/usr/bin/env python3
"""Export compact residual Gaussianity and whiteness diagnostics."""
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

from detection_metrics import (
    _sample_background_times,
    extract_windows,
    validate_frame_alignment,
)
from residual_statistics import analyze_domain


def _native_to_microvolts(recording, traces: np.ndarray) -> np.ndarray:
    num_channels = recording.get_num_channels()
    try:
        gains = np.asarray(recording.get_channel_gains(), dtype=np.float32)
        offsets = np.asarray(recording.get_channel_offsets(), dtype=np.float32)
    except Exception:
        gains = np.ones(num_channels, dtype=np.float32)
        offsets = np.zeros(num_channels, dtype=np.float32)
    return np.asarray(traces, dtype=np.float32) * gains + offsets


def select_gt_free_starts(
    spike_frames: np.ndarray,
    num_samples: int,
    length: int,
    count: int,
) -> np.ndarray:
    """Select deterministic, recording-spanning intervals without injected spikes."""
    spikes = np.unique(np.asarray(spike_frames, dtype=np.int64))
    boundaries = np.concatenate(([-1], spikes, [num_samples]))
    starts = []
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        available_start = int(left) + 1
        available_stop = int(right)
        if available_stop - available_start >= length:
            starts.append((available_start + available_stop - length) // 2)
    if len(starts) < count:
        raise RuntimeError(
            f"found only {len(starts)} GT-free intervals of {length} samples; "
            f"requested {count}"
        )
    if count == 1:
        midpoint = num_samples / 2
        centers = np.asarray(starts, dtype=np.float64) + length / 2
        return np.asarray([starts[int(np.argmin(np.abs(centers - midpoint)))]])
    selected = np.linspace(0, len(starts) - 1, count).round().astype(int)
    return np.asarray(starts, dtype=np.int64)[selected]


def _extract_segments(recording, starts: np.ndarray, length: int) -> np.ndarray:
    output = np.empty(
        (len(starts), length, recording.get_num_channels()), dtype=np.float32
    )
    for index, start in enumerate(starts):
        output[index] = recording.get_traces(
            segment_index=0,
            start_frame=int(start),
            end_frame=int(start) + length,
        )
    return output


def _hash_array(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    return hashlib.sha256(contiguous.view(np.uint8)).hexdigest()


def _spatial_summary(
    correlations: np.ndarray, distances: np.ndarray
) -> dict[str, float]:
    off_diagonal = ~np.eye(correlations.shape[0], dtype=bool)
    near = off_diagonal & (distances <= 40.0)
    far = distances >= 200.0
    return {
        "median_abs_spatial_correlation": float(
            np.median(np.abs(correlations[off_diagonal]))
        ),
        "median_abs_near_correlation": float(np.median(np.abs(correlations[near]))),
        "median_abs_far_correlation": float(np.median(np.abs(correlations[far]))),
    }


def _summary_row(
    model_label: str,
    domain: str,
    channel_table: pd.DataFrame,
    arrays: dict[str, np.ndarray],
    distances: np.ndarray,
    variance_ratio: float,
) -> dict[str, float | int | str]:
    row: dict[str, float | int | str] = {
        "model_label": model_label,
        "domain": domain,
        "channels": len(channel_table),
        "median_std_uV": float(channel_table["std"].median()),
        "median_abs_skewness": float(channel_table["skewness"].abs().median()),
        "median_excess_kurtosis": float(channel_table["excess_kurtosis"].median()),
        "median_normal_quantile_rmse": float(
            channel_table["normal_quantile_rmse"].median()
        ),
        "median_fraction_abs_gt_3": float(channel_table["fraction_abs_gt_3"].median()),
        "median_fraction_abs_gt_5": float(channel_table["fraction_abs_gt_5"].median()),
        "jarque_bera_fdr_reject_fraction": float(
            channel_table["jarque_bera_fdr_reject"].mean()
        ),
        "median_mean_abs_autocorrelation": float(
            channel_table["mean_abs_autocorrelation"].median()
        ),
        "median_max_abs_autocorrelation": float(
            channel_table["max_abs_autocorrelation"].median()
        ),
        "ljung_box_fdr_reject_fraction": float(
            channel_table["ljung_box_fdr_reject"].mean()
        ),
        "median_spectral_flatness": float(channel_table["spectral_flatness"].median()),
        "median_variance_ratio_to_raw": variance_ratio,
    }
    row.update(_spatial_summary(arrays["spatial_correlation"], distances))
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rec-url", required=True)
    parser.add_argument("--gt-url", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    parser.add_argument("--inference-code", required=True)
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--out-prefix", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--background-windows", type=int, default=512)
    parser.add_argument("--window-ms", type=float, default=4.0)
    parser.add_argument("--spectral-segments", type=int, default=32)
    parser.add_argument("--spectral-samples", type=int, default=1024)
    parser.add_argument("--overview-ms", type=float, default=30.0)
    parser.add_argument("--max-lag", type=int, default=30)
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    checkpoint_hash = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    if checkpoint_hash != args.checkpoint_sha256:
        raise ValueError(
            f"checkpoint SHA-256 mismatch: {checkpoint_hash} != {args.checkpoint_sha256}"
        )

    sys.path.insert(0, str(Path(args.inference_code).resolve()))
    import spikeinterface as si
    from di_ephys.inference import deepinterpolate

    recording = si.read_zarr(args.rec_url, storage_options={"anon": True})
    sorting = si.read_zarr(args.gt_url, storage_options={"anon": True})
    validate_frame_alignment(recording, sorting)
    if recording.get_num_channels() != 384 or len(sorting.unit_ids) != 10:
        raise ValueError("expected the frozen 384-channel, 10-unit NP1 benchmark")
    prediction = deepinterpolate(
        recording,
        checkpoint_path,
        device=args.device,
        batch_size=args.batch_size,
    )

    sampling_frequency = float(recording.get_sampling_frequency())
    num_samples = int(recording.get_num_samples(segment_index=0))
    all_spikes = np.sort(
        np.concatenate(
            [
                np.asarray(sorting.get_unit_spike_train(unit_id, segment_index=0))
                for unit_id in sorting.unit_ids
            ]
        )
    )
    window_samples = int(round(args.window_ms * sampling_frequency / 1000.0))
    before = window_samples // 2
    after = window_samples - before
    random = np.random.default_rng(args.seed)
    candidate_times = _sample_background_times(
        random,
        all_spikes,
        args.background_windows * 3,
        guard=window_samples + 64,
        num_samples=num_samples,
        exclusion_radius=window_samples,
    )
    background_times = []
    for candidate in candidate_times:
        if all(abs(int(candidate) - selected) > window_samples for selected in background_times):
            background_times.append(int(candidate))
        if len(background_times) == args.background_windows:
            break
    if len(background_times) != args.background_windows:
        raise RuntimeError("could not select nonoverlapping background windows")
    background_times = np.asarray(background_times, dtype=np.int64)

    raw_windows = _native_to_microvolts(
        recording, extract_windows(recording, background_times, before, after)
    )
    prediction_windows = _native_to_microvolts(
        recording, extract_windows(prediction, background_times, before, after)
    )
    residual_windows = raw_windows - prediction_windows

    spectral_starts = select_gt_free_starts(
        all_spikes,
        num_samples,
        args.spectral_samples,
        args.spectral_segments,
    )
    raw_segments = _native_to_microvolts(
        recording, _extract_segments(recording, spectral_starts, args.spectral_samples)
    )
    prediction_segments = _native_to_microvolts(
        recording, _extract_segments(prediction, spectral_starts, args.spectral_samples)
    )
    residual_segments = raw_segments - prediction_segments

    overview_samples = int(round(args.overview_ms * sampling_frequency / 1000.0))
    overview_start = int(
        select_gt_free_starts(all_spikes, num_samples, overview_samples, 1)[0]
    )
    raw_overview = _native_to_microvolts(
        recording,
        recording.get_traces(
            segment_index=0,
            start_frame=overview_start,
            end_frame=overview_start + overview_samples,
        ),
    )
    prediction_overview = _native_to_microvolts(
        recording,
        prediction.get_traces(
            segment_index=0,
            start_frame=overview_start,
            end_frame=overview_start + overview_samples,
        ),
    )
    residual_overview = raw_overview - prediction_overview

    locations = np.asarray(recording.get_channel_locations(), dtype=np.float32)
    distances = np.linalg.norm(locations[:, None, :] - locations[None, :, :], axis=2)
    depth_order = np.lexsort((locations[:, 0], locations[:, 1]))[::-1]
    raw_variances = raw_windows.reshape(-1, raw_windows.shape[-1]).var(axis=0)
    domains = {
        "raw": (raw_windows, raw_segments),
        "prediction": (prediction_windows, prediction_segments),
        "residual": (residual_windows, residual_segments),
    }
    payload: dict[str, np.ndarray] = {
        "sampling_frequency": np.asarray(sampling_frequency),
        "channel_locations_um": locations,
        "channel_depth_order": depth_order,
        "spatial_distance_um": distances.astype(np.float32),
        "background_times": background_times,
        "spectral_starts": spectral_starts,
        "overview_start_frame": np.asarray(overview_start),
        "overview_time_ms": np.arange(overview_samples, dtype=np.float32)
        / sampling_frequency
        * 1000.0,
        "raw_overview_uV": raw_overview[:, depth_order].T.astype(np.float32),
        "prediction_overview_uV": prediction_overview[:, depth_order].T.astype(np.float32),
        "residual_overview_uV": residual_overview[:, depth_order].T.astype(np.float32),
    }
    channel_frames = []
    summary_rows = []
    for domain, (windows, segments) in domains.items():
        channel_table, arrays = analyze_domain(
            windows,
            segments,
            sampling_frequency=sampling_frequency,
            max_lag=args.max_lag,
        )
        channel_table.insert(0, "domain", domain)
        channel_table.insert(0, "model_label", args.model_label)
        channel_table["x_um"] = locations[:, 0]
        channel_table["depth_um"] = locations[:, 1]
        channel_frames.append(channel_table)
        domain_variances = windows.reshape(-1, windows.shape[-1]).var(axis=0)
        summary_rows.append(
            _summary_row(
                args.model_label,
                domain,
                channel_table,
                arrays,
                distances,
                variance_ratio=float(np.median(domain_variances / raw_variances)),
            )
        )
        for key, values in arrays.items():
            payload[f"{domain}_{key}"] = np.asarray(values, dtype=np.float32)

    prediction_flat = prediction_windows.reshape(-1, prediction_windows.shape[-1])
    residual_flat = residual_windows.reshape(-1, residual_windows.shape[-1])
    prediction_residual_correlation = np.asarray(
        [
            np.corrcoef(prediction_flat[:, index], residual_flat[:, index])[0, 1]
            for index in range(prediction_flat.shape[1])
        ]
    )
    payload["prediction_residual_correlation"] = prediction_residual_correlation.astype(
        np.float32
    )

    output_prefix = Path(args.out_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_prefix.with_suffix(".npz"), **payload)
    pd.concat(channel_frames, ignore_index=True).to_csv(
        output_prefix.with_name(output_prefix.name + "_channels.csv"), index=False
    )
    summary = pd.DataFrame(summary_rows)
    summary["median_abs_prediction_residual_correlation"] = float(
        np.median(np.abs(prediction_residual_correlation))
    )
    summary.to_csv(
        output_prefix.with_name(output_prefix.name + "_summary.csv"), index=False
    )
    metadata = {
        "recording_url": args.rec_url,
        "sorting_url": args.gt_url,
        "model_label": args.model_label,
        "checkpoint_sha256": checkpoint_hash,
        "inference_commit": "808d7fa",
        "seed": args.seed,
        "background_windows": args.background_windows,
        "window_ms": args.window_ms,
        "spectral_segments": args.spectral_segments,
        "spectral_samples": args.spectral_samples,
        "overview_ms": args.overview_ms,
        "overview_start_frame": overview_start,
        "injected_gt_spikes": len(all_spikes),
        "raw_overview_sha256": _hash_array(raw_overview),
        "background_times_sha256": _hash_array(background_times),
        "interpretation": (
            "Residual equals raw minus model prediction. Injected GT events are excluded "
            "from analysis windows, but native spikes remain unlabeled. Gaussianity and "
            "whiteness are descriptive diagnostics, not necessary success conditions."
        ),
    }
    output_prefix.with_name(output_prefix.name + "_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n"
    )
    print(f"wrote residual diagnostics for {args.model_label}")


if __name__ == "__main__":
    main()