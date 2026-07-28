# Kilosort4 fixed-template event lineage

This directory contains compact evidence from Code Ocean computation
`d0efc11d-4141-443b-b381-98c9dbeecd6a`, capsule commit `b20567c`. The run used
Kilosort 4.1.7 and SpikeInterface 0.104.7 on the exact first 1,200 seconds of the
ProbeC `recording1_3` hybrid benchmark.

The diagnostic learned templates, whitening, drift, and channel selection once
from Full96 omission1 denoised voltage at `Th_learned=8`. It replayed that fixed
transform on matched raw and denoised voltage at `Th_learned=8` and `10.75`, then
traced every accepted event through detection template, final clustering, CCG
merging, and duplicate removal. This controlled transform isolates input-domain
score and subtraction behavior. It is not the production raw baseline, which
learns its own raw-native templates and matches 7/10 GT units at the default
9/8 thresholds.

The Code Ocean process returned exit code 1 only after all scientific artifacts
were written, while serializing the final manifest. Commit `d200d09` fixes that
bookkeeping defect. The denoised `Th_learned=8` final times and cluster partition
exactly match the template-learning sort, allowing cluster-ID permutation.

## Artifacts

| File | Contents | SHA-256 |
|---|---|---|
| `event_lineage_score_summary.csv` | accepted score mean and 10th/median/90th percentiles by domain, threshold, stage, status, and peel | `7842074595c7df6c8bc73112caf91149366583e422006a94ce1015a15c276e46` |
| `event_lineage_stage_summary.csv` | event, cluster, TP/FN/FP, and unmatched counts at every downstream stage | `297e6d026df6c39fb06c293767437c8acaad215bdec8576c5518959bfc93757a` |
| `event_lineage_stage_deltas.csv` | adjacent-stage changes identifying clustering, merging, and dedup effects | `cb4411cf11427d87b11b8d9a2e6819dc445362fabca453a2b3790a9bf32006eb` |
| `event_lineage_replay_alignment.csv` | independent replay versus exact inline-extraction agreement audit | `84c036924f29979624c5d47650c0571adbaceb1810e758f4491386b9e4038613` |
| `fp_by_peel.csv` | TP/FP counts, per-peel FP fraction, FP share, and cumulative FP share | `4e7378e2d298eb3b28846cbbdf2a8d5c90ecfe179950a2694d9e1b3994a38d5c` |
| `accepted_score_margin_by_peel.csv` | accepted score statistics transformed to `score - Th_learned` | `b55a6293c9e2d08d50faaa92e3b6fe5b07880f073e045378dc5c3d4f0969801d` |
| `accepted_score_margin_summary.csv` | event totals, peel quantiles, and event-weighted mean score margins | `92655e79caafeea277b43bf890a6d2bf3d4b5fd47e821cdbf578f7c988152c07` |

Figures:

- `figures/kilosort4_fp_by_peel.{png,pdf}`
- `figures/kilosort4_score_margin_by_peel.{png,pdf}`

Regenerate locally with:

```bash
python code/figures/kilosort4_fp_by_peel.py
python code/figures/kilosort4_score_margin_by_peel.py
```

## Accepted-score analysis

The saved score is the normalized learned-template score at the peel where an
event was accepted from the current subtraction residual. Every saved event has
`score > Th_learned`; the margin is therefore

$$
\Delta s = s - Th_{learned} > 0.
$$

At `Th_learned=10.75`, final TP events have event-weighted mean margins of
12.03 on raw and 10.95 on denoised voltage. Final matched-cluster FPs have much
smaller margins, 2.29 and 2.99, and occur later: median peel 22 versus 6 on raw,
and 13 versus 6 on denoised voltage. This supports repeated subtraction exposing
increasingly marginal events.

The same pattern is present for denoised `Th_learned=8`: TP mean margin 12.31 at
median peel 7, versus FP mean margin 2.85 at median peel 25. Raw `Th_learned=8`
under the denoised-derived transform is pathological: it retains only two
GT-matched clusters, has no evaluator-defined FP in those clusters, and assigns
21,112,308 events to unmatched clusters. It must not be interpreted as the
production raw 9/8 result.

The score tables contain all accepted events, including later peels. They do not
contain every rejected subthreshold template/time candidate after peel 0.
