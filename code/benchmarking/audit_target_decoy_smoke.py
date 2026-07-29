#!/usr/bin/env python3
"""Audit a target-decoy Kilosort smoke computation."""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
import pandas as pd
import requests
from codeocean import CodeOcean


EXPECTED_POLICY = {
    "target_fdr": 0.05,
    "minimum_Th_learned": 8.0,
    "duration_s": 60.0,
    "requested_domain": "raw",
}


def download(client: CodeOcean, computation_id: str, path: str) -> bytes:
    urls = client.computations.get_result_file_urls(computation_id, path)
    response = requests.get(urls.download_url, timeout=120)
    response.raise_for_status()
    return response.content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("computation_id")
    args = parser.parse_args()
    client = CodeOcean(
        domain=os.environ["CODEOCEAN_DOMAIN"],
        token=os.environ["CODEOCEAN_TOKEN"],
    )
    computation = client.computations.get_computation(args.computation_id)
    if computation.exit_code != 0 or not computation.has_results:
        raise RuntimeError(
            f"smoke result is unavailable: state={computation.state}, "
            f"exit={computation.exit_code}, results={computation.has_results}"
        )

    manifest = json.loads(
        download(client, args.computation_id, "target_decoy_manifest.json")
    )
    for key, expected in EXPECTED_POLICY.items():
        if manifest[key] != expected:
            raise ValueError(f"manifest {key} differs: {manifest[key]} != {expected}")
    if manifest["uses_ground_truth_for_decisions"] is not False:
        raise ValueError("target-decoy decisions unexpectedly use ground truth")

    gate = pd.read_csv(
        io.BytesIO(
            download(
                client,
                args.computation_id,
                "target_decoy_gate_by_batch_peel.csv",
            )
        )
    )
    stages = pd.read_csv(
        io.BytesIO(
            download(client, args.computation_id, "target_decoy_stage_summary.csv")
        )
    )
    required_gate = {
        "domain",
        "batch",
        "peel",
        "selected_threshold",
        "target_fdr",
        "estimated_fdr",
        "positive_count_above_floor",
        "negative_count_above_floor",
        "negative_to_positive_floor_ratio",
        "accepted_events",
    }
    missing = required_gate - set(gate.columns)
    if missing:
        raise ValueError(f"gate table is missing columns: {sorted(missing)}")
    if set(gate["domain"]) != {"raw_native_fdr"}:
        raise ValueError(f"unexpected smoke domains: {sorted(gate['domain'].unique())}")
    if not gate["target_fdr"].eq(EXPECTED_POLICY["target_fdr"]).all():
        raise ValueError("target FDR changed within the smoke run")
    accepted = gate.loc[gate["accepted_events"].gt(0)]
    if accepted.empty:
        raise ValueError("target-decoy smoke accepted no events")
    if not np.isfinite(accepted["selected_threshold"]).all():
        raise ValueError("accepted peel has a nonfinite threshold")
    if {"selected_target_count", "selected_decoy_count"}.issubset(gate.columns):
        selected_targets = accepted["selected_target_count"].astype(np.int64)
        selected_decoys = accepted["selected_decoy_count"].astype(np.int64)
    else:
        # The first smoke predates explicit count columns. Reconstruct the exact
        # integer decoy count from the float32 estimate and accepted target count.
        selected_targets = accepted["accepted_events"].astype(np.int64)
        selected_decoys = (
            accepted["estimated_fdr"] * selected_targets - 1
        ).round().astype(np.int64)
    if not selected_targets.eq(accepted["accepted_events"].astype(np.int64)).all():
        raise ValueError("selected target count differs from accepted events")
    exact_fdr = (1 + selected_decoys) / selected_targets
    if exact_fdr.gt(EXPECTED_POLICY["target_fdr"]).any():
        raise ValueError("accepted peel exceeds target FDR")
    if gate["positive_count_above_floor"].sum() == 0:
        raise ValueError("smoke has no positive target support")
    if gate["negative_count_above_floor"].sum() == 0:
        raise ValueError("smoke has no negative decoy support")
    if stages.empty or not {"detection_template", "duplicate_removal"}.issubset(
        stages["stage"]
    ):
        raise ValueError("lineage stage table is incomplete")

    final = stages.loc[stages["stage"].eq("duplicate_removal")].iloc[0]
    summary = {
        "computation_id": computation.id,
        "runtime_s": computation.run_time,
        "gate_rows": len(gate),
        "accepted_gate_rows": len(accepted),
        "median_selected_threshold": float(accepted["selected_threshold"].median()),
        "max_selected_threshold": float(accepted["selected_threshold"].max()),
        "max_exact_fdr": float(exact_fdr.max()),
        "median_sign_balance": float(
            gate["negative_to_positive_floor_ratio"].replace([np.inf], np.nan).median()
        ),
        "events": int(final["events_present"]),
        "matched_gt_units": int(final["matched_gt_units"]),
        "tp": int(final["tp"]),
        "fn": int(final["fn"]),
        "fp": int(final["fp_in_matched_clusters"]),
        "unmatched_events": int(final["events_in_unmatched_clusters"]),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
