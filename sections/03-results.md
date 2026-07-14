# Results

:::{warning} Placeholder
This section is the pre-registered results skeleton. Each subsection states the question and the
figure/table that answers it; **the in-domain numbers and figures are inserted once scoring
completes.** The experimental design that produces them is fixed in advance in
[the pre-registered design](reproducibility/regeneration-plan.md).
:::

## Detection under an in-domain noise floor

Master results table (all models × all metrics, sorted by `d′_self`, read against the champion ±2σ
band) and the d′-ranking figure. **Headline read-out (a): does denoising still lower d′ when trained
and scored in the same band?**

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

Six matched Charbonnier↔L2 pairs (base, omission, capacity, best-architecture, fuse-width,
SNR-trap) plus the loss × capacity 2×2. Does the training loss change the outcome, or is it
redundant with capacity as previously suggested?

<!-- ```{figure} figures/f3_loss_pairs.png
:label: fig-loss-pairs
The six Charbonnier↔L2 matched pairs (Δ per axis).
```
```{figure} figures/f2_loss_capacity_2x2.png
:label: fig-loss-capacity
Loss × capacity 2×2.
``` -->

## Capacity and the SNR trap

Whether added capacity / higher SNR translates into detectability, or trades against it
(the SNR-gain vs Δd′ plot). Includes the enlarged-architecture case that previously collapsed an
individual unit.

<!-- ```{figure} figures/f4_snr_vs_dprime.png
:label: fig-snr-trap
SNR gain vs Δd′ — the SNR trap.
```
```{figure} figures/f5_amp_vs_quality.png
:label: fig-amp-quality
Amplitude preservation vs baseline unit quality (shrinkage).
``` -->

## The omission gap (the primary lever)

The temporal-design change — revealing the immediately-adjacent frames t±1 (`omission=0`) — versus
hiding them (`omission=1`). **Headline read-out (b): does the omission gap survive in-domain, and in
both losses?** Reported as an A/B with seed replicates.

## Per-unit structure

Amplitude preservation as a function of unit quality (the shrinkage law), and the per-unit
amplitude and Δd′ matrices across all models (appendix [Appendix B/C](sections/05-appendix.md)).

## Training length and saturation

SUPPORT-scale trajectories (~3.3 M updates, 12 log-spaced checkpoints) for the omission A/B in both
losses: do the spike-level metrics keep improving past the short-run budget, or saturate early?
Also tests whether validation-loss checkpoint selection coincides with the d′/amp optimum.

<!-- ```{figure} figures/f8_trajectory.png
:label: fig-trajectory
d′ and amplitude vs training updates for the omission A/B at SUPPORT scale.
```
```{figure} figures/f9_val_loss_overfit.png
:label: fig-val-loss
Validation-loss / overfit curves with best-checkpoint markers.
``` -->
