#!/usr/bin/env python3
"""Launch a tier of in-band training runs on Code Ocean from results/runs.csv.

For each run whose ``tier`` matches, builds the champion-base parameter set + the run's
``override`` + ``seed`` and POSTs a computation to the training capsule, then writes the
returned ``co_id`` and ``state=running`` back into runs.csv. Runs that already carry a
``co_id`` are skipped (idempotent).

Usage:
    python launch_tier.py <tier> [tier ...]        # e.g. 1
    python launch_tier.py 1 --dry-run              # print parameter sets, POST nothing

Reads CODEOCEAN_DOMAIN / CODEOCEAN_TOKEN from the environment
(``set -a; source ~/.codeocean.env; set +a``). NEVER prints the token.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "results" / "runs.csv"

CAPSULE = "cb03dc8b-be21-42fe-aec0-e60607ff1bfe"
ASSET = {"id": "384bf77c-f37b-4ab1-a008-03f10a0c49c9", "mount": "hybrid_np1"}
REC = ("hybrid_np1/ecephys_681532_2023-10-18_13-01-15/"
       "experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3/recording.zarr")

# Champion base + short-run recipe (includes the champion loss/omission/bs_frames defaults).
BASE = {
    "train_recording_path": REC,
    "slice_start_s": "60", "slice_dur_s": "150",
    "val_slice_start_s": "0", "val_slice_dur_s": "60",
    "checkpoint_steps": "12", "train_chunks": "4",
    "base_channels": "32", "depth": "3", "bs_frames": "3",
    "bs_channels": "64", "bs_depth": "5", "fuse_channels": "64",
    "loss": "charbonnier", "omission": "1",
    "geometry": "fold", "blind_spot": "1",
    "batch_size": "64", "traces_dtype": "float16",
    "lr": "0.001", "lr_scheduler": "cosine",
}


def build_params(override: str, seed: str) -> dict:
    p = dict(BASE)
    for tok in (override or "").split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            p[k] = v
    if p.get("omission") == "0":
        p["bs_frames"] = "1"   # omission=0 uses a 1-frame temporal blind spot
    p["seed"] = str(seed)
    return p


def post_computation(domain: str, token: str, params: dict) -> dict:
    body = {
        "capsule_id": CAPSULE,
        "parameters": [f"{k}={v}" for k, v in params.items()],
        "data_assets": [ASSET],
    }
    req = urllib.request.Request(
        f"{domain}/api/v1/computations",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Basic " + base64.b64encode(f"{token}:".encode()).decode()},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tiers", nargs="+", help="tier value(s) from runs.csv, e.g. 1")
    ap.add_argument("--dry-run", action="store_true", help="print parameter sets, POST nothing")
    args = ap.parse_args()
    tiers = set(args.tiers)

    domain = os.environ["CODEOCEAN_DOMAIN"]
    token = os.environ.get("CODEOCEAN_TOKEN", "")
    rows = list(csv.DictReader(open(RUNS)))

    launched: dict[str, str] = {}
    for row in rows:
        if row["tier"] not in tiers:
            continue
        if row.get("co_id"):
            print(f"skip {row['label']} (already launched: {row['co_id']})")
            continue
        params = build_params(row["override"], row["seed"])
        if args.dry_run:
            print(f"{row['label']:22s} loss={params['loss']:11s} omission={params['omission']} "
                f"batch={params['batch_size']} lr={params['lr']} "
                f"warmup={params.get('warmup_frac', '0')} "
                f"accum={params.get('grad_accum_mode', 'none')}:"
                f"{params.get('grad_accum_max', '1')} "
                f"diag={params.get('grad_noise_diag_steps', '0')} "
                f"importance={params.get('importance_pool_mult', '1')}x "
                f"seed={params['seed']}")
            continue
        try:
            resp = post_computation(domain, token, params)
        except Exception as e:  # keep going so one failure can't orphan the batch
            print(f"FAILED   {row['label']}: {e}")
            continue
        cid = resp.get("id", "")
        launched[row["label"]] = cid
        print(f"launched {row['label']} -> {cid}")

    if launched:
        for row in rows:
            if row["label"] in launched:
                row["co_id"] = launched[row["label"]]
                row["state"] = "running"
        with open(RUNS, "w", newline="") as f:
            fieldnames = [k for k in rows[0].keys() if k is not None]
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    print(f"\n{'DRY-RUN, nothing launched' if args.dry_run else f'launched {len(launched)} run(s); runs.csv updated'}")


if __name__ == "__main__":
    main()
