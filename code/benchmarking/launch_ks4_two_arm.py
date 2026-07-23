#!/usr/bin/env python3
"""Launch an exact-ProbeC raw-vs-Full96 Kilosort4 benchmark.

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
CASE_MOUNT = "probec_recording1_3"
MODEL_SPECS = {
    "om0": {
        "asset_id": "a9bcbf5b-0e7c-49ad-a9d5-c36c77647cc2",
        "mount": "full96_om0_duration_outputs",
        "sha256": "f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506",
    },
    "om1": {
        "asset_id": "d7821e06-dbba-4060-a7bb-6eab2d8c2ba6",
        "mount": "full96_om1_duration_outputs",
        "sha256": "90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a",
    },
}

DISPATCH = "capsule_job_dispatch_hybrid_ecephys_1"
INFERENCE = "capsule_aind_ephys_deepinterpolation_inference_8"
PREPROCESS_RAW = "capsule_preprocess_ecephys_3"
PREPROCESS_DEEP = "capsule_preprocess_ecephys_10"
KS4_RAW = "capsule_spikesort_kilosort_4_ecephys_5"
KS4_DEEP = "capsule_spikesort_kilosort_4_ecephys_9"


def checkpoint_path(route: str) -> str:
    return f"../data/{MODEL_SPECS[route]['mount']}/ckpt_step_00210923.pt"


def build_full_request(route: str) -> RunParams:
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
                    "--checkpoint", checkpoint_path(route),
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


def build_model_smoke_request(route: str) -> RunParams:
    model = MODEL_SPECS[route]
    return RunParams(
        capsule_id=INFERENCE_CAPSULE_ID,
        data_assets=[
            DataAssetsRunParam(id=CASE_ASSET_ID, mount=CASE_MOUNT),
            DataAssetsRunParam(id=model["asset_id"], mount=model["mount"]),
        ],
        parameters=[
            "--checkpoint", checkpoint_path(route),
            "--device", "cuda",
            "--batch-size", "256",
            "--chunk-duration", "1s",
            "--norm-sample-seconds", "2",
            "--max-test-recordings", "1",
            "--test-duration-s", "2",
        ],
    )


def expected_smoke_assets(route: str) -> list[tuple[str, str]]:
    model = MODEL_SPECS[route]
    return [(CASE_ASSET_ID, CASE_MOUNT), (model["asset_id"], model["mount"])]


def require_succeeded_smoke(
    client: CodeOcean, computation_id: str, route: str
) -> None:
    computation = client.computations.get_computation(computation_id)
    if not str(computation.end_status).lower().endswith("succeeded"):
        raise RuntimeError(
            f"smoke computation {computation_id} is not succeeded: "
            f"state={computation.state}, end_status={computation.end_status}"
        )
    if not computation.has_results:
        raise RuntimeError(f"smoke computation {computation_id} has no results")
    actual = [(asset.id, asset.mount) for asset in computation.data_assets or []]
    if actual != expected_smoke_assets(route):
        raise RuntimeError(f"smoke computation used unexpected assets: {actual!r}")
    outputs = {
        item.path for item in client.computations.list_computation_results(computation_id).items
    }
    if not {"recording_denoised", "output"}.issubset(outputs):
        raise RuntimeError(f"smoke computation has unexpected outputs: {sorted(outputs)}")


def isolate_inference_model(client: CodeOcean, route: str, attach: bool) -> None:
    for model in MODEL_SPECS.values():
        client.capsules.detach_data_assets(
            INFERENCE_CAPSULE_ID, [model["asset_id"]]
        )
    if not attach:
        return
    model = MODEL_SPECS[route]
    attached = client.capsules.attach_data_assets(
        INFERENCE_CAPSULE_ID,
        [DataAssetAttachParams(id=model["asset_id"], mount=model["mount"])],
    )
    if not attached or not attached[0].ready:
        raise RuntimeError(f"model asset is not ready on inference capsule: {attached}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("model-smoke", "full"), default="model-smoke"
    )
    parser.add_argument("--route", choices=tuple(MODEL_SPECS), default="om1")
    parser.add_argument("--launch", action="store_true", help="submit to Code Ocean")
    parser.add_argument(
        "--validated-smoke",
        help="succeeded smoke computation ID; required to launch --mode full",
    )
    args = parser.parse_args()

    request = (
        build_model_smoke_request(args.route)
        if args.mode == "model-smoke"
        else build_full_request(args.route)
    )
    print(json.dumps(request.to_dict(), indent=2))
    print(f"checkpoint_sha256={MODEL_SPECS[args.route]['sha256']}")
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
        require_succeeded_smoke(client, args.validated_smoke, args.route)
        isolate_inference_model(client, args.route, attach=True)
    else:
        isolate_inference_model(client, args.route, attach=False)

    computation = (
        client.computations.run_capsule(request)
        if args.mode == "model-smoke"
        else client.computations.run_pipeline(request)
    )
    label = (
        f"Full96 {args.route} checkpoint 2s inference smoke"
        if args.mode == "model-smoke"
        else f"Full96 {args.route} ProbeC KS4 two-arm full"
    )
    client.computations.rename_computation(computation.id, label)
    created = client.computations.get_computation(computation.id)
    if args.mode == "model-smoke":
        actual = [(asset.id, asset.mount) for asset in created.data_assets or []]
        if actual != expected_smoke_assets(args.route):
            client.computations.delete_computation(created.id)
            raise RuntimeError(f"Code Ocean changed smoke mounts: {actual!r}")
    print(f"launched {created.id}: {label}")


if __name__ == "__main__":
    main()