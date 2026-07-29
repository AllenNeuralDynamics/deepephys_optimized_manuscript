#!/usr/bin/env python3
"""Audit full target-decoy results against native default 9/8 baselines."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from codeocean import CodeOcean


REPO = Path(__file__).resolve().parents[2]
BASELINE = REPO / "results" / "benchmarking" / "ks4_native_baseline"
OUTPUT = REPO / "results" / "benchmarking" / "ks4_target_decoy"
EXPECTED_POLICY = {
    "target_fdr": 0.05,
    "minimum_Th_learned": 8.0,
    "duration_s": 1200.0,
    "requested_domain": "both",
}
DOMAIN_MAP = {
    "raw_native_fdr": "raw_native",
    "denoised_native_fdr": "denoised",
}


def download(client: CodeOcean, computation_id: str, path: str) -> bytes:
    urls = client.computations.get_result_file_urls(computation_id, path)
    response = requests.get(urls.download_url, timeout=120)
    response.raise_for_status()
    return response.content


def load_remote_csv(client: CodeOcean, computation_id: str, path: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(download(client, computation_id, path)))


def event_summary(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    final = scores.query("stage == 'duplicate_removal'")
    for (domain, status), group in final.groupby(["domain", "status"]):
        events = int(group["events"].sum())
        if events == 0:
            continue
        ordered = group.sort_values("peel")
        cumulative = ordered["events"].cumsum()
        rows.append(
            {
                "domain": domain,
                "status": status,
                "events": events,
                "mean_peel": float((group["peel"] * group["events"]).sum() / events),
                "median_peel": int(
                    ordered.loc[cumulative.ge(events * 0.5), "peel"].iloc[0]
                ),
                "q90_peel": int(
                    ordered.loc[cumulative.ge(events * 0.9), "peel"].iloc[0]
                ),
                "weighted_mean_score": float(
                    (group["score_mean"] * group["events"]).sum() / events
                ),
            }
        )
    return pd.DataFrame(rows)


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
            f"full result is unavailable: state={computation.state}, "
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

    adaptive_stages = load_remote_csv(
        client, args.computation_id, "target_decoy_stage_summary.csv"
    )
    adaptive_scores = load_remote_csv(
        client, args.computation_id, "target_decoy_score_summary.csv"
    )
    gate = load_remote_csv(
        client, args.computation_id, "target_decoy_gate_by_batch_peel.csv"
    )
    final_adaptive = adaptive_stages.query("stage == 'duplicate_removal'").copy()
    if set(final_adaptive["domain"]) != set(DOMAIN_MAP):
        raise ValueError(f"unexpected adaptive domains: {final_adaptive['domain'].tolist()}")
    final_adaptive["baseline_domain"] = final_adaptive["domain"].map(DOMAIN_MAP)

    baseline_stages = pd.read_csv(BASELINE / "native_baseline_stage_summary.csv")
    final_baseline = baseline_stages.query("stage == 'duplicate_removal'").copy()
    expected_baseline = set(DOMAIN_MAP.values())
    if set(final_baseline["domain"]) != expected_baseline:
        raise ValueError("native baseline domains differ from target-decoy domains")

    metrics = [
        "events_present",
        "clusters",
        "matched_gt_units",
        "tp",
        "fn",
        "fp_in_matched_clusters",
        "events_in_unmatched_clusters",
        "pooled_precision",
        "pooled_recall",
    ]
    comparison = final_baseline[["domain", *metrics]].merge(
        final_adaptive[["baseline_domain", *metrics]],
        left_on="domain",
        right_on="baseline_domain",
        suffixes=("_baseline", "_target_decoy"),
        validate="one_to_one",
    ).drop(columns="baseline_domain")
    for metric in metrics:
        comparison[f"{metric}_change"] = (
            comparison[f"{metric}_target_decoy"]
            - comparison[f"{metric}_baseline"]
        )

    accepted = gate.loc[gate["accepted_events"].gt(0)].copy()
    if accepted.empty:
        raise ValueError("target-decoy run accepted no events")
    required_counts = {"selected_target_count", "selected_decoy_count"}
    if not required_counts.issubset(gate.columns):
        raise ValueError(f"gate table is missing exact counts: {sorted(required_counts)}")
    selected_targets = accepted["selected_target_count"].astype(np.int64)
    selected_decoys = accepted["selected_decoy_count"].astype(np.int64)
    if not selected_targets.eq(accepted["accepted_events"].astype(np.int64)).all():
        raise ValueError("selected target count differs from accepted events")
    exact_fdr = (1 + selected_decoys) / selected_targets
    if exact_fdr.gt(EXPECTED_POLICY["target_fdr"]).any():
        raise ValueError("accepted peel exceeds target FDR")
    gate["exact_fdr"] = np.nan
    gate.loc[accepted.index, "exact_fdr"] = exact_fdr
    if gate["negative_count_above_floor"].sum() == 0:
        raise ValueError("target-decoy run has no negative null support")
    gate_summary = (
        gate.groupby("domain")
        .agg(
            gate_rows=("peel", "size"),
            accepted_gate_rows=("accepted_events", lambda values: int((values > 0).sum())),
            accepted_events=("accepted_events", "sum"),
            median_selected_threshold=(
                "selected_threshold",
                lambda values: float(np.nanmedian(values.replace(np.inf, np.nan))),
            ),
            max_selected_threshold=(
                "selected_threshold",
                lambda values: float(np.nanmax(values.replace(np.inf, np.nan))),
            ),
            median_sign_balance=(
                "negative_to_positive_floor_ratio",
                lambda values: float(np.nanmedian(values.replace(np.inf, np.nan))),
            ),
            max_exact_fdr=("exact_fdr", "max"),
        )
        .reset_index()
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(OUTPUT / "target_decoy_vs_native_baseline.csv", index=False)
    event_summary(adaptive_scores).to_csv(
        OUTPUT / "target_decoy_event_summary.csv", index=False
    )
    gate_summary.to_csv(OUTPUT / "target_decoy_gate_summary.csv", index=False)
    adaptive_stages.to_csv(OUTPUT / "target_decoy_stage_summary.csv", index=False)
    adaptive_scores.to_csv(OUTPUT / "target_decoy_score_summary.csv", index=False)
    gate.to_csv(OUTPUT / "target_decoy_gate_by_batch_peel.csv", index=False)
    (OUTPUT / "target_decoy_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(comparison.to_string(index=False))
    print(gate_summary.to_string(index=False))


if __name__ == "__main__":
    main()
