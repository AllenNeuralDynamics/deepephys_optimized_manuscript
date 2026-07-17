#!/usr/bin/env python3
"""Download result files from a Code Ocean computation by filename glob.

Usage:
    python co_dl.py <computation_id> <out_dir> [glob ...]

Downloads every result file whose name matches any glob. By default this includes
checkpoints plus optimization telemetry needed for exact convergence plots.
Reads ``CODEOCEAN_DOMAIN`` and ``CODEOCEAN_TOKEN`` from the environment, e.g.::

    set -a; source ~/.codeocean.env; set +a
    python co_dl.py ccf82c60-... /tmp/ib_om0_scale "best_model.pt" "ckpt_step_*.pt"

Requires: ``pip install codeocean`` (the official Code Ocean SDK). The plain
REST ``/results`` endpoint returns streaming/NDJSON and 404s for file listing,
so the SDK is used instead.
"""
import fnmatch
import os
import sys
import urllib.request

from codeocean import CodeOcean


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cid = sys.argv[1]
    out_dir = sys.argv[2]
    patterns = sys.argv[3:] or [
        "*.pt", "checkpoint_manifest.json", "gradient_diagnostics.jsonl",
        "losses.jsonl", "metrics.json",
    ]

    client = CodeOcean(
        domain=os.environ["CODEOCEAN_DOMAIN"],
        token=os.environ["CODEOCEAN_TOKEN"],
    )
    results = client.computations.list_computation_results(cid)
    os.makedirs(out_dir, exist_ok=True)

    n = 0
    for item in results.items:
        name = getattr(item, "name", None) or os.path.basename(item.path)
        if str(getattr(item, "type", "file")).lower().endswith("folder"):
            continue
        if not any(fnmatch.fnmatch(name, p) for p in patterns):
            continue
        url = client.computations.get_result_file_urls(cid, item.path).download_url
        out_path = os.path.join(out_dir, name)
        print(f"  {name} ({getattr(item, 'size', '?')} B)")
        urllib.request.urlretrieve(url, out_path)
        n += 1
    print(f"downloaded {n} file(s) to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
