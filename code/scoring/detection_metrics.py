"""Frozen GT-event versus background scoring used by the manuscript.

The primary metric is a matched-filter d-prime computed separately for every
ground-truth unit. It uses the full distributions of projection scores at known
spike times and at deterministically sampled spike-excluded background times.
No peak counting, threshold selection, or extreme-value statistic enters d-prime.

This module vendors the scoring core used at inference commit ``808d7fa`` and
adds an optional details return for reproducible qualitative figures. Ground-truth
labels are used only here, after self-supervised model training.
"""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def validate_frame_alignment(recording, sorting) -> None:
    """Reject recording/sorting pairs that do not share one frame coordinate system."""
    recording_fs = float(recording.get_sampling_frequency())
    sorting_fs = float(sorting.get_sampling_frequency())
    if recording_fs != sorting_fs:
        raise ValueError(
            f"sampling-frequency mismatch: recording={recording_fs} sorting={sorting_fs}"
        )
    recording_segments = int(recording.get_num_segments())
    sorting_segments = int(sorting.get_num_segments())
    if recording_segments != sorting_segments:
        raise ValueError(
            f"segment-count mismatch: recording={recording_segments} sorting={sorting_segments}"
        )
    if recording_segments != 1:
        raise ValueError(f"scorer requires exactly one segment, got {recording_segments}")

    num_samples = int(recording.get_num_samples(segment_index=0))
    for unit_id in sorting.unit_ids:
        spike_train = np.asarray(
            sorting.get_unit_spike_train(unit_id, segment_index=0)
        )
        if spike_train.ndim != 1:
            raise ValueError(f"unit {unit_id} spike train is not one-dimensional")
        if not np.issubdtype(spike_train.dtype, np.integer):
            raise ValueError(
                f"unit {unit_id} spike train must contain integer frame indices, "
                f"got {spike_train.dtype}"
            )
        if spike_train.size and (
            spike_train.min() < 0 or spike_train.max() >= num_samples
        ):
            raise ValueError(
                f"unit {unit_id} spike frames fall outside recording [0, {num_samples})"
            )


def extract_windows(recording, times, nbefore: int, nafter: int) -> np.ndarray:
    """Return ``(events, time, channels)`` windows in native recording units."""
    window_length = nbefore + nafter
    num_channels = recording.get_num_channels()
    output = np.empty((len(times), window_length, num_channels), dtype=np.float32)
    for index, time in enumerate(times):
        traces = recording.get_traces(
            segment_index=0,
            start_frame=int(time) - nbefore,
            end_frame=int(time) + nafter,
        )
        output[index] = np.asarray(traces, dtype=np.float32)
    return output


def standardized_separation(hit_scores, background_scores) -> float:
    r"""Return pooled-variance d-prime for two score distributions.

    .. math::

       d' = \frac{\mu_{hit} - \mu_{bg}}
                  {\sqrt{(\sigma^2_{hit} + \sigma^2_{bg}) / 2}}

    NumPy population variances (``ddof=0``) reproduce the frozen endpoint scorer.
    """
    hit = np.asarray(hit_scores, dtype=float)
    background = np.asarray(background_scores, dtype=float)
    denominator = np.sqrt(0.5 * (hit.var() + background.var()))
    return float((hit.mean() - background.mean()) / max(denominator, 1e-9))


def auc(hit_scores, background_scores) -> float:
    """Return threshold-free probability that a hit score exceeds background."""
    try:
        from scipy.stats import mannwhitneyu

        hit = np.asarray(hit_scores)
        background = np.asarray(background_scores)
        statistic = mannwhitneyu(hit, background, alternative="greater").statistic
        return float(statistic / (len(hit) * len(background)))
    except Exception:
        return float("nan")


def _sample_background_times(
    rng: np.random.Generator,
    all_spikes: np.ndarray,
    count: int,
    guard: int,
    num_samples: int,
    exclusion_radius: int,
) -> np.ndarray:
    keep: list[int] = []
    attempts = 0
    while len(keep) < count and attempts < 50:
        candidates = rng.integers(guard, num_samples - guard, size=2 * count)
        if all_spikes.size:
            indices = np.searchsorted(all_spikes, candidates)
            distance_left = candidates - all_spikes[
                np.clip(indices - 1, 0, all_spikes.size - 1)
            ]
            distance_right = all_spikes[
                np.clip(indices, 0, all_spikes.size - 1)
            ] - candidates
            distances = np.minimum(
                np.where(indices > 0, distance_left, 1 << 30),
                np.where(indices < all_spikes.size, distance_right, 1 << 30),
            )
            candidates = candidates[distances > exclusion_radius]
        keep.extend(candidates.tolist())
        attempts += 1
    if len(keep) < count:
        raise RuntimeError(f"could sample only {len(keep)}/{count} background events")
    return np.asarray(keep[:count], dtype=np.int64)


def compute_surrogate(
    raw_recording,
    denoised_recording,
    gt_sorting,
    n_spikes: int = 200,
    n_background: int = 500,
    ms_before: float = 1.5,
    ms_after: float = 2.5,
    peak_fraction: float = 0.5,
    max_channels: int = 24,
    max_units: int | None = None,
    seed: int = 0,
    detail_units: Iterable[int] = (),
    verbose: bool = True,
) -> tuple[pd.DataFrame, dict[int, dict[str, np.ndarray | int]]]:
    """Score every GT unit and optionally retain plotting arrays for selected units.

    The denoised-domain primary score uses a template learned from denoised hit
    windows. The fixed-template score projects denoised windows onto the raw
    empirical template. Templates and hit scores reuse the same events, making
    absolute d-prime optimistic; all model comparisons freeze the same events.
    """
    validate_frame_alignment(raw_recording, gt_sorting)
    sampling_frequency = float(raw_recording.get_sampling_frequency())
    nbefore = int(round(ms_before * sampling_frequency / 1000.0))
    nafter = int(round(ms_after * sampling_frequency / 1000.0))
    num_samples = int(raw_recording.get_num_samples(segment_index=0))
    guard = nbefore + nafter + 64
    rng = np.random.default_rng(seed)
    requested_details = {int(unit_id) for unit_id in detail_units}

    unit_ids = list(gt_sorting.unit_ids)
    if max_units is not None:
        unit_ids = unit_ids[:max_units]
    all_spikes = (
        np.sort(
            np.concatenate(
                [
                    np.asarray(
                        gt_sorting.get_unit_spike_train(unit_id, segment_index=0)
                    )
                    for unit_id in unit_ids
                ]
            )
        )
        if unit_ids
        else np.array([], dtype=np.int64)
    )
    background_times = _sample_background_times(
        rng,
        all_spikes,
        n_background,
        guard,
        num_samples,
        nbefore + nafter,
    )
    if verbose:
        print(
            f"[surrogate] fs={sampling_frequency:.0f} window=({nbefore},{nafter}) "
            f"background={len(background_times)}",
            flush=True,
        )
    raw_background_full = extract_windows(
        raw_recording, background_times, nbefore, nafter
    )
    denoised_background_full = extract_windows(
        denoised_recording, background_times, nbefore, nafter
    )

    rows: list[dict[str, float | int]] = []
    details: dict[int, dict[str, np.ndarray | int]] = {}
    for unit_index, unit_id in enumerate(unit_ids):
        spike_train = np.asarray(
            gt_sorting.get_unit_spike_train(unit_id, segment_index=0)
        )
        spike_train = spike_train[
            (spike_train > guard) & (spike_train < num_samples - guard)
        ]
        if spike_train.size == 0:
            continue
        selected = (
            spike_train
            if spike_train.size <= n_spikes
            else rng.choice(spike_train, n_spikes, replace=False)
        )

        raw_waveforms = extract_windows(
            raw_recording, selected, nbefore, nafter
        )
        raw_template_all = raw_waveforms.mean(axis=0)
        peak_to_peak = np.ptp(raw_template_all, axis=0)
        peak_channel = int(np.argmax(peak_to_peak))
        channels = np.where(
            peak_to_peak >= peak_fraction * peak_to_peak[peak_channel]
        )[0]
        if channels.size > max_channels:
            channels = channels[
                np.argsort(peak_to_peak[channels])[::-1][:max_channels]
            ]
        if peak_channel not in channels:
            channels = np.append(channels, peak_channel)
        peak_index = int(np.where(channels == peak_channel)[0][0])

        denoised_waveforms = extract_windows(
            denoised_recording, selected, nbefore, nafter
        )[:, :, channels]
        raw_waveforms = raw_waveforms[:, :, channels]
        raw_background = raw_background_full[:, :, channels]
        denoised_background = denoised_background_full[:, :, channels]
        raw_template = raw_waveforms.mean(axis=0)
        denoised_template = denoised_waveforms.mean(axis=0)

        snr_raw = float(
            np.ptp(raw_template[:, peak_index])
            / max(raw_background[:, :, peak_index].std(), 1e-9)
        )
        snr_denoised = float(
            np.ptp(denoised_template[:, peak_index])
            / max(denoised_background[:, :, peak_index].std(), 1e-9)
        )

        normalize = lambda vector: vector / max(np.linalg.norm(vector), 1e-9)
        project = lambda windows, template: windows.reshape(windows.shape[0], -1) @ template
        raw_filter = normalize(raw_template.reshape(-1))
        denoised_filter = normalize(denoised_template.reshape(-1))
        raw_hits = project(raw_waveforms, raw_filter)
        raw_background_scores = project(raw_background, raw_filter)
        denoised_hits = project(denoised_waveforms, denoised_filter)
        denoised_background_scores = project(denoised_background, denoised_filter)
        fixed_hits = project(denoised_waveforms, raw_filter)
        fixed_background_scores = project(denoised_background, raw_filter)

        row = {
            "unit_id": int(unit_id),
            "n_spikes": int(selected.size),
            "peak_ch": peak_channel,
            "n_ch": int(channels.size),
            "snr_raw": snr_raw,
            "snr_deep": snr_denoised,
            "dsnr": snr_denoised - snr_raw,
            "dprime_raw": standardized_separation(raw_hits, raw_background_scores),
            "dprime_deep": standardized_separation(
                denoised_hits, denoised_background_scores
            ),
            "dprime_deep_fixed": standardized_separation(
                fixed_hits, fixed_background_scores
            ),
            "auc_raw": auc(raw_hits, raw_background_scores),
            "auc_deep": auc(denoised_hits, denoised_background_scores),
            "auc_deep_fixed": auc(fixed_hits, fixed_background_scores),
        }
        rows.append(row)
        if int(unit_id) in requested_details:
            details[int(unit_id)] = {
                "spike_times": np.asarray(selected, dtype=np.int64),
                "background_times": background_times.copy(),
                "channels": np.asarray(channels, dtype=np.int64),
                "peak_channel": peak_channel,
                "peak_index": peak_index,
                "raw_template": raw_template.astype(np.float32),
                "denoised_template": denoised_template.astype(np.float32),
                "raw_hit_scores": raw_hits.astype(np.float32),
                "raw_background_scores": raw_background_scores.astype(np.float32),
                "denoised_hit_scores": denoised_hits.astype(np.float32),
                "denoised_background_scores": denoised_background_scores.astype(
                    np.float32
                ),
            }
        if verbose:
            print(
                f"[surrogate] unit {unit_id} ({unit_index + 1}/{len(unit_ids)}): "
                f"d' {row['dprime_raw']:.2f}->{row['dprime_deep']:.2f}",
                flush=True,
            )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["ddprime"] = frame["dprime_deep"] - frame["dprime_raw"]
        frame["ddprime_fixed"] = (
            frame["dprime_deep_fixed"] - frame["dprime_raw"]
        )
        frame["dauc"] = frame["auc_deep"] - frame["auc_raw"]
    return frame, details