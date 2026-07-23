# Kilosort4 benchmark launch

`launch_ks4_two_arm.py` submits the existing Code Ocean no-generation pipeline
with two arms on the manuscript's exact frozen hybrid case:

1. raw hybrid AP recording -> high-pass + CMR -> Kilosort4;
2. Full96 omission1 -> the identical high-pass + CMR -> Kilosort4.

Both arms feed the same hybrid ground-truth evaluator. The selected checkpoint is
`ib_w96_om1_scale/ckpt_step_00210923.pt` at 53,996,288 training windows, SHA-256
`90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a`.

The model smoke uses run-scoped assets:

```text
probec_recording1_3/{recording.zarr,sorting.zarr}
full96_om1_duration_outputs/ckpt_step_00210923.pt
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
python code/benchmarking/launch_ks4_two_arm.py --mode model-smoke --launch
```

The full launch is gated on a succeeded smoke computation:

```bash
python code/benchmarking/launch_ks4_two_arm.py \
  --mode full --launch --validated-smoke <computation-id>
```

Validated model smoke: `0e027dc4-e16e-4935-948d-e037abba5c00` (247 s; wrote
`recording_denoised`). Full two-arm computation:
`2ad21011-a937-44dc-a370-5280049621ef`. The inference capsule was synced to commit
`808d7fa` before both launches.

Code Ocean resources:

| role | id |
|---|---|
| no-generation KS4 pipeline | `5a096db9-3fd7-4984-b5a3-f409b4c8b6ee` |
| exact ProbeC cache computation | `6962e3fb-8ff9-40c1-8d7f-e0cb058cb036` |
| exact ProbeC external asset | `8046af5a-6e53-420e-9e28-52bd54514342` |
| omission1 duration outputs | `d7821e06-dbba-4060-a7bb-6eab2d8c2ba6` |

The primary outputs are per-GT-unit accuracy, precision, and recall plus the
number of units above 80% accuracy. Unit counts, sorter runtime, and matched-unit
quality metrics are secondary outputs.