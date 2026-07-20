#!/usr/bin/env python3
"""Measure empirical-template attenuation and temporal/spatial fidelity.

For each GT unit, this driver extracts the same raw and denoised event windows,
selects channels from the raw empirical footprint, and compares the resulting
templates. It writes a per-unit CSV and an NPZ containing the template arrays.
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
import spikeinterface as si

from detection_metrics import extract_windows


def _unit(vector):
    return vector / max(np.linalg.norm(vector), 1e-9)


def _rank1(matrix):
    matrix = matrix - np.median(matrix[:5], axis=0, keepdims=True)
    left, singular_values, right = np.linalg.svd(matrix, full_matrices=False)
    temporal = left[:, 0]
    spatial = right[0]
    strongest = int(np.argmax(np.abs(spatial)))
    if spatial[strongest] < 0:
        spatial = -spatial
        temporal = -temporal
    rank1_fraction = float(
        singular_values[0] ** 2 / max((singular_values**2).sum(), 1e-12)
    )
    return temporal, spatial, rank1_fraction


def _fwhm(waveform):
    waveform = waveform - np.median(waveform[:5])
    trough = int(np.argmin(waveform))
    half = waveform[trough] * 0.5
    left = trough
    while left > 0 and waveform[left] <= half:
        left -= 1
    right = trough
    while right < len(waveform) - 1 and waveform[right] <= half:
        right += 1
    return float(right - left)


def _lag(reference, waveform):
    reference = _unit(reference - reference.mean())
    waveform = _unit(waveform - waveform.mean())
    correlation = np.correlate(waveform, reference, mode="full")
    return int(np.argmax(correlation) - (len(reference) - 1))


def diagnose(
    raw_recording,
    denoised_recording,
    sorting,
    n_spikes=200,
    ms_before=1.5,
    ms_after=2.5,
    peak_fraction=0.5,
    max_channels=24,
    seed=0,
):
    sampling_frequency = float(raw_recording.get_sampling_frequency())
    nbefore = int(round(ms_before * sampling_frequency / 1000.0))
    nafter = int(round(ms_after * sampling_frequency / 1000.0))
    num_samples = int(raw_recording.get_num_samples(0))
    guard = nbefore + nafter + 64
    rng = np.random.default_rng(seed)
    locations = np.asarray(raw_recording.get_channel_locations())
    rows = []
    templates = {}

    for unit_id in sorting.unit_ids:
        spike_train = np.asarray(
            sorting.get_unit_spike_train(unit_id, segment_index=0)
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
        raw_all = raw_waveforms.mean(axis=0)
        peak_to_peak = np.ptp(raw_all, axis=0)
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
        raw_template = raw_waveforms[:, :, channels].mean(axis=0)
        denoised_template = denoised_waveforms.mean(axis=0)

        raw_temporal, raw_spatial, raw_rank1 = _rank1(raw_template)
        deep_temporal, deep_spatial, deep_rank1 = _rank1(denoised_template)
        raw_peak = raw_template[:, peak_index] - np.median(
            raw_template[:5, peak_index]
        )
        deep_peak = denoised_template[:, peak_index] - np.median(
            denoised_template[:5, peak_index]
        )
        raw_amplitude = np.ptp(raw_template, axis=0)
        deep_amplitude = np.ptp(denoised_template, axis=0)
        depths = locations[channels, 1]

        def spread(amplitude):
            center = np.sum(amplitude * depths) / max(amplitude.sum(), 1e-9)
            return np.sqrt(
                np.sum(amplitude * (depths - center) ** 2)
                / max(amplitude.sum(), 1e-9)
            )

        rows.append(
            {
                "unit_id": int(unit_id),
                "n": int(selected.size),
                "peak_ch": peak_channel,
                "n_ch": int(channels.size),
                "peakSNRamp": float(peak_to_peak[peak_channel]),
                "temporal_cos": float(
                    abs(np.dot(_unit(raw_temporal), _unit(deep_temporal)))
                ),
                "spatial_cos": float(
                    abs(np.dot(_unit(raw_spatial), _unit(deep_spatial)))
                ),
                "temporal_corr": float(np.corrcoef(raw_peak, deep_peak)[0, 1]),
                "spatial_corr": float(np.corrcoef(raw_amplitude, deep_amplitude)[0, 1]),
                "amp_ratio": float(
                    np.ptp(deep_peak) / max(np.ptp(raw_peak), 1e-9)
                ),
                "fwhm_ratio": float(
                    _fwhm(deep_peak) / max(_fwhm(raw_peak), 1e-9)
                ),
                "lag": _lag(raw_peak, deep_peak),
                "spread_ratio": float(
                    spread(deep_amplitude) / max(spread(raw_amplitude), 1e-9)
                ),
                "rank1_raw": raw_rank1,
                "rank1_deep": deep_rank1,
            }
        )
        templates[str(unit_id)] = {
            "Traw": raw_template,
            "Tdeep": denoised_template,
            "pc": np.asarray(peak_index),
        }
        print(
            f"[diag] unit {unit_id}: amp={rows[-1]['amp_ratio']:.3f} "
            f"tcos={rows[-1]['temporal_cos']:.3f} "
            f"scos={rows[-1]['spatial_cos']:.3f}",
            flush=True,
        )
    return pd.DataFrame(rows), templates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rec-url", required=True)
    parser.add_argument("--gt-url", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--n-spikes", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--out", default="template_diag.csv")
    parser.add_argument("--npz", default="template_diag.npz")
    args = parser.parse_args()
    start = time.time()
    recording = si.read_zarr(args.rec_url, storage_options={"anon": True})
    sorting = si.read_zarr(args.gt_url, storage_options={"anon": True})
    from di_ephys.inference import deepinterpolate

    denoised = deepinterpolate(
        recording,
        args.checkpoint,
        device=args.device,
        batch_size=args.batch_size,
    )
    frame, templates = diagnose(
        recording, denoised, sorting, n_spikes=args.n_spikes
    )
    frame.to_csv(args.out, index=False)
    np.savez_compressed(
        args.npz,
        **{
            f"{unit_id}_{key}": value
            for unit_id, values in templates.items()
            for key, value in values.items()
        },
    )
    print("\n" + frame.round(3).to_string())
    print(f"\n[run] TOTAL {time.time() - start:.0f}s -> {args.out}, {args.npz}")


if __name__ == "__main__":
    main()