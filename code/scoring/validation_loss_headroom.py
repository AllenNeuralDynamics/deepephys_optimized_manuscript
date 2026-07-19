#!/usr/bin/env python3
"""Measure how much perfect spike reconstruction can move validation loss.

The analysis reconstructs the checkpoint's exact fixed validation subset. Spike
support uses GT times, the scorer's temporal window, and empirical channels at
least ``peak_frac`` of the unit's peak-to-peak maximum. It reports two bounds:

* meaningful headroom: reduce spike-support loss to the same-channel off-spike
  floor;
* zero-residual upper bound: reduce spike-support residual to exactly zero.

The script requires the inference environment (PyTorch, SpikeInterface, and
``di_ephys.model``) and is intended to run on the scoring GPU partition.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch


def context_offsets(pre: int, post: int, omission: int, blind_spot: bool,
                    bs_frames: int) -> np.ndarray:
    left = np.arange(-(omission + pre), -omission)
    right = np.arange(omission + 1, omission + post + 1)
    offsets = np.concatenate([left, right])
    if blind_spot:
        center = np.array([-1, 0, 1]) if bs_frames == 3 else np.array([0])
        offsets = np.concatenate([offsets, center])
    return offsets.astype(np.int64)


def validation_centers(num_frames: int, pre: int, post: int, omission: int,
                       max_windows: int) -> np.ndarray:
    margin = omission + max(pre, post)
    centers = np.arange(margin, num_frames - margin, dtype=np.int64)
    if centers.size > max_windows:
        stride = int(math.ceil(centers.size / max_windows))
        centers = centers[::stride]
    return centers


def spike_support(raw: np.ndarray, centers: np.ndarray, sorting, slice_start: int,
                  fs: float, before_ms: float, after_ms: float, peak_frac: float,
                  max_channels: int, seed: int) -> tuple[np.ndarray, pd.DataFrame]:
    before = int(round(before_ms * fs / 1000.0))
    after = int(round(after_ms * fs / 1000.0))
    num_frames, num_channels = raw.shape
    support = np.zeros((centers.size, num_channels), dtype=bool)
    unit_rows = []
    rng = np.random.default_rng(seed)

    for unit_id in sorting.unit_ids:
        absolute = np.asarray(
            sorting.get_unit_spike_train(unit_id, segment_index=0), dtype=np.int64
        )
        spikes = absolute - slice_start
        spikes = spikes[(spikes >= before) & (spikes < num_frames - after)]
        if spikes.size == 0:
            continue
        selected = spikes if spikes.size <= 100 else rng.choice(spikes, 100, replace=False)
        waveforms = np.stack([raw[t - before:t + after] for t in selected])
        template = waveforms.mean(axis=0)
        peak_to_peak = template.max(axis=0) - template.min(axis=0)
        peak_channel = int(np.argmax(peak_to_peak))
        channels = np.where(peak_to_peak >= peak_frac * peak_to_peak[peak_channel])[0]
        if channels.size > max_channels:
            channels = channels[np.argsort(peak_to_peak[channels])[::-1][:max_channels]]
        if peak_channel not in channels:
            channels = np.append(channels, peak_channel)

        elements_before = int(support.sum())
        for spike in spikes:
            lo = int(np.searchsorted(centers, spike - before, side="left"))
            hi = int(np.searchsorted(centers, spike + after, side="left"))
            if hi > lo:
                support[lo:hi][:, channels] = True
        unit_rows.append({
            "unit_id": unit_id,
            "spikes_in_slice": int(spikes.size),
            "template_spikes": int(selected.size),
            "peak_channel": peak_channel,
            "support_channels": int(channels.size),
            "new_support_elements": int(support.sum()) - elements_before,
        })
    return support, pd.DataFrame(unit_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--rec-url", required=True)
    parser.add_argument("--gt-url", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", default="ib_r5_bs256")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--support-before-ms", type=float, default=1.5)
    parser.add_argument("--support-after-ms", type=float, default=2.5)
    parser.add_argument("--peak-frac", type=float, default=0.5)
    parser.add_argument("--max-channels", type=int, default=24)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    import spikeinterface as si
    from di_ephys.model import build_model

    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    config = payload["config"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(config, payload["in_frames"], payload.get("grid")).to(device)
    model.load_state_dict(payload["state_dict"], strict=True)
    model.eval()

    recording = si.read_zarr(args.rec_url, storage_options={"anon": True})
    sorting = si.read_zarr(args.gt_url, storage_options={"anon": True})
    fs = float(recording.get_sampling_frequency())
    if fs != float(sorting.get_sampling_frequency()):
        raise ValueError("recording/sorting sampling-frequency mismatch")

    slice_start = int(round(float(config["val_slice_start_s"]) * fs))
    slice_frames = int(round(float(config["val_slice_dur_s"]) * fs))
    slice_end = min(recording.get_num_samples(0), slice_start + slice_frames)
    raw = np.asarray(recording.get_traces(
        segment_index=0, start_frame=slice_start, end_frame=slice_end
    ), dtype=np.float32)
    mean = np.asarray(payload["norm_mean"], dtype=np.float32).reshape(1, -1)
    std = np.asarray(payload["norm_std"], dtype=np.float32).reshape(1, -1)
    normalized = (raw - mean) / std
    if str(config.get("traces_dtype", "float32")).lower() == "float16":
        normalized = normalized.astype(np.float16)

    pre = int(config["pre"])
    post = int(config["post"])
    omission = int(config["omission"])
    offsets = context_offsets(
        pre, post, omission, bool(config["blind_spot"]), int(config["bs_frames"])
    )
    if offsets.size != int(payload["in_frames"]):
        raise ValueError(f"context mismatch: {offsets.size} != {payload['in_frames']}")
    centers = validation_centers(
        raw.shape[0], pre, post, omission, int(config["val_max_windows"])
    )
    support, unit_rows = spike_support(
        raw, centers, sorting, slice_start, fs, args.support_before_ms,
        args.support_after_ms, args.peak_frac, args.max_channels, args.seed,
    )

    num_channels = raw.shape[1]
    total_loss = 0.0
    support_loss_by_channel = np.zeros(num_channels, dtype=np.float64)
    support_count_by_channel = np.zeros(num_channels, dtype=np.int64)
    background_loss_by_channel = np.zeros(num_channels, dtype=np.float64)
    background_count_by_channel = np.zeros(num_channels, dtype=np.int64)
    loss_name = str(config["loss"]).lower()
    epsilon = float(config.get("charbonnier_eps", 0.4))

    with torch.no_grad():
        for start in range(0, centers.size, args.batch_size):
            batch_centers = centers[start:start + args.batch_size]
            context = normalized[batch_centers[:, None] + offsets[None, :]]
            target = normalized[batch_centers].astype(np.float32, copy=False)
            prediction = model(torch.from_numpy(context).float().to(device))[:, 0]
            residual = prediction.cpu().numpy() - target
            if loss_name == "charbonnier":
                element_loss = np.sqrt(residual * residual + epsilon * epsilon)
                minimum_loss = epsilon
            elif loss_name == "l2":
                element_loss = residual * residual
                minimum_loss = 0.0
            else:
                raise ValueError(f"unsupported validation loss: {loss_name}")

            mask = support[start:start + batch_centers.size]
            inverse = ~mask
            total_loss += float(element_loss.sum(dtype=np.float64))
            support_loss_by_channel += (element_loss * mask).sum(axis=0, dtype=np.float64)
            support_count_by_channel += mask.sum(axis=0)
            background_loss_by_channel += (element_loss * inverse).sum(axis=0, dtype=np.float64)
            background_count_by_channel += inverse.sum(axis=0)

    num_elements = int(centers.size * num_channels)
    support_count = int(support_count_by_channel.sum())
    background_mean_by_channel = np.divide(
        background_loss_by_channel, background_count_by_channel,
        out=np.full(num_channels, np.nan), where=background_count_by_channel > 0,
    )
    matched_background_sum = float(
        np.nansum(background_mean_by_channel * support_count_by_channel)
    )
    support_loss_sum = float(support_loss_by_channel.sum())
    validation_loss = total_loss / num_elements
    support_loss_mean = support_loss_sum / support_count
    matched_background_mean = matched_background_sum / support_count
    meaningful_drop = (support_loss_sum - matched_background_sum) / num_elements
    zero_residual_drop = (
        support_loss_sum - minimum_loss * support_count
    ) / num_elements
    reported_loss = float(payload.get("val_loss", np.nan))
    if np.isfinite(reported_loss) and abs(validation_loss - reported_loss) > 2e-5:
        raise ValueError(
            f"recomputed validation loss {validation_loss:.9f} does not match "
            f"checkpoint {reported_loss:.9f}"
        )

    row = {
        "label": args.label,
        "loss": loss_name,
        "charbonnier_epsilon": epsilon if loss_name == "charbonnier" else np.nan,
        "validation_loss": validation_loss,
        "checkpoint_validation_loss": reported_loss,
        "validation_loss_abs_error": abs(validation_loss - reported_loss),
        "validation_windows": int(centers.size),
        "channels": num_channels,
        "total_elements": num_elements,
        "gt_spikes_in_slice": int(unit_rows["spikes_in_slice"].sum()),
        "support_elements": support_count,
        "support_fraction": support_count / num_elements,
        "support_loss_mean": support_loss_mean,
        "matched_background_loss_mean": matched_background_mean,
        "meaningful_loss_drop": meaningful_drop,
        "zero_residual_loss_drop_upper": zero_residual_drop,
        "meaningful_drop_pct_total_loss": 100.0 * meaningful_drop / validation_loss,
        "meaningful_drop_pct_excess_above_minimum": (
            100.0 * meaningful_drop / (validation_loss - minimum_loss)
        ),
        "support_before_ms": args.support_before_ms,
        "support_after_ms": args.support_after_ms,
        "peak_frac": args.peak_frac,
        "max_channels": args.max_channels,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(out_path, index=False)
    unit_rows.to_csv(out_path.with_name(out_path.stem + "_units.csv"), index=False)
    out_path.with_suffix(".json").write_text(json.dumps(row, indent=2) + "\n")
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()