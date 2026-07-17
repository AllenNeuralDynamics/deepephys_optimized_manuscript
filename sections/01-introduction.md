# Introduction

## Detection is the target

DeepInterpolation [@lecoq2021deepinterpolation] denoises without clean targets by predicting each
sample from its spatiotemporal neighbourhood while **excluding the sample itself** — a "blind spot."
Because the network can never copy the point it must predict, it cannot learn the independent noise,
only the structure shared with the surround. Applied to extracellular electrophysiology, the hope is
that spikes (spatiotemporally correlated across channels) are preserved while thermal/independent
noise is removed, improving downstream spike sorting.

Denoising is not itself the downstream objective. Peak-channel template SNR combines empirical
waveform amplitude and background variance, while a sorter must separate multichannel spike events
from background events. A blind-spot predictor can therefore raise template SNR while attenuating or
reshaping information used for detection. This distinction matters most for weak units near a sorting
threshold, where conditional-mean prediction is expected to shrink uncertain waveforms toward
baseline. We test that behavior directly rather than treating SNR as a surrogate for detectability.

## Study question and reference model

This study asks which architecture and training choices preserve matched-filter detectability and
empirical waveform shape, particularly for weak units. The reference (`base32`) is a 0.85-M-parameter
`fold` model with a temporal U-Net, a spatial blind-spot branch, and a pointwise fuse head. The
**omission configuration** controls where adjacent t±1 information enters the model. We compare that modern reference
with the original temporal-only ephys network, wider and deeper bodies, alternative wiring and losses,
training recipes, and two long-duration trajectories. All models are trained self-supervised and
scored against injected ground truth in one frozen AP-band hybrid recording. This design isolates
model-output differences on that benchmark, but architecture selection on the same recording means
the conclusions require replication on held-out recordings and with a full spike sorter.

The layer-level model definition is in [Methods](sections/02-methods.md), the model glossary is in
[Appendix A](sections/05-appendix.md), and the evolving study design is documented in the
[versioned analysis plan](reproducibility/regeneration-plan.md).
