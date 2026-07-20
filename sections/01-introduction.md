# Introduction

## Detection is the target

DeepInterpolation [@lecoq2021deepinterpolation] denoises without clean targets by predicting each
sample from its spatiotemporal neighbourhood while **excluding the sample itself** — a "blind spot."
Because the network can never copy the point it must predict, it cannot learn the independent noise,
only the structure shared with the surround. Applied to extracellular electrophysiology, the hope is
that spikes (spatiotemporally correlated across channels) are preserved while thermal/independent
noise is removed, improving downstream spike sorting.

## What the benchmark and denoising output look like

The frozen input is a 30-kHz, 384-contact Neuropixels 1.0 AP-band recording. Before comparing model
means, we inspect the same raw frames and channels before and after the selected full96 omission0
model. The full-probe view treats probe depth as the vertical axis and time as the horizontal axis;
color is voltage in microvolts. Only a per-channel median is removed for display so stationary
channel offsets do not dominate the color scale. That display operation is not applied in scoring.

The first two panels show that denoising reduces rapid background fluctuation while retaining the
localized spatiotemporal footprint around a deterministically selected GT event from unit 1143. The
close-up uses the same event, frames, and 24 physically nearest contacts, and the peak-channel trace
shows the pre-denoising voltage directly against the model output. This is the exact frozen benchmark
and scored checkpoint, not a separate example dataset.

```{figure} figures/benchmark_raw_denoised_example.png
:label: fig-benchmark-example
**Raw and denoised views of the frozen hybrid benchmark.** **A–B**, the same 30-ms interval across
all 384 contacts ordered by probe depth; the dotted line marks one known event from injected GT unit
1143. **C–D**, a 4-ms close-up on the 24 contacts nearest that unit's raw peak channel. Raw and
denoised panels share a voltage scale within each view. **E**, the corresponding raw and denoised
peak-channel voltage traces. Full96 omission0 is shown because it is the highest-d′ omission0 model,
but it was selected after screening; this figure is a diagnostic view rather than held-out evidence.
```

One event cannot establish waveform preservation. We therefore also compare empirical templates
averaged over the same 100 GT events used by the detection endpoint for four units spanning the raw
separability range. Raw and denoised heatmaps share a voltage scale within each row. The strong unit
is nearly unchanged, whereas the weak examples lose more peak-channel amplitude even when temporal
and spatial shapes remain recognizable. This is the qualitative counterpart of the per-unit
amplitude matrices reported later.

```{figure} figures/unit_attenuation_examples.png
:label: fig-unit-attenuation-examples
**Denoising attenuates weak GT units more strongly.** Rows show units 2143, 1143, 720, and 1129 in
descending raw detectability. The first two columns are raw and full96 omission0 empirical templates
on raw-selected contacts within 120 µm of the raw peak contact, ordered by physical depth; the third
overlays their raw peak-channel waveforms and reports raw→denoised d′ plus the amplitude ratio. Each
template averages the same 100 GT-centered windows used by the detection endpoint, while the reported
d′ retains the complete frozen channel selection. Color limits are shared between raw and denoised
within a unit, not across units, so weak templates remain visible without implying equal absolute voltage.
```

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
training recipes, a matched base96 width/depth/channel-schedule follow-up, and two long-duration trajectories.
All models are trained self-supervised and
scored against injected ground truth in one frozen AP-band hybrid recording. This design isolates
model-output differences on that benchmark, but architecture selection on the same recording means
the conclusions require replication on held-out recordings and with a full spike sorter.

The layer-level model definition is in [Methods](sections/02-methods.md), the model glossary is in
[Appendix A](sections/05-appendix.md), and the evolving study design is documented in the
[versioned analysis plan](reproducibility/regeneration-plan.md).
