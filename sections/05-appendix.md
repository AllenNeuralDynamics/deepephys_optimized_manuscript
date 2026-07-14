# Appendix

## A. Model glossary

One line per model (champion + ablations). The operational definition of every configuration —
the exact training override and its rationale — is tabulated in
[the pre-registered design](reproducibility/regeneration-plan.md) §4. Families:

- **Baseline** — the champion (`fold` geometry, `base_channels=32`, `depth=3`, 3-frame temporal
  blind spot, Charbonnier loss).
- **Loss shape** — Charbonnier vs L2, across six matched pairs.
- **Capacity** — `base64` (double width) and the 15× enlarged architecture.
- **Head / fuse-decoder width** — `fuse128…1024`, temporal hand-off width.
- **Spike-weighting** — magnitude, unbiased position-gate, and hard-gate peak-aware losses.
- **SUPPORT-style wiring** — dense centre re-injection, staged features, multiscale hole-convs.
- **Temporal / blind-spot design** — the omission gap (`omission=0/1`) and blind-spot width.

## B. Per-unit amplitude across models

`amp_ratio` for each ground-truth unit (rows, sorted by baseline separability) across every model
(columns), with a heatmap. The dominant pattern is expected to be vertical (a unit-quality
gradient), i.e. amplitude undershoot is a property of the *unit*, not the architecture.

<!-- Uncomment when produced by code/figures/collate.py + make_perunit_heatmaps.py:
```{include} results/tables/perunit_amp.md
```
```{figure} figures/f6_perunit_amp_heatmap.png
:label: fig-perunit-amp
Per-unit amplitude preservation across models (green ≈ preserved, red = smoothed).
``` -->

## C. Per-unit detection (Δd′) across models

Change in detectability from denoising, `d′_deep − d′_raw`, per unit × model, as a heatmap (red =
denoising hurts, blue = helps). Exposes per-unit collapses that the mean hides.

<!-- Uncomment when produced by code/figures/collate.py + make_perunit_heatmaps.py:
```{include} results/tables/perunit_dprime.md
```
```{figure} figures/f7_perunit_dprime_delta_heatmap.png
:label: fig-perunit-dprime
Per-unit change in detectability from denoising, across models.
``` -->
