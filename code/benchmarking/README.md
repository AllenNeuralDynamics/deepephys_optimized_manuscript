# Kilosort4 benchmark launch

`launch_ks4_two_arm.py` submits the existing Code Ocean no-generation pipeline
with two arms on the manuscript's exact frozen hybrid case:

1. raw hybrid AP recording -> high-pass + CMR -> Kilosort4;
2. one selected Full96 omission route -> the identical high-pass + CMR -> Kilosort4.

Both arms feed the same hybrid ground-truth evaluator. Each route uses its
`ckpt_step_00210923.pt` state at 53,996,288 training windows, preserving matched
exposure between omission0 and omission1.

`audit_ks4_results.py` validates both completed computations and regenerates the
compact aggregate/per-unit tables in `results/benchmarking/`. In addition to the
evaluator metrics, it reads the remote SpikeInterface array headers to count all
sorter spike events without downloading the 0.6–0.9-GB arrays.

`build_ks4_all_runs_table.py` combines those audited full-recording outputs,
the complete threshold matrix, and both short calibration sweeps into one
15-row CSV and Markdown table. It verifies that overlapping raw and omission1
baseline rows agree before merging, labels every row by duration scope, and
computes accuracy, precision, recall, TP, FN, and FP on the same seven GT units
matched by raw 9/8 and every denoised full-recording condition. A condition that
loses a reference unit retains its zero metrics and full FN count. The other
three GT units are excluded from these fixed-seven metrics but remain represented
by zeros in the all-10 macro metrics:

```bash
python code/benchmarking/build_ks4_all_runs_table.py
```

`build_ks4_per_unit_snr_table.py` joins all nine full-recording sorter
conditions to the exact scheduled-step raw, omission0, and omission1 GT-template
SNR values. It writes a 63-row long-form comparison and a focused seven-row raw
versus omission1 9/10.75 precision pairing, both ordered by descending raw SNR:

```bash
python code/benchmarking/build_ks4_per_unit_snr_table.py
```

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
| omission0 | `f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506` | `723ac820-576a-4da9-a274-759afdea3584` (succeeded) | `28b36eb8-2763-47b1-8fd6-19b007f08bf5` (failed); `db76c533-9f39-46e6-98fe-e83adf56ea51` (succeeded) |
| omission1 | `90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a` | `0e027dc4-e16e-4935-948d-e037abba5c00` (succeeded) | `2ad21011-a937-44dc-a370-5280049621ef` (succeeded) |

The first omission0 run completed raw Kilosort4 (672 units) and the 16,668-s
DeepInterpolation inference, then exited 1 when denoised preprocessing received
an incomplete 8-MiB download from Code Ocean's internal S3 cache. It produced no
evaluation results. Retry `db76c533-9f39-46e6-98fe-e83adf56ea51` resumed that
run, reused the dispatcher, omission0 inference, raw preprocessing, and raw
Kilosort4 caches, then completed denoised preprocessing, Kilosort4, and hybrid
evaluation in 24,358 s. The failure was an infrastructure transfer error, not a
model or sorter exception.

The two completed runs have exactly identical raw per-unit accuracy, precision,
recall, sorter-unit count, runtime, and spike-event count. Aggregate results are:

```{include} ../../results/benchmarking/kilosort4_summary.md
```

Event accounting for the seven GT-matched clusters is:

```{include} ../../results/benchmarking/kilosort4_event_accounting.md
```

Both denoised routes shift the fixed Kilosort4 configuration toward recall at
the expense of precision without changing detected-unit or well-detected-unit
counts. Omission1 exceeds omission0 mean accuracy by only 0.0014; omission0
produces 35 fewer sorter units. Both denoised arms produce about 55.4% more
sorter spike events than raw, and false-positive spikes in GT-matched clusters
approximately triple. Because native spikes are unlabeled, the all-sorter event
totals are not global false-positive counts, and GT-relative false positives can
include native activity. These are single-run results on one hybrid case,
not a tuned sorter comparison.

The inference capsule was synced to commit `808d7fa` before these launches. The
launcher detaches the other route's asset before every submission so model
selection cannot depend on stale capsule attachments.

## Kilosort parameter sensitivity

The completed raw and denoised arms both executed the pinned Kilosort wrapper
defaults (`03d3522`): `Th_universal=9`, `Th_learned=8`, `Th_single_ch=6`,
`whitening_range=32`, `do_CAR=true`, `highpass_cutoff=300`, and
`skip_kilosort_preprocessing=false`. The upstream preprocessing capsule also
applied high-pass filtering and CMR. These settings were verified from each
saved sorting's SpikeInterface provenance rather than inferred from the wrapper
repository.

The first parameter sensitivity should change only the final learned-template
detection threshold:

| candidate | `Th_learned` | purpose |
|---|---:|---|
| frozen baseline | 8 | completed raw/om0/om1 comparison |
| threshold 9 | 9 | moderate precision-recall recalibration |
| threshold 10 | 10 | stronger suppression of low-score template matches |

The primary readout remains mean per-GT-unit accuracy. Precision, recall,
false-positive spikes in GT-matched clusters, total sorter events, sorter-unit
count, and recovered-unit count are required secondary readouts. This is a
post-hoc sensitivity on the same hybrid case, not independent validation.

`ks4_parameter_sweep.py` generates the complete JSON strings required by the
wrapper's `--params` option and asserts that each candidate changes only
`sorter.Th_learned`:

```bash
python code/benchmarking/ks4_parameter_sweep.py --th-learned 9 10
python code/benchmarking/ks4_parameter_sweep.py \
  --th-learned 9 10 --output-dir /tmp/ks4-thresholds
```

The full payload deliberately includes wrapper-level controls such as
`min_drift_channels=64`. Omitting them would make `--params` override the four
pipeline arguments and silently restore the wrapper's 96-channel drift default.

The production Kilosort capsule app panel exposes only `raise if fails`, `skip
motion correction`, `min channels for drift`, and `clear cache`; no `params`
field is available. The dedicated fork
`AllenNeuralDynamics/aind-deepephys-spikesort-kilosort4` is linked to owned Code
Ocean capsule `eb0a6d2f-2418-4a0a-9765-beaa973745db` (slug `1234998`). This is
the preferred calibration capsule.

An App Panel is not required for the short sweep. Pin each threshold as an
immutable one-line `code/params.json` commit in the fork, sync the owned capsule,
and launch it directly through the API against the same prepared asset. Restore
the threshold-8 default after launching the threshold-9 and threshold-10
snapshots. Every computation then records the exact code commit, and no
production capsule or pipeline is modified. The optional `--params` App Panel
can still be added later for interactive use.

The short sweep does not require modifying the hybrid dispatcher or the
benchmark pipeline. Prepare the exact five-minute omission1 recording once,
apply the frozen upstream high-pass/CMR preprocessing, and publish that
preprocessed BinaryFolder together with the frame-sliced GT sorting as a data
asset. Attach the same asset directly to three Kilosort capsule computations
using the threshold-8, -9, and -10 payloads. Evaluate their sorting outputs with
the repository's GT accounting code. This makes the Kilosort capsule the only
Code Ocean component whose configuration must change.

The deployed calibration commit `d3b57d2` performs all three thresholds
inside one owned-capsule computation. It accepts a five-minute omission1 binary
and the exact hybrid case as run-scoped assets, applies the frozen preprocessing
chain once, runs Kilosort at thresholds 8/9/10, and writes per-unit and summary
CSV tables. `launch_ks4_subset_sweep.py` guards result-asset capture and launch:

```bash
python code/benchmarking/launch_ks4_subset_sweep.py status
python code/benchmarking/launch_ks4_subset_sweep.py create-asset
python code/benchmarking/launch_ks4_subset_sweep.py launch --asset-id <ready-id>
```

The five-minute inference completed as computation
`b1745055-ce00-4cb9-8344-44087a0dd3e6` and was captured as result asset
`0eed5c9d-02c8-4709-b322-15c8ea400aef`. The first calibration attempt
`eb45ea21-3913-43fc-a196-e71738741466` exited before sorting because it assumed
the result asset mount name contained `denoised`. Commit `d3b57d2` removed that
assumption. Replacement computation `93d1865b-a451-45df-90b2-dbcf554544cb` was
launched with the same result asset and exact ProbeC hybrid asset
`8046af5a-6e53-420e-9e28-52bd54514342`.

The replacement completed successfully in 2,012 s. Mean accuracy increased
monotonically from 0.4044 at threshold 8 to 0.4615 at 9 and 0.5002 at 10.
Threshold 10 reduced total sorter events by 47.4% and false-positive spikes in
GT-matched clusters by 73.5% relative to threshold 8, while preserving 7/10
detected and 2/10 well-detected GT units. Recall fell from 0.6528 to 0.5996.
Thresholds 9 and 10 should advance to a longer confirmation because their paired
unit-bootstrap accuracy difference was not conclusive. Compact evidence and the
chunk-boundary check are in `results/benchmarking/ks4_threshold_sweep/`.

The longer confirmation uses the same thresholds and evaluator at 1,200 s.
Inference computation `6add9fa7-e1ff-435d-b9d9-52a3e360901f` produced result
asset `e7134769-b8c9-437a-ba0d-f5bd9ee0078b`. Calibration computation
`c474cfbf-d8ff-4548-93b6-7df282523473` completed successfully from commit
`0a6ffac` in 8,433 s. Threshold 10 again had the highest mean accuracy, although
it exceeded threshold 9 by only 0.0016 and their paired unit-bootstrap interval
crossed zero. Relative to 9, threshold 10 reduced total events by 25.5% and
GT-matched-cluster false-positive spikes by 39.9%, while losing one weakly
matched GT unit and 0.0500 recall. Threshold 10 is selected for the next
precision-first sensitivity; threshold 9 is selected for the next benchmark to
prioritize unit retention. Compact evidence is in
`results/benchmarking/ks4_threshold_confirmation/`.

### Full-recording threshold-9 benchmark

The visual pipeline's production Kilosort node exposes only four positional
controls and strips undeclared `--params` arguments from API submissions. A
guarded test submission confirmed that behavior and deleted the rejected run
before it consumed resources. The selected threshold was instead deployed by
replacing only the denoised Kilosort node with owned capsule
`eb0a6d2f-2418-4a0a-9765-beaa973745db` at commit `ff43f0d`. That commit uses the
normal production entry point and changes only `sorter.Th_learned` from 8 to 9.

An API probe of the edited graph verified the live process bindings. Code Ocean
assigned new process suffixes when the graph was edited, so the suffixes no
longer identify the original branch:

| branch | process | capsule |
|---|---|---|
| raw | `capsule_spikesort_kilosort_4_ecephys_9` | production `e41ff24a-791c-4a11-a810-0106707d3617` |
| Full96 omission1 | `capsule_spikesort_kilosort_4_ecephys_12` | threshold-9 `eb0a6d2f-2418-4a0a-9765-beaa973745db` |

Full computation `748787df-c7f1-4d45-9d51-9f9b5fd9cedc` resumed successful
omission1 computation `2ad21011-a937-44dc-a370-5280049621ef` after validating
the prior model smoke. Its launch guard checked every process-to-capsule binding
and parameter vector before retaining the run. The redundant standalone
inference `eac55c7b-29f9-4d7d-a21a-20d2fe97db81` was canceled after the pipeline
entered the running state.

The full computation succeeded in 21,871 s. Saved sorter provenance verified
that all 55 denoised sorter parameters were identical except
`Th_learned: 8 -> 9`; the raw outputs were also exactly identical between runs.
Threshold 9 increased denoised mean accuracy from 0.4503 to 0.4715 and precision
from 0.4808 to 0.5303, with recall decreasing from 0.6124 to 0.5823. Total sorter
events fell 22.9% and GT-matched-cluster false-positive spikes fell 36.4%, with
no change in detected or well-detected GT-unit counts. Regenerate the compact
audit in `results/benchmarking/ks4_full_threshold9/` with:

```bash
python code/benchmarking/audit_ks4_threshold9.py
```

Threshold 9 remains provisional because its full-recording mean precision
(0.5303) is below raw (0.5851), and GT-matched-cluster false-positive spikes
remain 91.3% above raw. A precision-first full-recording threshold-10 follow-up
was launched as computation `9c4dd3bf-f773-49f8-b332-683aa17947d3`, resuming the
successful threshold-9 computation so upstream inference, preprocessing, and
the raw sorter can be reused. Owned sorter commit `1f7d371` differs from the
threshold-9 commit only at `sorter.Th_learned: 9 -> 10`. The launch guard
verified the raw production capsule and denoised owned-capsule bindings before
retaining the run.

An orthogonal discovery-stage test completed as computation
`a7a8065f-b4b2-43a4-acf6-b87e7ff02201`. Owned sorter commit `43b46d9` uses
`Th_universal=10` and `Th_learned=9`; relative to the completed threshold-9
commit `ff43f0d`, its only changed sorter parameter is
`sorter.Th_universal: 9 -> 10`. It also resumes the completed threshold-9
computation. This separates stricter initial universal-template discovery from
the learned-10 run's stricter final event extraction. The universal-threshold
test may reduce final unit count, so detected GT units and well-detected GT
units are required readouts alongside precision, recall, and event counts.

The 10/9 result was nearly neutral versus 9/9: +0.0006 accuracy, +0.0061
precision, -0.0024 recall, and -2.3% matched-cluster false positives, with 12
more sorter units. The 9/10 sorter completed successfully but its pipeline
evaluator failed only in optional SNR binned plotting. Its immutable task output
was recovered and evaluated directly as computation
`07338f3d-31b2-43d3-bc78-62b3a1852858`. The recovered result has accuracy
0.4688, precision 0.5626, recall 0.5430, 689 sorter units, and 156,203
matched-cluster false-positive spikes. Compact evidence and full recovery
provenance are in `results/benchmarking/ks4_full_threshold_matrix/` and are
regenerated with:

```bash
python code/benchmarking/audit_ks4_threshold_matrix.py
```

Fractional refinement computation `418f3a7b-1e3a-4d11-a85d-191fd05a37da`
completed successfully in 18,520 s from sorter commit `4826f2e` with
`Th_universal=9` and `Th_learned=10.75`. Saved provenance verifies that the
commit differs from completed 9/10 commit `1f7d371` only at
`sorter.Th_learned`, and the pipeline raw output is exactly identical. The
result has accuracy 0.4533, precision 0.5783, recall 0.5077, 682 sorter units,
and 120,202 matched-cluster false-positive spikes. This is the closest tested
raw-selectivity match; 9/10 remains the higher-recall and higher-accuracy
operating point.

Matched-threshold omission0 computation
`a2ccfc54-5109-44ef-9968-b3c1435fcffc` completed successfully in 17,981 s. It
resumed successful omission0 computation
`db76c533-9f39-46e6-98fe-e83adf56ea51`, was gated by succeeded omission0 smoke
`723ac820-576a-4da9-a274-759afdea3584`, and used sorter commit `4826f2e` with
`Th_universal=9`, `Th_learned=10.75`. Saved provenance verifies exact raw-arm
identity and `sorter.Th_learned: 8 -> 10.75` as the only omission0 sorter change.
The result has accuracy 0.4548, precision 0.5779, recall 0.5099, 673 sorter
units, and 121,759 common-seven FP spikes. It is practically tied with omission1
9/10.75, with 2,361 more TP and 1,557 more FP.

Raw AP matched-threshold control computation
`fab61c02-f1d5-4d26-965b-2cdb47aad29b` completed successfully in 14,618 s after
launching from completed omission0 10.75
computation `a2ccfc54-5109-44ef-9968-b3c1435fcffc`. The visual graph replaces
only production raw sorter process `capsule_spikesort_kilosort_4_ecephys_9`
with owned process `capsule_spikesort_kilosort_4_ecephys_13` on capsule
`eb0a6d2f-2418-4a0a-9765-beaa973745db` at commit `4826f2e`. The raw process
receives `capsule_preprocess_ecephys_10`, and evaluator target `ks4` receives the
new raw process. Denoised process `capsule_spikesort_kilosort_4_ecephys_12`, its
`deepks4` evaluator target, inference checkpoint, and every other process remain
unchanged. Creation-time guards verified all seven process bindings and
parameters before retaining the run. Saved raw provenance verifies
`Th_universal=9`, `Th_learned=10.75`, with `sorter.Th_learned: 8 -> 10.75` as
the only change from raw baseline; the denoised arm is byte-identical to its
resume source. Raw 10.75 detects only 3/10 GT units and has fixed-seven counts
TP=274,830, FN=474,726, FP=3,565. Both denoised 10.75 arms retain 7/10 units,
demonstrating that this threshold is viable only after denoising on this case.
After completion, the temporary control graph was restored and verified:
production capsule `e41ff24a-791c-4a11-a810-0106707d3617` again owns raw process
`capsule_spikesort_kilosort_4_ecephys_9`, while owned 10.75 process
`capsule_spikesort_kilosort_4_ecephys_12` remains only on the denoised branch.

### Short-recording calibration

The first threshold screen can use the first 300 seconds of the exact ProbeC
`recording1_3` case. That interval is 4.2% of the full recording but contains
4,443--4,584 injected spikes for every GT unit (44,896 total), which is ample
for a preliminary within-clip ranking of `Th_learned=8,9,10`.

All three thresholds must be run on the same clipped denoised recording. The
existing full-recording threshold-8 result is not a valid baseline for the
short runs because Kilosort template learning and clustering depend on recording
duration. Compare event rates rather than raw event totals, and retain the same
accuracy, precision, recall, matched-cluster false-positive, unit-count, and
recovered-GT outputs used by the full benchmark.

The prepared calibration asset must slice both recording and GT sorting to
frames 0--9,000,000 before preprocessing. This is equivalent to the hybrid
dispatcher's debug behavior but avoids its unsafe broad-S3 `max_recordings=1`
path, where selection is random and the parsed seed is not used.

Use the five-minute result only to eliminate clearly poor thresholds. Confirm
the baseline and selected threshold on at least 20 minutes, then lock the value
before a full-recording or held-out-hybrid evaluation. Short-recording sorting
can rank thresholds quickly, but it cannot establish the final cluster count,
drift behavior, or full-recording precision-recall tradeoff.

If raising `Th_learned` does not restore precision, the next tests should remain
separate and attributable: first `Th_universal=10`, then a matched raw/denoised
`do_CAR=false` ablation because CMR is already applied upstream. Changes to
whitening, clustering, merging, or quality labels should not be mixed into the
first threshold sweep.

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