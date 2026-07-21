#!/usr/bin/env python3
"""Test whether temporal or spatial template support explains the d-prime gap.

The frozen endpoint uses a 4-ms template and raw-template channels above 50% of
the peak amplitude. This diagnostic rescans nested temporal crops and raw-ranked
channel counts using the same GT events and spike-excluded background windows.
It reports both the original in-sample calculation and two-fold cross-fitted
scores whose templates and channel rankings never use the held-out spikes.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from detection_metrics import (
    _sample_background_times,
    auc,
    extract_windows,
    standardized_separation,
    validate_frame_alignment,
)


def centered_time_slice(
    duration_ms: float,
    sampling_frequency: float,
    nbefore: int,
    window_length: int,
) -> slice:
    """Return a center-aligned crop; the maximum duration retains the full window."""
    sample_count = int(round(duration_ms * sampling_frequency / 1000.0))
    if sample_count <= 0 or sample_count > window_length:
        raise ValueError(
            f"duration {duration_ms} ms gives invalid {sample_count}/{window_length} samples"
        )
    if sample_count == window_length:
        return slice(0, window_length)
    start = nbefore - sample_count // 2
    stop = start + sample_count
    if start < 0 or stop > window_length:
        raise ValueError(
            f"centered {duration_ms}-ms crop [{start}, {stop}) exceeds the window"
        )
    return slice(start, stop)


def channel_supports(
    raw_training_template: np.ndarray,
    top_ks: tuple[int, ...],
    peak_fraction: float = 0.5,
    max_channels: int = 24,
) -> list[tuple[str, int, np.ndarray]]:
    """Return the frozen endpoint support plus nested raw-amplitude-ranked supports."""
    peak_to_peak = np.ptp(raw_training_template, axis=0)
    ranking = np.argsort(peak_to_peak, kind="stable")[::-1]
    peak_channel = int(ranking[0])
    endpoint = np.flatnonzero(
        peak_to_peak >= peak_fraction * peak_to_peak[peak_channel]
    )
    if endpoint.size > max_channels:
        endpoint = endpoint[
            np.argsort(peak_to_peak[endpoint], kind="stable")[::-1][:max_channels]
        ]
    if peak_channel not in endpoint:
        endpoint = np.append(endpoint, peak_channel)

    supports = [("endpoint", int(endpoint.size), endpoint.astype(np.int64))]
    for requested in top_ks:
        count = min(int(requested), raw_training_template.shape[1])
        supports.append(
            (f"top{requested}", count, ranking[:count].astype(np.int64))
        )
    return supports


def _project(windows: np.ndarray, template: np.ndarray) -> np.ndarray:
    vector = template.reshape(-1)
    vector = vector / max(float(np.linalg.norm(vector)), 1e-9)
    return windows.reshape(windows.shape[0], -1) @ vector


def _score_support(
    raw_hits: np.ndarray,
    denoised_hits: np.ndarray,
    raw_background: np.ndarray,
    denoised_background: np.ndarray,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    time_slice: slice,
    channels: np.ndarray,
) -> dict[str, float]:
    raw_training = raw_hits[train_indices][:, time_slice, :][:, :, channels]
    denoised_training = denoised_hits[train_indices][:, time_slice, :][:, :, channels]
    raw_template = raw_training.mean(axis=0)
    denoised_template = denoised_training.mean(axis=0)

    raw_hit_scores = _project(
        raw_hits[test_indices][:, time_slice, :][:, :, channels], raw_template
    )
    deep_hit_scores = _project(
        denoised_hits[test_indices][:, time_slice, :][:, :, channels],
        denoised_template,
    )
    raw_background_scores = _project(
        raw_background[:, time_slice, :][:, :, channels], raw_template
    )
    deep_background_scores = _project(
        denoised_background[:, time_slice, :][:, :, channels], denoised_template
    )
    dprime_raw = standardized_separation(raw_hit_scores, raw_background_scores)
    dprime_deep = standardized_separation(
        deep_hit_scores, deep_background_scores
    )
    return {
        "dprime_raw": dprime_raw,
        "dprime_deep": dprime_deep,
        "ddprime": dprime_deep - dprime_raw,
        "auc_raw": auc(raw_hit_scores, raw_background_scores),
        "auc_deep": auc(deep_hit_scores, deep_background_scores),
    }


def score_supports(
    raw_hits: np.ndarray,
    denoised_hits: np.ndarray,
    raw_background: np.ndarray,
    denoised_background: np.ndarray,
    sampling_frequency: float,
    nbefore: int,
    temporal_ms: tuple[float, ...] = (0.5, 1.0, 2.0, 3.0, 4.0),
    top_ks: tuple[int, ...] = (1, 2, 4, 8, 16, 24),
    peak_fraction: float = 0.5,
    max_channels: int = 24,
) -> pd.DataFrame:
    """Score nested supports in-sample and with deterministic two-fold cross-fitting."""
    if raw_hits.shape != denoised_hits.shape:
        raise ValueError("raw and denoised hit windows must have identical shapes")
    if raw_background.shape != denoised_background.shape:
        raise ValueError("raw and denoised background windows must have identical shapes")
    if raw_hits.shape[1:] != raw_background.shape[1:]:
        raise ValueError("hit and background windows must share time/channel dimensions")
    if raw_hits.shape[0] < 4:
        raise ValueError("cross-fitting requires at least four hit windows")

    all_indices = np.arange(raw_hits.shape[0], dtype=np.int64)
    heldout_fold = all_indices % 2
    splits = [("in_sample", -1, all_indices, all_indices)]
    for fold in (0, 1):
        splits.append(
            (
                "crossfit",
                fold,
                all_indices[heldout_fold != fold],
                all_indices[heldout_fold == fold],
            )
        )

    rows: list[dict[str, float | int | str]] = []
    for evaluation, fold, train_indices, test_indices in splits:
        raw_training_template = raw_hits[train_indices].mean(axis=0)
        supports = channel_supports(
            raw_training_template,
            top_ks=top_ks,
            peak_fraction=peak_fraction,
            max_channels=max_channels,
        )
        for duration_ms in temporal_ms:
            time_slice = centered_time_slice(
                duration_ms,
                sampling_frequency,
                nbefore,
                raw_hits.shape[1],
            )
            for spatial_support, channel_count, channels in supports:
                scores = _score_support(
                    raw_hits,
                    denoised_hits,
                    raw_background,
                    denoised_background,
                    train_indices,
                    test_indices,
                    time_slice,
                    channels,
                )
                rows.append(
                    {
                        "evaluation": evaluation,
                        "fold": fold,
                        "temporal_ms": duration_ms,
                        "temporal_samples": time_slice.stop - time_slice.start,
                        "spatial_support": spatial_support,
                        "n_channels": channel_count,
                        "n_train_hits": len(train_indices),
                        "n_test_hits": len(test_indices),
                        **scores,
                    }
                )
    return pd.DataFrame(rows)


def _summarize(detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_columns = ["model_label", "unit_id", "evaluation", "temporal_ms", "spatial_support"]
    numeric = [
        "n_channels",
        "dprime_raw",
        "dprime_deep",
        "ddprime",
        "auc_raw",
        "auc_deep",
    ]
    per_unit = detail.groupby(group_columns, as_index=False)[numeric].mean()
    summary_columns = ["model_label", "evaluation", "temporal_ms", "spatial_support"]
    summary = per_unit.groupby(summary_columns, as_index=False)[numeric].mean()
    improved = (
        per_unit.assign(improved=per_unit["ddprime"] > 0)
        .groupby(summary_columns, as_index=False)["improved"]
        .sum()
        .rename(columns={"improved": "units_improved"})
    )
    summary = summary.merge(improved, on=summary_columns, validate="one_to_one")
    return per_unit, summary


def main() -> None:
    import spikeinterface as si

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rec-url", required=True)
    parser.add_argument("--gt-url", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--reference-scores", required=True)
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--out-prefix", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--n-spikes", type=int, default=100)
    parser.add_argument("--n-background", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    start = time.time()
    recording = si.read_zarr(args.rec_url, storage_options={"anon": True})
    sorting = si.read_zarr(args.gt_url, storage_options={"anon": True})
    validate_frame_alignment(recording, sorting)
    from di_ephys.inference import deepinterpolate

    denoised = deepinterpolate(
        recording,
        args.checkpoint,
        device=args.device,
        batch_size=args.batch_size,
    )
    sampling_frequency = float(recording.get_sampling_frequency())
    nbefore = int(round(1.5 * sampling_frequency / 1000.0))
    nafter = int(round(2.5 * sampling_frequency / 1000.0))
    window_length = nbefore + nafter
    guard = window_length + 64
    num_samples = int(recording.get_num_samples(segment_index=0))
    unit_ids = list(sorting.unit_ids)
    all_spikes = np.sort(
        np.concatenate(
            [
                np.asarray(sorting.get_unit_spike_train(unit_id, segment_index=0))
                for unit_id in unit_ids
            ]
        )
    )
    rng = np.random.default_rng(args.seed)
    background_times = _sample_background_times(
        rng,
        all_spikes,
        args.n_background,
        guard,
        num_samples,
        window_length,
    )
    raw_background = extract_windows(
        recording, background_times, nbefore, nafter
    )
    denoised_background = extract_windows(
        denoised, background_times, nbefore, nafter
    )

    frames = []
    for unit_index, unit_id in enumerate(unit_ids):
        spike_train = np.asarray(
            sorting.get_unit_spike_train(unit_id, segment_index=0)
        )
        spike_train = spike_train[
            (spike_train > guard) & (spike_train < num_samples - guard)
        ]
        selected = (
            spike_train
            if spike_train.size <= args.n_spikes
            else rng.choice(spike_train, args.n_spikes, replace=False)
        )
        selected = np.sort(selected)
        raw_hits = extract_windows(recording, selected, nbefore, nafter)
        denoised_hits = extract_windows(denoised, selected, nbefore, nafter)
        frame = score_supports(
            raw_hits,
            denoised_hits,
            raw_background,
            denoised_background,
            sampling_frequency=sampling_frequency,
            nbefore=nbefore,
        )
        frame.insert(0, "unit_id", int(unit_id))
        frame.insert(0, "model_label", args.model_label)
        frames.append(frame)
        print(
            f"[support] unit {unit_id} ({unit_index + 1}/{len(unit_ids)})",
            flush=True,
        )

    detail = pd.concat(frames, ignore_index=True)
    reference = pd.read_csv(args.reference_scores).set_index("unit_id")
    endpoint = detail[
        (detail["evaluation"] == "in_sample")
        & (detail["temporal_ms"] == 4.0)
        & (detail["spatial_support"] == "endpoint")
    ].set_index("unit_id")
    for column in ("dprime_raw", "dprime_deep"):
        error = float(np.max(np.abs(endpoint[column] - reference.loc[endpoint.index, column])))
        if error > 1e-6:
            raise ValueError(f"frozen {column} reproduction error {error}")
    channel_mismatch = endpoint["n_channels"].astype(int) != reference.loc[
        endpoint.index, "n_ch"
    ].astype(int)
    if channel_mismatch.any():
        raise ValueError(
            "frozen endpoint channel-count mismatch for units "
            + ", ".join(str(unit_id) for unit_id in endpoint.index[channel_mismatch])
        )
    per_unit, summary = _summarize(detail)
    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(prefix.with_name(prefix.name + "_detail.csv"), index=False)
    per_unit.to_csv(prefix.with_name(prefix.name + "_per_unit.csv"), index=False)
    summary.to_csv(prefix.with_name(prefix.name + "_summary.csv"), index=False)
    print(
        f"[support] endpoint reproduced; wrote {prefix.name}_*.csv in "
        f"{time.time() - start:.0f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()