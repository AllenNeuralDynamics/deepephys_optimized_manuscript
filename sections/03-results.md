# Results

:::{note} Current state
All training and endpoint scoring underlying the 89 completed analyses below are complete. The two
matched √2 channel-schedule runs added after the coverage audit are now checkpoint-validated and
scored. The matched depth-2 base96 controls added afterward are also checkpoint-validated and
scored. The completed analyses include the 21-configuration architecture screen, the nine-run matched R5
width/channel-schedule/depth follow-up, six-recipe screen, original-network reference, R0/R1/R5 recipe
replications, R8 gradient diagnostics, four integration and sampling controls, the capacity-matched
NAF control, ten confounded legacy weighting audit endpoints, seven corrected matched-L2 weighting
arms, two legacy duration trajectories, and two Full96 duration trajectories. All
results use the same AP-band `recording1_3` hybrid benchmark; the raw reference is **d′ = 4.497**.
`results/tables/master_table.csv` contains all 89 completed endpoint runs with experiment-family and
budget labels; `table_coverage.csv` records the intentionally aborted R7 run as the sole row without
an endpoint. The global table is an inventory rather than one causal
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

**Read-out (a): denoising lowers the frozen 4-ms endpoint.** Every original-screen configuration sits
below the raw d′ of 4.497, from **−0.088** (`arch`) to **−0.362** (`origdi`). All nine completed width/schedule/depth
follow-ups also remain below raw; the closest is full base96 omission1 at **−0.083**. Thus every
tested short-budget denoised output reduces this particular all-unit matched-filter mean on this
benchmark. The support-sensitivity analysis below shows that the aggregate direction is not invariant
to filter duration and channel count. This
direction is not unique to the pooled-variance d′ formula: for full96 omission0, the threshold-free
mean AUC also falls from 0.9612 to 0.9536, with 8/10 units lower. Neither metric establishes the same
effect on other recordings or under a complete spike sorter.

```{figure} figures/f1_dprime_ranking.png
:label: fig-dprime-ranking
**d′ across the original architecture screen and matched R5 follow-up on one ranked axis.** The 21
short-budget architectures and ten matched-R5 endpoints are sorted together for direct visual
comparison. Original-screen bars show mean ± 2 seed SD where replicated; base32 (grey) anchors a
descriptive 5-seed ±2-SD band, `origdi` (crimson) is the published reference, and the dotted line is
raw data (4.497). Outlined bars are the matched-R5 follow-up, printed with their single-seed endpoint
means; hatching marks omission1. Full base96 has the highest observed all-unit mean, cap384 is
intermediate, growth1.5 and depth2 are near their matched base64 R5 reference, and √2 omission0 is
lower. The shared ordering is for
comparison, not evidence that the single-seed follow-up belongs to the original seed-averaged screen.
The selected Full96 omission routes are compared over a separate 54.0-M-window trajectory in the
final duration section.
```

## The aggregate d′ deficit depends on template support, but weak-unit losses do not

The frozen endpoint uses a 4-ms window and a raw-template 50%-amplitude channel rule (2–12 channels,
median 5). At fixed top-2 support, shortening the filter from 4 to 1 ms changes the cross-fitted mean
denoised-minus-raw d′ from **−0.043 to +0.016** for Full96 omission0 and from **−0.036 to +0.090**
for Full96 omission1. These are not reversals caused by making both domains unusable: at 1 ms/top-2,
raw d′ is 4.543, versus 4.559 for omission0 and 4.633 for omission1. The original DI gap narrows but
remains negative (**−0.322 to −0.170**; denoised d′ 4.372). The in-sample estimator gives the same
qualitative result at 1 ms/top-2: gaps of −0.004, +0.054, and −0.242, respectively.

Space matters too. At fixed 1 ms, widening the cross-fitted filter from two to four raw-ranked
channels changes the Full96 gaps from +0.016 to −0.046 and from +0.090 to −0.013. Thus the frozen
4-ms multichannel endpoint overstates the **aggregate** Full96 disadvantage relative to a compact
linear filter. It does not establish that the larger support is intrinsically wrong for a sorter;
whitening, temporal search, template competition, and clustering are absent here.

Most importantly, the aggregate reversal is driven by stronger units. At the cross-fitted frozen
endpoint, the four post hoc weak units have mean gaps of −0.061 (omission0) and −0.097 (omission1).
At 1 ms/top-2 those weak-unit gaps become **more negative**, −0.167 and −0.291, while the other six
units move to +0.139 and +0.344. Only 3/10 units improve in either Full96 model at that compact
support. Original DI likewise remains negative overall, with its weak-unit gap worsening from −0.207
to −0.587. Smaller support therefore explains why the all-unit Full96 mean need not be below raw; it
does **not** explain away denoising's weak-unit attenuation or loss of separability. Full curves and
unit bands are in [Appendix E](#appendix-template-support).

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
The ten matched-R5 endpoints make the instability more explicit: their aggregate changes rank
together across all 10 units (ρ = 0.70), but the association reverses for the four post hoc weak
units (ρ = −0.67). These ten designed endpoints are not independent samples for correlation
inference; the reversal shows that the apparent SNR–d′ relationship depends on which units are
aggregated.

```{figure} figures/f4_snr_vs_dprime.png
:label: fig-snr-dprime
**Peak-channel template SNR does not provide a stable matched-filter ranking.** All 31 comparison
entries are overlaid and direct-labeled. Fill color encodes the exact trainable parameter count on a
logarithmic scale; circles denote omission0 and triangles omission1. The `origdi` triangle reflects
its configured temporal context omission, although that temporal-only reference has no modern
spatial blind-spot branch. The original-screen association is ρ = 0.02 and the combined 31-entry
association remains weak (ρ = 0.14), even though the ten
designed follow-up endpoints alone have ρ = 0.70. For the four post hoc weak units that follow-up
association reverses to ρ = −0.67 (reported in the inset rather than overlaid because it changes the
aggregation). These coefficients are descriptive, not inferential. SNR is empirical-template
peak-to-peak divided by spike-excluded background SD on one channel; d′ uses multichannel temporal
event scores.
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

## A matched R5 follow-up separates depth and channel allocation from parameter count

Nine single-seed follow-ups hold the R5 recipe, sample budget, blind-spot branch, fusion head, and
seed fixed while changing temporal U-Net width, channel growth, or depth. Together with the matched
base64 R5 reference, the ten directly compared endpoints are:

| R5 body | omission | temporal schedule | params | CO runtime | d′ | Δ vs base64 om0 | weak-unit d′* | amp | temporal cos |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| base64 2× | 0 | 64→128→256→512 | 3.15 M | 2.65 h | 4.3575 | — | 1.7149 | 0.9404 | 0.99655 |
| base96, growth √2 | 0 | 96→136→192→272 | 1.83 M | 2.65 h | 4.3395 | −0.0180 | 1.7124 | 0.9382 | 0.99663 |
| base96, depth 2 | 0 | 96→192→384 | 1.80 M | 2.67 h | 4.3538 | −0.0037 | 1.7147 | 0.9400 | 0.99667 |
| base96, growth 1.5× | 0 | 96→144→216→324 | 2.23 M | 2.75 h | 4.3599 | +0.0024 | 1.7122 | 0.9381 | 0.99674 |
| base96, cap 384 | 0 | 96→192→384→384 | 4.60 M | 3.97 h | 4.3773 | +0.0198 | 1.7152 | 0.9404 | 0.99663 |
| **base96, full 2×** | **0** | **96→192→384→768** | **6.96 M** | **4.63 h** | **4.3939** | **+0.0363** | **1.7165** | **0.9414** | **0.99668** |
| base96, growth √2 | 1 | 96→136→192→272 | 1.83 M | 2.68 h | 4.3588 | +0.0013 | 1.6017 | 0.8767 | 0.98484 |
| base96, depth 2 | 1 | 96→192→384 | 1.80 M | 2.72 h | 4.3651 | +0.0075 | 1.6049 | 0.8822 | 0.98593 |
| base96, growth 1.5× | 1 | 96→144→216→324 | 2.24 M | 2.85 h | 4.3886 | +0.0311 | 1.6032 | 0.8790 | 0.98513 |
| **base96, full 2×** | **1** | **96→192→384→768** | **6.96 M** | **4.61 h** | **4.4141** | **+0.0566** | **1.6376** | **0.8938** | **0.98712** |

The √2 schedule (`96→136→192→272`) was added after the coverage audit found that it had only a
synthetic GPU benchmark. Both matched runs reached 70,308 optimizer steps, their checkpoints
strict-loaded under the schedule-aware inference code, and frozen scoring produced 10-unit d′ and
waveform endpoints. At 1.83 M parameters and 2.65–2.68 h, √2 is the smallest and fastest base96
schedule tested, but its omission0 endpoint is below matched base64.

The depth-2 pair (`96→192→384`) was then added as a parameter-matched test against √2. Both runs
completed the same 70,308-step budget, strict-loaded, and received frozen endpoint scoring. Under
omission0, depth2 has 1.9% fewer parameters than √2 and nearly identical runtime, yet exceeds it by
**+0.0143 d′** (7/10 units; descriptive paired-unit interval **[+0.0014, +0.0307]**). It is tied with
base64 at −0.0037 (5/10; [−0.0208, +0.0103]). Thus an extra U-Net scale is not intrinsically
beneficial at matched parameter count; where channels are allocated across scales matters.

\*The four previously defined, post hoc weak units have raw d′ ≤ 2.2. The depth2, √2, and 1.5×
models are smaller than base64 despite their wider first stage. Within the depth-3 base96 omission0
series, d′ rises as deeper channel capacity expands: growth1.5 exceeds √2 by +0.0204 (7/10;
[−0.0032, +0.0559]), cap384 exceeds growth1.5 by +0.0174
(8/10 units improve; descriptive paired-unit bootstrap interval
[+0.0045, +0.0340]), and full 2× exceeds cap384 by +0.0165 (9/10;
[+0.0004, +0.0399]).

Against matched base64 R5, √2 changes d′ by −0.0180 (4/10 units; [−0.0405, +0.0010]),
depth2 by −0.0037 (5/10; [−0.0208, +0.0103]), growth1.5 by +0.0024 (4/10 units;
[−0.0185, +0.0293]), cap384 by +0.0198 (5/10; [−0.0046, +0.0592]), and full base96 by
**+0.0363, or +0.83%** (8/10; **[+0.0030, +0.0850]**). Only the full-pyramid interval excludes zero,
but all five comparisons use one trained model per configuration and the same 10 fixed units. The
intervals are descriptive unit-mixture sensitivity analyses, not independent biological or
training-seed inference.

The mean gain is not a weak-unit rescue. Relative to base64, full base96 changes the four-weak-unit
mean by only +0.0016 while changing the other-six mean by +0.0595; cap384 gives +0.0003 and +0.0328,
respectively; depth2 gives −0.0002 and −0.0060; √2 gives −0.0025 and −0.0283. Omission0 waveform
fidelity is effectively tied across the models: FWHM ratio is 0.9764 throughout, amplitude spans
0.9381–0.9414, temporal cosine 0.99655–0.99674, and spatial cosine 0.999799–0.999831.

Compute generally rises with deeper capacity and the detection mean. Relative to full base96
omission0, √2 reduces Code Ocean end-to-end runtime by 42.7%, depth2 by 42.4%, growth1.5 by 40.5%,
and cap384 by 14.3%; full base96 takes 74.5% longer than base64. Thus full 2× is the all-unit d′
choice, depth2 is the smallest base64-level omission0 model tested, growth1.5 is another base64-level
compute-efficient choice, and cap384 is intermediate rather than a free replacement.

The four omission1 endpoints sharpen the aggregation warning. √2, depth2, growth1.5, and full 2×
reach d′ 4.3588, 4.3651, 4.3886, and 4.4141, +0.0193, +0.0112, +0.0287, and +0.0202 over their
omission0 twins, but only 2/10 units improve in each comparison and all descriptive intervals are
wide. Their weak-unit means fall to 1.6017, 1.6049, 1.6032, and 1.6376; amplitude falls to 0.8767,
0.8822, 0.8790, and 0.8938; and temporal cosine falls to 0.9848, 0.9859, 0.9851, and 0.9871. Depth2
omission1 is +0.0063 over √2 omission1 (8/10; [−0.0113, +0.0208]), so its small aggregate lead is
not a resolved parameter-matched effect. Omission1 raises
the ten-unit mean through heterogeneous strong-unit gains while moving the weak-unit and waveform
objectives in the opposite direction.

```{figure} figures/width_schedule_followup.png
:label: fig-width-schedule-followup
**Matched R5 width, depth, and channel-schedule follow-up.** **A**, omission0 mean d′ versus Code Ocean
end-to-end runtime; marker area scales with parameter count and the dotted line is raw data. **B**,
paired mean d′ changes from base64 with descriptive 95% paired-unit bootstrap intervals. **C**, all
four paired models have a higher ten-unit mean under omission1. **D**, the same routing lowers the
mean for the four weak units. All nine scored follow-ups use one training seed; panels B–D resolve the same
10 benchmark units and are not biological-replicate inference.
```

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

The amplitude pattern is not confined to base32 and omission0. Across all 31 architecture-comparison
entries, including the ten matched-R5 endpoints, the per-model Spearman correlation between
empirical-template amplitude and raw d′ ranges from 0.62 to 0.94 (median 0.85; original 21-model
median 0.88). This is consistent with conditional-mean shrinkage: waveforms that are poorly
constrained by surrounding samples are attenuated more. It is not direct evidence that neighbouring
samples are pure noise or that regression-to-the-mean is the only mechanism.

```{figure} figures/f5_amp_vs_quality.png
:label: fig-amp-quality
**Amplitude preservation across all 31 architecture-comparison entries.** **A**, the original 21
architectures plus the ten matched-R5 endpoints (grey points), with the per-unit median and
10th–90th percentile across endpoints (black). The unit-quality gradient persists after adding the
width/schedule family. **B**, the matched base32–omission0 compound contrast: moving t±1 into the
temporal branch while changing the spatial input and outer context raises amplitude primarily for
weak units. Values are denoised/raw empirical-template peak-to-peak ratios, not amplitudes relative
to a noise-free injected waveform.
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

Ten earlier weighted endpoints are intentionally absent from this matched comparison. They remain
in the 89-endpoint master and per-unit inventories, but their weighting implementation silently used
Charbonnier despite requesting L2. Mixing them into the corrected figure would confound weighting
with the executed objective; `table_coverage` identifies them as the separate
`legacy_weighting_screen` family.

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

## How do the selected Full96 omission trajectories evolve with longer training?

Two single-seed Full96 runs repeat the matched omission comparison under a 54.0 M-window training
horizon (210,924 updates at batch 256), with 11 log-spaced scheduled states. Both use the
selected `96→192→384→768` body, Charbonnier objective, and R5 recipe; only the omission route differs.
This is a post-selection trajectory diagnostic, not independent validation of the width choice. Its
cosine schedule spans 12 chunks, so its intermediate states are not spliced to the earlier 4-chunk
runs, whose schedule completed at ~18.0 M windows.

- **Both d′ trajectories remain duration-sensitive.** From 15.85 M to 54.0 M windows, d′ rises by
  +0.107 for om0 and +0.205 for om1. Neither curve is visibly flat at the final state.
- **The observed routing order reverses in the last sampled interval.** At 15.85 M windows om0 leads
  by 0.022 d′; at 54.0 M, om1 leads by 0.075 (4.504 versus 4.429). The crossover is interval-censored
  because no state was scored between those exposures.
- **Detection and amplitude still disagree.** At 54.0 M windows om1 is 0.007 d′ above raw while om0
  remains 0.068 below raw, but om1 retains the lower amplitude ratio (0.920 versus 0.949).

The validation-best model for each route occurs at the final update and gives essentially the same
values as the final scheduled state. These trajectories therefore show that the within-run routing
order is exposure-sensitive and that omission routing changes both convergence and the
detection–amplitude tradeoff. They do not establish either route's asymptote, and d′ remains the
frozen 4-ms all-unit surrogate rather than sorter-level performance.

```{figure} figures/f8_trajectory.png
:label: fig-trajectory
**Full96 duration diagnostic.** Frozen 4-ms all-unit d′ (left) and empirical-template amplitude
(right) versus cumulative training windows for matched omission0 and omission1 runs. The dotted line
is raw d′. Both routes improve in the final sampled interval; omission1 finishes higher in d′ but
lower in amplitude. Curves show repeated states from one seed per route, not independent replicates.
```
