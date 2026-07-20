#!/usr/bin/env python3
"""Run a scoring driver with inference modules pinned to INFERENCE_CODE."""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import runpy
import sys


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("usage: run_with_inference.py <driver.py> [driver args ...]")

    inference_code = Path(os.environ["INFERENCE_CODE"]).resolve()
    driver = Path(sys.argv.pop(1)).resolve()
    sys.argv[0] = str(driver)
    sys.path.insert(0, str(inference_code))

    modules = [
        importlib.import_module("di_ephys.inference"),
        importlib.import_module("tier1_surrogate"),
    ]
    for module in modules:
        module_path = Path(module.__file__).resolve()
        if not module_path.is_relative_to(inference_code):
            raise RuntimeError(
                f"{module.__name__} resolved outside INFERENCE_CODE: {module_path}"
            )
        print(f"[scoring] {module.__name__}={module_path}", flush=True)

    runpy.run_path(str(driver), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())