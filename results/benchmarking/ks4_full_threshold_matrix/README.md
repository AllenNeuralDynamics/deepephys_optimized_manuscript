# Full-recording Kilosort4 threshold matrix

This directory records the full-recording raw 9/8 and 9/10.75 controls, five
Full96 omission1 Kilosort configurations, and the matched Full96 omission0
9/10.75 endpoint on the exact 681532 ProbeC `recording1_3` hybrid case.

## Results

| input | `Th_universal` | `Th_learned` | accuracy | precision | recall | GT detected | GT >0.8 | sorter units | events/s | FP spikes in GT-matched clusters |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| raw AP | 9 | 8 | 0.4471 | **0.5851** | 0.4939 | 7/10 | 2/10 | 672 | 3,466.8 | 119,881 |
| raw AP | 9 | 10.75 | 0.2549 | 0.2945 | 0.2567 | 3/10 | 2/10 | **634** | **2,083.7** | **3,565** |
| Full96 omission0 | 9 | 10.75 | 0.4548 | 0.5779 | 0.5099 | 7/10 | 2/10 | 673 | **2,987.8** | 121,759 |
| Full96 omission1 | 9 | 8 | 0.4503 | 0.4808 | **0.6124** | 7/10 | 2/10 | 725 | 5,388.8 | 360,588 |
| Full96 omission1 | 9 | 9 | 0.4715 | 0.5303 | 0.5823 | 7/10 | 2/10 | 706 | 4,154.9 | 229,311 |
| Full96 omission1 | 9 | 10 | 0.4688 | 0.5626 | 0.5430 | 7/10 | 2/10 | 689 | 3,393.0 | 156,203 |
| Full96 omission1 | 9 | 10.75 | 0.4533 | 0.5783 | 0.5077 | 7/10 | 2/10 | 682 | 2,988.5 | 120,202 |
| Full96 omission1 | 10 | 9 | **0.4720** | 0.5364 | 0.5799 | 7/10 | 2/10 | 718 | 4,185.7 | 224,003 |

All raw baseline arms that retain `Th_learned=8` are exactly identical. The raw
control intentionally changes `Th_learned` to 10.75; its cached omission0
denoised arm is exactly identical to its resume source. Saved sorting provenance
verifies that each threshold candidate differs from its stated reference at
exactly one sorter parameter.

## Interpretation

Raising only `Th_universal` from 9 to 10 has little practical effect relative
to the 9/9 run: accuracy changes by +0.0006, precision by +0.0061, recall by
-0.0024, and matched-cluster false-positive spikes by -2.3%. Total events rise
0.7% and sorter units rise from 706 to 718. Its descriptive paired-unit accuracy
interval is `[-0.0053, +0.0065]`. This does not support universal discovery as
the main source of the residual selectivity gap.

Raising only `Th_learned` from 9 to 10 produces the useful tradeoff. Relative
to 9/9, it raises precision by 0.0323, lowers recall by 0.0393, reduces total
events by 18.3%, reduces matched-cluster false-positive spikes by 31.9%, and
reduces sorter units from 706 to 689. Mean accuracy changes by only -0.0027; its
descriptive paired-unit interval is `[-0.0295, +0.0222]`.

Relative to raw, denoised 9/10 has 0.0217 higher accuracy and 0.0491 higher
recall, but 0.0225 lower precision. It emits 2.1% fewer total events while
recovering 10.0% more injected spikes. GT-matched-cluster false-positive spikes
remain 30.3% above raw, so it does not fully restore raw-like selectivity.

Raising omission1 `Th_learned` to 10.75 nearly restores raw-like selectivity.
Relative to raw, precision is only 0.0068 lower and matched-cluster
false-positive spikes are only 321 (0.27%) higher. Accuracy remains 0.0062
higher, recall remains 0.0138 higher, and 2.8% more injected spikes are
recovered, while total sorter events are 13.8% lower. Relative to 9/10, it gains
0.0157 precision and removes 23.0% of matched-cluster false-positive spikes at
the cost of 0.0353 recall and 0.0154 accuracy. Its descriptive paired-unit
accuracy interval versus 9/9 is `[-0.0649, +0.0219]`.

The matched omission0 9/10.75 result is nearly identical to omission1 9/10.75.
Omission0 has 0.0015 higher accuracy, 0.0022 higher recall, and 0.0005 lower
precision. Across the common seven matched GT units, omission0 recovers 2,361
more injected spikes and has 1,557 more false-positive spikes. It returns nine
fewer sorter units and only 4,835 fewer total events. Thus the calibrated
threshold transfers across the two denoisers, with no practically large route
advantage on this case.

The raw 9/10.75 control demonstrates that the threshold is not transferable
from denoised to raw voltage. Relative to raw 9/8, it loses matched units 337,
664, 1122, and 1300, reducing detected GT units from 7/10 to 3/10 and
fixed-seven TP from 528,844 to 274,830. Its fixed-seven FN count rises from
220,712 to 474,726. The surviving three matches have only 3,565 FP spikes and
pooled precision 0.9872, but this selectivity is achieved by discarding four
reference units; it is not a superior overall operating point.

At the identical 9/10.75 setting, omission0 and omission1 retain all seven
reference units and recover 546,055 and 543,694 TP, respectively. Thus
denoising shifts the useful Kilosort score range: a threshold that is too strict
for raw remains viable after denoising. This supports a denoising-dependent
operating-point shift, rather than a universal threshold recommendation.

For this case, denoised 9/10.75 is the closest tested match to the raw 9/8
deployment tradeoff, while omission1 9/10 remains the higher-recall and
higher-accuracy denoised operating point. Raw and denoised data require separate
threshold calibration. These results are still within-case calibration
follow-ups, not independent validation.

## Recovery provenance

The original 9/10 pipeline computation
`9c4dd3bf-f773-49f8-b332-683aa17947d3` completed Kilosort successfully with 689
units, then failed in an optional SNR binned-average plot because SciPy received
a zero-width bin edge. The completed sorter task was preserved as external asset
`07a54bd7-f145-41c8-b19e-1d8e05c060b2`. Recovery computation
`07338f3d-31b2-43d3-bc78-62b3a1852858` evaluated that immutable sorting directly
against the exact GT in 21 s. It verified `Th_universal=9`, `Th_learned=10`,
1,070,127 GT events, and the full saved sorter parameter dictionary before
writing metrics.

Regenerate all compact tables with authenticated Code Ocean access:

```bash
set -a; source ~/.codeocean.env; set +a
python code/benchmarking/audit_ks4_threshold_matrix.py
```