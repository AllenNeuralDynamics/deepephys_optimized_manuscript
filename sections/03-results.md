# Results

:::{note} Current state
In-band scoring is complete for **Tier 1** (champion, omission0, champ_l2, omission0_l2, base64 — with
seed replicates) and the two **SUPPORT-scale** omission runs. The remaining sweep (SUPPORT wiring,
fuse width, enlarged architecture, spike-weighting — Tier 2/3) is in progress; those rows and the
figure panels are added as they land. All numbers below are in-band (train = eval on `recording1_3`,
AP band); the raw-data reference is **d′ = 4.497**. Full ledger: `results/tables/master_table.csv`.
:::

## Detection under an in-band noise floor

Five configurations were retrained across seeds to fix the in-band noise floor. The champion's
5-seed spread gives **σ_d′ ≈ 0.015** (decision band **±2σ ≈ 0.03**) and σ_amp ≈ 0.004.

| config | loss | d′ (mean) | Δ vs raw | amp | σ_d′ |
|---|---|---|---|---|---|
| base64 | Charbonnier | **4.382** | −0.115 | 0.880 | 0.017 |
| omission0 | Charbonnier | 4.312 | −0.185 | **0.932** | 0.007 |
| omission0 | L2 | 4.305 | −0.192 | 0.931 | 0.004 |
| champ_l2 | L2 | 4.289 | −0.208 | 0.861 | 0.041 |
| champion | Charbonnier | 4.277 | −0.220 | 0.859 | 0.015 |

**Read-out (a): denoising still lowers detectability in-band.** Every configuration sits below the
raw d′ of 4.497, by 0.11–0.22. Training in the correct band does not remove the deficit — the central
puzzle is not a wide-band artifact.

<!-- Uncomment each block once code/figures/collate.py + the figure scripts have written the file.
Master results table (T1):
```{include} results/tables/master_table.md
```
d′ ranking figure (F1):
```{figure} figures/f1_dprime_ranking.png
:label: fig-dprime-ranking
d′ across all models against the champion ±2σ noise band; dotted line = raw data.
``` -->

## The loss axis: Charbonnier vs L2

Switching Charbonnier → L2 on the champion body moves d′ from 4.277 to 4.289 — **+0.012, within the
noise band**; and `champ_l2` is the noisiest config (σ = 0.041), i.e. its apparent gain is seed
scatter, not signal. L2 is effectively **neutral** in-band, matching the prior report's replicated
walk-back. The full six Charbonnier↔L2 matched pairs complete with Tier 2/3.

<!-- ```{figure} figures/f3_loss_pairs.png
:label: fig-loss-pairs
The six Charbonnier↔L2 matched pairs (Δ per axis).
```
```{figure} figures/f2_loss_capacity_2x2.png
:label: fig-loss-capacity
Loss × capacity 2×2.
``` -->

## Capacity — the dominant detection lever

Doubling the U-Net base width (`base64`) lifts d′ to **4.382, +0.105 over the champion (~7σ)** — the
largest reproducible detection gain so far, and the config closest to raw. **Capacity, not the
temporal design, is the leading in-band detection lever.** The enlarged-architecture case and the
SNR-vs-d′ "trap" plot complete with Tier 2/3.

<!-- ```{figure} figures/f4_snr_vs_dprime.png
:label: fig-snr-trap
SNR gain vs Δd′ — the SNR trap.
```
```{figure} figures/f5_amp_vs_quality.png
:label: fig-amp-quality
Amplitude preservation vs baseline unit quality (shrinkage).
``` -->

## The omission gap — an amplitude lever, not a detection lever

Revealing the adjacent frames t±1 (`omission=0`) vs hiding them (`omission=1`):

| | Δ d′ | Δ amp |
|---|---|---|
| Charbonnier (×5 vs ×5) | **+0.035** (p < 0.01) | **+0.073** |
| L2 (×3 vs ×3) | +0.016 (within noise) | +0.071 |

**Read-out (b):** in-band the omission **detection** gain is small (+0.035 d′, Charbonnier) and not
resolvable in L2 — **~6× smaller than the prior out-of-band +0.204**. Its **amplitude** effect is
robust (+0.07) and concentrates on the marginal low-SNR units (per-unit matrices, appendix). So
`omission=0` is primarily an **amplitude/waveform-fidelity** lever in-band, not the detection lever
the earlier report claimed.

## Per-unit structure

Amplitude preservation as a function of unit quality (the shrinkage law), and the per-unit
amplitude and Δd′ matrices across all models (appendix [Appendix B/C](sections/05-appendix.md)).

## Training length and saturation

The two SUPPORT-scale runs (~3.3 M updates, 12 log-spaced checkpoints) settle the point. Both metrics
saturate within ~10⁴ updates — the models are **not undertrained**. Crucially, the **d′ omission gap
closes at convergence**: at the final step om0 and om1 reach the *same* d′ (4.361 vs 4.361), while the
amplitude gap persists (0.931 vs 0.870). The mid-training lead of `omission=0` (~+0.13 d′ around
10⁴–10⁵ updates) is thus a **convergence-speed** effect, not a permanent advantage. As a corollary,
the validation-loss-selected checkpoint is suboptimal (om1's `best_model` d′ 4.275 < its final 4.361)
— the spike-blind-loss symptom.

<!-- ```{figure} figures/f8_trajectory.png
:label: fig-trajectory
d′ and amplitude vs training updates for the omission A/B at SUPPORT scale.
```
```{figure} figures/f9_val_loss_overfit.png
:label: fig-val-loss
Validation-loss / overfit curves with best-checkpoint markers.
``` -->
