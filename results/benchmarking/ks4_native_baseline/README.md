# Kilosort4 native default 9/8 baseline lineage

This directory compares Kilosort 4.1.7 default-threshold lineage on matched
1,200-second raw and Full96 omission1 denoised inputs. Each domain independently
derives its channel mask, whitening, drift estimate, and learned templates with
`Th_universal=9` and `Th_learned=8`.

Sources:

- Raw-native computation `adaf8bcd-453d-472c-a98e-bf00158b6b67`, capsule
  commit `29a7da3`, completed successfully in 4,629 seconds with exact
  threshold-8 template-learning sort identity.
- Denoised-native threshold-8 rows from computation
  `d0efc11d-4141-443b-b381-98c9dbeecd6a`, capsule commit `b20567c`, also with
  exact template-learning sort identity.

Both use the same first 1,200 seconds of the frozen ProbeC `recording1_3` hybrid
case and SpikeInterface benchmark matching (`delta_time=0.4 ms`, Hungarian unit
assignment, `match_score=0.2`). These are interval-matched diagnostics, not the
full 7,144-second production sort.

## Final default-baseline accounting

| Input | Events | Clusters | Matched GT units | TP | FN | FP in matched clusters | Events in unmatched clusters | Pooled precision | Pooled recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw-native | 4,273,542 | 567 | 7/10 | 97,677 | 81,689 | 31,012 | 4,144,853 | 0.7590 | 0.5446 |
| Full96 denoised-native | 10,184,212 | 649 | 8/10 | 125,183 | 54,183 | 80,624 | 9,978,405 | 0.6083 | 0.6979 |

Relative to raw-native, denoising adds 27,506 recovered injected spikes and one
matched GT unit, while adding 49,612 evaluator-defined FPs in matched clusters.
The latter can include native biological spikes and are not synonymous with
electrical noise.

## Peel and accepted-score behavior

| Input | Status | Events | Median peel | 90% by peel | Event-weighted mean score margin `score - 8` |
|---|---|---:|---:|---:|---:|
| Raw-native | TP | 97,677 | 7 | 17 | 6.89 |
| Raw-native | FP in matched cluster | 31,012 | 13 | 22 | 2.20 |
| Denoised-native | TP | 125,183 | 7 | 21 | 12.31 |
| Denoised-native | FP in matched cluster | 80,624 | 25 | 46 | 2.85 |

In both native baselines, matched-cluster FPs are later and substantially closer
to the acceptance boundary than TPs. Denoising extends productive peeling and
also extends the FP tail: the median FP shifts from peel 13 to 25.

The stage audit shows that merging changes no TP/FN/FP totals. From learned
extraction to final clustering, raw gains 392 TP and 1,232 FP; denoised loses
1,920 TP and 18,991 FP. Duplicate removal eliminates only 16 raw and 54 denoised
matched-cluster FPs. Most of the final FP population therefore already exists in
the learned-template extraction output.

## Artifacts

| File | Contents | SHA-256 |
|---|---|---|
| `raw_native_event_lineage_score_summary.csv` | raw-native accepted score statistics by peel/status | `e4c56b9b6ce3da430dda0eeab48dc18f05c2843434af0fd4f823ce49232161a1` |
| `raw_native_event_lineage_stage_summary.csv` | raw-native stage totals | `278f7acafa55030e12741db1378a3146ce828fd7152aa637a7f72de2ae569e24` |
| `raw_native_event_lineage_stage_deltas.csv` | raw-native adjacent-stage changes | `0cc431768d59bad194d25c6aadc4faffce6b963eabbad0c80b6d2125de0d20df` |
| `raw_native_event_lineage_unit_summary.csv` | per-GT-unit raw-native lineage accounting | `3e70a4fa6555dde730469064b14c602771824752ff429321ff2f60ac32f48383` |
| `raw_native_event_lineage_cluster_summary.csv` | per-cluster raw-native properties | `b66b4b8f6fd54e8517af3bd41ec5e539f22e0afcff5fc40cde4fe736f1f203a9` |
| `raw_native_event_lineage_replay_alignment.csv` | exact extraction/replay agreement audit | `40792d635ff8ccf776a6ca2db2e518eefc667987bd1c52a4c702dddaf437dcbc` |
| `raw_native_score_diagnostic_manifest.json` | raw-native input, transform, version, and channel provenance | `b720cb4ee98d0dc0d47e1604658b475542eaa8024a3b31624a4acb1868343218` |
| `native_baseline_by_peel.csv` | paired TP/FP counts and FP proportions by peel | `8bfc2eda59518812e4794019b61ed065bccf290c158628708c86ecd2a2672523` |
| `native_baseline_score_margin_by_peel.csv` | paired accepted-score margins by peel/status | `b18b31144f4a75880a1dd2307669dc20447ca55a991e92a07a7d9c3e49abc27b` |
| `native_baseline_stage_summary.csv` | paired stage-level accounting | `6af7e2e8c462cfde1077d46b6949c677d8c46b9078d4dc2dd62cc92066b382ff` |
| `native_baseline_summary.csv` | compact paired event/peel/score summary | `2f4abc76f77bd440fbe8102cd529189c65320815c1ebd4ef188a0839e11f08de` |

Figure: `figures/kilosort4_native_baseline_by_peel.{png,pdf}`. Regenerate with:

```bash
python code/figures/kilosort4_native_baseline.py
```

The remaining `raw_native_*.csv` files preserve the full compact diagnostic
record: template-to-cluster transitions, status transitions, first-peel local
maxima, threshold replay, per-unit GT scores, per-peel event counts, template
background scores, and sampled event/background scores. `raw_native_output.log`
is the complete successful Code Ocean execution log. The compact 51-MB
event-level NPZ remains attached to the source computation and is intentionally
not duplicated in this repository.
