# Results

:::{note} Current state
In-band scoring is complete for **Tier 1** (base32, omission0, champ_l2, omission0_l2, base64 — with
seed replicates) and the two **SUPPORT-scale** omission runs. The remaining sweep (SUPPORT wiring,
fuse width, enlarged architecture, spike-weighting — Tier 2/3) is in progress; those rows and the
figure panels are added as they land. All numbers below are in-band (train = eval on `recording1_3`,
AP band); the raw-data reference is **d′ = 4.497**. Full ledger: `results/tables/master_table.csv`.
:::

## The master table and the noise floor

Twenty-one models are scored so far — the five replicated noise-floor configurations and the two
SUPPORT-scale omission runs. Read against the raw-data reference of **d′ = 4.497**:

| config | loss | n | d′_self | d′_fixed | Δ vs raw | amp | fwhm | snr_deep |
|---|---|---|---|---|---|---|---|---|
| **base64** | charb | 3 | **4.382** | 4.410 | −0.115 | 0.880 | 1.009 | 7.70 |
| om0_scale | L2 | 1 | 4.363 | 4.400 | −0.134 | **0.939** | 0.976 | 6.90 |
| omission0 | charb | 5 | 4.312 | 4.354 | −0.185 | 0.932 | 0.976 | 6.89 |
| omission0_l2 | L2 | 3 | 4.305 | 4.346 | −0.192 | 0.931 | 0.976 | 6.89 |
| champ_l2 | L2 | 3 | 4.289 | 4.313 | −0.208 | 0.861 | 1.007 | 7.60 |
| base32 | charb | 5 | 4.277 | 4.300 | −0.220 | 0.859 | 1.007 | 7.60 |
| om1_scale | L2 | 1 | 4.274 | 4.296 | −0.223 | 0.869 | 1.041 | 7.68 |

(`om0_scale` / `om1_scale` are the SUPPORT-scale `support_all` runs; the rest are the base32 body.
Per-config seed spread: base32 σ = 0.015, omission0 0.007, champ_l2 **0.041**, omission0_l2 0.004,
base64 0.017. `d′_fixed` tracks `d′_self` throughout — the gains are real signal, not self-consistent
template sharpening.)

Two facts make any *single* run an unreliable ranking, and both recur in-band: training is stochastic
(GPU non-determinism, initialisation, data order), and the validation loss is nearly flat with respect
to spikes, so the loss-selected "best" checkpoint is effectively drawn from a plateau. We therefore
retrained the key configurations 3–5 times, changing only the seed. base32's five seeds scatter
with **σ_d′ = 0.015** and **σ_amp = 0.004**, which fixes the decision rule for everything below: **a
difference is real only if it clears ≈ 2σ (≈ 0.03 d′, ≈ 0.01 amp)**, confirmed by a Welch t-test against
base32. The rule immediately disciplines the table — `champ_l2` carries by far the widest spread
(σ = 0.041, ~3× base32), so its mid-table placement is seed scatter, not signal.

**Read-out (a): denoising still lowers detectability in-band.** Every configuration — the best
included — sits below the raw d′ of 4.497, by 0.11 to 0.22. Training in the model's own band does not
remove the deficit, so the central puzzle of the prior study is a genuine property of the denoiser,
not an out-of-domain artifact.

```{figure} figures/f1_dprime_ranking.png
:label: fig-dprime-ranking
**d′ across architectures vs the base32 ±2σ noise floor.** Bars are d′ (mean ± 2σ over seeds); the
grey band is base32's 5-seed ±2σ, the dotted line is raw data (4.497). Only `base64` clears the band;
`champ_l2`'s wide error bar is why single runs cannot be ranked.
```

## The loss axis is neutral

Switching Charbonnier → L2 on the base32 body moves d′ by only **+0.012 (t = 0.49, NS)** and does
nothing for amplitude (0.859 → 0.861). `champ_l2` is the study's single noisiest replicate set
(σ = 0.041): its occasional high draws are lucky seeds — exactly the pattern the prior report walked
back after replication (its headline +0.13 collapsed to a non-significant mean). L2 stacked on the
omission change is likewise flat (omission0_l2 − champ_l2 = +0.016, t = 0.67, NS). On the evidence so
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

Doubling the U-Net base width (`base64`, 32 → 64 channels) is the largest reproducible move in the
study so far: **d′ 4.277 → 4.382, +0.105 (Welch t = 8.7, p < 10⁻³)** — roughly three-quarters of the
way to closing base32's deficit against raw, and it nudges amplitude up as well (0.859 → 0.880).
It is not merely above base32 but **significantly above every other configuration**, omission0
included (+0.071, t = 6.8). Within the base32 temporal design the reproducible detection ordering
is therefore unambiguous — **capacity dominates**, and on the sorting-relevant axis rather than by
simply removing more noise. The enlarged (15×) architecture, which in the prior report bought the most
SNR yet the *worst* detection, is retested in Tier 2/3.

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

## The omission gap: an amplitude lever, not a detection lever

The temporal choice the prior report crowned "the largest single lever" is the omission gap — whether
the temporal branch sees the immediately-adjacent frames t±1 (`omission=0`) or hides them
(`omission=1`). In-band the two effects it drives come apart sharply:

| axis | Charbonnier (×5 vs ×5) | L2 (×3 vs ×3) |
|---|---|---|
| **detection** Δd′ | +0.035 (t = 4.6, p ≈ 0.003) | +0.016 (t = 0.67, NS) |
| **amplitude** Δamp | +0.073 (t ≈ 30) | +0.071 |

The **detection** gain is real in Charbonnier but small — **+0.035 d′, about one-sixth of the prior
out-of-band +0.204** — and not even resolvable in L2. The **amplitude** gain, by contrast, is one of
the most significant effects in the whole study (t ≈ 30). So in-band `omission=0` is an
**amplitude / waveform-fidelity** lever, not the detection lever it was billed as. *Where* that
amplitude gain lands (next section) is what makes the two axes decouple.

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
SNR/detection dissociation, first flagged out of band, reproduces cleanly in-band and is the crux of
the whole detection deficit.

## Training length: amplitude saturates, detection does not

Two matched runs trained ~7× longer (SUPPORT scale, ~3.3 M updates, 12 log-spaced checkpoints) test
whether the short runs were undertrained. The two metrics behave **oppositely**:

- **Amplitude saturates early** — flat to ±0.02 after ~10³–10⁵ updates (om0 −0.016, om1 +0.027 across
  the final 2.4 decades). For amplitude the short budget is well past convergence.
- **Detection does not.** d′ keeps climbing to 3.3 M: **om0 +0.11, om1 +0.30** from 14 k onward, and
  om1's *largest late gain is its final step* (+0.11 from 844 k → 3.3 M). om1 (t±1 hidden) has **not
  converged** even at 3.3 M.

So the models are **undertrained for detection**: the short budget (~0.28 M) sits on the rising part
of the d′ curve and *under-measures* it, biased toward faster-converging configs. (This reverses the
out-of-band report's "converges in one epoch" reading, which was taken off the spike-blind validation
loss.) Short-run d′ rankings are therefore a **convergence-speed-biased screen**, to be read only
alongside the trajectory; near-converged comparisons need SUPPORT-scale training — and even 3.3 M is a
lower bound for slow configs.

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
