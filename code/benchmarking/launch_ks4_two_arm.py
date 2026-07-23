#!/usr/bin/env python3
"""Launch the exact ProbeC raw-vs-Full96-om1 Kilosort4 benchmark.

The command is a dry run unless ``--launch`` is supplied. Full-recording launch
resumes a proven exact-case cache and requires a succeeded model smoke.
"""
from __future__ import annotations

import argparse
import json
import os

from codeocean import CodeOcean
from codeocean.computation import (
    DataAssetsRunParam,
    PipelineProcessParams,
    RunParams,
)
from codeocean.data_asset import DataAssetAttachParams

PIPELINE_ID = "5a096db9-3fd7-4984-b5a3-f409b4c8b6ee"
INFERENCE_CAPSULE_ID = "fa034446-63c2-40f3-8a39-a95ea2b4f5fd"
EXACT_CASE_CACHE_ID = "6962e3fb-8ff9-40c1-8d7f-e0cb058cb036"
CASE_ASSET_ID = "8046af5a-6e53-420e-9e28-52bd54514342"
MODEL_ASSET_ID = "d7821e06-dbba-4060-a7bb-6eab2d8c2ba6"
CASE_MOUNT = "probec_recording1_3"
MODEL_MOUNT = "full96_om1_duration_outputs"
CHECKPOINT = f"../data/{MODEL_MOUNT}/ckpt_step_00210923.pt"
CHECKPOINT_SHA256 = "90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a"

DISPATCH = "capsule_job_dispatch_hybrid_ecephys_1"
INFERENCE = "capsule_aind_ephys_deepinterpolation_inference_8"
PREPROCESS_RAW = "capsule_preprocess_ecephys_3"
PREPROCESS_DEEP = "capsule_preprocess_ecephys_10"
KS4_RAW = "capsule_spikesort_kilosort_4_ecephys_5"
KS4_DEEP = "capsule_spikesort_kilosort_4_ecephys_9"


def build_full_request() -> RunParams:
    preprocess = [
        "cmr", "highpass", "true", "true", "0.5", "compute",
        "dredge_fast", "2", "", "", "120", "-1",
    ]
    ks4 = ["true", "false", "64", "false"]
    return RunParams(
        pipeline_id=PIPELINE_ID,
        resume_run_id=EXACT_CASE_CACHE_ID,
        processes=[
            PipelineProcessParams(
                name=DISPATCH,
                parameters=[
                    "false", "30", "1",
                    "s3://aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/",
                ],
            ),
            PipelineProcessParams(
                name=INFERENCE,
                parameters=[
                    "--checkpoint", CHECKPOINT,
                    "--device", "cuda",
                    "--batch-size", "256",
                    "--chunk-duration", "1s",
                    "--norm-sample-seconds", "60",
                ],
            ),
            PipelineProcessParams(name=PREPROCESS_RAW, parameters=preprocess),
            PipelineProcessParams(name=PREPROCESS_DEEP, parameters=preprocess),
            PipelineProcessParams(name=KS4_RAW, parameters=ks4),
            PipelineProcessParams(name=KS4_DEEP, parameters=ks4),
        ],
    )


def build_model_smoke_request() -> RunParams:
    return RunParams(
        capsule_id=INFERENCE_CAPSULE_ID,
        data_assets=[
            DataAssetsRunParam(id=CASE_ASSET_ID, mount=CASE_MOUNT),
            DataAssetsRunParam(id=MODEL_ASSET_ID, mount=MODEL_MOUNT),
        ],
        parameters=[
            "--checkpoint", CHECKPOINT,
            "--device", "cuda",
            "--batch-size", "256",
            "--chunk-duration", "1s",
            "--norm-sample-seconds", "2",
            "--max-test-recordings", "1",
            "--test-duration-s", "2",
        ],
    )


def expected_smoke_assets() -> list[tuple[str, str]]:
    return [(CASE_ASSET_ID, CASE_MOUNT), (MODEL_ASSET_ID, MODEL_MOUNT)]


def require_succeeded_smoke(client: CodeOcean, computation_id: str) -> None:
    computation = client.computations.get_computation(computation_id)
    if not str(computation.end_status).lower().endswith("succeeded"):
        raise RuntimeError(
            f"smoke computation {computation_id} is not succeeded: "
            f"state={computation.state}, end_status={computation.end_status}"
        )
    if not computation.has_results:
        raise RuntimeError(f"smoke computation {computation_id} has no results")
    actual = [(asset.id, asset.mount) for asset in computation.data_assets or []]
    if actual != expected_smoke_assets():
        raise RuntimeError(f"smoke computation used unexpected assets: {actual!r}")
    outputs = {
        item.path for item in client.computations.list_computation_results(computation_id).items
    }
    if not {"recording_denoised", "output"}.issubset(outputs):
        raise RuntimeError(f"smoke computation has unexpected outputs: {sorted(outputs)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("model-smoke", "full"), default="model-smoke"
    )
    parser.add_argument("--launch", action="store_true", help="submit to Code Ocean")
    parser.add_argument(
        "--validated-smoke",
        help="succeeded smoke computation ID; required to launch --mode full",
    )
    args = parser.parse_args()

    request = build_model_smoke_request() if args.mode == "model-smoke" else build_full_request()
    print(json.dumps(request.to_dict(), indent=2))
    print(f"checkpoint_sha256={CHECKPOINT_SHA256}")
    if not args.launch:
        print("DRY RUN: no computation launched")
        return

    client = CodeOcean(
        domain=os.environ["CODEOCEAN_DOMAIN"],
        token=os.environ["CODEOCEAN_TOKEN"],
    )
    if args.mode == "full":
        if not args.validated_smoke:
            parser.error("--validated-smoke is required to launch --mode full")
        require_succeeded_smoke(client, args.validated_smoke)
        attached = client.capsules.attach_data_assets(
            INFERENCE_CAPSULE_ID,
            [DataAssetAttachParams(id=MODEL_ASSET_ID, mount=MODEL_MOUNT)],
        )
        if not attached or not attached[0].ready:
            raise RuntimeError(f"model asset is not ready on inference capsule: {attached}")

    computation = (
        client.computations.run_capsule(request)
        if args.mode == "model-smoke"
        else client.computations.run_pipeline(request)
    )
    label = (
        "Full96 om1 checkpoint 2s inference smoke"
        if args.mode == "model-smoke"
        else "Full96 om1 ProbeC KS4 two-arm full"
    )
    client.computations.rename_computation(computation.id, label)
    created = client.computations.get_computation(computation.id)
    if args.mode == "model-smoke":
        actual = [(asset.id, asset.mount) for asset in created.data_assets or []]
        if actual != expected_smoke_assets():
            client.computations.delete_computation(created.id)
            raise RuntimeError(f"Code Ocean changed smoke mounts: {actual!r}")
    print(f"launched {created.id}: {label}")


if __name__ == "__main__":
    main()