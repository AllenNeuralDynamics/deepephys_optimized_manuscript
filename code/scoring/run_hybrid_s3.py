#!/usr/bin/env python3
"""Score one checkpoint on the frozen S3-hosted hybrid benchmark.

This is the repository copy of the driver invoked by ``run_ckpt.sbatch``. The
metric implementation is in ``detection_metrics.py``; model construction comes
from the inference checkout pinned by ``run_with_inference.py``.
"""
from __future__ import annotations

import argparse
import time

import spikeinterface as si

from detection_metrics import compute_surrogate


def summarize(frame) -> str:
    if frame.empty:
        return "no units scored"
    columns = [
        "snr_raw",
        "snr_deep",
        "dprime_raw",
        "dprime_deep",
        "dprime_deep_fixed",
        "auc_raw",
        "auc_deep",
    ]
    means = frame[columns].mean()
    return (
        f"units={len(frame)}\n"
        f"  SNR       raw {means.snr_raw:.3f} -> deep {means.snr_deep:.3f}\n"
        f"  d' self   raw {means.dprime_raw:.3f} -> deep {means.dprime_deep:.3f}\n"
        f"  d' fixed  raw {means.dprime_raw:.3f} -> deep {means.dprime_deep_fixed:.3f}\n"
        f"  AUC self  raw {means.auc_raw:.3f} -> deep {means.auc_deep:.3f}\n"
        f"  units with d' improved: "
        f"{int((frame.dprime_deep > frame.dprime_raw).sum())}/{len(frame)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rec-url", required=True)
    parser.add_argument("--gt-url", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--n-spikes", type=int, default=100)
    parser.add_argument("--n-bg", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="scores.csv")
    args = parser.parse_args()

    start = time.time()
    import torch

    print(
        f"[run] torch {torch.__version__} cuda={torch.cuda.is_available()} "
        f"{torch.cuda.get_device_name(0) if torch.cuda.is_available() else ''}",
        flush=True,
    )
    recording = si.read_zarr(args.rec_url, storage_options={"anon": True})
    sorting = si.read_zarr(args.gt_url, storage_options={"anon": True})
    print(
        f"[run] recording={recording.get_num_channels()}ch "
        f"{recording.get_num_samples(0) / recording.get_sampling_frequency():.0f}s "
        f"GT={len(sorting.unit_ids)} units",
        flush=True,
    )

    from di_ephys.inference import deepinterpolate

    denoised = deepinterpolate(
        recording,
        args.checkpoint,
        device=args.device,
        batch_size=args.batch_size,
    )
    frame, _ = compute_surrogate(
        recording,
        denoised,
        sorting,
        n_spikes=args.n_spikes,
        n_background=args.n_bg,
        seed=args.seed,
    )
    frame.to_csv(args.out, index=False)
    print("\n" + frame.round(3).to_string())
    print("\n" + summarize(frame))
    print(f"\n[run] TOTAL {time.time() - start:.0f}s -> {args.out}", flush=True)


if __name__ == "__main__":
    main()