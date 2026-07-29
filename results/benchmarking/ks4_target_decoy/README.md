# Kilosort4 sign-decoy target-FDR experiment

This directory records a GT-blind experimental change to Kilosort 4.1.7 matching
pursuit. For every batch and peel, positive signed learned-template local maxima
were treated as targets and negative signed maxima as decoys. The matcher selected
the smallest threshold at or above 8 satisfying the knockoff-plus estimate

$$
\widehat{FDR} = \frac{1 + N_{decoy}}{N_{target}} \leq 0.05.
$$

Accepted events used Kilosort's unchanged amplitude fit, subtraction, feature
extraction, clustering, merging, and duplicate removal. Ground truth was not used
for any matching decision; it was applied only afterward for evaluation.

The policy was fixed before observing the result: target FDR 5%, threshold floor
8, independently learned native transforms/templates, both raw and Full96
omission1 domains, and the same first 1,200 seconds of the frozen ProbeC hybrid
case.

## Provenance

- Matcher capsule commit: `0da9f28`
- Full computation: `2fea74b8-783d-4175-9dd7-8a4caf5b3f64`
- Runtime: 9,320 seconds
- Exit code: 0; results published successfully
- Preregistered audit: manuscript commit `8353d1e`
- Kilosort 4.1.7; SpikeInterface 0.104.7

A 60-second raw smoke computation (`61f84bd0-2237-441b-8a30-b9f2a7902087`)
first established nonzero sign-decoy support, exact FDR control, downstream
compatibility, and successful publication. No policy parameter was changed after
that smoke result.

## Result

| Input | Method | Events | Clusters | GT units | TP | FN | Matched-cluster FP | Pooled precision | Pooled recall |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw-native | Native 9/8 | 4,273,542 | 567 | 7/10 | 97,677 | 81,689 | 31,012 | 0.7590 | 0.5446 |
| Raw-native | Target-decoy 5% | 1,243,227 | 320 | 2/10 | 30,920 | 148,446 | 18 | 0.9994 | 0.1724 |
| Denoised-native | Native 9/8 | 10,184,212 | 649 | 8/10 | 125,183 | 54,183 | 80,624 | 0.6083 | 0.6979 |
| Denoised-native | Target-decoy 5% | 1,062,610 | 297 | 2/10 | 35,082 | 144,284 | 4 | 0.9999 | 0.1956 |

The only GT units retained in either domain were 793 and 2143, the two strongest
reference units. Therefore, the near-perfect matched-cluster precision is caused
by severe unit and TP loss, not a useful improvement in the sorting tradeoff.

Relative to native 9/8, the target-decoy rule retained 31.7% of raw TP and 28.0%
of denoised TP while eliminating more than 99.9% of matched-cluster FP. It also
removed 5 of 7 raw and 6 of 8 denoised GT matches. This operating point is too
conservative for spike sorting.

## Gate behavior

| Input | Accepted events | Median selected threshold | Maximum threshold | Median negative/positive floor ratio | Maximum exact FDR |
|---|---:|---:|---:|---:|---:|
| Raw-native | 1,243,369 | 18.61 | 35.12 | 0.964 | 0.05 |
| Denoised-native | 1,062,810 | 25.38 | 52.61 | 0.959 | 0.05 |

The decoy null was well populated: negative and positive local-max counts above
the original threshold were nearly equal. To make their ratio at most 1:20, the
candidate-level 5% rule raised the median threshold far above Kilosort's value of
8, including peel 0. Thus candidate-level sign symmetry is too stringent a null
for preserving moderate-SNR units.

This does not invalidate residual-null calibration in general. It rejects this
particular formulation: independent per-batch/per-peel 5% FDR using the complete
negative signed local-max tail. More promising versions should separate the
initial detection prior from later residual peeling, use held-out channel
support, or calibrate conditional residual artifacts rather than all negative
excursions. Tuning the FDR target on this hybrid case is not recommended.

## Artifacts

| File | Contents | SHA-256 |
|---|---|---|
| `target_decoy_vs_native_baseline.csv` | exact baseline/adaptive comparison and deltas | `8b5daf29bf2a0249766e831126ad1222733d95fcb85733fa3ce2b43478c25395` |
| `target_decoy_gate_by_batch_peel.csv` | exact target/decoy counts, selected thresholds, FDR, and events | `c1114b2caf02067a7849338e60d352a6f4ec4d505331bcab93bd15c6067d806e` |
| `target_decoy_gate_summary.csv` | compact per-domain gate summary | `c75ba68fa635ec81d78355ef24aed7955962afd5bc9ef5b381bbb1306ce2b710` |
| `target_decoy_stage_summary.csv` | adaptive stage-level TP/FN/FP accounting | `b54d5f957588139997e099a8f588677b96cbf97a76931d2d47e72785e71eda39` |
| `target_decoy_unit_summary.csv` | per-GT-unit adaptive results | `18d2f2e42704a175229fec2b5f6ef7d43b2791c6d703b39fe408545b34fab348` |
| `target_decoy_score_summary.csv` | accepted scores by stage/status/peel | `cb5ed75c9700e80c518cb0e69f2deed737ee57e73c1536fe80ce570691dcb678` |
| `target_decoy_manifest.json` | fixed policy, versions, domains, and transform provenance | `951b6aecb6542bf71353b64219800300b38d8731bccc3496d5d0374e22b8db4c` |
| `target_decoy_output.log` | complete successful Code Ocean execution log | `a6085ad234995443511e4abb614410fe96486406b3cc9003befe03c31df5e846` |

Figure: `figures/kilosort4_target_decoy_result.{png,pdf}`. Regenerate with:

```bash
python code/figures/kilosort4_target_decoy.py
```
