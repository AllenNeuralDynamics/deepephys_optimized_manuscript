# Full-recording Kilosort4 threshold-9 result

This directory records the controlled full-recording comparison of
`Th_learned=8` and `Th_learned=9` on the exact 681532 ProbeC `recording1_3`
hybrid case after Full96 omission1 denoising.

## Provenance

- Pipeline: `5a096db9-3fd7-4984-b5a3-f409b4c8b6ee`
- Threshold-8 computation: `2ad21011-a937-44dc-a370-5280049621ef`
- Threshold-9 computation: `748787df-c7f1-4d45-9d51-9f9b5fd9cedc`
- Threshold-9 capsule: `eb0a6d2f-2418-4a0a-9765-beaa973745db`
- Threshold-9 capsule commit: `ff43f0d`
- Recording duration: 7,144.262 s
- Injected GT events: 1,070,127 across 10 units

The threshold-9 computation resumed the successful threshold-8 omission1 run.
The raw arm is exactly identical between computations in per-unit performance,
sorter-unit count, runtime, and total spike-event count. Saved sorting
provenance contains 55 sorter parameters; the only difference between the two
denoised sortings is `Th_learned: 8 -> 9`.

## Results

| input | `Th_learned` | mean accuracy | precision | recall | GT detected | GT >0.8 | sorter units | events/s | FP spikes in GT-matched clusters |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| raw AP | 8 | 0.4471 | **0.5851** | 0.4939 | 7/10 | 2/10 | **672** | **3,466.8** | **119,881** |
| Full96 omission1 | 8 | 0.4503 | 0.4808 | **0.6124** | 7/10 | 2/10 | 725 | 5,388.8 | 360,588 |
| Full96 omission1 | 9 | **0.4715** | 0.5303 | 0.5823 | 7/10 | 2/10 | 706 | 4,154.9 | 229,311 |

Relative to threshold 8, threshold 9:

- increased mean accuracy by 0.0212 and precision by 0.0495;
- reduced recall by 0.0302 and recovered 4.9% fewer injected spikes;
- reduced total sorter events by 22.9%;
- reduced false-positive spikes in GT-matched clusters by 36.4%; and
- preserved both detected-unit and well-detected-unit counts.

Six GT units improved in accuracy, one ceiling unit decreased by 0.00034, and
three undetected units were unchanged. A descriptive paired unit bootstrap gave
a threshold-9 minus threshold-8 mean accuracy interval of
`[+0.0031, +0.0436]`. This interval describes these ten injected units on one
case; it is not independent validation.

## Raw comparator

Threshold 9 substantially closes, but does not eliminate, the denoised/raw
selectivity gap. Relative to the exact raw result, threshold-9 denoised sorting
has 0.0244 higher mean accuracy and 0.0883 higher recall, but 0.0548 lower
precision. It produces 19.9% more total events and 91.3% more false-positive
spikes in GT-matched clusters, alongside 17.9% more recovered injected spikes.

The full result supports `Th_learned=9` as a provisional unit-retention setting
for Full96 omission1. It improves the primary accuracy metric and markedly
suppresses excess events without losing recovered units, but its precision
remains below raw. Full threshold-10 computation
`9c4dd3bf-f773-49f8-b332-683aa17947d3` is the precision-first follow-up. The
threshold-9 result does not establish that all remaining extra sorter events are
noise: all-sorter totals include unlabeled native activity, and GT-relative
false positives can include native spikes in a cluster matched to an injected
unit.

Two controlled full-recording follow-ups completed from this result:

| computation | `Th_universal` | `Th_learned` | result |
|---|---:|---:|---|
| `9c4dd3bf-f773-49f8-b332-683aa17947d3` | 9 | 10 | sorting succeeded; evaluation recovered as `07338f3d-31b2-43d3-bc78-62b3a1852858` |
| `a7a8065f-b4b2-43a4-acf6-b87e7ff02201` | 10 | 9 | completed normally; nearly neutral versus 9/9 |

The complete comparison is in `../ks4_full_threshold_matrix/`.

Regenerate the compact files with authenticated Code Ocean access:

```bash
set -a; source ~/.codeocean.env; set +a
python code/benchmarking/audit_ks4_threshold9.py
```