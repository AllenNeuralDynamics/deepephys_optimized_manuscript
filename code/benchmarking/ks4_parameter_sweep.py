#!/usr/bin/env python3
"""Generate controlled Kilosort4 parameter payloads for denoised-data sweeps."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

KS4_WRAPPER_COMMIT = "03d3522e2d4ba191b94c9d640c5b09f1299efc15"
CURRENT_PIPELINE_ID = "5a096db9-3fd7-4984-b5a3-f409b4c8b6ee"
CURRENT_TH_LEARNED = 8.0
FIRST_SWEEP = (9.0, 10.0)

# Exact code/params.json content at KS4_WRAPPER_COMMIT, plus the wrapper-level
# controls needed to preserve the settings used by the completed benchmark.
BASELINE_PARAMS = {
    "raise_if_fails": True,
    "skip_motion_correction": False,
    "min_drift_channels": 64,
    "clear_cache": False,
    "job_kwargs": {
        "chunk_duration": "1s",
        "progress_bar": False,
    },
    "sorter": {
        "batch_size": 60000,
        "nblocks": 5,
        "Th_universal": 9,
        "Th_learned": 8,
        "do_CAR": True,
        "invert_sign": False,
        "nt": 61,
        "shift": None,
        "scale": None,
        "artifact_threshold": None,
        "nskip": 25,
        "whitening_range": 32,
        "highpass_cutoff": 300,
        "binning_depth": 5,
        "sig_interp": 20,
        "drift_smoothing": [0.5, 0.5, 0.5],
        "nt0min": None,
        "dmin": None,
        "dminx": 32,
        "min_template_size": 10,
        "template_sizes": 5,
        "nearest_chans": 10,
        "nearest_templates": 100,
        "max_channel_distance": None,
        "templates_from_data": True,
        "n_templates": 6,
        "n_pcs": 6,
        "Th_single_ch": 6,
        "acg_threshold": 0.2,
        "ccg_threshold": 0.25,
        "cluster_downsampling": 20,
        "x_centers": None,
        "duplicate_spike_ms": 0.25,
        "save_preprocessed_copy": False,
        "torch_device": "auto",
        "bad_channels": None,
        "clear_cache": False,
        "save_extra_vars": False,
        "do_correction": True,
        "keep_good_only": False,
        "skip_kilosort_preprocessing": False,
        "use_binary_file": None,
        "delete_recording_dat": True,
    },
}


def build_params(th_learned: float) -> dict:
    """Return a full wrapper payload that changes only ``Th_learned``."""
    if th_learned <= 0:
        raise ValueError("Th_learned must be positive")
    params = copy.deepcopy(BASELINE_PARAMS)
    params["sorter"]["Th_learned"] = float(th_learned)
    return params


def changed_paths(candidate: dict) -> list[str]:
    """List leaf paths whose values differ from the frozen baseline."""
    changes: list[str] = []

    def compare(baseline, current, prefix: str) -> None:
        if isinstance(baseline, dict) and isinstance(current, dict):
            for key in sorted(set(baseline) | set(current)):
                path = f"{prefix}.{key}" if prefix else key
                if key not in baseline or key not in current:
                    changes.append(path)
                else:
                    compare(baseline[key], current[key], path)
        elif baseline != current:
            changes.append(prefix)

    compare(BASELINE_PARAMS, candidate, "")
    return changes


def compact_json(params: dict) -> str:
    """Serialize a payload for the wrapper's ``--params`` argument."""
    return json.dumps(params, sort_keys=True, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--th-learned",
        type=float,
        nargs="+",
        default=list(FIRST_SWEEP),
        help="learned-template thresholds to generate (default: 9 10)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="optional directory for one full JSON payload per threshold",
    )
    args = parser.parse_args()

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    for threshold in args.th_learned:
        params = build_params(threshold)
        changes = changed_paths(params)
        if changes != ["sorter.Th_learned"]:
            raise RuntimeError(f"candidate changed unexpected settings: {changes}")
        payload = compact_json(params)
        label = str(threshold).replace(".", "p")
        if args.output_dir:
            destination = args.output_dir / f"ks4_th_learned_{label}.json"
            destination.write_text(json.dumps(params, indent=2) + "\n")
            print(f"{threshold:g}\t{destination}\t{len(payload)} bytes")
        else:
            print(f"Th_learned={threshold:g}\tchanges={','.join(changes)}")
            print(payload)


if __name__ == "__main__":
    main()