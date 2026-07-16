# Introduction

:::{note} Manuscript status
Methods, Results and Discussion report the complete in-band sweep — Tier 1 (noise-floor
configurations), Tier 2, the Tier 3 spike-aware loss family, the original DeepInterpolation network as
a published reference, and the two SUPPORT-scale runs (see
[the pre-registered design](reproducibility/regeneration-plan.md)).
:::

## Self-supervised denoising with a blind spot

DeepInterpolation [@lecoq2021deepinterpolation] denoises without clean targets by predicting each
sample from its spatiotemporal neighbourhood while **excluding the sample itself** — a "blind spot."
Because the network can never copy the point it must predict, it cannot learn the independent noise,
only the structure shared with the surround. Applied to extracellular electrophysiology, the hope is
that spikes (spatiotemporally correlated across channels) are preserved while thermal/independent
noise is removed, improving downstream spike sorting.

## The reference architecture (`base32`)

The reference denoiser is a `fold`-geometry ephys DeepInterpolation network (`FoldDeepInterp1D`,
~0.85 M parameters). Its input is a short stack of frames across all 384 channels; the channels are
scattered onto the Neuropixels 1.0 probe grid (a 192 × 4 checkerboard) and the four probe *columns*
are folded into the feature axis, turning the expensive 2-D problem into a cheap 1-D one along probe
depth. Each output sample is predicted by **two branches**, fused per channel:

- a **temporal branch** — a 1-D U-Net (encode → bottleneck → decode with skips) that reads a window
  of neighbouring *frames* (±30) and predicts the target from how the signal evolves in time;
- a **spatial blind-spot branch** — a stack of dilated "hole" convolutions whose centre kernel tap is
  zeroed, so each channel is predicted only from its *neighbours* on the probe at the centre frame,
  never from its own value.

The two branch outputs are merged by a pointwise (1×1) **fuse head**, which keeps the whole network
*blind-spot-safe*: the prediction for a channel never sees that channel's own value at the target
frame, so the network cannot learn the independent noise. The one design choice this study turns on
lives in the temporal branch — the **omission gap**: whether it may see the frames immediately
adjacent to the target (t±1) or hides them along with the target. The base32 reference hides them
(`omission=1`); the SUPPORT denoiser [@eom2023support] that inspired this work does not. The full
layer-by-layer configuration, and how each swept variant is built from it, are given in
[Methods](sections/02-methods.md); every configuration is also enumerated in the model glossary
([Appendix A](sections/05-appendix.md)).

## The limitation: denoising can cost spike detection

Denoising is meant to help downstream sorting, but a self-supervised blind-spot denoiser is not
optimised for detection — it is optimised to predict each sample from its surround. A practically
important consequence is that raising the amount of denoising (higher SNR) does **not** reliably
improve — and can *reduce* — spike **detectability**, measured here by a matched-filter d′. Detection
and waveform fidelity behave as distinct, weakly-coupled axes, and the cost falls hardest on the
**weak, low-amplitude units** that are already near the sorting threshold: the blind spot rebuilds
each peak from its neighbours, and for a faint unit those neighbours are mostly noise, so the
estimator hedges toward baseline and flattens the spike.

This manuscript sets out to **optimise the ephys DeepInterpolation architecture to protect those weak
units** — asking which architectural, loss, and training-length choices reduce the detection cost —
measured directly against injected ground truth rather than by SNR. Because DeepInterpolation is
self-supervised, we train and score every model in its deployment band (Methods), so the numbers
reflect how the denoiser actually behaves where it is used.
