#!/usr/bin/env python3
"""Copy a run's checkpoints into the local (git-ignored) model store, with a manifest.

The store lives at ``<repo>/models/<label>/`` and is **not** committed (see .gitignore):
the manuscript repo tracks scores/tables, not weights. Each run folder receives the
run's ``*.pt`` checkpoints plus a ``manifest.json`` recording the config, the Code Ocean
computation id, and a per-file size + sha256 so the weights are reusable and trackable.

Usage:
    python store_model.py <label> <src_ckpt_dir>
        <label>         run label present in results/runs.csv, e.g. ib_om0_scale
        <src_ckpt_dir>  directory containing the run's *.pt files (e.g. /tmp/ib_om0_scale)
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STORE = REPO / "models"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def step_of(name: str) -> int | None:
    if name.startswith("ckpt_step_"):
        s = name[len("ckpt_step_"):].split(".")[0]
        return int(s) if s.isdigit() else None
    return None


def run_meta(label: str) -> dict:
    runs = REPO / "results" / "runs.csv"
    if runs.exists():
        for row in csv.DictReader(open(runs)):
            if row.get("label") == label:
                return row
    return {"label": label}


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    label, src = sys.argv[1], Path(sys.argv[2])
    dst = STORE / label
    dst.mkdir(parents=True, exist_ok=True)
    meta = run_meta(label)

    ckpts = []
    for pt in sorted(src.glob("*.pt")):
        target = dst / pt.name
        if not target.exists() or target.stat().st_size != pt.stat().st_size:
            shutil.copy2(pt, target)
        ckpts.append({
            "file": pt.name,
            "step": step_of(pt.name),
            "bytes": target.stat().st_size,
            "sha256": sha256(target),
        })
    if not ckpts:
        print(f"no *.pt found in {src}")
        return 1

    manifest = {
        "label": label,
        "tier": meta.get("tier"),
        "config": meta.get("config"),
        "loss": meta.get("loss"),
        "override": meta.get("override"),
        "co_id": meta.get("co_id"),
        "n_checkpoints": len(ckpts),
        "stored_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checkpoints": sorted(ckpts, key=lambda c: (c["step"] is None, c["step"] or 0)),
    }
    (dst / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"stored {len(ckpts)} checkpoint(s) -> {dst}")
    print(f"  config={manifest['config']} loss={manifest['loss']} co_id={manifest['co_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
