# Results

:::{note} Current state
All Code Ocean training and all 610 HPC scoring jobs underlying the analyses below are complete. Two
post-report width-96 controls (`omission=0/1`) are training and are not included here. The completed
analyses include the 21-configuration architecture screen, six-recipe screen, original-network
reference, R0/R1/R5 recipe replications, R8 gradient diagnostics, four integration and sampling
controls, the capacity-matched NAF control, seven corrected matched-L2 weighting arms, and two
long-duration trajectories. All results use the same AP-band `recording1_3` hybrid benchmark;
the raw reference is **d′ = 4.497**. `results/tables/master_table.csv` contains all 78 completed
endpoint runs with experiment-family and budget labels; `table_coverage.csv` records the sole
exclusion, the intentionally aborted R7 run. The global table is an inventory rather than one causal
ranking. Matched architecture, recipe, integration, NAF, and weighting conclusions use their
family-specific tables and seed context.
:::

## Fixed-budget architecture screen

Twenty-one short-budget architectures are scored in-band — the twenty swept configurations plus the
original DeepInterpolation network (`origdi`) as a published reference. The two `support_all`
duration runs process ~11.8× more updates and are held for the final section. The table is seed-averaged where
replicated and sorted by detection d′, read against the raw-data reference of **d′ = 4.497**:

| config | loss | n | d′_self | d′_fixed | Δ vs raw | amp | fwhm | snr_deep |
|---|---|---|---|---|---|---|---|---|
| **arch** | charb | 1 | **4.409** | 4.437 | −0.088 | 0.871 | 1.020 | 7.81 |
| arch_l2 | L2 | 1 | 4.407 | 4.434 | −0.090 | 0.877 | 1.003 | 7.84 |
| base64 | charb | 3 | 4.382 | 4.410 | −0.115 | 0.880 | 1.009 | 7.70 |
| arch_om0 | charb | 1 | 4.367 | 4.403 | −0.130 | 0.936 | 0.976 | 6.96 |
| base64_l2 | L2 | 1 | 4.366 | 4.398 | −0.131 | 0.880 | 1.003 | 7.70 |
| arch_l2_om0 | L2 | 3 | 4.360 | 4.400 | −0.137 | **0.937** | 0.976 | 7.00 |
| base64_om0 | charb | 1 | 4.359 | 4.397 | −0.138 | 0.934 | 0.976 | 6.91 |
| support_sd | charb | 1 | 4.313 | 4.339 | −0.184 | 0.857 | 1.023 | 7.56 |
| support_all | charb | 1 | 4.312 | 4.334 | −0.185 | 0.864 | 1.003 | 7.57 |
| omission0 | charb | 5 | 4.312 | 4.354 | −0.185 | 0.932 | 0.976 | 6.89 |
| omission0_l2 | L2 | 3 | 4.305 | 4.346 | −0.192 | 0.931 | 0.976 | 6.89 |
| support_all_l2 | L2 | 1 | 4.295 | 4.320 | −0.202 | 0.868 | 1.034 | 7.59 |
| base32_l2 | L2 | 3 | 4.289 | 4.313 | −0.208 | 0.861 | 1.007 | 7.60 |
| no_norm | charb | 1 | 4.284 | 4.310 | −0.213 | 0.856 | 1.023 | 7.55 |
| fuse256_l2 | L2 | 1 | 4.282 | 4.311 | −0.215 | 0.857 | 1.023 | 7.59 |
| base32 | charb | 5 | 4.277 | 4.300 | −0.220 | 0.859 | 1.007 | 7.60 |
| ho | charb | 1 | 4.272 | 4.300 | −0.225 | 0.852 | 1.014 | 7.58 |
| fuse256 | charb | 1 | 4.265 | 4.296 | −0.232 | 0.853 | 1.003 | 7.50 |
| tmult8 | charb | 1 | 4.257 | 4.286 | −0.240 | 0.857 | 1.003 | 7.61 |
| fuse512 | charb | 1 | 4.244 | 4.266 | −0.253 | 0.859 | 1.003 | 7.57 |
| **origdi** *(published ref.)* | charb | 3 | **4.135** | 4.139 | **−0.362** | 0.811 | 1.122 | **8.15** |

(Single-seed Tier-2 rows carry no inferential error bar. Per-config seed spread on the replicated
rows: base32 SD = 0.015, omission0 0.007,
base32_l2 **0.041**, omission0_l2 0.004, base64 0.017. `d′_fixed` tracks `d′_self` throughout — the
architecture ordering is not driven by whether the filter adapts to the denoised template.)

Training is stochastic because of GPU nondeterminism, initialization, and data order, so key
configurations were retrained 3–5 times. Validation reconstruction loss is also not the downstream d′
objective. In the short screen it selected the terminal step in all 33 Tier 1/2 runs with both
manifests; in the long om1 run it did not select the best observed d′ checkpoint. base32's five seeds scatter with
**SD_d′ = 0.015** and **SD_amp = 0.004**. Its ±2-SD interval (~0.03 d′, ~0.01 amplitude) is shown as a
descriptive screening reference, not a confidence interval. Exploratory Welch comparisons are used
only for replicated rows and are not corrected for multiple testing. `base32_l2` has the widest seed
spread (SD = 0.041), so its mean is particularly uncertain.

**Read-out (a): denoising still lowers detectability.** Every configuration — the best
included — sits below the raw d′ of 4.497, from **−0.09** (`arch`) to **−0.36** (`origdi`). Thus every
tested short-budget denoised output reduces the all-unit matched-filter mean on this benchmark. This
does not establish the same effect on other recordings or under a complete spike sorter.

```{figure} figures/f1_dprime_ranking.png
:label: fig-dprime-ranking
**d′ across the 21 short-budget architectures.** Bars are d′ (mean ± 2 seed SD where replicated;
single-seed Tier-2 rows have no bar); base32 (grey) anchors a descriptive 5-seed ±2-SD band, the
original DeepInterpolation network (`origdi`, **crimson**) is the published reference, and the dotted
line is raw data (4.497). The `arch` / `base64` capacity family sits at the top, the fuse-width /
temporal variants at or below the band, and **`origdi` sits far below all of them** — the optimized
architecture has climbed most of the way from the original toward raw. The two 3.30-M-update
`support_all` runs are compared separately in the final duration section.
```

## The modern model package improves detection despite lower template SNR

Anchoring the ranking is the **original DeepInterpolation ephys network** (`origdi`; the faithful
`unet_single_ephys_1024` of [@lecoq2021deepinterpolation] — a temporal-only 2-D U-Net with **no spatial
blind-spot branch**, [Methods](sections/02-methods.md)), trained and scored identically to every other
model. It is the **worst detector in the study — d′ = 4.135 ± 0.010, −0.362 below raw** — with the
**lowest empirical-template amplitude (0.811)**, yet the **highest peak-channel template SNR of any
model (8.15 vs base32's 7.60)**. This does not prove that `origdi` removes the most noise: template SNR
also depends on spike amplitude. It shows that the single-channel SNR ratio does not rank the
multichannel event-separation metric.

Two model-package comparisons close most of that gap at matched training budget:

| step | d′ | amp | weak-unit d′* |
|---|---|---|---|
| `origdi` — original, temporal-only | 4.135 | 0.811 | 1.35 |
| complete modernization → `base32` | 4.277 (+0.142) | 0.859 (+0.048) | 1.56 |
| larger body + omission0 routing → `arch_l2_om0` | 4.360 (+0.225) | 0.937 (+0.126) | 1.71 |

*Descriptive mean over the four units with raw d′ ≤ 2.2. `origdi` and `base32` differ in geometry,
branch structure, and parameterization, so their +0.14 d′ difference cannot be assigned to the spatial
branch alone. The full modern package, followed by the larger omission0 body, reaches +0.23 d′ and
+0.13 empirical-template amplitude relative to `origdi`; the weak-unit subgroup rises by +0.36 d′.
This is evidence for the matched-filter proxy on this benchmark, not yet for sorter-level yield.

Across all 21 short-budget architectures, every template-SNR change is positive (+1.09 to +2.34),
while every d′ change is negative (−0.09 to −0.36). More importantly, the two changes have almost no
rank association (**Spearman ρ = 0.02**; ρ = 0.18 after excluding `origdi`). Template SNR is therefore
useful as a waveform/noise summary, but not as a selection objective for matched-filter detection.

```{figure} figures/f4_snr_vs_dprime.png
:label: fig-snr-dprime
**Peak-channel template SNR does not rank multichannel matched-filter detectability.** All 21
short-budget architectures are shown. Blue marks capacity variants, orange marks omission0
variants, black is base32, red is the original architecture, and grey marks the remaining screen.
SNR is empirical-template peak-to-peak divided by spike-excluded background SD on one channel; d′
uses multichannel temporal event scores. Their architecture-level changes are essentially
uncorrelated.
```

## The tested L2 substitutions are small and inconsistent

Across seven matched bodies, L2-minus-Charbonnier changes range from −0.017 to +0.017 d′ and from
−0.001 to +0.006 amplitude, with no consistent direction:

| body | Δd′ (L2 − Charb.) | Δamp | replication |
|---|---:|---:|---|
| base32 | +0.012 | +0.002 | 5 vs 3 seeds |
| omission0 | −0.007 | −0.000 | 5 vs 3 seeds |
| base64 | −0.017 | −0.001 | 3 vs 1 seed |
| arch | −0.002 | +0.006 | 1 vs 1 seed |
| arch_om0 | −0.007 | +0.001 | 1 vs 3 seeds |
| support_all | −0.017 | +0.004 | 1 vs 1 seed |
| fuse256 | +0.017 | +0.004 | 1 vs 1 seed |

The replicated base32 comparison is uncertain (`base32_l2` SD = 0.041 d′), and most other pairs are
single-seed. The supported conclusion is not that L2 is universally neutral, but that none of the
tested substitutions produces a robust improvement on this screen.

## Capacity leads the all-unit mean, with diminishing returns

Doubling the U-Net base width (`base64`, 32 → 64 channels) is the largest reproducible move on the
base32 body in the **ten-unit mean**: **d′ 4.277 → 4.382, +0.105** (5 vs 3 seeds; exploratory Welch
p = 0.0010), with amplitude 0.859 → 0.880.

Tier 2 adds the two larger bodies. The enlarged **`arch`** (base 64, depth 4, `bs_channels=128`,
`bs_depth=7`) has the highest observed single-run mean, d′ = 4.409, with its L2 twin at 4.407. The
increment over replicated `base64` is only +0.027, however, and neither `arch` row is replicated.
Thus the fixed-budget capacity sequence is monotone but sharply diminishing; `arch` is a promising
screen result, not a demonstrated optimum or a long-budget conclusion.

## The leading intervention depends on which units are averaged

The ten-unit mean obscures the study's stated target: the four units with raw d′ ≤ 2.2. Their
response reverses the simple "capacity versus omission" summary:

| configuration | all-unit d′ | Δ vs base32 | weak-unit d′* | Δ vs base32 | mean amp |
|---|---:|---:|---:|---:|---:|
| base32 | 4.277 | — | 1.562 | — | 0.859 |
| omission0 | 4.312 | +0.035 | **1.710** | **+0.148** | 0.932 |
| base64 | **4.382** | **+0.105** | 1.596 | +0.034 | 0.880 |
| arch | 4.409† | +0.132 | 1.551† | −0.012 | 0.871 |
| arch_l2_om0 | 4.360 | +0.083 | **1.711** | **+0.149** | **0.937** |

*Descriptive subgroup of units 94, 664, 720, and 1129; †single-seed screen. Among replicated rows,
omission0 and arch_l2_om0 reproduce the ~+0.15 weak-unit gain, whereas base64 gives +0.034. Width
improves the all-unit mean substantially, but much of that advantage comes from already-strong units;
the omission0 routing produces the larger change in the weak subgroup and in empirical-template
amplitude. Because omission0 changes temporal offsets and the spatial-branch input together, this
effect cannot be assigned to t±1 alone.
Because the subgroup threshold was chosen during analysis and contains only four units, it is
descriptive rather than a population-level confirmatory test.

The amplitude pattern is not confined to base32 and omission0. Across all 21 short-budget
architectures, the per-model Spearman correlation between empirical-template amplitude and raw d′
ranges from 0.66 to 0.94 (median 0.88). This is consistent with conditional-mean shrinkage: waveforms
that are poorly constrained by surrounding samples are attenuated more. It is not direct evidence
that neighbouring samples are pure noise or that regression-to-the-mean is the only mechanism.

```{figure} figures/f5_amp_vs_quality.png
:label: fig-amp-quality
**Amplitude preservation across the complete short-budget architecture screen.** **A**, all 21
architectures (grey points) with the per-unit median and 10th–90th percentile across models (black).
The unit-quality gradient persists across the full screen. **B**, the matched base32–omission0
compound contrast: moving t±1 into the temporal branch while changing the spatial input and outer
context raises amplitude primarily for weak units. Values are denoised/raw empirical
template peak-to-peak ratios, not amplitudes relative to a noise-free injected waveform.
```

Combining the two design choices yields a useful compromise. `base64_om0` and `arch_om0` preserve
amplitude near 0.935 and weak-unit d′ near 1.71 while retaining an all-unit d′ near 4.36. Relative to
their t±1-hidden twins, however, their all-unit means are lower (base64: −0.023; arch: −0.042), again
because gains on weak units coexist with losses on some strong units. `arch_l2_om0` is therefore a
balanced candidate on this benchmark, not a configuration that dominates every unit or metric.

## Blind-spot wiring, fuse width, and temporal variants

The remaining Tier-2 levers change wiring rather than raw capacity. Each is a single-seed screen;
their distance from the base32 mean is shown descriptively against base32's ±2-seed-SD reference:

| lever | config | d′ | amp | position relative to base32 reference |
|---|---|---|---|---|
| bigger / denser blind-spot branch | support_sd, support_all | 4.313, 4.312 | 0.857, 0.864 | just above |
| L2 on that wiring | support_all_l2 | 4.295 | 0.868 | inside |
| widest fusion | fuse256, fuse512 | 4.265, 4.244 | 0.853, 0.859 | inside / just below |
| deeper temporal hand-off | tmult8 | 4.257 | 0.857 | inside |
| no input normalisation | no_norm | 4.284 | 0.856 | inside |
| 1-frame blind spot, omission on | ho | 4.272 | 0.852 | inside |

The `support_*` observations sit just above the upper edge of that reference; fuse256, tmult8,
no_norm, and ho lie inside it, while fuse512 is just below. All leave amplitude near 0.86. These rows
are unreplicated, so the two `support_*` observations are leads rather than confirmed gains.
`fuse512` is the lowest modern architecture in the
short screen, but `origdi` is lower overall. These single runs provide no evidence that wider fusion,
the tested temporal hand-off, or normalization removal improves the endpoint.

## Training-efficiency recipe screen and replication

A separate six-run screen uses `base64_om0` as a fixed candidate body and processes the same ~18.0 M
training windows under different compound recipes. The initial screen has one seed per recipe and 12
log-spaced checkpoints. Checkpoint times were not recorded directly; GPU-hours are estimated by
apportioning total runtime by checkpoint step and linearly interpolating threshold crossings.

| recipe | final d′ | estimated GPU-h to d′ = 4.30 | estimated GPU-h to d′ = 4.35 |
|---|---|---|---|
| R0 AdamW / cosine / lr 1e-3 | 4.350 | 1.44 h | 2.73 h |
| R1 +3% warmup | 4.365 | 0.65 h | 2.22 h |
| R2 one-cycle (lr 3e-3) | 4.319 | 2.18 h | — |
| R3 AdamW lr 2e-3, β₂ 0.98, wd 0.05 | 4.320 | 1.96 h | — |
| R4 tested Lion setting | 4.219 | — | — |
| **R5 batch 256, lr 2e-3, 5% warmup** | **4.358** | **0.33 h** | **2.42 h** |

R5 has the lowest estimated time to d′ = 4.30 among these six single runs: 0.33 versus 1.44 GPU-h
for R0. The nominal 4.4× ratio is not an isolated batch-size effect because R5 also changes learning
rate and warmup, and the checkpoint times are inferred. R0 starts at full learning rate; R1 and R5
warm up. Their apparent convergence near 0.1 GPU-h overlaps the end of warmup, while R0 has no
checkpoint between ~0.089 and ~0.279 h, so the curves do not localize a shared task transition.

The completed matched-seed replications separate recipe-level consistency from the original
one-seed ordering. R0, R1, and R5 each have seeds 0–2 and 25 scored states per new replicate
(24 scheduled checkpoints plus the validation-selected endpoint). All runs process ~18.0 M windows;
the new replicates record checkpoint telemetry directly, while the original seed's window count is
its deterministic update count × physical batch.

| recipe | endpoint d′, mean ± seed SD | paired Δd′ vs R0 | paired seeds improved | median windows to d′ = 4.30 | d′ = 4.35 reached / median windows |
|---|---|---|---|---|---|
| R0 baseline | 4.361 ± 0.011 | — | — | 5.38 M | 3/3 / 13.99 M |
| R1 +3% warmup | 4.358 ± 0.013 | −0.0031 | 1/3 | 5.14 M | 2/3 / 13.68 M* |
| **R5 batch 256, lr 2e-3, 5% warmup** | **4.365 ± 0.008** | **+0.0043** | **3/3** | **2.25 M** | **3/3 / 14.90 M** |

\*Median among the two R1 seeds that cross 4.35.

Warmup alone is not a reproducible endpoint improvement: R1 gains in one matched seed and loses in
two. R5 gives a smaller but directionally consistent endpoint change, with paired differences of
+0.0075, +0.0034, and +0.0020 d′. The exact two-sided seed sign-flip p-value is 0.25, the smallest
possible value with three pairs, so this is not a confirmatory significance result. R5's mean effect
is positive for 8/10 units after averaging seeds, but only 18/30 seed–unit cells are positive.

R5 reaches d′ = 4.30 with 58% fewer median windows than R0, but one matched R5 seed is slower at that
threshold and its median crossing at d′ = 4.35 is slightly later. The evidence therefore supports a
mid-training efficiency lead, not a uniform acceleration at every target. At the endpoint, R5 moves
the amplitude ratio from 0.938 to 0.940, leaves temporal and spatial cosine effectively unchanged,
and changes FWHM ratio from 0.990 to 0.976, consistent with mild additional temporal narrowing. R5
remains a compound recipe, so these replications do not attribute its effect to physical batch alone.
The R4 result pertains only to its tested Lion hyperparameters, not to the optimizer family.

```{figure} figures/recipe_replication.png
:label: fig-recipe-replication
**Matched-seed recipe replication.** Individual seed trajectories and their recipe means are shown
against training windows (left); matched endpoint seeds are connected on the right. R5 improves the
endpoint in all three seed pairs, but the effect is small relative to seed spread. R1 warmup does not
replicate as an endpoint gain.
```

As a single-seed body-transfer check, applying R5 to `arch_l2_om0` reaches **d′ = 4.374** with
empirical-template amplitude **0.935**. This is close to R5 on `base64_om0` (4.358 / 0.940) and to the
three-seed short-screen `arch_l2_om0` endpoint (4.360 / 0.937). The observation argues against a
large body-specific ceiling loss, but it is neither a replicated recipe comparison nor an isolated
architecture effect.

```{figure} figures/recipe_convergence.png
:label: fig-recipe-convergence
**Single-seed compound-recipe screen.** d′ versus windows seen (left) and estimated GPU-hours (right)
on the fixed `base64_om0` body. R5 has the lowest interpolated time to 4.30; the matched-seed result
above supersedes this one-seed endpoint ordering, while batch-only controls remain required for
causal attribution.
```

```{figure} figures/recipe_convergence_loglog.png
:label: fig-recipe-convergence-loglog
**The same recipe screen on log–log deficit axes.** Deficit is raw d′ − denoised d′ (lower is better).
R0 descends earliest; R1 and R5 finish close together. GPU-hours are step-proportional
estimates, and the sparse checkpoints do not resolve a common transition near 0.1 GPU-h.
```

## Gradient measurements motivate late-integration controls

R8 repeats the R1 recipe while measuring four equal microbatch gradients at the same parameter state
at 12 points during training. Early microbatch gradients are strongly aligned (mean pairwise cosine
~0.90). Alignment declines with training and is near zero at several late checkpoints, with some
negative pairs. Estimated gradient-noise scale is below six early, but exceeds the physical batch of
64 at several late measurements (for example ~567 at 6.0 M windows and >10⁴ at 13.2 M windows).

The estimates are not monotone and are unresolved at three checkpoints because the finite-K noise
term is as large as the observed mean-gradient norm. With K=4, the sample covariance also has rank at
most three. R8's scored endpoint is d′ = 4.383, but it uses the same seed as the original R1 run and
adds diagnostic probes, so it is not an independent recipe replicate. These diagnostics support
testing late larger-batch integration, but they do not identify a precise schedule and do not justify
a parameter-space preconditioner. Adaptive, fixed-effective-batch, physical-batch, and
objective-preserving sampling controls are reported below.

```{figure} figures/ib_r8_gradstats_gradient_diagnostics.png
:label: fig-gradient-diagnostics
**Same-parameter microbatch gradient diagnostics for R8.** The estimated noise scale rises above the
physical batch at several late checkpoints, while mean pairwise cosine falls from ~0.9 toward zero.
Missing noise-scale points indicate unresolved signal after finite-K correction. The covariance
spectrum is limited to at most three nonzero sample-space components because only four microbatches
were measured; it is not evidence for a low-rank parameter-space optimizer.
```

## Integration controls alter compute and update count, not endpoint detection

R9–R12 use the same seed-0 body, objective, learning rate, warmup, and ~18 M gradient-window budget
as R1. R9 changes the effective-batch schedule through adaptive accumulation; R10 screens four
candidate batches per update with objective-preserving importance sampling; R11 changes the physical
batch from 64 to 256; and R12 retains physical batch 64 but accumulates four batches per update.

| method | endpoint d′ | Δd′ vs matched R1 | optimizer updates | update reduction | Code Ocean runtime |
|---|---:|---:|---:|---:|---:|
| R1 warmup, batch 64 | 4.3651 | — | 281,244 | — | 2.80 h |
| R9 adaptive accumulation | 4.3656 | +0.0005 | 175,778 | 37.5% | 2.70 h |
| R10 importance sampling | 4.3651 | −0.0000 | 281,244 | 0% | 6.13 h |
| R11 physical batch 256 | 4.3446 | −0.0205 | 70,308 | 75.0% | 2.46 h |
| R12 accumulated batch 256 | 4.3472 | −0.0179 | 70,311 | 75.0% | 2.66 h |

R9 holds effective batch 64 through 9.0 M windows, then uses 128 to 10.8 M, 512 to 14.4 M, and 256
for the remainder. It preserves the matched R1 endpoint while removing 37.5% of optimizer updates,
but serial accumulation still processes every physical microbatch and reduces total Code Ocean time
by only 3.4%. Its apparent early crossing is not durable: it first interpolates through d′ = 4.30 at
2.94 M windows, drops to 4.278 at 6.05 M, and first remains above 4.30 at a scored state after 10.43 M
windows, versus 5.75 M for R1.

R10 is endpoint-neutral relative to matched R1 (Δd′ = −0.00003; 5/10 units improve), but screening
four candidates raises runtime from 2.80 to 6.13 h. Thus the corrected inverse-probability estimator
does not turn candidate prioritization into a benchmark gain at this budget. R11 and R12 are also
close despite their four-fold difference in physical batch: R12 exceeds R11 by only +0.0026 mean
d′, has a median paired unit change of −0.0026, and improves 4/10 units. Their common effective batch
and near-identical update count, rather than physical batch itself, therefore best explain their
similar lower endpoints in this single-seed comparison.

Endpoint means hide opposing unit effects. R9 improves only 2/10 units relative to matched R1
(median Δd′ = −0.0055): unit 2143 gains +0.150 while unit 793 loses −0.098. R11 improves 3/10 units
(median −0.0050), with its mean loss dominated by unit 793 (−0.147). All four control endpoints lie
inside the observed three-seed R1 range (4.3426–4.3662), so none establishes a method effect in
expectation.

```{figure} figures/integration_controls.png
:label: fig-integration-controls
**Integration and objective-preserving sampling controls.** **A**, d′ trajectories against equal
gradient windows seen; faint grey lines show the three R1 seeds. **B**, every single-run control
endpoint lies within the observed R1 seed range. **C**, paired unit effects show opposing changes
hidden by the means. **D**, runtime versus endpoint d′ exposes the extra cost of R10 candidate
screening and the close R11/R12 outcomes at effective batch 256.
```

## Capacity-matched NAF blocks do not improve this benchmark

R13 replaces only the R5 temporal DoubleConv stages with 1-D NAF-style blocks and narrows the base
width to 58, yielding 3,162,950 trainable parameters versus 3,149,704 for R5 (+0.42%). The R5
training recipe, blind-spot branch, fusion head, objective, seed, and sample budget are unchanged.
R13 reaches d′ = 4.3352, which is −0.0223 relative to matched R5 seed 0 and below the complete R5
three-seed range of 4.3575–4.3730. It improves only 2/10 paired units.

The negative detection result is not predicted by the training objective. Final normalized
validation loss differs from R5 seed 0 by only +0.00000285, while the NAF run takes 3.43 h versus
2.44 h (+41%). This single-seed control therefore provides no evidence that importing a contemporary
image-restoration block improves this blind-spot temporal denoiser; it also demonstrates that tied
reconstruction loss does not guarantee tied spike detectability.

```{figure} figures/naf_control.png
:label: fig-naf-control
**Capacity-matched NAF temporal-block control.** **A**, checkpoint d′ versus equal training windows
for matched seed-0 R5 and R13, with the other R5 seeds in grey. **B**, the R13 endpoint lies below the
observed three-seed R5 range. **C**, only two paired units improve. **D**, validation losses converge
to nearly the same value, but R13 trains 41% longer.
```

## Strong spike weighting harms detection despite amplitude gains

The corrected matched-L2 screen compares seven center-excluded weighting rules with unweighted
`arch_l2_om0` seed 0. Small magnitude weights raise empirical-template amplitude, but only λ = 3
raises endpoint d′; all stronger rules reduce it.

| weighting arm | endpoint d′ | Δd′ vs unweighted seed 0 | amplitude ratio |
|---|---:|---:|---:|
| unweighted | 4.3670 | — | 0.9350 |
| soft magnitude λ = 3 | 4.3725 | +0.0055 | 0.9397 |
| soft magnitude λ = 10 | 4.3521 | −0.0150 | 0.9413 |
| soft magnitude λ = 30 | 4.3503 | −0.0167 | 0.9402 |
| soft gate λ = 100 | 4.3437 | −0.0233 | 0.9411 |
| soft gate λ = 300 | 4.1046 | −0.2624 | 0.9437 |
| soft gate λ = 1000 | 4.2294 | −0.1376 | 0.9414 |
| hard gate λ = 1000 | 4.2033 | −0.1638 | 0.9248 |

Soft λ = 3 improves 6/10 units and amplitude by +0.0047, but its +0.0055 d′ change remains inside
the unweighted three-seed range (4.3387–4.3737; SD 0.0186). It is therefore an unreplicated lead,
not a selected recipe. Strong gates decouple amplitude from fidelity and detection: λ = 300 raises
amplitude by +0.0087 while temporal and spatial template cosine fall to 0.883 and 0.948, and unit 337
loses 2.66 d′. The hard λ = 1000 arm improves only 1/10 units and also lowers amplitude.

```{figure} figures/weighting_controls.png
:label: fig-weighting-controls
**Corrected matched-L2 spike-weighting endpoint screen.** **A**, endpoint d′ with the observed
unweighted three-seed range shaded. **B**, modest amplitude increases do not predict detection.
**C**, strong soft gates distort temporal and spatial templates. **D**, unit-level d′ changes show
that the λ = 3 lead is distributed but small, whereas high weights produce large losses.
```

## Do the two omission trajectories stabilize with longer training?

Two single-seed `support_all` + L2 runs extend the omission comparison to 3.30 M updates, ~11.8× the
short-screen update budget, with 12 log-spaced checkpoints. They are duration diagnostics for this
body, not long-budget validations of `base64`, `arch`, or the recipe winner.

- **Empirical-template amplitude stabilizes early in both trajectories** — changing by −0.016 (om0)
  and +0.027 (om1) across the final 2.4 decades of updates.
- **All-unit d′ remains duration-sensitive.** From 14 k to 3.3 M updates, d′ rises by +0.11 for om0
  and +0.30 for om1. The last om1 interval (844 k → 3.3 M) adds another +0.11, so om1 is not visibly
  flat at the final checkpoint.

These trajectories demonstrate that a reconstruction-loss endpoint need not imply a stable detection
metric and that fixed-budget screens can mix optimization speed with endpoint quality. They do not
show that every screened architecture is undertrained or predict how the capacity and recipe winners
would rank after 3.3 M updates.

At the final sampled checkpoint the two all-unit means happen to be equal (4.361), while amplitude
remains separated (0.931 om0 versus 0.870 om1). Because om1 is still rising, equality at that one point
does not establish equal asymptotes or that omission affects only convergence speed. The om1
validation-best checkpoint (d′ 4.275) is also below its final checkpoint (4.361), showing directly
that validation-loss selection can miss the best observed detection checkpoint on a long run.

```{figure} figures/f8_trajectory.png
:label: fig-trajectory
**Long-duration `support_all` omission diagnostic.** d′ (left) and empirical-template amplitude
(right) versus updates for one om0 and one om1 run; dotted line is raw d′. Amplitude stabilizes much
earlier than d′, and om1 is still rising at 3.3 M. Transfer of this behavior to the capacity and
recipe candidates is untested.
```
