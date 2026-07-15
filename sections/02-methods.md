# Methods

## Frozen hybrid benchmark

Every model is scored on one fixed benchmark: a real Neuropixels 1.0 recording
(`ecephys_681532`, ProbeC) into which **10 ground-truth units** were injected at known times and
amplitudes (a *hybrid* recording). Because the true spike times and waveforms are known, detection
and waveform fidelity are measured directly, without running a spike sorter (the matched-filter
surrogate below stands in for one). The evaluation is identical for all models — the same 10 units
and the same `seed=0` subsample of 100 spikes/unit and 200 background windows — so **every difference
between models reflects training, not the evaluation.** Exact asset paths are in
[Data & compute provenance](data/provenance.md).

## The in-domain rule (the correction)

The prior study trained on **wide-band** data (retaining LFP) but scored on **high-passed AP-band**
data: a power-spectral-density check shows ~21% of training-data power below 300 Hz versus ~0.4% in
the AP-band evaluation recording. The denoiser therefore ran outside its training domain, and every
prior absolute number and ranking is out-of-band.

This manuscript enforces a single rule:

> **Train and evaluate in the same band, on the same recording the model is deployed on**
> (`681532` ProbeC `recording1_3`, AP-band).

This is legitimate because DeepInterpolation is self-supervised (blind-spot): ground-truth spike
labels are used only for *scoring*, never for training. Per-recording train = evaluate is the
intended deployment, not label leakage.

<!-- ```{figure} figures/f10_psd_band_mismatch.png
:label: fig-psd
Power spectral density of the training data vs the AP-band evaluation recording — the band mismatch.
``` -->

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

We therefore retrain the key configurations across **3–5 seeds**; the champion's 5-seed standard
deviation defines the significance scale (σ), and a difference is treated as real only if it clears
**~2σ**, confirmed by a Welch t-test against the champion. The spike-fraction decomposition that makes
the loss spike-blind is **re-measured in-band** (Tier 2/3), since removing the LFP changes the
fraction of variance spikes occupy and could sharpen — though not eliminate — the effect.

:::{note} In-band anchors
Raw-data reference **d′ = 4.497**; in-band champion **d′ = 4.277 ± 0.015** (5 seeds) → decision band
**±2σ ≈ 0.03 d′** (σ_amp ≈ 0.004). See Results.
:::
