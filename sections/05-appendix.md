# Appendix

## A. Model glossary

Except for the published `origdi` reference, screened models use the `fold` ephys denoiser (channels
scattered on the NP1 grid, width columns folded into features, a 1-D U-Net along probe depth, and a
probe-axis blind-spot branch). Every override is defined in the
[versioned analysis plan](reproducibility/regeneration-plan.md) §4.

**Scored model and control families.**
- **origdi** — the published temporal-only 2-D DeepInterpolation ephys network, trained and scored
  under the common in-band protocol. d′ 4.135 ± 0.010, amp 0.811 (3 seeds).
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
- **Matched R5 width/schedule/depth follow-up** — one seed each, with the R5 recipe and omission0 unless
  noted. `width96_g15` uses 96→144→216→324 (2.23 M params; d′ 4.360), `width96_cap384` uses
  96→192→384→384 (4.60 M; d′ 4.377), and full `width96` uses 96→192→384→768 (6.96 M;
  d′ 4.394). The growth1.5 and full omission1 twins reach 4.389 / 4.414 but lower the four-weak-unit
  mean and waveform amplitude relative to omission0. The √2 schedule (96→136→192→272; 1.83 M)
  reaches d′ 4.340 / 4.359 under omission0 / omission1; its omission1 twin likewise lowers the
  four-weak-unit mean and waveform amplitude. The nearly parameter-matched depth-2 schedule
  (96→192→384; 1.80 M) reaches 4.354 / 4.365; omission0 is +0.014 above √2 while tied with base64.
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
- **om0_scale / om1_scale** — the two long-duration runs (`support_all` wiring, L2, ~211.5 M training windows)
  with `omission=0` / `omission=1`. Final-step d′ 4.361 / 4.361; amp 0.931 / 0.870. These remain in
  the evidence inventory but are no longer the Figure 16 comparison.
- **w96_om0_scale / w96_om1_scale** — the selected Full96 body under the matched R5 recipe and
  Charbonnier objective, trained under a 54.0 M-window horizon with 11 scheduled states. This is the
  Figure 16 duration comparison; both routes use batch 256 and seed 0.
- **R0–R6 recipe family** — eight single-seed recipe-screen endpoints on `base64_om0`; R0, R1,
  and R5 each have two additional matched seeds. These change optimization, not architecture.
- **R8–R12 diagnostics and integration controls** — R8 records same-parameter gradient diagnostics;
  R9–R12 test adaptive accumulation, objective-preserving importance sampling, physical batch 256,
  and accumulated effective batch 256 against R1.
- **R13 NAF58** — a capacity-matched NAF temporal-block substitution against the R5 DoubleConv body;
  d′ 4.335 and 41% longer runtime than matched R5 seed 0.
- **Corrected weighting family** — seven matched-L2 weighted arms plus three unweighted
  `arch_l2_om0` seeds for context. The ten separately classified legacy weighted endpoints are
  scored but audit-only because their executed objective was Charbonnier rather than requested L2.

**Complete endpoint coverage.** `results/tables/master_table.csv` and its Markdown twin contain all
89 completed run endpoints with all detection and waveform metrics. The associated
`model_family_summary` and `table_coverage` tables make comparison boundaries and exclusions
explicit:

| experiment family | budget | endpoint runs |
|---|---|---:|
| architecture screen | ~18 M windows | 39 |
| width/schedule/depth follow-up | ~18 M windows | 9 |
| legacy weighting screen | ~18 M windows | 10 |
| recipe screen | ~18 M windows | 8 |
| recipe replication | ~18 M windows | 6 |
| gradient diagnostic | ~18 M windows | 1 |
| integration controls | ~18 M windows | 4 |
| NAF control | ~18 M windows | 1 |
| corrected weighting | ~18 M windows | 7 |
| duration diagnostics | 54.0 M and 211.5 M training windows | 4 |
| **total completed endpoints** |  | **89** |

The global d′ sort is an inventory, not an omnibus method ranking. Comparisons should stay within
the relevant family, body, budget, and seed context; the dedicated recipe, integration, NAF, and
weighting tables implement those matched comparisons. The intentionally aborted R7 PCGrad entry is
the sole row without an endpoint in `table_coverage`.

## B. Per-unit amplitude across models

`amp_ratio` for each ground-truth unit (rows, sorted by raw matched-filter separability) across a
representative set of the **original short-budget screen**; seeds averaged. The matched-R5 follow-up
is reported immediately below. The two long `support_all` runs are excluded here (different training
budget — see the duration section);
the full 10-unit × 89-endpoint matrix is in `results/tables/perunit_amp.csv`.

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
31 architecture-comparison entries the median correlation is 0.85 (range 0.62–0.94; original
21-model median 0.88). The omission gap shifts weak units most (1129 0.67 → 0.83, 94 0.81 → 0.97);
`base64` and `arch` lift them only mildly; `base32_l2` tracks base32 almost exactly;
and the combos `base64_om0` / `arch_om0` reproduce the full omission lift at high capacity (94 → 0.96–0.97,
1129 → 0.82–0.83).

**Matched-R5 width/schedule/depth follow-up, all ten endpoints.** This companion table prevents the
single-seed follow-up from disappearing behind the representative original-screen table:

```{include} ../results/tables/width_schedule_perunit_amp.md
```

Omission0 models are nearly tied in mean amplitude (0.938–0.941), whereas all four omission1
endpoints lower it (0.877–0.894), especially for the four weak units.

```{figure} figures/f6_perunit_amp_heatmap.png
:label: fig-perunit-amp
**Per-unit amplitude across all 31 architecture-comparison entries** (green ≈ preserved, red =
attenuated). The final ten columns are the matched-R5 reference and nine width/schedule/depth follow-ups.
The repeated vertical gradient shows strong dependence on unit quality; column shifts, especially for
omission variants, show that architecture also matters.
```

## C. Per-unit detection (Δd′) across models

Change in detectability from denoising, Δd′ = d′_deep − d′_raw, per unit × representative
original-screen model (seeds averaged; the matched-R5 follow-up is reported immediately below; full
10-unit × 89-endpoint matrix in `results/tables/perunit_dprime_delta.csv`). Negative = denoising made
that unit *harder* to detect.

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

**Matched-R5 width/schedule/depth follow-up, all ten endpoints.** Values are paired Δd′ from each endpoint's
common raw reference:

```{include} ../results/tables/width_schedule_perunit_dprime_delta.md
```

The omission0 capacity gain is concentrated in units 2143 and 793; the four weak-unit deltas remain
nearly unchanged. Omission1 further improves those two strong units while making each weak-unit mean
worse, which explains the all-unit versus weak-unit reversal.

```{figure} figures/f7_perunit_dprime_delta_heatmap.png
:label: fig-perunit-dprime
**Per-unit change in detectability Δd′ across all 31 architecture-comparison entries** (red =
denoising hurts, blue = helps). The final ten columns are the matched-R5 reference and nine
width/schedule/depth follow-ups. Almost every weak-unit cell is red; the strongest unit (2143) is the main
exception. Capacity raises the aggregate mean mainly through strong-unit gains, while omission0
retains the least-negative weak-unit columns.
```

## D. Manuscript comparison coverage

The manuscript uses two complementary comparison levels. Broad architecture figures compare the 21
seed-averaged original configurations plus the matched R5 reference and nine scored follow-ups (**31
comparison entries**). Family-specific figures preserve matched bodies, budgets, and objectives. The complete
tables retain **all 89 scored endpoints**, including audit-only confounded runs.

| manuscript surface | models included | models intentionally outside that surface |
|---|---|---|
| master, family, coverage, and full per-unit tables | all 89 scored endpoints | R7 PCGrad was aborted |
| Figures 1–2, qualitative benchmark and template diagnostics | raw + matched Full96 omission routes + seed-0 original DI; four displayed GT units | all other models; post-screen illustration is not held-out model evidence |
| Figure 3, d′ score distributions | Full96 omission0; complete scores for one strong and one weak unit | other endpoints; this panel explains the metric rather than comparing models |
| Figure 4, architecture definition/evolution | original DI, base32, R5 base64, one depth-2 and four depth-3 base96 designs, R13 NAF | wiring/loss variants that do not introduce a new depicted topology |
| Figures 5, 6, and 8; Figures 17–18 heatmaps | 21 original architecture configurations + matched R5 base64 + nine scored width/schedule/depth follow-ups = 31 | recipe replicates, integration/sampling controls, weighting interventions, and long-duration repeats |
| Figure 7 and matched-R5 tables | matched R5 base64 + nine scored width/schedule/depth follow-ups = 10 | models with a different body, recipe, or sample budget |
| Figures 9–11, recipe comparisons | R0–R6 screen; R0/R1/R5 matched replications where applicable | architecture and method controls |
| Figure 12, gradient diagnostics | R8 trajectory only | endpoints without same-parameter microbatch diagnostics |
| Figure 13, integration controls | R1 seed context + R9–R12 | unrelated architecture, weighting, and duration families |
| Figure 14, NAF control | R5 DoubleConv seeds + matched R13 NAF58 | non-capacity-matched architectures |
| Figure 15, corrected weighting | unweighted `arch_l2_om0` seed context + seven corrected arms | ten legacy weighting endpoints whose executed loss was confounded |
| Figure 16, duration diagnostic | two 54.0-M-window Full96 trajectories | legacy `support_all` duration pair and short-budget endpoints |
| Figure 19, template-support sensitivity | Full96 omission0/omission1 and seed-0 original DI; in-sample and two-fold event-level cross-fitted d′ | other models and sorter-level outcomes |
| Figures 20–22, learning-stage voltage and unit profiles | five repeated checkpoints from each 54.0-M-window Full96 trajectory; one fixed event and four fixed GT units | independent seeds, other events/units, and sorter-level outcomes |

This coverage rule prevents a missing model from being mistaken for a favorable comparison while
also avoiding omnibus plots that mix training replicates, unmatched objectives, or different budgets
as if they were independent architecture choices.

(appendix-template-support)=
## E. Template-support sensitivity

Figure 19 tests whether the raw-versus-denoised d′ result is caused by a template that is too large
in time or space. It does not replace the frozen endpoint used to rank all models: it measures how
that endpoint's interpretation changes across nested linear filters in three representative models.

```{figure} figures/template_support_sweep.png
:label: fig-template-support-sweep
**The all-unit Full96 d′ deficit is support-sensitive, whereas weak-unit losses persist.** Columns
show Full96 omission0, Full96 omission1, and seed-0 original DI. **Top**, denoised-minus-raw d′ versus
template duration at fixed top-2 raw-ranked channels. **Middle**, the same gap versus raw-ranked
channel count at fixed 1 ms. Grey circles are in-sample estimates; orange squares are deterministic
two-fold event-level cross-fitted estimates. Bands span the 10th–90th percentile over the 10 fixed GT
units; stars mark each estimator's frozen 4-ms/50%-amplitude endpoint. **Bottom**, cross-fitted gaps
at the frozen endpoint and at 1 ms/top-2 for all 10 units, the four post hoc weak units, and the other
six. Compact support makes the Full96 all-unit means neutral or positive but makes the weak-unit gaps
more negative. Original DI remains below raw overall at every tested support. This post hoc linear
filter sensitivity does not measure Kilosort precision, recall, or yield.
```

(appendix-learning-evolution)=
## F. Qualitative evolution during learning

Figures 20–22 revisit one fixed event and four fixed GT units at five scheduled
checkpoints from each Full96 duration run. Every stage uses the same raw voltage,
event, contacts, unit templates, and physical heatmap limits. The colored trace
bands are normalized by the raw peak-to-peak voltage only to make shape and
relative amplitude legible; each row reports its unnormalized stage/raw
peak-to-peak ratio. These are repeated observations from one training seed per
route, not independent replicates.

```{figure} figures/learning_voltage_evolution.png
:label: fig-learning-voltage-evolution
**The same-event voltage estimate forms rapidly, then changes more subtly at late
exposure.** Columns show raw voltage and five checkpoints spanning 34.6k to 54.0M
cumulative training windows; rows compare omission0 and omission1. All-probe and
local-contact heatmaps retain fixed physical voltage scales within their display
domains. The bottom band in each route overlays every checkpoint's peak-channel
trace on the same raw trace (gray), normalized by raw peak-to-peak voltage; labels
give the corresponding unnormalized amplitude ratio. Both routes are nearly
collapsed at 34.6k windows, acquire a recognizable event by 117.5k, and are close
to their mature same-event waveform by 400.6k. Later exposure mainly refines
amplitude and background structure rather than introducing a new event shape.
```

```{figure} figures/learning_unit_profile_evolution_om0.png
:label: fig-learning-units-om0
**Omission0 learns strong-unit templates first and preserves unit-dependent
attenuation.** Each row follows one fixed GT unit from raw through the five
checkpoints. Heatmaps share the raw unit's physical voltage range across columns;
the annotations report per-unit d′ and peak-channel amplitude ratio. Separated
trace bands overlay each stage on raw (gray), making the rapid transition between
34.6k and 400.6k windows visible without independently rescaling checkpoints.
Strong unit 2143 forms earliest and approaches raw amplitude most closely, while
weaker units 720 and 1129 remain more attenuated at the endpoint.
```

```{figure} figures/learning_unit_profile_evolution_om1.png
:label: fig-learning-units-om1
**Omission1 develops the same unit hierarchy more slowly and continues evolving
later.** Layout, units, domains, and scales match Figure 21 exactly. The route has
smaller intermediate amplitudes than omission0, especially at 117.5k and 400.6k
windows, but continues to improve through the two late checkpoints. The endpoint
therefore combines the duration trajectory's higher aggregate d′ with lower mean
amplitude preservation than omission0. This selected-event view illustrates that
trajectory; it does not establish sorter-level recovery or seed-level
reproducibility.
```
