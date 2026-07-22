#!/usr/bin/env python3
"""Validate paired d-prime and waveform CSVs for completed trajectories."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

DPRIME_COLUMNS = {"unit_id", "dprime_raw", "dprime_deep", "dprime_deep_fixed", "ddprime"}
DIAG_COLUMNS = {"unit_id", "amp_ratio", "fwhm_ratio", "temporal_cos", "spatial_cos"}


def validate_csv(path: Path, required: set[str], expected_rows: int) -> set[str]:
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        rows = list(reader)
    if len(rows) != expected_rows:
        raise ValueError(f"{path}: expected {expected_rows} rows, found {len(rows)}")
    unit_ids = {row["unit_id"] for row in rows}
    if len(unit_ids) != expected_rows:
        raise ValueError(f"{path}: expected {expected_rows} unique unit IDs, found {len(unit_ids)}")
    for row in rows:
        for column in required.difference({"unit_id"}):
            if not math.isfinite(float(row[column])):
                raise ValueError(f"{path}: non-finite {column} for unit {row['unit_id']}")
    return unit_ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score_dir", type=Path)
    parser.add_argument("labels", nargs="+")
    parser.add_argument("--states", type=int, default=12)
    parser.add_argument("--units", type=int, default=10)
    args = parser.parse_args()

    for label in args.labels:
        dprime = sorted(args.score_dir.glob(f"{label}_*_dprime.csv"))
        diag = sorted(args.score_dir.glob(f"{label}_*_diag.csv"))
        if len(dprime) != args.states or len(diag) != args.states:
            raise ValueError(
                f"{label}: expected {args.states} paired states, "
                f"found {len(dprime)} d-prime and {len(diag)} diagnostic CSVs"
            )
        prefix = f"{label}_"
        dprime_suffix = "_dprime.csv"
        diag_suffix = "_diag.csv"
        dprime_tags = {path.name[len(prefix):-len(dprime_suffix)] for path in dprime}
        diag_tags = {path.name[len(prefix):-len(diag_suffix)] for path in diag}
        if dprime_tags != diag_tags or "best" not in dprime_tags:
            raise ValueError(f"{label}: unpaired state tags: d-prime={sorted(dprime_tags)}, "
                             f"diagnostic={sorted(diag_tags)}")
        for tag in sorted(dprime_tags):
            dprime_units = validate_csv(
                args.score_dir / f"{label}_{tag}_dprime.csv", DPRIME_COLUMNS, args.units
            )
            diag_units = validate_csv(
                args.score_dir / f"{label}_{tag}_diag.csv", DIAG_COLUMNS, args.units
            )
            if dprime_units != diag_units:
                raise ValueError(f"{label} {tag}: d-prime and diagnostic unit IDs differ")
        print(f"{label}: validated {args.states} paired states x {args.units} units")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
