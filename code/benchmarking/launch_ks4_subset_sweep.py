#!/usr/bin/env python3
"""Capture and launch the exact-ProbeC 20-minute Kilosort threshold sweep."""
from __future__ import annotations

import argparse
import os

from codeocean import CodeOcean
from codeocean.computation import DataAssetsRunParam, RunParams
from codeocean.data_asset import (
    ComputationSource,
    DataAssetParams,
    DataAssetSearchParams,
    Source,
)


INFERENCE_COMPUTATION_ID = "6add9fa7-e1ff-435d-b9d9-52a3e360901f"
INFERENCE_RESULT_PATH = "recording_denoised"
ASSET_NAME = "Full96 om1 ProbeC recording1_3 first 1200s"
ASSET_MOUNT = "full96_om1_probec_1200s"
EXACT_CASE_ASSET_ID = "8046af5a-6e53-420e-9e28-52bd54514342"
EXACT_CASE_MOUNT = "probec_recording1_3"
KILOSORT_CAPSULE_ID = "eb0a6d2f-2418-4a0a-9765-beaa973745db"
KILOSORT_CALIBRATION_COMMIT = "0a6ffac"


def client() -> CodeOcean:
    return CodeOcean(
        domain=os.environ["CODEOCEAN_DOMAIN"],
        token=os.environ["CODEOCEAN_TOKEN"],
    )


def require_inference_result(co: CodeOcean) -> None:
    computation = co.computations.get_computation(INFERENCE_COMPUTATION_ID)
    if computation.exit_code != 0 or not computation.has_results:
        raise RuntimeError(
            "20-minute inference is not ready: "
            f"state={computation.state}, exit={computation.exit_code}, "
            f"has_results={computation.has_results}"
        )
    paths = {
        item.path
        for item in co.computations.list_computation_results(
            INFERENCE_COMPUTATION_ID
        ).items
    }
    if INFERENCE_RESULT_PATH not in paths:
        raise RuntimeError(f"missing inference result: {INFERENCE_RESULT_PATH}")


def matching_assets(co: CodeOcean) -> list:
    response = co.data_assets.search_data_assets(
        DataAssetSearchParams(query=ASSET_NAME, ownership="created", limit=100)
    )
    return [asset for asset in response.results if asset.name == ASSET_NAME]


def create_asset(co: CodeOcean):
    require_inference_result(co)
    matches = matching_assets(co)
    if matches:
        raise RuntimeError(
            f"refusing duplicate asset creation; existing IDs: {[a.id for a in matches]}"
        )
    return co.data_assets.create_data_asset(
        DataAssetParams(
            name=ASSET_NAME,
            description=(
                "Full96 omission1 denoising of the first 1200 seconds of the exact "
                "681532 ProbeC recording1_3 hybrid benchmark case."
            ),
            tags=["deepinterpolation", "kilosort4", "calibration", "hybrid"],
            mount=ASSET_MOUNT,
            source=Source(
                computation=ComputationSource(
                    id=INFERENCE_COMPUTATION_ID,
                    path=INFERENCE_RESULT_PATH,
                )
            ),
        )
    )


def require_ready_asset(co: CodeOcean, asset_id: str):
    asset = co.data_assets.get_data_asset(asset_id)
    if asset.name != ASSET_NAME:
        raise RuntimeError(f"unexpected asset name: {asset.name}")
    state = str(asset.state).lower()
    if not state.endswith("ready"):
        raise RuntimeError(f"asset is not ready: id={asset.id}, state={asset.state}")
    return asset


def launch_sweep(co: CodeOcean, asset_id: str):
    require_ready_asset(co, asset_id)
    request = RunParams(
        capsule_id=KILOSORT_CAPSULE_ID,
        data_assets=[
            DataAssetsRunParam(id=asset_id, mount=ASSET_MOUNT),
            DataAssetsRunParam(id=EXACT_CASE_ASSET_ID, mount=EXACT_CASE_MOUNT),
        ],
    )
    computation = co.computations.run_capsule(request)
    co.computations.rename_computation(
        computation.id,
        "Full96 om1 ProbeC 1200s Kilosort Th_learned 8-9-10",
    )
    return co.computations.get_computation(computation.id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("status", "create-asset", "launch")
    )
    parser.add_argument("--asset-id", help="ready 20-minute inference asset")
    args = parser.parse_args()
    co = client()

    if args.action == "status":
        computation = co.computations.get_computation(INFERENCE_COMPUTATION_ID)
        print(
            f"inference={computation.id} state={computation.state} "
            f"exit={computation.exit_code} results={computation.has_results}"
        )
        for asset in matching_assets(co):
            print(f"asset={asset.id} state={asset.state} name={asset.name}")
        return

    if args.action == "create-asset":
        asset = create_asset(co)
        print(f"created asset={asset.id} state={asset.state}")
        return

    if not args.asset_id:
        parser.error("--asset-id is required for launch")
    computation = launch_sweep(co, args.asset_id)
    print(
        f"launched computation={computation.id} state={computation.state} "
        f"capsule_commit={KILOSORT_CALIBRATION_COMMIT}"
    )


if __name__ == "__main__":
    main()