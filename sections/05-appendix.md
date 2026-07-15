# Appendix

## A. Model glossary

All models are the `fold` DeepInterpolation ephys denoiser (channels scattered on the NP1 grid, W
columns folded into the feature axis, a 1-D U-Net along probe depth, fused per channel with a
probe-axis blind-spot branch). Every override is defined in
[the pre-registered design](reproducibility/regeneration-plan.md) §4.

**Scored (Tier 1 + SUPPORT scale).**
- **champion** — the reference: `base_channels=32, depth=3`, 3-frame temporal blind spot
  (`omission=1`), `bs_channels=64 / bs_depth=5`, `fuse_channels=64`, Charbonnier loss. In-band
  d′ 4.277 ± 0.015, amp 0.859 (5 seeds).
- **omission0** — champion with the omission gap removed (`omission=0`, which also forces a 1-frame
  blind spot): the temporal branch now sees t±1. d′ 4.312, amp 0.932 (5 seeds).
- **champ_l2** — champion with L2/MSE instead of Charbonnier; nothing else changed. d′ 4.289,
  amp 0.861 (3 seeds; the study's noisiest replicate set, σ = 0.041).
- **omission0_l2** — omission0 in L2, completing the loss × omission 2×2. d′ 4.305, amp 0.931 (3 seeds).
- **base64** — champion with the U-Net base width doubled (32 → 64, 3.15 M params). d′ 4.382,
  amp 0.880 (3 seeds) — the leading detection config.
- **om0_scale / om1_scale** — the two SUPPORT-scale runs (`support_all` wiring, L2, ~3.3 M updates)
  with `omission=0` / `omission=1`; the saturation A/B. Final-step d′ 4.361 / 4.361; amp 0.939 / 0.870.

**Pending (Tier 2/3).** SUPPORT wiring (`support_sd`, `support_all`), fuse width (`fuse256/512`),
temporal hand-off (`tmult8`), the 15× enlarged architecture (`arch`), and the spike-weight amp-lever
family (`weighted`, `l10g1/g2`, `archL10`, `hard1000`, `uL100`) plus their L2 pairs — defined in the
plan, not yet scored.

## B. Per-unit amplitude across models

`amp_ratio` for each ground-truth unit (rows, sorted by baseline separability = intrinsic unit
quality) across a representative model set; seeds averaged, full 21-model matrix in
`results/tables/perunit_amp.csv`.

| unit | base d′ | champion | omission0 | champ_l2 | omission0_l2 | base64 | om0_scale | om1_scale |
|---|---|---|---|---|---|---|---|---|
| 2143 | 12.53 | 1.005 | 0.990 | 1.001 | 0.987 | 1.011 | 0.984 | 1.009 |
| 793 | 8.57 | 1.003 | 0.962 | 1.005 | 0.957 | 1.012 | 0.949 | 1.023 |
| 1143 | 5.32 | 0.918 | 0.957 | 0.923 | 0.957 | 0.921 | 0.977 | 0.923 |
| 1300 | 4.07 | 0.872 | 0.952 | 0.873 | 0.950 | 0.880 | 0.948 | 0.868 |
| 1122 | 3.80 | 0.852 | 0.924 | 0.855 | 0.925 | 0.880 | 0.929 | 0.824 |
| 337 | 3.15 | 0.915 | 0.948 | 0.917 | 0.947 | 0.937 | 0.959 | 0.896 |
| 720 | 2.18 | 0.775 | 0.891 | 0.781 | 0.897 | 0.804 | 0.895 | 0.783 |
| 94 | 2.17 | 0.807 | 0.971 | 0.806 | 0.968 | 0.818 | 0.969 | 0.857 |
| 1129 | 2.14 | 0.670 | 0.831 | 0.675 | 0.834 | 0.723 | 0.877 | 0.701 |
| 664 | 1.04 | 0.773 | 0.889 | 0.772 | 0.890 | 0.817 | 0.903 | 0.805 |
| **mean** | — | 0.859 | 0.932 | 0.861 | 0.931 | 0.880 | 0.939 | 0.869 |

The dominant structure is **vertical, not horizontal**: strong units (top) return near 1.0 in *every*
model, weak units (bottom) are smoothed to 0.67–0.82 in the champion-body configs — amplitude
undershoot is a property of the *unit*, not the architecture (Spearman with baseline d′ = 0.94). The
one lever that shifts a column is the omission gap: `omission0` and `om0_scale` lift precisely the weak
units (1129 0.67 → 0.83/0.88, 94 0.81 → 0.97) while leaving strong units unchanged; `base64` lifts them
mildly; `champ_l2` tracks the champion almost exactly.

<!-- Heatmap F6 added by code/figures/make_perunit_heatmaps.py -> figures/f6_perunit_amp_heatmap.png -->

## C. Per-unit detection (Δd′) across models

Change in detectability from denoising, Δd′ = d′_deep − d′_raw, per unit × representative model (seeds
averaged; full matrix in `results/tables/perunit_dprime_delta.csv`). Negative = denoising made that
unit *harder* to detect.

| unit | base d′ | champion | omission0 | champ_l2 | omission0_l2 | base64 | om0_scale | om1_scale |
|---|---|---|---|---|---|---|---|---|
| 2143 | 12.53 | +0.730 | +0.087 | +0.684 | +0.023 | +1.038 | +0.205 | +0.580 |
| 793 | 8.57 | +0.056 | −0.298 | +0.196 | −0.327 | +0.365 | −0.050 | +0.088 |
| 1143 | 5.32 | −0.376 | −0.216 | −0.363 | −0.211 | −0.312 | −0.206 | −0.378 |
| 1300 | 4.07 | −0.480 | −0.260 | −0.483 | −0.258 | −0.421 | −0.249 | −0.480 |
| 1122 | 3.80 | −0.470 | −0.239 | −0.455 | −0.240 | −0.359 | −0.238 | −0.512 |
| 337 | 3.15 | −0.381 | −0.238 | −0.395 | −0.232 | −0.315 | −0.191 | −0.417 |
| 720 | 2.18 | −0.372 | −0.178 | −0.369 | −0.167 | −0.352 | −0.171 | −0.390 |
| 94 | 2.17 | −0.246 | −0.139 | −0.246 | −0.140 | −0.233 | −0.123 | −0.160 |
| 1129 | 2.14 | −0.496 | −0.267 | −0.482 | −0.265 | −0.419 | −0.225 | −0.424 |
| 664 | 1.04 | −0.166 | −0.105 | −0.165 | −0.105 | −0.139 | −0.093 | −0.133 |
| **mean** | — | −0.220 | −0.185 | −0.208 | −0.192 | −0.115 | −0.134 | −0.222 |

Two things stand out. First, **almost every cell is negative** — denoising reduces separability for
nearly every unit (the cost that motivates the whole study), with column means from −0.115 (base64) to
−0.22 (champion, om1_scale). Second, the damage is **not uniform**: it concentrates on the mid-to-weak
units (unit 1129 −0.50, 1300 −0.48 in the champion), while the single strongest unit (2143, baseline
d′ 12.5) actually *gains* (+0.73 champion, +1.04 base64) — a well-isolated unit whose denoised template
sharpens. `base64` damages least across the board (mean −0.115), consistent with capacity being the
detection lever; the omission configs sit between (−0.185 to −0.19), their amplitude rescue not
translating into detection.

<!-- Heatmap F7 added by code/figures/make_perunit_heatmaps.py -> figures/f7_perunit_dprime_delta_heatmap.png -->
