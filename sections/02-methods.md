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

## Basic validation before model comparison

Before computing any model ranking, the scoring code verifies that recording and sorting have the
same sampling frequency, one shared segment, and integer GT spike frames inside the recording. The
checkpoint must strict-load against the pinned inference model, and every raw/denoised comparison
uses identical frame centers, channel identities, and native voltage calibration. The AP-band input
is evaluated before common-median referencing or any additional scoring-time filter. A mismatch in
any of these checks stops scoring rather than producing a partial endpoint.

The qualitative export applies the same frozen extraction independently to Full96 omission0,
Full96 omission1, and seed-0 original DI. Each export must reproduce its own committed per-unit SNR
and d′ columns to within `1e-6` before writing figure data. The renderer then requires exact agreement
in event frame, time axes, raw probe and local voltages, contact coordinates, selected template
channels, and raw empirical templates across all three artifacts. The overview and template figures
therefore compare actual scored checkpoints on identical inputs, not separate demonstration
recordings. The illustrated models, units, and event were selected for explanation after the model
screen; the images are diagnostic views, not independent validation evidence. The subsequent d′
score-distribution figure remains a focused explanation of the Full96 omission0 endpoint.

The complete implementation is vendored in
[`code/scoring/detection_metrics.py`](code/scoring/detection_metrics.py), with executable S3 and
waveform drivers in [`code/scoring/run_hybrid_s3.py`](code/scoring/run_hybrid_s3.py) and
[`code/scoring/template_diag.py`](code/scoring/template_diag.py). Focused equation and alignment
tests are in [`code/tests/test_detection_metrics.py`](code/tests/test_detection_metrics.py); exact
commands and every output column are documented in the
[`code/scoring` README](code/scoring/README.md).

## What matched-filter d′ measures

For each unit, the raw empirical template determines the peak channel and up to 24 channels whose
peak-to-peak amplitude is at least 50% of that peak. Each 4-ms multichannel event window is flattened
and projected onto an L2-normalized empirical template. The 100 **hit scores** come from the frozen
GT event times. The 200 **background scores** come from randomly sampled centers, with seed 0, after
excluding centers within one analysis window of any injected GT spike. For hit scores $h$ and
background scores $b$,

$$
d' = \frac{\mu_h-\mu_b}{\sqrt{\left(\sigma_h^2+\sigma_b^2\right)/2}}.
$$

Every hit and background score contributes through its mean and population variance. The endpoint
does **not** count extrema, select maxima, slide a detector over the trace, choose a threshold, or
count threshold crossings. AUC is retained as a threshold-free companion: the probability that a
random hit score exceeds a random background score.

`d′_self` uses the raw empirical template for raw windows and a separately learned denoised
empirical template for denoised windows, analogous to a sorter learning templates in its input
domain. `d′_fixed` projects denoised windows onto the raw empirical template. Both use exactly the
same event and background centers. Because template estimation and hit scoring reuse the same 100
events, absolute d′ is optimistically in-sample. Comparisons are frozen identically; the event-level
cross-fitted sensitivity below tests this optimism for three representative models.

Lower voltage variance alone does not guarantee higher d′. Denoising can attenuate or reshape the
spike, reducing $\mu_h-\mu_b$, and structured residual background can still project onto the learned
template. d′ rises only if separation between the complete hit and background score distributions
increases relative to their pooled spread. The score-distribution figure displays those terms for a
strong and a weak GT unit before and after denoising.

```{figure} figures/dprime_score_distributions.png
:label: fig-dprime-distributions
**d′ uses complete GT-event and background score distributions, not extrema.** Rows show a strong
and a weak injected unit; columns show raw and full96 omission0-denoised domains. Vertical lines are
the two distribution means. Scores are displayed in pooled-SD units, so the horizontal distance
between means is d′. All 100 GT-event scores and 200 spike-excluded background scores are shown;
the same centers enter raw and denoised calculations. The empirical template and hit scores reuse
events, so absolute separation is in-sample optimistic even though model comparisons are frozen.
```

## Template-support sensitivity

The primary endpoint intentionally freezes one filter definition across all 87 scored models, but a
linear matched-filter result can depend on how much time and space enter the template. We therefore
ran a post hoc support sensitivity on Full96 omission0, Full96 omission1, and seed-0 original DI.
Each run reused the endpoint's 100 GT events, 200 background centers, seed 0, and raw/denoised
windows. Temporal support was centered on the GT frame and swept over 0.5, 1, 2, 3, and 4 ms.
Spatial support used the top 1, 2, 4, 8, 16, or 24 channels ranked by raw empirical-template
peak-to-peak amplitude; the frozen 50%-amplitude channel rule was retained as a separate endpoint
cell. Raw and denoised scores always used the same events, crop, and channels, while each domain
learned its own normalized filter.

We report both the frozen in-sample calculation and deterministic two-fold event-level cross-fitting.
For cross-fitting, selected spike times were sorted and assigned to alternating folds; raw channel
ranking and both domain templates were learned only from the 50 training events, then scored on the
other 50 events, with folds averaged within unit before averaging the 10 units. The same 200
background windows enter both folds, preserving paired raw/denoised comparison but making fold
estimates correlated. The fold-specific 50%-amplitude rule is less stable with 50 events than the
frozen 100-event rule (mean 8.8 versus 5.4 channels), so temporal conclusions are also shown at fixed
top-2 support and spatial conclusions at fixed 1 ms. No support was selected as an optimum; the full
prespecified curves and six named cells are reported. This analysis remains post hoc, unwhitened,
and specific to one recording; it tests metric support, not Kilosort performance.

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

## Experiment families

The 87 scored endpoints belong to ten related but non-equivalent ledger families:

| family | model body | training budget | replication | question |
|---|---|---|---|---|
| architecture screen | 21 short-budget configurations (39 endpoints) | ~0.281 M updates (~18 M windows at batch 64) | key configurations 3–5 seeds; most Tier 2 rows one seed | which model changes the fixed-budget endpoint? |
| width/schedule/depth follow-up | R5 `base64_om0`; depth-3 base96 with full 2× growth, a 384-channel cap, 1.5× growth, or √2 growth; depth-2 base96 with full 2× growth; matched schedules use both omission routings | the R5 ~18 M-window budget at batch 256 | nine scored base96 follow-ups; matched R5 seed 0 reference | do base width, deeper channel growth, and U-Net depth explain d′ at matched compute or parameter count? |
| recipe screen | `base64_om0`, R0–R6 | the same ~18 M windows; update count depends on batch | one seed per initial recipe | which tested compound recipe reaches a d′ target fastest? |
| recipe replication | R0/R1/R5 | the same ~18 M windows | two added seeds per recipe, giving three matched seeds including each screen anchor | does the initial recipe ordering repeat across seeds? |
| gradient diagnostic | R8 on the R1 body and recipe | the same ~18 M windows | one trajectory; 12 diagnostic states | when do same-parameter microbatch gradients stop agreeing? |
| integration controls | `base64_om0` with the R1 recipe | the same ~18 M gradient windows; R10 additionally screens 4× candidates | one seed per control | do adaptive accumulation, importance sampling, or effective batch 256 improve detection or only alter compute? |
| NAF control | R13 NAF58 versus R5 DoubleConv64 | the same ~18 M windows | one matched R13 seed; three R5 seeds for context | does a capacity-matched modern temporal block improve detection or runtime? |
| legacy weighting audit | two omission0 bodies with the original weighting path | ~18 M windows | 10 single-seed endpoints | retained for provenance only; the requested L2 objective was silently replaced by Charbonnier in the weighted path |
| corrected weighting screen | `arch_l2_om0`, L2 objective | ~18 M windows | one seed per arm; three unweighted seeds provide context | can center-excluded spike weighting improve amplitude or d′ without waveform distortion? |
| duration diagnostic | `support_all` + L2, om0 vs om1 | 3.30 M updates (~11.8× the short screen) | one seed per arm | do amplitude and d′ stabilize at the same rate? |

The duration diagnostic is not a long-budget validation of the architecture or recipe winner; it
uses a different body. Likewise, the recipe screen does not establish an architecture ordering. The
width/schedule/depth study is an exploratory, single-seed follow-up and is reported separately from the
original 21-configuration architecture screen. The √2 schedule had synthetic compute measurements
but no trained endpoint in the initial follow-up; its omission0 and omission1 runs were subsequently
trained and scored under the same frozen endpoint protocol. A parameter-matched depth test was then
completed with omission0 and omission1 `96→192→384` bodies; both received the same frozen endpoint
scoring. The ten legacy weighting endpoints remain in the
complete inventory and per-unit matrices, but are excluded from weighting-effect conclusions because
their executed objective did not match the requested L2 comparison.

**Gradient diagnostics.** R8 uses the R1 body and recipe and, at 12 scheduled parameter states,
splits one physical batch of 64 into four equal microbatches. It computes each microbatch-mean
gradient without updating parameters, then records pairwise cosine, mean-gradient norm, sample
covariance trace and spectrum, and a finite-K-corrected gradient-noise scale. Because K=4, the
sample-space covariance has rank at most three and individual noise-scale estimates can be unresolved.
These measurements diagnose when gradient disagreement grows; they are not per-example gradients and
do not by themselves define an optimal batch schedule.

**Integration and sampling controls.** R9 keeps the R1 physical batch of 64 and maps a log-EMA of the
measured gradient-noise scale to a power-of-two accumulation target; unresolved measurements retain
the prior target. R10 screens four uniformly sampled candidate batches under `no_grad`, samples one
batch from a uniform/loss-proportional proposal mixture, and applies inverse-probability correction so
the expected gradient remains the original uniform objective. R11 uses physical batch 256 with no
accumulation; R12 uses physical batch 64 with fixed accumulation 4, giving the same effective batch
of 256. All retain the R1 seed, model, Charbonnier objective, learning rate, 3% warmup,
sample-progress schedule, and ~18 M gradient-window budget. They are compared at equal gradient
windows seen, endpoint d′, waveform fidelity, and runtime; R10's 72 M screened candidates are also
reported as compute. Checkpoints within a trajectory are repeated states of one training run, not
independent replicates; the three R1 seeds provide descriptive seed-scale context only.

**Corrected weighting screen.** Seven arms use the same `arch_l2_om0` body, seed 0, L2 objective,
sample budget, and training recipe as the unweighted anchor. Soft magnitude weights use
`1 + λ|neighbour|`; soft and hard position gates use center-excluded spatial neighbours after CAR,
with thresholds of 5× and 8× the robust background scale, respectively. We test magnitude λ = 3,
10, 30; soft-gate λ = 100, 300, 1000; and hard-gate λ = 1000. The weights never use the target
channel's own center sample, preserving the blind-spot objective. These are single-seed endpoint
screens; the three unweighted seeds provide descriptive variation, not an inferential error bar.

**Legacy weighting audit.** Ten earlier weighted endpoints are fully scored and retained in the
87-endpoint master and per-unit tables. Their weighting implementation bypassed the requested L2
path and executed a Charbonnier-weighted objective, so they are not matched-L2 controls. They are
classified separately as `legacy_weighting_screen` and are not mixed into the corrected weighting
figure or causal text.

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

```{figure} figures/architecture_evolution.png
:label: fig-architecture-evolution
:alt: Three-panel schematic of the current two-branch denoiser, its evolution from original DeepInterpolation, and the DoubleConv-to-NAF temporal-stage substitution.
**Architecture and tested evolution.** **A**, the shared R5/R13 topology uses 60 centre-excluded
temporal neighbours and a separate centre-frame `ConvHole1D` branch; pointwise fusion preserves the
self-supervised blind spot. **B**, the principal representation changes from original
DeepInterpolation through `base32` and the replicated `base64_om0` R5 body to the completed
base96 depth-2 body and four depth-3 channel schedules. **C**, the capacity-matched R13 follow-up replaces only the temporal
`DoubleConv1d` stages with 1-D NAF-style gated restoration blocks [@chen2022nafnet]. R13 and the
base96 schedules are exploratory; training-recipe
changes are intentionally excluded from this architecture figure.
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
| matched R5 width/schedule/depth follow-up | `width96`, `width96_cap384`, `width96_g15`, `width96_gsqrt2`, `width96_depth2` | depth-3 schedules 96→192→384→768, 96→192→384→384, 96→144→216→324, or 96→136→192→272; depth-2 schedule 96→192→384 |
| fuse-head width | `fuse256`, `fuse512` | `fuse_channels=256 / 512` |
| temporal-feature width | `tmult8` | `temporal_mult=8` |
| input normalisation | `no_norm` | `norm=none` |
| blind-spot frames | `ho` | `bs_frames=1` (1-frame blind spot) |
| SUPPORT wiring | `support_sd`, `support_all` | `bs_stage=1 bs_dense=1` (+ `bs_multiscale=1`) |
| temporal omission | `omission0` | route t±1 through the temporal U-Net, drop t±31, and reduce the spatial branch from {t−1,t,t+1} to {t} |
| temporal block (exploratory follow-up) | `ib_r13_naf58` | `temporal_block=naf base_channels=58`; capacity-matched to `base64_om0` |
| loss | `*_l2` pairs | `loss=l2` |

The **SUPPORT wiring** options restore three pieces the `fold` reference dropped relative to the
published SUPPORT denoiser [@eom2023support]: dense re-injection of the centre input (`bs_dense`),
staging the temporal feature into the blind-spot branch (`bs_stage`), and a parallel multi-scale
stack (`bs_multiscale`). Across the sweep, capacity and the enlarged `arch` body span
**0.85 M → 12.6 M parameters**.

**Matched R5 width, depth, and channel schedules.** The follow-up holds the R5 batch-256 recipe, sample
budget, blind-spot branch (`bs_channels=64`, `bs_depth=5`), fusion head, loss, and seed fixed. Its
omission0 reference is the 3.15-M-parameter base64 pyramid (64→128→256→512). The base96 full pyramid
uses 96→192→384→768 (6.96 M parameters); the cap-384 and 1.5× schedules use 96→192→384→384
(4.60 M) and 96→144→216→324 (2.23 M), respectively. Thus the 1.5× model has a wider first stage but
fewer total parameters than base64: it tests an efficient schedule, not isolated monotonic growth in
model size. The √2 schedule resolves to 96→136→192→272 and has 1.83 M parameters; both omission
routes completed checkpoint validation and frozen endpoint scoring. Code Ocean `run_time` is used
for end-to-end compute comparisons; it includes capsule overhead as well as training. The completed
depth-2 controls use 96→192→384 and 1.796 / 1.798 M parameters under omission0 / omission1, making
them parameter-matched tests of depth allocation against the depth-3 √2 pair.

## Quantification (identical for every run)

All models are scored by one uniform protocol (full catalog and formulas in
[the versioned analysis plan](reproducibility/regeneration-plan.md), §5). Per-unit metrics are computed on each of the 10
GT units, then averaged.

**Detection (primary).** The event/background matched-filter calculation is defined above and
implemented in the vendored scoring module. `d′_fixed` measures compatibility with the raw empirical
waveform, not agreement with a noise-free injected template. Agreement between self- and
fixed-template rankings indicates that template adaptation is not driving the architecture ordering;
disagreement can reflect either representation adaptation or distortion. The raw-data reference is
**d′ = 4.497**, and **Δd′ = d′_deep − d′_raw** measures the change from denoising under this
surrogate.

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

For the width/schedule/depth follow-up, we also report paired per-unit d′ differences and a descriptive
nonparametric bootstrap that resamples the 10 fixed unit differences 200,000 times. Each comparison
uses a recorded deterministic seed beginning at 20260719. These intervals describe sensitivity to
the particular unit mix; they are not biological confidence intervals, and they do not replace
training-seed replication.

The short-budget screen saved a validation-loss-selected `best_model` and a terminal model. For all
33 available Tier 1/2/original runs with both manifests, the selected checkpoint was the terminal
step, so the architecture table is effectively a common terminal-budget comparison. That equivalence
does not hold generally: in the long om1 trajectory, the validation-best checkpoint has lower d′ than
the final checkpoint. We therefore use d′ trajectories, not reconstruction loss alone, to assess
detection convergence.
