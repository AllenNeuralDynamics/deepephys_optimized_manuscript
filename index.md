---
title: Optimizing DeepInterpolation for Neuropixels spike detection
short_title: DeepEphys Optimized
abstract: |
  DeepInterpolation [@lecoq2021deepinterpolation] is a self-supervised, blind-spot denoiser that
  can raise peak-channel template signal-to-noise ratio (SNR), but that metric need not track how well
  spike and background events separate. We evaluated DeepInterpolation variants on one frozen hybrid
  Neuropixels 1.0 recording containing 10 injected ground-truth units [@buccino2020spikeinterface].
  Models were trained self-supervised and scored in the high-passed AP band using multichannel
  matched-filter d′ and empirical-template waveform metrics. Across 21 short-budget architectures,
  every denoised output had lower mean d′ than raw data. The complete modernization from the original
  ephys network to the two-branch `base32` model improved d′ by 0.14; the best observed modern body
  improved it by 0.27, although several high-capacity results are single-seed screens. Width produced
  the largest replicated gain in the all-unit mean (+0.105 d′), whereas the compound `omission0`
  configuration, which routes t±1 through the temporal branch, produced the larger gain among four
  weak units (+0.148 d′) and improved amplitude preservation toward raw. Across architectures,
  change in template SNR did not rank change in d′ (Spearman ρ = 0.02). In a three-seed matched
  replication, warmup alone did not improve the endpoint consistently, whereas a compound batch-256
  recipe improved mean d′ by 0.004 in all three pairs and reached d′ = 4.30 after a median 2.25 M
  versus 5.38 M windows for baseline. Four single-seed controls did not isolate a better method:
  adaptive accumulation and objective-preserving importance sampling matched the warmup endpoint,
  but importance sampling required 2.2× the runtime; physical and accumulated effective batch 256
  both finished lower. A capacity-matched NAF temporal block was 0.022 d′ lower and 41% slower than
  matched seed-0 DoubleConv despite nearly identical validation loss. Corrected soft magnitude
  weighting at λ = 3 gave a +0.0055 d′ lead within unweighted seed spread, while stronger weighting
  reduced d′ by as much as 0.262 and could distort template shape. Absolute self-template d′ is
  in-sample optimistic because template estimation and hit scoring reuse events. The conclusions are
  therefore specific to one hybrid benchmark and a matched-filter proxy; cross-fitted, held-out, and
  sorter-level validation remain necessary. The versioned train → score → figure pipeline is
  reproducible from this repository.
---

```{include} sections/01-introduction.md
```

```{include} sections/02-methods.md
```

```{include} sections/03-results.md
```

```{include} sections/04-discussion.md
```

```{include} sections/05-appendix.md
```
