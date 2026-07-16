# Results

:::{note} Current state
In-band scoring is complete for the full sweep: **Tier 1** (base32, omission0, champ_l2, omission0_l2,
base64 — with seed replicates), **Tier 2** (SUPPORT blind-spot wiring, fuse width, the enlarged `arch`
body, temporal / normalisation variants, and the capacity × `omission=0` combos), **Tier 3** (the
spike-aware loss sweep on the `arch_l2_om0` body), the original DeepInterpolation architecture
(`origdi`, 3 seeds), and the two **SUPPORT-scale** omission runs. All numbers below are in-band
(train = eval on `recording1_3`, AP band); the raw-data reference is **d′ = 4.497**. Full ledger:
`results/tables/master_table.csv`.
:::

## The master table and the noise floor

Twenty short-budget architectures are scored in-band — the nineteen swept configurations plus the
original DeepInterpolation network (`origdi`) as a published reference (the two SUPPORT-scale runs,
trained ~7× longer, are held for the training-length section below). The table is seed-averaged where
replicated and sorted by detection d′, read against the raw-data reference of **d′ = 4.497**:

| config | loss | n | d′_self | d′_fixed | Δ vs raw | amp | fwhm | snr_deep |
|---|---|---|---|---|---|---|---|---|
| **arch** | charb | 1 | **4.409** | 4.437 | −0.088 | 0.871 | 1.020 | 7.81 |
| arch_l2 | L2 | 1 | 4.407 | 4.434 | −0.090 | 0.877 | 1.003 | 7.84 |
| base64 | charb | 3 | 4.382 | 4.410 | −0.115 | 0.880 | 1.009 | 7.70 |
| arch_om0 | charb | 1 | 4.367 | 4.403 | −0.130 | **0.936** | 0.976 | 6.96 |
| base64_l2 | L2 | 1 | 4.366 | 4.398 | −0.131 | 0.880 | 1.003 | 7.70 |
| base64_om0 | charb | 1 | 4.359 | 4.397 | −0.138 | 0.934 | 0.976 | 6.91 |
| support_sd | charb | 1 | 4.313 | 4.339 | −0.184 | 0.857 | 1.023 | 7.56 |
| support_all | charb | 1 | 4.312 | 4.334 | −0.185 | 0.864 | 1.003 | 7.57 |
| omission0 | charb | 5 | 4.312 | 4.354 | −0.185 | 0.932 | 0.976 | 6.89 |
| omission0_l2 | L2 | 3 | 4.305 | 4.346 | −0.192 | 0.931 | 0.976 | 6.89 |
| support_all_l2 | L2 | 1 | 4.295 | 4.320 | −0.202 | 0.868 | 1.034 | 7.59 |
| champ_l2 | L2 | 3 | 4.289 | 4.313 | −0.208 | 0.861 | 1.007 | 7.60 |
| no_norm | charb | 1 | 4.284 | 4.310 | −0.213 | 0.856 | 1.023 | 7.55 |
| fuse256_l2 | L2 | 1 | 4.282 | 4.311 | −0.215 | 0.857 | 1.023 | 7.59 |
| base32 | charb | 5 | 4.277 | 4.300 | −0.220 | 0.859 | 1.007 | 7.60 |
| ho | charb | 1 | 4.272 | 4.300 | −0.225 | 0.852 | 1.014 | 7.58 |
| fuse256 | charb | 1 | 4.265 | 4.296 | −0.232 | 0.853 | 1.003 | 7.50 |
| tmult8 | charb | 1 | 4.257 | 4.286 | −0.240 | 0.857 | 1.003 | 7.61 |
| fuse512 | charb | 1 | 4.244 | 4.266 | −0.253 | 0.859 | 1.003 | 7.57 |
| **origdi** *(published ref.)* | charb | 3 | **4.135** | 4.139 | **−0.362** | 0.811 | 1.122 | **8.15** |

(Single-seed rows — the Tier-2 configurations — carry no error bar and are judged against base32's
noise floor below. Per-config seed spread on the replicated rows: base32 σ = 0.015, omission0 0.007,
champ_l2 **0.041**, omission0_l2 0.004, base64 0.017. `d′_fixed` tracks `d′_self` throughout — the
gains are real signal, not self-consistent template sharpening.)

Two facts make any *single* run an unreliable ranking, and both recur in-band: training is stochastic
(GPU non-determinism, initialisation, data order), and the validation loss is nearly flat with respect
to spikes, so the loss-selected "best" checkpoint is effectively drawn from a plateau. We therefore
retrained the key configurations 3–5 times, changing only the seed. base32's five seeds scatter
with **σ_d′ = 0.015** and **σ_amp = 0.004**, which fixes the decision rule for everything below: **a
difference is real only if it clears ≈ 2σ (≈ 0.03 d′, ≈ 0.01 amp)**, confirmed by a Welch t-test against
base32. The rule immediately disciplines the table — `champ_l2` carries by far the widest spread
(σ = 0.041, ~3× base32), so its mid-table placement is seed scatter, not signal.

**Read-out (a): denoising still lowers detectability.** Every configuration — the best
included — sits below the raw d′ of 4.497, from **−0.09** (`arch`) to **−0.36** (the original `origdi`
network). Training in the model's own band does not remove the deficit, so the detection cost is a
genuine property of the denoiser — the central problem this study targets. How much of it the modern
architecture has already recovered from the original is the next section.

```{figure} figures/f1_dprime_ranking.png
:label: fig-dprime-ranking
**d′ across the 20 short-budget architectures vs the base32 ±2σ noise floor.** Bars are d′ (mean ± 2σ
over seeds; single-seed Tier-2 rows have no bar); base32 (grey) anchors its own 5-seed ±2σ band, the
original DeepInterpolation network (`origdi`, **crimson**) is the published reference, and the dotted
line is raw data (4.497). The `arch` / `base64` capacity family sits at the top, the fuse-width /
temporal variants at or below the band, and **`origdi` sits far below all of them** — the optimized
architecture has climbed most of the way from the original toward raw. (The two SUPPORT-scale runs,
7× longer training, are compared separately in the training-length section below.)
```

## How far the architecture has come from the original

Anchoring the ranking is the **original DeepInterpolation ephys network** (`origdi`; the faithful
`unet_single_ephys_1024` of [@lecoq2021deepinterpolation] — a temporal-only 2-D U-Net with **no spatial
blind-spot branch**, [Methods](sections/02-methods.md)), trained and scored identically to every other
model. It is the **worst detector in the study — d′ = 4.135 ± 0.010, −0.362 below raw** — with the
**lowest amplitude (0.811)**, yet the **highest SNR of any model (8.15 vs base32's 7.60)**. The original
architecture removes the most noise and is the hardest to sort: the SNR trap in its starkest form, and
precisely the limitation this study sets out to fix.

Two architectural steps close most of that gap, at matched training and budget:

| step | d′ | amp | weak-unit d′* |
|---|---|---|---|
| `origdi` — original, temporal-only | 4.135 | 0.811 | 1.35 |
| **+ spatial blind-spot branch** → `base32` | 4.277 (+0.142) | 0.859 (+0.048) | 1.56 |
| **+ capacity + omission=0** → `arch_l2_om0` | 4.360 (+0.225) | 0.937 (+0.126) | 1.71 |

*mean d′ over the four weakest ground-truth units (baseline d′ ≤ 2.2). Adding the SUPPORT-style
**spatial blind spot** (`origdi` → `base32`) alone buys **+0.14 d′ and +0.05 amp**; layering on capacity
and the recovered t±1 frames (`arch_l2_om0`) reaches **+0.23 d′ / +0.13 amp** — and the gain is
**largest on the weak units** (+0.36 d′, a 27 % lift on the hardest-to-sort cells). The optimized
network is a markedly better *sorting* front-end than the original, even though its SNR is lower.

## The loss axis is neutral

Switching Charbonnier → L2 on the base32 body moves d′ by only **+0.012 (t = 0.49, NS)** and does
nothing for amplitude (0.859 → 0.861). `champ_l2` is the study's single noisiest replicate set
(σ = 0.041): its occasional high draws are lucky seeds — exactly why the ±2σ rule matters, since a
single lucky L2 run would otherwise read as a real gain. L2 stacked on the omission change is likewise
flat (omission0_l2 − champ_l2 = +0.016, t = 0.67, NS). On the evidence so
far L2 is a free but negligible nudge: never worse, never clearing the band. The full six
Charbonnier↔L2 matched pairs — which test whether loss stacks with capacity, fuse width, SUPPORT
wiring, and the enlarged body — complete with Tier 2/3.

<!-- ```{figure} figures/f3_loss_pairs.png
:label: fig-loss-pairs
The six Charbonnier↔L2 matched pairs (Δ per axis).
```
```{figure} figures/f2_loss_capacity_2x2.png
:label: fig-loss-capacity
Loss × capacity 2×2.
``` (F2/F3 pending Tier 2/3) -->

## Capacity is the leading detection lever

Doubling the U-Net base width (`base64`, 32 → 64 channels) is the largest reproducible move on the
base32 body: **d′ 4.277 → 4.382, +0.105 (Welch t = 8.7, p < 10⁻³)** — roughly three-quarters of the
way to closing base32's deficit against raw, nudging amplitude up as well (0.859 → 0.880), and
significantly above omission0 (+0.071, t = 6.8).

Tier 2 adds the two larger bodies. The enlarged **`arch`** (base 64, depth 4, `bs_channels=128`,
`bs_depth=7`) — the largest network in the sweep — is here the **top detector, d′ = 4.409**,
corroborated by its L2 twin `arch_l2` (4.407). But the increment over `base64` is small — **+0.027,
inside base64's ±2σ band** — even though `arch` roughly doubles the parameter count again. On the short
screen the capacity axis therefore runs base32 (4.277) → base64 (4.382, +0.105) → arch (4.409, +0.027):
monotone but **sharply diminishing**, and still 0.088 below raw. Whether `arch`'s larger body keeps
climbing at a longer budget — a bigger network may simply converge more slowly — is what the
training-length section below, and the planned scale-validation, are for.

```{figure} figures/f4_snr_vs_dprime.png
:label: fig-snr-trap
**The SNR trap.** SNR gain (snr_deep − snr_raw) vs Δd′ (deep − raw) per architecture — removing more
noise does not buy detectability.
```
```{figure} figures/f5_amp_vs_quality.png
:label: fig-amp-quality
**Amplitude follows unit quality.** amp_ratio vs baseline d′ (log) for base32 (black) and omission0
(blue); grey links join the same unit — weak units are smoothed, omission0 rescues them.
```

## Blind-spot wiring, fuse width, and temporal variants

The remaining Tier-2 levers change the network's wiring rather than its raw capacity. Read against the
base32 band (4.277 ± 0.03), none of them moves detection:

| lever | config | d′ | amp | vs base32 band |
|---|---|---|---|---|
| bigger / denser blind-spot branch | support_sd 4.313, support_all 4.312 | ~4.31 | 0.86 | top edge |
| L2 on that wiring | support_all_l2 4.295 | 4.295 | 0.868 | inside |
| widest fusion | fuse256 4.265, fuse512 4.244 | 4.24–4.27 | 0.85–0.86 | at / below |
| deeper temporal hand-off | tmult8 4.257 | 4.257 | 0.857 | below |
| no input normalisation | no_norm 4.284 | 4.284 | 0.856 | inside |
| 1-frame blind spot, omission on | ho 4.272 | 4.272 | 0.852 | inside |

The two `support_*` runs (a larger, denser blind-spot sub-network) sit marginally at the top of the
band; everything else — including the *widest* fusion (`fuse512`), the lowest-d′ configuration in the
whole table — is inside or below it, and none shifts amplitude off ~0.86. Widening or deepening the
sub-networks is not where the detection budget is.

## The omission gap: an amplitude lever, not a detection lever

The temporal design choice the reference turns on is the omission gap — whether the temporal branch
sees the immediately-adjacent frames t±1 (`omission=0`) or hides them (`omission=1`). It might be
expected to matter most for detection; in-band the two effects it drives come apart sharply:

| axis | Charbonnier (×5 vs ×5) | L2 (×3 vs ×3) |
|---|---|---|
| **detection** Δd′ | +0.035 (t = 4.6, p ≈ 0.003) | +0.016 (t = 0.67, NS) |
| **amplitude** Δamp | +0.073 (t ≈ 30) | +0.071 |

The **detection** gain is real in Charbonnier but small — **+0.035 d′** — and not even resolvable in
L2. The **amplitude** gain, by contrast, is one of the most significant effects in the whole study
(t ≈ 30). So `omission=0` is an **amplitude / waveform-fidelity** lever, not a detection lever.
*Where* that amplitude gain lands (next section) is what makes the two axes decouple.

## Capacity × omission=0: stacking the two levers

The two axes that *do* move things — capacity (detection) and `omission=0` (amplitude) — are combined
for the first time in `base64_om0` and `arch_om0`:

| pairing | d′ | amp | Δ vs its om1 twin |
|---|---|---|---|
| base64 → base64_om0 | 4.382 → 4.359 | 0.880 → 0.934 | d′ −0.023, amp +0.054 |
| arch → arch_om0 | 4.409 → 4.367 | 0.871 → 0.936 | d′ −0.042, amp +0.065 |

The trade seen on the base32 body holds at high capacity: `omission=0` lifts amplitude to ~0.935 — the
best in the table, matching the dedicated `omission0` runs — for a small d′ cost. The combos land at
d′ ≈ 4.36 with amp ≈ 0.935, so both `arch_om0` and `base64_om0` sit above base32 on *both* axes at once
(base32 4.277 / 0.859). Per-unit, the amplitude rescue again concentrates on the weak units (unit 94
0.81 → 0.97, unit 1129 0.69 → 0.82; [Appendix B](sections/05-appendix.md)).

## Spike-aware loss does not move detection

The one lever left that directly targets the weak-unit detection deficit is the **spike-aware loss** —
multiply the reconstruction loss at spike-like samples so the network is penalised for flattening the
peak (Methods). We swept it on the best body, `arch_l2_om0` (d′ = 4.360 ± 0.019, amp 0.937): a soft
magnitude weight at λ = 3/10/30, a focal variant (γ = 2), and a saturating position gate at
λ = 100/300/1000 (soft and hard).

| spike weight | d′ | Δ vs base | amp |
|---|---|---|---|
| — (baseline) | 4.360 | — | 0.937 |
| soft λ = 3 / 10 / 30 | 4.372 / 4.377 / 4.378 | +0.01 to +0.02 | 0.94 |
| gate λ = 100 / 300 | 4.319 / 4.369 | −0.04 / +0.01 | 0.94 |
| focal γ = 2 (λ = 10) | **4.051** | **−0.31** | 0.94 |
| gate λ = 1000 / hard | 4.102 / 4.219 | **−0.26 / −0.14** | 0.95 |

**No setting clears the noise floor.** The best case — soft λ = 30 — is **+0.019 d′, inside the
baseline's own ±0.019 σ** (not significant), and every aggressive setting (focal γ = 2, λ ≥ 1000) *hurts*
detection sharply as the over-weighted loss distorts the waveform. Critically, the effect is null
**even on the weak units it was designed to protect**: their mean d′ moves from 1.708 (baseline) to
1.719 (λ = 30) to 1.724 (gate λ = 300) — a **+0.01–+0.02** nudge, versus the **+0.15** the blind-spot
branch and the **+0.36** the full optimization already delivered there. The same holds on the base32
body (`omission0_l2` + spike weight: +0.008 to +0.023, all within noise), and amplitude — already near-
maximal from `omission=0` — barely moves.

So the residual detection deficit **is not recoverable by loss-level spike emphasis**: once the
architecture is optimized, up-weighting spikes cannot convert the recovered amplitude into
detectability, which points to the deficit being intrinsic to the blind-spot objective rather than a
loss-weighting oversight (Discussion).

## Per-unit amplitude: who gets smoothed, and why

The single "0.86 amplitude" is a mean over a steep quality gradient, and that gradient — not the
architecture — is the dominant structure. Ranking the ten ground-truth units by intrinsic
separability (raw d′, spanning 1.0–12.5) and reading base32 amplitude down the ranking gives a
textbook law: **Spearman(amp, baseline d′) = +0.94**. Loud, well-isolated units come back at full
height (unit 2143, raw d′ 12.5 → amp 1.00; unit 793, 8.6 → 1.00); faint units near the sorting floor
are smoothed hard (unit 1129, raw d′ 2.1 → 0.67; unit 664, 1.0 → 0.77; unit 720, 2.2 → 0.78).

The mechanism is **regression to the mean**. The blind spot rebuilds each peak from its neighbours;
for a strong unit those neighbours pin the peak down and it returns intact, but for a weak unit the
neighbours are mostly noise, so the estimator hedges toward baseline and flattens the peak. The
undershoot therefore lives almost entirely on the marginal units that are hardest to sort to begin
with — a shrinkage estimator, resolved unit by unit.

This is precisely why `omission=0` is an amplitude lever: recovering t±1 undoes the shrinkage **where
it costs the most**. Its per-unit amplitude gain is monotone in weakness — strong units are unchanged
or slightly lower (2143 −0.01, 793 −0.04) while the weak units are rescued: unit 94 (raw d′ 2.2)
0.81 → 0.97 (+0.16), unit 1129 0.67 → 0.83 (+0.16), unit 720 0.78 → 0.89 (+0.12), unit 664 0.77 → 0.89
(+0.12). The mean +0.07 is a floor-lifting effect concentrated on the bottom of the quality ladder.
The full per-unit amplitude and Δd′ matrices across all models are in
[Appendix B/C](sections/05-appendix.md).

## The SNR trap

Denoising unambiguously improves signal-to-noise — base32 lifts mean per-unit SNR from **5.80
(raw) to 7.63 (+32%)** — and yet its detectability *falls* (4.497 → 4.277). Higher SNR and better
detection are simply not the same axis, and optimising the former is actively misleading for sorting:
the configuration that removes the most noise is not the one that is easiest to sort. This
SNR/detection dissociation is the crux of the whole detection deficit.

## Training length: amplitude saturates, detection does not

Two matched runs trained ~7× longer (SUPPORT scale, ~3.3 M updates, 12 log-spaced checkpoints) test
whether the short runs were undertrained. The two metrics behave **oppositely**:

- **Amplitude saturates early** — flat to ±0.02 after ~10³–10⁵ updates (om0 −0.016, om1 +0.027 across
  the final 2.4 decades). For amplitude the short budget is well past convergence.
- **Detection does not.** d′ keeps climbing to 3.3 M: **om0 +0.11, om1 +0.30** from 14 k onward, and
  om1's *largest late gain is its final step* (+0.11 from 844 k → 3.3 M). om1 (t±1 hidden) has **not
  converged** even at 3.3 M.

So the models are **undertrained for detection**: the short budget (~0.28 M) sits on the rising part
of the d′ curve and *under-measures* it, biased toward faster-converging configs. (A spike-blind
validation loss can look converged within one epoch precisely because spikes barely move it, so it is
a poor readout of detection convergence.) Short-run d′ rankings are therefore a
**convergence-speed-biased screen**, to be read only alongside the trajectory; near-converged
comparisons need SUPPORT-scale training — and even 3.3 M is a lower bound for slow configs.

This also nuances the omission gap. At 3.3 M the two arms meet (om0 4.361, om1 4.361) and the
**amplitude gap persists** (0.931 vs 0.870) — but om0 has ~flattened while om1 is still rising, so the
*asymptotic* d′ ordering is unresolved (with more training om1 could match or overtake om0). And the
validation-loss-selected `best_model` is a poor ruler for spike quality — om1's best-by-loss (d′ 4.275)
is beaten by its own final checkpoint (4.361), the spike-blind-loss signature.

```{figure} figures/f8_trajectory.png
:label: fig-trajectory
**SUPPORT-scale omission A/B.** d′ (left) and amplitude (right) vs training updates (log) for om0
(t±1 visible) and om1 (t±1 hidden); dotted line = raw d′. Amplitude saturates early; d′ keeps rising
(om1 still climbing at 3.3 M), the two arms meeting only at the last checkpoint.
```
<!-- F9 val-loss/overfit curves: pending losses.jsonl download -->
