# Introduction

:::{note} Manuscript status
Prose is carried over from the prior internal report; **all quantitative claims are being
re-established strictly in-domain** (see [the pre-registered design](reproducibility/regeneration-plan.md)) before they
appear here. Numbers shown in the superseded v1 report were measured out-of-band and are archived,
not used.
:::

## Self-supervised denoising with a blind spot

DeepInterpolation [@lecoq2021deepinterpolation] denoises without clean targets by predicting each
sample from its spatiotemporal neighbourhood while **excluding the sample itself** — a "blind spot."
Because the network can never copy the point it must predict, it cannot learn the independent noise,
only the structure shared with the surround. Applied to extracellular electrophysiology, the hope is
that spikes (spatiotemporally correlated across channels) are preserved while thermal/independent
noise is removed, improving downstream spike sorting.

## The model under study (the "champion")

The reference denoiser is a `fold`-geometry ephys DeepInterpolation network: channels are scattered
onto the Neuropixels 1.0 probe grid, a 1-D U-Net runs along probe depth, and a probe-axis blind-spot
branch is fused per channel. The champion configuration and every ablation are enumerated in the
model glossary ([Appendix A](sections/05-appendix.md)) and defined operationally in
[the pre-registered design](reproducibility/regeneration-plan.md).

## The puzzle: denoising helps SNR but hurts detection

The motivating paradox from the prior study: increasing the amount of denoising (higher SNR) did
**not** improve — and often *reduced* — spike **detectability** as measured by a matched-filter
d′. Detection and waveform fidelity appear to be distinct, weakly-coupled axes. Whether that puzzle
survives an in-domain evaluation, or was partly an artifact of the train/deploy band mismatch, is
the central question this manuscript re-examines.
