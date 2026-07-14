---
title: Optimizing DeepInterpolation for Neuropixels spike detection
short_title: DeepEphys Optimized
abstract: |
  DeepInterpolation is a self-supervised, blind-spot denoiser proposed to improve
  the signal-to-noise ratio of extracellular electrophysiology. A prior internal
  study swept its architecture and training choices against a frozen hybrid
  Neuropixels 1.0 benchmark and reported that denoising counter-intuitively tends
  to *reduce* spike detectability (d′), while an overlooked temporal-design
  choice — hiding the frames immediately adjacent to the predicted sample (the
  "omission gap") — dominates every other lever. That study, however, trained on
  wide-band data and evaluated on high-passed AP-band data, so the denoiser
  operated outside its training domain and every reported number is out-of-band.
  Here we re-run the entire evaluation strictly in-domain: every model is trained
  and scored on the same AP-band recording it is deployed on, under a single
  uniform quantification protocol (matched-filter d′, amplitude and waveform
  fidelity, resolved per-unit and per-model, read against a replicate-derived
  noise floor). The full design is pre-registered (see
  [the pre-registered design](reproducibility/regeneration-plan.md)) and the entire train → score → figure
  pipeline is reproducible from this repository.
  **Quantitative results are being regenerated in-domain and will be reported here.**
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
