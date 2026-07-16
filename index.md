---
title: Optimizing DeepInterpolation for Neuropixels spike detection
short_title: DeepEphys Optimized
abstract: |
  DeepInterpolation [@lecoq2021deepinterpolation] is a self-supervised, blind-spot denoiser that
  improves the signal-to-noise ratio of extracellular electrophysiology. A practically important
  limitation, however, is that denoising can *reduce* spike **detectability** (d′) even as it raises
  SNR — and the cost falls hardest on the weaker, low-amplitude units that are already near the
  sorting threshold. Here we set out to optimise the ephys DeepInterpolation architecture to protect
  those weak units, drawing on advances in self-supervised "blind-spot" denoising
  [@eom2023support] and measuring detection directly against a frozen **hybrid ground-truth**
  Neuropixels 1.0 benchmark [@buccino2020spikeinterface] — known units injected into a real recording,
  so detection and waveform fidelity are read out without running a spike sorter. Because
  DeepInterpolation is self-supervised, every model is **trained and scored in its deployment band**
  (the high-passed AP band), under one uniform quantification protocol (matched-filter d′, amplitude
  and waveform fidelity, resolved per-unit and per-model, read against a replicate-derived noise
  floor). The full design is pre-registered (see
  [the pre-registered design](reproducibility/regeneration-plan.md)) and the entire train → score →
  figure pipeline is reproducible from this repository.
  **We find that denoising still lowers detectability (every model below raw); network capacity is the
  leading detection lever; the temporal "omission" design is an amplitude / waveform lever whose small
  detection advantage is a convergence-speed effect; and detection keeps rising with training (not
  converged even at 3.3 M updates), so training length is a lever too. Against the original
  DeepInterpolation architecture the optimized network recovers +0.23 d′ and +0.13 amplitude — most of
  it on the weak units — while a spike-aware loss aimed directly at those units does not move detection,
  indicating the residual sub-raw deficit is intrinsic to the blind-spot objective.**
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
