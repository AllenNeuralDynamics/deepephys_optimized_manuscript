# Appendix

## A. Model glossary

Except for the published `origdi` reference, screened models use the `fold` ephys denoiser (channels
scattered on the NP1 grid, width columns folded into features, a 1-D U-Net along probe depth, and a
probe-axis blind-spot branch). Every override is defined in the
[versioned analysis plan](reproducibility/regeneration-plan.md) §4.

**Scored (Tier 1 + Tier 2 + SUPPORT scale).**
- **base32** — the reference: `base_channels=32, depth=3`, 3-frame temporal blind spot
  (`omission=1`), `bs_channels=64 / bs_depth=5`, `fuse_channels=64`, Charbonnier loss. In-band
  d′ 4.277 ± 0.015, amp 0.859 (5 seeds).
- **omission0** — compound routing change: t±1 move into the temporal U-Net, t±31 are removed, and
  the spatial branch changes from three frames to the center only. d′ 4.312, amp 0.932 (5 seeds).
- **base32_l2** (`ib_champ_l2`) — base32 with L2/MSE instead of Charbonnier; nothing else changed. d′ 4.289,
  amp 0.861 (3 seeds; the study's noisiest replicate set, σ = 0.041).
- **omission0_l2** — omission0 in L2, completing the loss × omission 2×2. d′ 4.305, amp 0.931 (3 seeds).
- **base64** — base32 with the U-Net base width doubled (32 → 64, 3.15 M params). d′ 4.382,
  amp 0.880 (3 seeds).
- **arch** — the enlarged body: base 64, depth 4, `bs_channels=128`, `bs_depth=7`. Its single run has
  the highest observed short-screen mean (d′ 4.409, amp 0.871); L2 twin `arch_l2` is 4.407.
- **base64_om0 / arch_om0** — the two capacity bodies with the omission gap removed (`omission=0`,
  1-frame blind spot). d′ 4.359 / 4.367, amp 0.934 / 0.936 — capacity's detection with omission0's
  amplitude rescue.
- **SUPPORT wiring / fuse width / temporal (Tier 2, single seed).** `support_sd` 4.313, `support_all`
  4.312, `support_all_l2` 4.295 (larger, denser blind-spot branch); `fuse256` 4.265, `fuse256_l2`
  4.282, `fuse512` 4.244 (wider fusion); `tmult8` 4.257 (deeper temporal hand-off); `no_norm` 4.284;
  `ho` 4.272 (1-frame blind spot, omission on). Only the unreplicated `support_sd` and `support_all`
  observations exceed the upper edge of the base32 ±2-seed-SD reference; amp is ~0.86 throughout.
- **om0_scale / om1_scale** — the two long-duration runs (`support_all` wiring, L2, ~3.3 M updates)
  with `omission=0` / `omission=1`. Final-step d′ 4.361 / 4.361; amp 0.931 / 0.870.

## B. Per-unit amplitude across models

`amp_ratio` for each ground-truth unit (rows, sorted by raw matched-filter separability) across a
representative set of the **short-budget** models; seeds averaged. The two long `support_all` runs are
excluded here (different training budget — see the duration section);
the full matrix across every run is in `results/tables/perunit_amp.csv`.

| unit | base d′ | base32 | omission0 | base32_l2 | omission0_l2 | base64 | arch | base64_om0 | arch_om0 |
|---|---|---|---|---|---|---|---|---|---|
| 2143 | 12.53 | 1.005 | 0.990 | 1.001 | 0.987 | 1.011 | 1.016 | 0.991 | 0.988 |
| 793 | 8.57 | 1.003 | 0.962 | 1.005 | 0.957 | 1.012 | 1.015 | 0.962 | 0.971 |
| 1143 | 5.32 | 0.918 | 0.957 | 0.923 | 0.957 | 0.921 | 0.915 | 0.959 | 0.963 |
| 1300 | 4.07 | 0.872 | 0.952 | 0.873 | 0.950 | 0.880 | 0.872 | 0.947 | 0.951 |
| 1122 | 3.80 | 0.852 | 0.924 | 0.855 | 0.925 | 0.880 | 0.883 | 0.929 | 0.934 |
| 337 | 3.15 | 0.915 | 0.948 | 0.917 | 0.947 | 0.937 | 0.925 | 0.953 | 0.948 |
| 720 | 2.18 | 0.775 | 0.891 | 0.781 | 0.897 | 0.804 | 0.786 | 0.897 | 0.893 |
| 94 | 2.17 | 0.807 | 0.971 | 0.806 | 0.968 | 0.818 | 0.812 | 0.964 | 0.973 |
| 1129 | 2.14 | 0.670 | 0.831 | 0.675 | 0.834 | 0.723 | 0.687 | 0.833 | 0.823 |
| 664 | 1.04 | 0.773 | 0.889 | 0.772 | 0.890 | 0.817 | 0.798 | 0.910 | 0.910 |
| **mean** | — | 0.859 | 0.932 | 0.861 | 0.931 | 0.880 | 0.871 | 0.934 | 0.936 |

The dominant repeated structure is vertical: strong units return near 1.0 across models, whereas weak
units are attenuated more. Architecture still matters, as shown by the spread within each row and the
systematic shift of omission variants. In base32, Spearman correlation with raw d′ is 0.94; across all
21 short-budget architectures the median correlation is 0.88 (range 0.66–0.94). The omission gap
shifts weak units most (1129 0.67 → 0.83, 94 0.81 → 0.97); `base64` and `arch` lift them only mildly;
`base32_l2` tracks base32 almost exactly;
and the combos `base64_om0` / `arch_om0` reproduce the full omission lift at high capacity (94 → 0.96–0.97,
1129 → 0.82–0.83).

```{figure} figures/f6_perunit_amp_heatmap.png
:label: fig-perunit-amp
**Per-unit amplitude across the 21 short-budget architectures** (green ≈ preserved, red = attenuated).
The repeated vertical gradient shows strong dependence on unit quality; column shifts, especially for
omission variants, show that architecture also matters.
```

## C. Per-unit detection (Δd′) across models

Change in detectability from denoising, Δd′ = d′_deep − d′_raw, per unit × representative model (seeds
averaged; full matrix in `results/tables/perunit_dprime_delta.csv`). Negative = denoising made that
unit *harder* to detect.

| unit | base d′ | base32 | omission0 | base32_l2 | omission0_l2 | base64 | arch | base64_om0 | arch_om0 |
|---|---|---|---|---|---|---|---|---|---|
| 2143 | 12.53 | +0.730 | +0.087 | +0.684 | +0.023 | +1.038 | +1.345 | +0.309 | +0.286 |
| 793 | 8.57 | +0.056 | −0.298 | +0.196 | −0.327 | +0.365 | +0.564 | −0.167 | −0.101 |
| 1143 | 5.32 | −0.376 | −0.216 | −0.363 | −0.211 | −0.312 | −0.343 | −0.194 | −0.204 |
| 1300 | 4.07 | −0.480 | −0.260 | −0.483 | −0.258 | −0.421 | −0.440 | −0.245 | −0.222 |
| 1122 | 3.80 | −0.470 | −0.239 | −0.455 | −0.240 | −0.359 | −0.392 | −0.202 | −0.175 |
| 337 | 3.15 | −0.381 | −0.238 | −0.395 | −0.232 | −0.315 | −0.284 | −0.196 | −0.189 |
| 720 | 2.18 | −0.372 | −0.178 | −0.369 | −0.167 | −0.352 | −0.376 | −0.178 | −0.173 |
| 94 | 2.17 | −0.246 | −0.139 | −0.246 | −0.140 | −0.233 | −0.302 | −0.144 | −0.146 |
| 1129 | 2.14 | −0.496 | −0.267 | −0.482 | −0.265 | −0.419 | −0.484 | −0.272 | −0.291 |
| 664 | 1.04 | −0.166 | −0.105 | −0.165 | −0.105 | −0.139 | −0.164 | −0.089 | −0.088 |
| **mean** | — | −0.220 | −0.185 | −0.208 | −0.192 | −0.115 | −0.088 | −0.138 | −0.130 |

Two things stand out. First, **most cells are negative** — denoising reduces separability for most
unit–architecture pairs, with column means from −0.088 (arch) to
−0.22 (base32). Second, the damage is **not uniform**: it concentrates on the mid-to-weak
units (unit 1129 −0.50, 1300 −0.48 in base32), while the single strongest unit (2143, baseline
d′ 12.5) actually *gains* — and gains more with capacity (+0.73 base32, +1.04 base64, **+1.35 arch**) —
a well-isolated unit with improved event separation under the denoised-domain template. `arch` has the least-negative displayed mean
(**−0.088**) and `base64` is next (−0.115), but much of their mean advantage comes from strong units.
Among the four weakest units, omission0 and the `*_om0` combinations improve more than capacity alone.
The intervention ranking therefore depends on whether the objective is the all-unit mean or
protection of marginal units.

```{figure} figures/f7_perunit_dprime_delta_heatmap.png
:label: fig-perunit-dprime
**Per-unit change in detectability Δd′** (units × architectures; red = denoising hurts, blue = helps).
Almost every cell is red; the strongest unit (2143) is the main exception. `arch` has the
least-negative displayed column mean, while omission variants give the largest weak-unit gains.
```
