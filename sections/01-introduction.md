# Introduction

:::{note} Manuscript status
The Methods, Results and Discussion report **in-band** numbers for Tier 1 (the noise-floor
configurations) and the two SUPPORT-scale runs; the remaining architecture/loss sweep (Tier 2/3) is
in progress. Numbers in the superseded v1 report were measured out-of-band and are archived, not used
(see [the pre-registered design](reproducibility/regeneration-plan.md)).
:::

## Self-supervised denoising with a blind spot

DeepInterpolation [@lecoq2021deepinterpolation] denoises without clean targets by predicting each
sample from its spatiotemporal neighbourhood while **excluding the sample itself** — a "blind spot."
Because the network can never copy the point it must predict, it cannot learn the independent noise,
only the structure shared with the surround. Applied to extracellular electrophysiology, the hope is
that spikes (spatiotemporally correlated across channels) are preserved while thermal/independent
noise is removed, improving downstream spike sorting.

## The reference architecture (`base32`)

The reference denoiser is a `fold`-geometry ephys DeepInterpolation network. Channels are scattered
onto the Neuropixels 1.0 probe grid and the array's W columns are folded into the feature axis; a
1-D U-Net then runs along probe depth. Two branches predict each output sample and are fused per
channel: a **temporal** branch that reads a short window of frames around the target, and a
probe-axis **spatial blind-spot** branch over the centre frame. The single design choice this study
turns on lives in the temporal branch — the **omission gap**: whether it may see the frames
immediately adjacent to the target (t±1) or hides them along with the target itself. The base32
reference hides them (`omission=1`); the SUPPORT denoiser that inspired this work does not. Every configuration
and ablation is enumerated in the model glossary ([Appendix A](sections/05-appendix.md)) and defined
operationally in [the pre-registered design](reproducibility/regeneration-plan.md).

## The puzzle, and why the study was redone

The motivating paradox from the prior study: increasing the amount of denoising (higher SNR) did
**not** improve — and often *reduced* — spike **detectability** as measured by the matched-filter d′.
Detection and waveform fidelity behaved as distinct, weakly-coupled axes, and a single temporal-design
change (the omission gap) appeared to dominate every other lever.

That study, however, was later found to have **trained on wide-band data but evaluated on high-passed
AP-band data** — the denoiser was run outside its training domain, so every absolute number and
ranking was out-of-band (Methods). This manuscript re-establishes the result strictly in-domain and
asks which conclusions survive: does denoising still cost detection when the model is trained in its
deployment band, and is the omission gap still the dominant lever — or was it a band artifact?
