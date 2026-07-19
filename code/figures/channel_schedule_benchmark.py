#!/usr/bin/env python3
"""Summarize synthetic GPU throughput for exploratory temporal channel schedules."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "results" / "tables"
ORDER = (
    "width64_2x",
    "full_2x",
    "cap512",
    "cap384",
    "growth1.5",
    "growth_sqrt2",
    "constant",
)


def main() -> None:
    raw = pd.read_csv(TABLES / "channel_schedule_gpu_benchmark.csv")
    if len(raw) != 21 or set(raw["status"]) != {"ok"}:
        raise ValueError("expected 21 successful schedule/batch benchmark rows")
    frame = raw.loc[raw["batch_size"] == 256].set_index("variant").loc[list(ORDER)].copy()
    full = frame.loc["full_2x"]
    width64 = frame.loc["width64_2x"]
    frame["parameter_reduction_vs_full96"] = 1.0 - frame["parameters"] / full["parameters"]
    frame["throughput_vs_full96"] = frame["windows_per_second"] / full["windows_per_second"]
    frame["throughput_vs_width64"] = frame["windows_per_second"] / width64["windows_per_second"]
    frame["memory_reduction_vs_full96"] = (
        1.0 - frame["peak_allocated_gib"] / full["peak_allocated_gib"]
    )
    columns = [
        "schedule",
        "parameters",
        "parameter_reduction_vs_full96",
        "step_seconds",
        "windows_per_second",
        "throughput_vs_full96",
        "throughput_vs_width64",
        "peak_allocated_gib",
        "memory_reduction_vs_full96",
    ]
    summary = frame.reset_index()[["variant", *columns]]
    summary.to_csv(TABLES / "channel_schedule_gpu_summary.csv", index=False)
    try:
        markdown = summary.to_markdown(index=False, floatfmt=".4g")
    except ImportError:
        markdown = summary.to_csv(index=False)
    (TABLES / "channel_schedule_gpu_summary.md").write_text(markdown.rstrip() + "\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
