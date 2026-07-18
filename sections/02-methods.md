# Methods

## Frozen hybrid benchmark

Every model is scored on one fixed benchmark built with the **hybrid ground-truth** approach
[@buccino2020spikeinterface]: a real Neuropixels 1.0 recording (`ecephys_681532`, ProbeC) into which
**10 ground-truth units** were injected at known event times. Detection is evaluated without running
a spike sorter; waveform diagnostics compare empirical spike-triggered templates in raw and denoised
domains rather than using a noise-free injected template. Every model uses the same units and
`seed=0` extraction: up to 100 spikes/unit plus 200 spike-excluded background windows for d′, and up
to 200 spikes/unit for waveform diagnostics. Exact asset paths are in
[Data & compute provenance](data/provenance.md).

Fixing the extraction removes evaluation-sampling noise from model comparisons. It does not provide
external validation: architectures and recipes were selected iteratively using this same recording
and unit set. Conclusions are therefore conditional on this benchmark until repeated on held-out
sessions.

## The in-domain rule

DeepInterpolation is a self-supervised denoiser, so it must be evaluated in the band it is deployed
in: a model trained on one frequency content and applied to another runs outside its training domain,
and its behaviour there need not match. Because spike sorting operates on the high-passed **AP band**,
we enforce a single rule throughout:

> **Train and evaluate in the same band, on the same recording the model is deployed on**
> (`681532` ProbeC `recording1_3`, AP-band).

This is legitimate because DeepInterpolation is self-supervised (blind-spot): ground-truth spike
labels are used only for *scoring*, never for training. Per-recording train = evaluate is the intended
deployment, not label leakage.

## Three experiment families

The study contains three related but non-equivalent experiments:

| family | model body | training budget | replication | question |
|---|---|---|---|---|
| architecture screen | 21 short-budget configurations | ~0.281 M updates (~18 M windows at batch 64) | key configurations 3–5 seeds; most Tier 2 rows one seed | which model changes the fixed-budget endpoint? |
| recipe screen | `base64_om0` | the same ~18 M windows; update count depends on batch | one seed in the initial screen; R0/R1/R5 completed at three matched seeds | which tested compound recipe reaches a d′ target fastest? |
| duration diagnostic | `support_all` + L2, om0 vs om1 | 3.30 M updates (~11.8× the short screen) | one seed per arm | do amplitude and d′ stabilize at the same rate? |

The duration diagnostic is not a long-budget validation of the architecture or recipe winner; it
uses a different body. Likewise, the recipe screen does not establish an architecture ordering.

**Gradient diagnostics.** R8 uses the R1 body and recipe and, at 12 scheduled parameter states,
splits one physical batch of 64 into four equal microbatches. It computes each microbatch-mean
gradient without updating parameters, then records pairwise cosine, mean-gradient norm, sample
covariance trace and spectrum, and a finite-K-corrected gradient-noise scale. Because K=4, the
sample-space covariance has rank at most three and individual noise-scale estimates can be unresolved.
These measurements diagnose when gradient disagreement grows; they are not per-example gradients and
do not by themselves define an optimal batch schedule.

## Architecture and the swept variants

**The `base32` reference, layer by layer.** The input `(B, 63, 384)` (63 frames × 384 channels) is
scattered onto the 192 × 4 probe grid and split into the two branches:

| component | setting |
|---|---|
| geometry | `fold` — 4 probe columns folded into features; 1-D U-Net along the 192 depth rows |
| temporal window | ±30 frames; `omission=1` hides the target and t±1, so 60 neighbour frames are used |
| temporal U-Net | `base_channels=32`, `depth=3` (32 → 64 → 128 → 256 bottleneck, then decode with skips) |
| spatial blind-spot | `bs_channels=64`, `bs_depth=5` dilated `ConvHole1D` (centre tap zeroed) over the `bs_frames=3` centre frames |
| fuse head | pointwise 1×1, `fuse_channels=64` (blind-spot-safe merge of the two branches) |
| loss | Charbonnier |
| size | ~0.85 M parameters (U-Net ≈ 87%) |

**Why `fold`.** A Neuropixels 1.0 probe is a long, narrow sensor: its 384 channels sit on a
~192-row-deep × 4-column-wide grid, and a spike appears on a small cluster of *vertically* adjacent
channels — so the informative spatial axis is **depth**, not the 4-wide axis. A full 2-D U-Net over
the (192 × 4) grid would spend most of its convolutions on the width dimension, where there is little
to learn. The `fold` geometry instead **folds the 4 width columns into the feature axis** and runs a
**1-D U-Net along probe depth only**: every depth row carries its 4 columns as 4× the feature maps, so
the network stays fully geometry-aware (no channel is discarded) while convolving along a single axis.
In our geometry search this matched the accuracy of the 2-D grid model at a fraction of the cost,
which is why every swept variant is built on the `fold` body. Two alternative geometries are kept as
controls: `1d`, which orders channels by index and ignores the grid, and `2d` / `orig`, the full
probe-grid 2-D U-Net — the latter being the original DeepInterpolation architecture (the `origdi`
baseline).

```{mermaid}
flowchart TD
    IN["Input context<br/>(B, 63, 384)"] --> SC["grid.scatter<br/>(B, 63, 192, 4)<br/>384 ch → 192×4 grid"]
    SC --> SPLIT{"split frames"}
    SPLIT -->|"60 neighbour frames"| FN["fold → (B, 240, 192)<br/>60 frames × 4 cols"]
    SPLIT -->|"3 centre frames {t-1,t,t+1}"| FC["fold → (B, 12, 192)<br/>3 frames × 4 cols"]
    subgraph UNET["TEMPORAL U-Net — centre + t±1 EXCLUDED — conv along DEPTH (H=192)"]
        FN --> ST["stem DoubleConv1d<br/>240→32, k3"]
        ST --> D1["Down1 pool/2 · 32→64 @H=96"]
        D1 --> D2["Down2 pool/2 · 64→128 @H=48"]
        D2 --> D3["Down3 pool/2 — bottleneck<br/>128→256 @H=24"]
        D3 --> U3["Up3 →128 @H=48 (+skip)"]
        U3 --> U2["Up2 →64 @H=96 (+skip)"]
        U2 --> U1["Up1 →32 @H=192 (+skip)"]
        U1 --> UH["head Conv1d 32→4, k1"]
    end
    UH --> UO["u : (B, 4, 192)"]
    subgraph BS["BLIND-SPOT branch — centre frame — dilated HOLE-convs (centre tap zeroed)"]
        FC --> H1["ConvHole1D k3 d=1<br/>12→64 · GELU"]
        H1 --> H2["ConvHole1D k3 d=2<br/>64→64 · GELU"]
        H2 --> H3["ConvHole1D k3 d=4"]
        H3 --> H4["ConvHole1D k3 d=8"]
        H4 --> H5["ConvHole1D k3 d=16"]
    end
    H5 --> BO["b : (B, 64, 192)<br/>±31 rows, own row EXCLUDED"]
    UO --> FUSE["FUSE — pointwise 1×1 only<br/>concat 4+64=68 → 68→64→64→4 (GELU)"]
    BO --> FUSE
    FUSE --> Y["y : (B, 4, 192)"]
    Y --> UF["unfold + grid.gather"]
    UF --> OUT["Denoised centre<br/>(B, 1, 384)"]
```

**The two-branch `base32` (`FoldDeepInterp1D`) denoiser.** The neighbour frames — with the target *and*
its immediate t±1 neighbours excluded — drive the **temporal U-Net** along probe depth; the three
centre frames drive the **blind-spot branch** of five dilated `ConvHole1D` layers whose centre kernel
tap is forced to zero (the "holes"), so a channel's prediction never uses its own value. A
pointwise-only (1×1) fuse head merges the two branches, which keeps the blind spot intact.

The name `omission0` is shorthand for a compound routing change, not the simple addition of two
frames. In base32 (`omission=1`, `bs_frames=3`), the temporal U-Net receives t−31…t−2 and t+2…t+31,
while t−1, t, and t+1 enter only the spatial hole-convolution branch. In `omission0`, the temporal
U-Net instead receives t−30…t−1 and t+1…t+30, and the spatial branch receives only t. Thus the
comparison moves t±1 into the temporal branch, removes t±31, changes spatial-branch input, and reduces
total input frames from 63 to 61. Effects cannot be attributed to t±1 visibility alone.

**How each swept variant is built.** Most screen variants change one intended axis of this reference;
explicit combination rows test whether selected effects stack. All runs are enumerated in the
[versioned analysis plan](reproducibility/regeneration-plan.md):

| axis | variant(s) | change (override) |
|---|---|---|
| capacity (U-Net width) | `base64` | `base_channels=64` |
| capacity (both branches) | `arch` | `base_channels=64 depth=4 bs_channels=128 bs_depth=7` (~12.6 M params) |
| fuse-head width | `fuse256`, `fuse512` | `fuse_channels=256 / 512` |
| temporal-feature width | `tmult8` | `temporal_mult=8` |
| input normalisation | `no_norm` | `norm=none` |
| blind-spot frames | `ho` | `bs_frames=1` (1-frame blind spot) |
| SUPPORT wiring | `support_sd`, `support_all` | `bs_stage=1 bs_dense=1` (+ `bs_multiscale=1`) |
| temporal omission | `omission0` | route t±1 through the temporal U-Net, drop t±31, and reduce the spatial branch from {t−1,t,t+1} to {t} |
| loss | `*_l2` pairs | `loss=l2` |

The **SUPPORT wiring** options restore three pieces the `fold` reference dropped relative to the
published SUPPORT denoiser [@eom2023support]: dense re-injection of the centre input (`bs_dense`),
staging the temporal feature into the blind-spot branch (`bs_stage`), and a parallel multi-scale
stack (`bs_multiscale`). Across the sweep, capacity and the enlarged `arch` body span
**0.85 M → 12.6 M parameters**.

## Quantification (identical for every run)

All models are scored by one uniform protocol (full catalog and formulas in
[the versioned analysis plan](reproducibility/regeneration-plan.md), §5). Per-unit metrics are computed on each of the 10
GT units, then averaged.

**Detection (primary).** For each unit, up to 100 GT-centered event windows and 200 sampled
spike-excluded background windows are projected onto normalized empirical templates; d′ is the
standardized separation between event and background projection scores. This is a GT-time
event-versus-background surrogate, not a continuously sliding detector. `d′_self` uses a denoised-domain
template, analogous to an adaptive sorter, while `d′_fixed` scores denoised windows with the empirical
raw-domain template. The event windows used to estimate each template are also used as hit windows,
so absolute d′ is optimistically in-sample; the identical procedure is used for all model comparisons.
`d′_fixed` measures compatibility with the raw waveform, not agreement with a noise-free injected
template. Agreement between rankings indicates that template adaptation is not driving the
architecture ordering; disagreement can reflect either representation adaptation or distortion. The
raw-data reference is **d′ = 4.497**, and **Δd′ = d′_deep − d′_raw** measures the change from
denoising under this surrogate.

**Waveform and SNR metrics.** `amp_ratio` is denoised-template ÷ raw-template peak-to-peak amplitude
on the empirical raw peak channel; `fwhm_ratio` is the corresponding trough-width ratio;
`temporal_cos` / `spatial_cos` compare rank-1 temporal shape and spatial footprint. `snr_deep` is the
denoised empirical-template peak-to-peak amplitude divided by the standard deviation of denoised,
spike-excluded background windows on that single channel. It combines amplitude preservation and
background variance and is not a direct measure of "noise removed." In contrast, d′ separates
multichannel temporal matched-filter scores at spike and background events.

**Per-unit × per-model resolution.** Both amplitude and detection are reported as matrices — rows =
the 10 units sorted by baseline separability, columns = every model — so an intervention's effect is
read across the whole unit population, not just at the 10-unit mean (appendix
[Appendix B/C](sections/05-appendix.md)).

## Replication, checkpoint choice, and descriptive uncertainty

Training is stochastic because of initialization, data order, and GPU nondeterminism. Key
configurations were therefore retrained across **3–5 seeds**. We report means and seed SDs; the
base32 ±2-SD interval (d′ SD 0.015; amplitude SD 0.004) is used as a descriptive screening reference,
not as a confidence interval or an electrophysiological noise floor. Welch tests are exploratory,
unadjusted comparisons among replicated configurations; single-seed Tier 2 rows carry no inferential
error bar.

The recipe replication pairs R0, R1, and R5 by seed index and reports seed-level endpoint
differences, target crossings versus windows seen, and an exact two-sided sign-flip test. With only
three paired seeds, the smallest attainable two-sided sign-flip p-value is 0.25; these comparisons
are therefore directional effect estimates, not confirmatory tests. The ten benchmark units provide
paired within-model resolution but are not independent training replicates.

The short-budget screen saved a validation-loss-selected `best_model` and a terminal model. For all
33 available Tier 1/2/original runs with both manifests, the selected checkpoint was the terminal
step, so the architecture table is effectively a common terminal-budget comparison. That equivalence
does not hold generally: in the long om1 trajectory, the validation-best checkpoint has lower d′ than
the final checkpoint. We therefore use d′ trajectories, not reconstruction loss alone, to assess
detection convergence.
