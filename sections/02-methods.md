# Methods

## Frozen hybrid benchmark

Every model is scored on one fixed benchmark built with the **hybrid ground-truth** approach
[@buccino2020spikeinterface]: a real Neuropixels 1.0 recording (`ecephys_681532`, ProbeC) into which
**10 ground-truth units** were injected at known times and amplitudes. Because the true spike times
and waveforms are known, detection and waveform fidelity are measured directly, without running a
spike sorter (the matched-filter surrogate below stands in for one). The evaluation is identical for
all models — the same 10 units and the same `seed=0` subsample of 100 spikes/unit and 200 background
windows — so **every difference between models reflects training, not the evaluation.** Exact asset
paths are in [Data & compute provenance](data/provenance.md).

## The in-domain rule

DeepInterpolation is a self-supervised denoiser, so it must be evaluated in the band it is deployed
in: a model trained on one frequency content and applied to another runs outside its training domain,
and its behaviour there need not match. Because spike sorting operates on the high-passed **AP band**,
we enforce a single rule throughout:

> **Train and evaluate in the same band, on the same recording the model is deployed on**
> (`681532` ProbeC `recording1_3`, AP-band).

This is legitimate because DeepInterpolation is self-supervised (blind-spot): ground-truth spike
labels are used only for *scoring*, never for training. Per-recording train = evaluate is the intended
deployment, not label leakage.

## Architecture and the swept variants

**The `base32` reference, layer by layer.** The input `(B, 63, 384)` (63 frames × 384 channels) is
scattered onto the 192 × 4 probe grid and split into the two branches:

| component | setting |
|---|---|
| geometry | `fold` — 4 probe columns folded into features; 1-D U-Net along the 192 depth rows |
| temporal window | ±30 frames; `omission=1` hides the target and t±1, so 60 neighbour frames are used |
| temporal U-Net | `base_channels=32`, `depth=3` (32 → 64 → 128 → 256 bottleneck, then decode with skips) |
| spatial blind-spot | `bs_channels=64`, `bs_depth=5` dilated `ConvHole1D` (centre tap zeroed) over the `bs_frames=3` centre frames |
| fuse head | pointwise 1×1, `fuse_channels=64` (blind-spot-safe merge of the two branches) |
| loss | Charbonnier |
| size | ~0.85 M parameters (U-Net ≈ 87%) |

```{mermaid}
flowchart TD
    IN["Input context<br/>(B, 63, 384)"] --> SC["grid.scatter<br/>(B, 63, 192, 4)<br/>384 ch → 192×4 grid"]
    SC --> SPLIT{"split frames"}
    SPLIT -->|"60 neighbour frames"| FN["fold → (B, 240, 192)<br/>60 frames × 4 cols"]
    SPLIT -->|"3 centre frames {t-1,t,t+1}"| FC["fold → (B, 12, 192)<br/>3 frames × 4 cols"]
    subgraph UNET["TEMPORAL U-Net — centre + t±1 EXCLUDED — conv along DEPTH (H=192)"]
        FN --> ST["stem DoubleConv1d<br/>240→32, k3"]
        ST --> D1["Down1 pool/2 · 32→64 @H=96"]
        D1 --> D2["Down2 pool/2 · 64→128 @H=48"]
        D2 --> D3["Down3 pool/2 — bottleneck<br/>128→256 @H=24"]
        D3 --> U3["Up3 →128 @H=48 (+skip)"]
        U3 --> U2["Up2 →64 @H=96 (+skip)"]
        U2 --> U1["Up1 →32 @H=192 (+skip)"]
        U1 --> UH["head Conv1d 32→4, k1"]
    end
    UH --> UO["u : (B, 4, 192)"]
    subgraph BS["BLIND-SPOT branch — centre frame — dilated HOLE-convs (centre tap zeroed)"]
        FC --> H1["ConvHole1D k3 d=1<br/>12→64 · GELU"]
        H1 --> H2["ConvHole1D k3 d=2<br/>64→64 · GELU"]
        H2 --> H3["ConvHole1D k3 d=4"]
        H3 --> H4["ConvHole1D k3 d=8"]
        H4 --> H5["ConvHole1D k3 d=16"]
    end
    H5 --> BO["b : (B, 64, 192)<br/>±31 rows, own row EXCLUDED"]
    UO --> FUSE["FUSE — pointwise 1×1 only<br/>concat 4+64=68 → 68→64→64→4 (GELU)"]
    BO --> FUSE
    FUSE --> Y["y : (B, 4, 192)"]
    Y --> UF["unfold + grid.gather"]
    UF --> OUT["Denoised centre<br/>(B, 1, 384)"]
```

**The two-branch `base32` (`FoldDeepInterp1D`) denoiser.** The neighbour frames — with the target *and*
its immediate t±1 neighbours excluded — drive the **temporal U-Net** along probe depth; the three
centre frames drive the **blind-spot branch** of five dilated `ConvHole1D` layers whose centre kernel
tap is forced to zero (the "holes"), so a channel's prediction never uses its own value. A
pointwise-only (1×1) fuse head merges the two branches, which keeps the blind spot intact. Each swept
variant below changes exactly one piece of this diagram.

**How each swept variant is built.** Every variant changes exactly one part of this reference (all
enumerated in [the pre-registered design](reproducibility/regeneration-plan.md)):

| axis | variant(s) | change (override) |
|---|---|---|
| capacity (U-Net width) | `base64` | `base_channels=64` |
| capacity (both branches) | `arch` | `base_channels=64 depth=4 bs_channels=128 bs_depth=7` (~12.6 M params) |
| fuse-head width | `fuse256`, `fuse512` | `fuse_channels=256 / 512` |
| temporal-feature width | `tmult8` | `temporal_mult=8` |
| input normalisation | `no_norm` | `norm=none` |
| blind-spot frames | `ho` | `bs_frames=1` (1-frame blind spot) |
| SUPPORT wiring | `support_sd`, `support_all` | `bs_stage=1 bs_dense=1` (+ `bs_multiscale=1`) |
| temporal omission | `omission0` | `omission=0` — the temporal branch sees t±1 (forces `bs_frames=1`) |
| loss | `*_l2` pairs | `loss=l2` |
| spike-aware loss | `weighted`, `l10g1/g2`, gate / hard | `spike_weight`, `spike_weight_gamma`, `spike_weight_thresh`, `spike_weight_car`, `spike_weight_hard` (below) |

The **SUPPORT wiring** options restore three pieces the `fold` reference dropped relative to the
published SUPPORT denoiser [@eom2023support]: dense re-injection of the centre input (`bs_dense`),
staging the temporal feature into the blind-spot branch (`bs_stage`), and a parallel multi-scale
stack (`bs_multiscale`). The **spike-aware loss** multiplies the reconstruction loss at spike-like
samples by `1 + spike_weight·|nbr|^gamma`, where `|nbr|` is the centre-excluded neighbour amplitude (a
spike detector that keeps the blind spot unbiased); a saturating position gate
(`spike_weight_thresh > 0`, with `spike_weight_car` / `spike_weight_hard`) lets the weight grow large
without biasing amplitude upward. Across the sweep, capacity and the enlarged `arch` body span
**0.85 M → 12.6 M parameters**.

## Quantification (identical for every run)

All models are scored by one uniform protocol (full catalog and formulas in
[the pre-registered design](reproducibility/regeneration-plan.md), §5). Per-unit metrics are computed on each of the 10
GT units, then averaged.

**Detection (primary).** Matched-filter d′: a per-unit template is slid over the trace as a matched
filter, and d′ is the standardized separation between the filter's response at true spike times and
at background — higher means easier to detect. It is computed two ways. `d′_self` uses a template
built from the *denoised* data (what a sorter operating on denoised traces actually sees), while
`d′_fixed` uses the *true/raw* template as a control: if `d′_self` rises but `d′_fixed` does not, the
apparent gain is a self-consistent artifact (the denoiser sharpened its own template) rather than
real recoverable signal. The raw-data reference is **d′ = 4.497**, and **Δd′ = d′_deep − d′_raw**
measures the change from denoising — negative means denoising made a unit *harder* to detect.

**Waveform fidelity.** `amp_ratio` (denoised ÷ true peak-to-peak on the peak channel), `fwhm_ratio`
(trough width), `temporal_cos` / `spatial_cos` (shape and footprint correlation), and `snr_deep`.

**Per-unit × per-model resolution.** Both amplitude and detection are reported as matrices — rows =
the 10 units sorted by baseline separability, columns = every model — so an intervention's effect is
read across the whole unit population, not just at the 10-unit mean (appendix
[Appendix B/C](sections/05-appendix.md)).

## The noise floor: why single runs cannot be trusted

Two facts make any single training run an unreliable ranking. First, training is stochastic — GPU
non-determinism, random initialisation and data order. Second, the validation loss is nearly flat
with respect to spikes: because spikes occupy only ~0.065% of (channel, sample) points, reconstructing
every spike *perfectly* would move the whole-frame validation loss by a rounding error, far below its
seed-to-seed noise. The loss-selected "best" checkpoint is therefore effectively a random draw along a
plateau — which is exactly why models are scored with the spike-level d′ surrogate, not the loss.

We therefore retrain the key configurations across **3–5 seeds**; base32's 5-seed standard
deviation defines the significance scale (σ), and a difference is treated as real only if it clears
**~2σ**, confirmed by a Welch t-test against base32. The spike-fraction decomposition that makes
the loss spike-blind is **re-measured in-band** (Tier 2/3), since removing the LFP changes the
fraction of variance spikes occupy and could sharpen — though not eliminate — the effect.

:::{note} In-band anchors
Raw-data reference **d′ = 4.497**; in-band base32 **d′ = 4.277 ± 0.015** (5 seeds) → decision band
**±2σ ≈ 0.03 d′** (σ_amp ≈ 0.004). See Results.
:::
