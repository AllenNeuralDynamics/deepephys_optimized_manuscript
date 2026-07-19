# In-Domain Regeneration and Analysis Plan

:::{note}
This is a versioned working plan, not an immutable preregistration. It preserves the original
decisions and later report-driven reprioritization. The authoritative execution ledger is
`results/runs.csv`; the manuscript states which analyses are confirmatory, exploratory, or confounded.
:::

**Status:** architecture and initial recipe screens executed; later replication and optimization
experiments tracked in `results/runs.csv`.
Last updated: 2026-07-18

---

## 0. Why we are redoing everything (root cause)

The entire previous study trained DeepInterpolation on **wide-band** data and evaluated it on **high-passed AP-band** data — the denoiser was run outside its training domain.

**Evidence (verified):**
- Training asset for 116/121 runs = `ecephys_np1_benchmark` (`51f9b4df`, GCP) — a collection of **raw wide-band** NP1 sessions. PSD: **21% of power < 300 Hz** (retains LFP).
- Cluster DI-input / scoring = `sorters/np1/…ProbeC-AP_recording1_3/recording.zarr` (AWS) — **high-passed AP band**. PSD: **0.4% of power < 300 Hz**.
- Same 681532 ProbeC session, but only ~0.68 correlated after alignment; evidence figure = `psd_plot.png`.

**Consequence:** every absolute number (amp≈0.85 undershoot, the "DI lowers detection" puzzle) and every relative ranking was measured out-of-band. They must be re-established in-band before anything is written.

**What was actually fine:** the scoring/benchmark (always AP-band `recording1_3`), the surrogate metrics, the noise-floor method, the training/scoring infrastructure, and all figure/table scripts. Only the **training band** was wrong.

---

## 1. The one rule that fixes it

> **Train and evaluate in the SAME band, on the SAME recording DI is deployed on: `681532 ProbeC recording1_3` (AP-band).**

This is legitimate because DeepInterpolation is **self-supervised** (blind-spot; spike labels are used only for scoring, never training). Per-recording train=eval is the intended deployment — not leakage.

- **Train on:** `hybrid_np1/…ProbeC-AP_recording1_3/recording.zarr` (asset `384bf77c`, mount `hybrid_np1`) for **every** run.
- **Score on:** the same recording (`run_ckpt.sbatch` / `template_diag.sbatch`, unchanged).

---

## 2. Naming convention (avoid confusion)

- Training run label: **`ib_<config>_s<seed>`**  (ib = in-band). e.g. `ib_champion_s0`, `ib_omission0_s3`.
- CO computation id recorded in the tracker (Section 7).
- Checkpoints downloaded to `/tmp/ib/<label>/`, staged to HPC `checkpoints_sweep/ib/<label>/`.
- Scores on HPC: `traj_scores/ib_<label>_{dprime.csv,_diag.csv}`.

---

## 3. Shared training recipe (identical for all runs unless overridden)

| param | value |
|---|---|
| train_recording_path | `hybrid_np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3/recording.zarr` |
| data_asset (mount) | `384bf77c-f37b-4ab1-a008-03f10a0c49c9` (`hybrid_np1`) |
| capsule | `cb03dc8b-be21-42fe-aec0-e60607ff1bfe` |
| slice_start_s / slice_dur_s | 60 / 150 |
| val_slice_start_s / val_slice_dur_s | 0 / 60 |
| checkpoint_steps | 12 |
| geometry / blind_spot | fold / 1 |
| batch_size / lr / lr_scheduler | 64 / 0.001 / cosine |
| traces_dtype | float16 |
| **short run** | `train_chunks=4` (~0.28 M updates, ~1.5 h) |
| **long-duration diagnostic** | `train_chunks=47` (~3.3 M updates, ~17 h) |

**Champion base config** (all short runs start here, override as noted):
`base_channels=32, depth=3, bs_frames=3, bs_channels=64, bs_depth=5, fuse_channels=64, loss=charbonnier (eps=0.4), omission=1`.

---

## 4. Training jobs (39 total)

The **loss axis is now first-class**: every headline config is run in **both** charbonnier (champion default) and **L2 (MSE)**, giving **six charbonnier↔L2 matched pairs** (base, omission, capacity, best-arch, fuse, SNR-trap). The previous report under-explored L2; here it is compared on matched configs.

### Tier 1 — decides whether the thesis survives (19 runs)
| # | label | seeds | override vs champion | training loss | dur | why |
|---|---|---|---|---|---|---|
| 1 | ib_champion | 5 (s0–4) | — (reference) | charbonnier (eps=0.4) | ~1.5 h | seed variability, DI-vs-raw |
| 2 | ib_omission0 | 5 (s0–4) | `omission=0` (forces bs_frames=1) | charbonnier (eps=0.4) | ~1.5 h | omission gap (charbonnier) |
| 3 | ib_champ_l2 | 3 (s0–2) | `loss=l2` | **L2 (MSE)** | ~1.5 h | loss axis + L2 reference |
| 4 | ib_omission0_l2 | 3 (s0–2) | `omission=0 loss=l2` | **L2 (MSE)** | ~1.5 h | omission gap (L2) → loss×omission 2×2 |
| 5 | ib_base64 | 3 (s0–2) | `base_channels=64` | charbonnier (eps=0.4) | ~1.5 h | capacity axis |

### Tier 2 — sweep re-quantification (12 runs)
| # | label | seeds | override vs champion | training loss | dur | why |
|---|---|---|---|---|---|---|
| 6 | ib_support_sd | 1 | `bs_stage=1 bs_dense=1` | charbonnier (eps=0.4) | ~1.5 h | SUPPORT wiring (§4.5) |
| 7 | ib_support_all | 1 | `bs_stage=1 bs_dense=1 bs_multiscale=1` | charbonnier (eps=0.4) | ~1.5 h | SUPPORT wiring (§4.5) |
| 8 | ib_support_all_l2 | 1 | `bs_stage=1 bs_dense=1 bs_multiscale=1 loss=l2` | **L2 (MSE)** | ~1.5 h | best-arch × L2 (brackets RUN3/4) |
| 9 | ib_fuse256 | 1 | `fuse_channels=256` | charbonnier (eps=0.4) | ~1.5 h | fuse width (§4.3) |
| 10 | ib_fuse256_l2 | 1 | `fuse_channels=256 loss=l2` | **L2 (MSE)** | ~1.5 h | fuse × L2 |
| 11 | ib_fuse512 | 1 | `fuse_channels=512` | charbonnier (eps=0.4) | ~1.5 h | fuse-width trend (§4.3) |
| 12 | ib_tmult8 | 1 | `temporal_mult=8` | charbonnier (eps=0.4) | ~1.5 h | temporal hand-off (§4.3) |
| 13 | ib_base64_l2 | 1 | `base_channels=64 loss=l2` | **L2 (MSE)** | ~1.5 h | loss×capacity 2×2 (§4.1) |
| 14 | ib_no_norm | 1 | `norm=none` | charbonnier (eps=0.4) | ~1.5 h | normalization (§4.7) |
| 15 | ib_ho | 1 | `bs_frames=1` (omission stays 1) | charbonnier (eps=0.4) | ~1.5 h | blind-spot width (§4.6) |
| 16 | ib_arch | 1 | `base_channels=64 depth=4 bs_channels=128 bs_depth=7` | charbonnier (eps=0.4) | ~1.5 h | enlarged body (§4.2) |
| 17 | ib_arch_l2 | 1 | `base_channels=64 depth=4 bs_channels=128 bs_depth=7 loss=l2` | **L2 (MSE)** | ~1.5 h | enlarged body × L2 |

### Tier 3 — spike-weight amp lever (§4.4) — 6 runs
Only spike-weighting moved the amp axis in the old report (0.85 → 1.47). Re-map that response curve in-band.
All keep the **charbonnier (eps=0.4)** base loss; the spike-weight only re-weights it per sample.
| # | label | seeds | override vs champion | training loss | dur | why |
|---|---|---|---|---|---|---|
| 18 | ib_weighted | 1 | `spike_weight=3` | charbonnier (eps=0.4) ×spike-wt | ~1.5 h | magnitude weight λ=3 |
| 19 | ib_l10g1 | 1 | `spike_weight=10 spike_weight_gamma=1` | charbonnier (eps=0.4) ×spike-wt | ~1.5 h | λ=10, γ=1 |
| 20 | ib_l10g2 | 1 | `spike_weight=10 spike_weight_gamma=2` | charbonnier (eps=0.4) ×spike-wt | ~1.5 h | λ=10, γ=2 (peakier) |
| 21 | ib_archL10 | 1 | arch body + `spike_weight=10` | charbonnier (eps=0.4) ×spike-wt | ~1.5 h | capacity+weight → amp ~1.47 overshoot |
| 22 | ib_hard1000 | 1 | `spike_weight=1000 spike_weight_hard=1 spike_weight_thresh=<X>` | charbonnier (eps=0.4) ×spike-wt | ~1.5 h | hard binary gate — weighting's strongest |
| 23 | ib_uL100 | 1 | `spike_weight=100 spike_weight_car=1 spike_weight_thresh=<X>` | charbonnier (eps=0.4) ×spike-wt | ~1.5 h | unbiased position gate λ=100 |

**⚠ Exact `spike_weight_thresh` for #22/#23 must be copied verbatim from the original `hard1000` / `uL100` runs before launch (see §9 gate 2).**

### Long-duration diagnostic launched during execution (2 runs)
| # | label | CO id | override | training loss | dur | why |
|---|---|---|---|---|---|---|
| 24 | RUN3 ib_om0_scale | `ccf82c60-…` | support_all + `loss=l2` + `omission=0`, train_chunks=47 | **L2 (MSE)** | ~17 h | saturation §7 |
| 25 | RUN4 ib_om1_scale | `5eec6d19-…` | support_all + `loss=l2` + `omission=1 bs_frames=3`, train_chunks=47 | **L2 (MSE)** | ~17 h | saturation §7 |

**Original planned counts:** 37 short + 2 long-duration runs = **39 total**. Later adaptive additions
are recorded in `results/runs.csv`.
**Loss coverage:** 6 charbonnier↔L2 matched pairs (base, omission, capacity, best-arch, fuse, SNR-trap); pure L2 = 10 short + 2 scale; charbonnier = 27 short (6 of them spike-weighted).

### Exploratory architecture follow-up added 2026-07-18

`ib_r13_naf58` replaces only the center-excluded temporal U-Net's residual double-convolution stages
with 1-D NAF-style gated restoration blocks [@chen2022nafnet]. The center-frame `ConvHole1D` branch, pointwise fusion,
Charbonnier objective, R5 training recipe, sample budget, and checkpoint schedule remain fixed.
`base_channels=58` gives 3,162,950 parameters, +0.42% versus the 3,149,704-parameter R5/R0 body;
this is therefore the capacity-matched architecture control. It is exploratory and must pass the
same blind-spot derivative check and frozen d′/waveform trajectory scoring as the existing recipes.

### Deliberately excluded (were within-noise "does X stack on Y" combos in the old report)
`fuse128/1024`, `archL3`, `fuse256_tmult8`, `fuse256_wL3/fuse512_wL3`, `uL30/300`, `support_sd_l2`. Pull any back if a section needs it.

### Tier 2/3 execution policy (set at the Tier-1 decision gate, 2026-07-15)
The in-band Tier-1 + scale results reframe both the sweep and its training durations.

**Reprioritized (report-driven).** Detection lever = capacity; the deficit is on weak units; omission = amplitude lever; L2 neutral. Run the **ceiling-test wave first**: `arch`, `archL10`, `uL100`, `hard1000`, `base64_l2` + the new omission=0 combos. Deprioritize likely-nulls (`no_norm`, `tmult8`, `fuse512`, `l10g2`, `arch_l2`, confirmatory `*_l2` pairs).

**NEW omission=0 combos (option c).** omission=0 rescues weak-unit amplitude while capacity drives detection, but the two are never combined in the sweep. Add (each `omission=0` → forces `bs_frames=1`):
- `ib_base64_om0` — capacity + weak-unit amplitude rescue (deployment-champion candidate).
- `ib_arch_om0` — max capacity + rescue.
- `ib_uL100_om0` — weak-unit protection from loss and temporal design together.

**Duration policy (option b) — d′ is NOT converged at 3.3 M.** The scale trajectories show amplitude saturates by ~10³–10⁵ but **d′ keeps rising to 3.3 M** (om0 +0.11, om1 +0.30 from step 14 k; om1 steepest at its final step). Therefore:
- **Screen** = `train_chunks=4` (~0.28 M) for all Tier 2/3 — matches Tier 1, but is a **convergence-speed-biased screen**, never a converged measurement. Trajectory-score (12 ckpts) the ceiling / high-capacity / combo configs so convergence state is visible.
- **Scale-validate** the top 2–4 screened configs at `train_chunks=47` (~3.3 M) with full trajectory — the near-converged comparison for the champion call (even 3.3 M is a *lower bound* for slow configs).
- Never claim convergence from a short run; report the end-of-curve slope.

**Gate 2 still required** for `uL100` / `hard1000` / `uL100_om0`: copy exact `spike_weight_thresh` from the original runs before launch.

---

## 5. Quantification & comparison — IDENTICAL for every run

Every checkpoint is scored by the same protocol on the same frozen substrate. This makes metric
values comparable, but does not make interventions interchangeable: training budgets, bodies,
replication, and the legacy weighted-loss implementation differ and are separated in the manuscript.

### 5.1 Frozen evaluation substrate (never varies)
- **Recording:** `681532 ProbeC recording1_3` (AP-band) — the deployment recording (= the training recording; self-supervised).
- **Ground truth:** the 10 hybrid GT units; spike trains fixed.
- **Extraction seed = 0:** identical spike windows and background windows for every model, so metric differences reflect the model alone.
- **Baseline:** the raw (undenoised) AP-band recording, scored by the identical protocol.

### 5.2 Quantification catalog — every measure the previous report used
The **union** of the old report's quantifications (nothing new invented). All per-unit metrics are computed on each of the 10 GT units, then averaged.

**Detection (primary axis) — `run_ckpt.sbatch`**
| quantity | level | meaning |
|---|---|---|
| `dprime_deep` (d′_self) | per-unit → mean | matched-filter d′, template from **denoised** data — **PRIMARY** |
| `dprime_deep_fixed` (d′_fixed) | per-unit → mean | matched-filter d′ using the empirical raw-domain template — raw-template compatibility control |
| `dprime_raw` | per-unit → mean | raw (undenoised) in-band baseline = 4.497 |
| **Δd′ = dprime_deep − dprime_raw** | per-unit | change from denoising — **help (+) / hurt (−)** |

**Waveform fidelity — `template_diag.sbatch`**
| quantity | level | meaning |
|---|---|---|
| `amp_ratio` | per-unit → mean | denoised-template ÷ raw-template peak-to-peak on the empirical raw peak channel |
| `fwhm_ratio` | per-unit → mean | trough-width ratio (peak sharpness) |
| `temporal_cos` | per-unit → mean | denoised-vs-true waveform temporal-shape correlation |
| `spatial_cos` | per-unit → mean | denoised-vs-true spatial-footprint correlation |
| `snr_deep` | per-unit → mean | SNR of the denoised spike |

**Seed variability — derived from replicates**
| quantity | level | meaning |
|---|---|---|
| seed replicates (mean ± SD) | per config | champion×5, omission0×5, champ_l2×3, omission0_l2×3, base64×3 |
| SD_d′, SD_amp | per config | training-seed spread |
| base32 ±2-SD band | descriptive | screening reference, not a confidence interval or electrophysiological noise floor |
| Welch t-test p vs base32 | exploratory | unadjusted comparison for replicated configurations only |

**Deferred validation-loss decomposition.** A GT-support versus off-GT contrast is not used in the
manuscript because the off-GT pool mixes independent noise, reconstructible correlated background,
and spikes from unlabeled native units. A defensible component decomposition requires the aligned
pre-injection recording, the exact injected waveform, and a strategy for native-spike support.

**Training progress — 12 log-spaced checkpoints**
| quantity | meaning |
|---|---|
| metric-vs-updates trajectory | d′_self, d′_fixed, amp, fwhm vs training updates (saturation) |
| best_model vs metric-optimum ckpt | does val-loss selection pick the d′/amp optimum? (old: no) |

**Structure / metadata**
| quantity | meaning |
|---|---|
| Spearman(amp, baseline d′), vs peak size, vs SNR | the shrinkage law (old: +0.92 / +0.88 / +0.79) |
| params | absolute parameter count per model |

Both sbatch scripts are pinned to the 5.1 substrate (hardcoded S3 path, 10 units, seed 0). The surrogate applies **no** preprocessing (no CMR/highpass/motion): DI output is measured pre-CMR, matching the pipeline's DI-input stage.

### 5.3 Per-unit × model matrices — the effect on ALL units across ALL models
The headline "who gets smoothed / who gets harder to detect" view (old report Appendices B & C). Rows = the 10 GT units **sorted by baseline d′ (unit quality)**; columns = every scored model; a **mean** row at the bottom.
- **Amplitude matrix** (App B eq.) — `amp_ratio` per unit × model + heatmap (green ≈1.0 preserved / red smoothed). Shows the vertical quality gradient (strong units ~0.97, weak units 0.66–0.83).
- **Detection matrix** (App C eq.) — `dprime_deep` per unit × model (absolute) **and** a **Δd′ = dprime_deep − dprime_raw** heatmap (red = DI hurts, blue = DI helps). Exposes per-unit collapses (old: `arch` erased unit 337, 3.15→0.16).
- **No extra runs:** every diagnostic run already stores per-unit values (§5.4); these matrices are
	pure collation across all completed endpoints (78 in the current revision).
- Because every model is a column, an intervention's effect is read **across the whole unit population at once**, not just at the 10-unit mean.

### 5.4 Per-run outputs (uniform)
- **best_model.pt → one master-table row** with every §5.2 metric.
- **12 checkpoints → trajectories** for the loss×omission saturation set: champion, omission0, champ_l2, omission0_l2 (1 seed each) + RUN3, RUN4. All other configs: best_model only.
- **Per-unit values (10 per metric) always retained** → feed the §5.3 matrices, heatmaps and paired stats.
- Saved as `traj_scores/ib_<label>_{dprime.csv,_diag.csv}`; collated by the `/tmp/collate_traj.py` pattern.

### 5.5 Replicates and descriptive seed variability
- Multi-seed configs — champion×5, omission0×5, champ_l2×3, omission0_l2×3, base64×3 — report **mean ± SD**.
- Report mean ± seed SD. The base32 ±2-SD band is a descriptive screen reference; Welch comparisons
	are exploratory and unadjusted, and single-seed rows receive no inferential error bar.

### 5.6 Comparison procedure (the same questions for every config)
1. **vs raw** — Δd′, amp_ratio, fwhm_ratio: does DI help or hurt?
2. **vs base32** — Δ on every metric: how large is the observation relative to seed variability?
3. **loss pairs (charbonnier ↔ L2)** — the six matched pairs: does the loss change the outcome?
4. **per-unit (§5.3)** — where does the effect land on the quality gradient (shrinkage: Spearman amp vs baseline d′)?
5. **trajectories** — ordering and saturation over training updates.
Differences are reported with their replication and uncertainty status rather than converted to a
binary "real/within noise" label.

### 5.7 Aggregation & provenance
- **Aggregate = arithmetic mean over the 10 GT units** (verified to reproduce the previous report's anchors).
- Every number traces run label → CO id → checkpoint file → CSV → collation script, recorded in §7.
- **Caveat (unchanged):** the surrogate detects on DI output *before* CMR, whereas the deployment KS4 detects *after* CMR — a measurement-stage gap noted once, not re-run per config.

---

## 6. Analysis, tables & figure collection (regenerated in-band)

Every §5 quantification gets a table and/or a plot. This is the in-band regeneration of the old report's figure set (8 data plots + 2 schematics) plus 2 new plots.

### 6.1 Tables
- **T1 — Master results** (sorted by d′_self, read against ±2σ): per model → `amp_ratio`, `d′_self`, `d′_fixed`, `fwhm_ratio`, `temporal_cos`, `spatial_cos`, `snr_deep`, `params`, **`training loss`**.
- **T2 — Seed variability**: SD_d′ and SD_amp for replicated configurations plus exploratory Welch comparisons.
- **T4 — Per-unit amp matrix** (App B) and **T5 — Per-unit d′ / Δd′ matrix** (App C): 10 units × all models, mean row.

### 6.2 Figure collection (one+ per quantification family)
| fig | plot | quantification (§5) | old fig / asset |
|---|---|---|---|
| F1 | d′ ranking — 21 short-budget architectures, base32 ±2 seed SD, raw line | detection + seed variability | Fig 3 / `fig1_dprime_ranking` |
| F2 | loss × capacity 2×2 | detection, loss axis | Fig 4 / `fig2_loss_capacity_2x2` |
| F3 | **loss-axis pairs — 6 charbonnier↔L2 Δ (NEW)** | loss axis (added pairs) | new |
| F4 | peak-channel template-SNR change vs matched-filter Δd′ | metric dissociation | Fig 5 / `f4_snr_vs_dprime` |
| F5 | amp vs unit quality: all architectures + omission contrast | per-unit amp / Spearman | Fig 7 / `f5_amp_vs_quality` |
| F6 | per-unit amp heatmap (units × all models) | §5.3 per-unit (App B) | Fig 9 / `fig6_perunit_heatmap` |
| F7 | per-unit Δd′ heatmap (units × all models) | §5.3 per-unit (App C) | Fig 10 / `fig7_dprime_delta_heatmap` |
| F8 | loss×omission trajectories — d′ & amp vs updates | training progress / saturation | Fig 8 / `fig_trajectory` |
| F9 | val-loss / overfit curves + best-ckpt markers | checkpoint selection | Fig 6 / `fig_overfit` |
| F10 | PSD band-mismatch (train vs eval) **(NEW)** | provenance / the band correction | new / `psd_plot` |

The current architecture schematic is regenerated by `code/figures/architecture_evolution.py`;
the historical omission-gap schematic is retained unchanged.

### 6.3 Decision read-outs
**(a) does DI still lower d′ in-band?  (b) does the omission gap survive (both losses)?** — answered from T1 + F1 + F8 at the Tier-1 gate.

---

## 7. Status tracker (fill as we go)

| label | CO id | state | ckpt dl | scored | d′_deep | amp | notes |
|---|---|---|---|---|---|---|---|
| ib_champion_s0 | | | | | | | |
| … (per run) | | | | | | | |
| RUN3 ib_om0_scale | ccf82c60-43c4-4829-9984-8d41e4639fc2 | running | | | | | in-domain om0 |
| RUN4 ib_om1_scale | 5eec6d19-f063-4f9d-a17a-b11da5a65869 | init | | | | | in-domain om1 |

---

## 8. New report structure (written AFTER in-band numbers land)
The outline is **conditional on the Tier-1 read-out**:
- **If DI still lowers detection in-band** → same skeleton as the old report (Background → Methods → sweep → omission gap → conclusions), re-quantified, plus a Methods subsection documenting the wide-band→AP-band correction (PSD figure).
- **If DI is neutral/helpful in-band** → the central premise changes; restructure around "DI in its correct band" and what the earlier out-of-band result was.
- Either way: **new file** `di_ephys_report_v2.md`, PDF build reuses `/tmp/build_report_pdf.py`.
- **Appendices retained (regenerated in-band):** A model glossary; **B per-unit amplitude matrix (all units × all models)**; **C per-unit detection Δd′ matrix** — the effect on every unit across every model.

---

## 9. Execution gates (do NOT skip)
1. **[ ] Review & approve this plan.** ← we are here.
2. **[ ] Look up exact `spike_weight_thresh` (and any gate params) for `hard1000` / `uL100` from the original CO runs' parameters — paste verbatim into §4 #22/#23.**
3. **[ ] Launch Tier 1 (19 runs)** + let RUN3/RUN4 finish.
4. **[ ] Score Tier 1 + RUN3/RUN4 → read the two decision questions.**
5. **[ ] Gate:** thesis survives? → set Tier 2/3 scope + report structure.
6. **[x] Launch Tier 2 + Tier 3 and score; legacy weighted-loss rows later marked confounded.**
7. **[ ] Regenerate figures/tables from in-band scores.**
8. **[ ] Write `di_ephys_report_v2.md`, build PDF, verify.**
