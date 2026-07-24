# Kilosort4 benchmark launch

`launch_ks4_two_arm.py` submits the existing Code Ocean no-generation pipeline
with two arms on the manuscript's exact frozen hybrid case:

1. raw hybrid AP recording -> high-pass + CMR -> Kilosort4;
2. one selected Full96 omission route -> the identical high-pass + CMR -> Kilosort4.

Both arms feed the same hybrid ground-truth evaluator. Each route uses its
`ckpt_step_00210923.pt` state at 53,996,288 training windows, preserving matched
exposure between omission0 and omission1.

The model smoke uses run-scoped assets:

```text
probec_recording1_3/{recording.zarr,sorting.zarr}
full96_om{0,1}_duration_outputs/ckpt_step_00210923.pt
```

The full run resumes successful computation `6962e3fb-8ff9-40c1-8d7f-e0cb058cb036`,
whose committed results identify the target as ProbeC `recording1_3`. This reuses
its exact dispatch and raw arm; the updated inference arguments invalidate the DI
branch and downstream comparison. The model asset is attached only to the
inference capsule.

Dry-run and smoke launch:

```bash
python code/benchmarking/launch_ks4_two_arm.py
set -a; source ~/.codeocean.env; set +a
python code/benchmarking/launch_ks4_two_arm.py --route om0 --mode model-smoke --launch
```

The full launch is gated on a succeeded smoke computation:

```bash
python code/benchmarking/launch_ks4_two_arm.py \
  --route om0 --mode full --launch --validated-smoke <computation-id>
```

To retry a failed compatible full run while preserving its successful cache,
add `--resume-run`. The launcher accepts only a completed nonzero-exit source
with the seven expected processes and the selected route's exact checkpoint:

```bash
python code/benchmarking/launch_ks4_two_arm.py \
  --route om0 --mode full --launch \
  --validated-smoke 723ac820-576a-4da9-a274-759afdea3584 \
  --resume-run 28b36eb8-2763-47b1-8fd6-19b007f08bf5
```

| route | checkpoint SHA-256 | model smoke | full computation(s) |
|---|---|---|---|
| omission0 | `f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506` | `723ac820-576a-4da9-a274-759afdea3584` (succeeded) | `28b36eb8-2763-47b1-8fd6-19b007f08bf5` (failed); `db76c533-9f39-46e6-98fe-e83adf56ea51` (resume retry active) |
| omission1 | `90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a` | `0e027dc4-e16e-4935-948d-e037abba5c00` (succeeded) | `2ad21011-a937-44dc-a370-5280049621ef` (succeeded) |

The first omission0 run completed raw Kilosort4 (672 units) and the 16,668-s
DeepInterpolation inference, then exited 1 when denoised preprocessing received
an incomplete 8-MiB download from Code Ocean's internal S3 cache. It produced no
evaluation results. Retry `db76c533-9f39-46e6-98fe-e83adf56ea51` resumes that
run so successful upstream stages are eligible for cache reuse; the failure was
an infrastructure transfer error, not a model or sorter exception.

The inference capsule was synced to commit `808d7fa` before these launches. The
launcher detaches the other route's asset before every submission so model
selection cannot depend on stale capsule attachments.

Code Ocean resources:

| role | id |
|---|---|
| no-generation KS4 pipeline | `5a096db9-3fd7-4984-b5a3-f409b4c8b6ee` |
| exact ProbeC cache computation | `6962e3fb-8ff9-40c1-8d7f-e0cb058cb036` |
| exact ProbeC external asset | `8046af5a-6e53-420e-9e28-52bd54514342` |
| omission0 duration outputs | `a9bcbf5b-0e7c-49ad-a9d5-c36c77647cc2` |
| omission1 duration outputs | `d7821e06-dbba-4060-a7bb-6eab2d8c2ba6` |

The primary outputs are per-GT-unit accuracy, precision, and recall plus the
number of units above 80% accuracy. Unit counts, sorter runtime, and matched-unit
quality metrics are secondary outputs.