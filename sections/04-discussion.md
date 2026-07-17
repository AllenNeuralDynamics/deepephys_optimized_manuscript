# Discussion

:::{note}
Conclusions from the complete in-band sweep — Tier 1 + Tier 2 + the Tier 3 spike-aware loss family +
the original-architecture reference + the SUPPORT-scale runs.
:::

Optimising DeepInterpolation for spike detection turns on a small number of levers, and measuring them
directly against injected ground truth — in the band the denoiser is deployed in — sorts them cleanly.
Detection and waveform amplitude are two weakly-coupled axes driven by different knobs; denoising
leaves a hard residual detection deficit; and the validation loss is effectively blind to spikes. The
practical upshot is a short list of what actually moves detection versus what only moves amplitude —
and where the remaining deficit lives (the weak units). Measured against the **original**
DeepInterpolation architecture, the optimised network recovers **+0.23 d′ and +0.13 amplitude** (and
+0.36 d′ on the weak units) — most of the way to raw — even as it gives up SNR.

## Two axes with different levers

Detection and waveform amplitude are two real, weakly-coupled axes, and each is moved by a different
knob. Detection is moved most by **capacity** (base64 +0.105 d′, ~7σ); the training loss is neutral
(L2 +0.012, NS); and the temporal **omission** design barely moves detection (+0.035 d′ Charbonnier,
nil in L2). Amplitude, by contrast, is moved almost entirely by the omission design (+0.07) and is
flat to capacity and loss. The decoupling has a concrete mechanism: amplitude is governed by a
per-unit **shrinkage estimator** (Spearman 0.94 with unit quality; see Results), so it moves only
under interventions that change what the blind spot can see *locally* — the adjacent t±1 frames —
whereas detection tracks the model's overall capacity to separate spike from background.

## The omission gap is an amplitude lever, not a detection lever

Hiding versus revealing the adjacent t±1 frames (`omission`) is often assumed to be the decisive
temporal choice for detection. It is not: in-band its detection effect is small (+0.035 d′), and at
SUPPORT scale the d′ gap **closes by 3.3 M** (om0 = om1 = 4.361 — though om1 is still rising there).
Revealing t±1 mainly **accelerates convergence** and **improves amplitude** rather than raising the
detection ceiling; its real, large effect is on waveform amplitude, concentrated on the weak units.

## Denoising still costs detection

Across every configuration, denoised output is less detectable than raw (−0.09 to −0.36 d′), even
though SNR improves throughout — most starkly in the **original architecture** (`origdi`), which posts
the *highest* SNR yet the *lowest* detection of any model. "Denoising helps SNR but hurts detection" is
thus a genuine property of the blind-spot denoiser in its deployment band — and closing that gap is the
real open problem, with SNR a misleading target for sorting.

## What is left of the deficit

The detection deficit is not spread evenly — it is concentrated on the marginal, low-SNR units that
the shrinkage estimator flattens (the same units that dominate the amplitude undershoot). Capacity
helps because it gives the network more power to separate those units; the omission gap helps their
*amplitude* but not their *detectability*. The most direct remaining intervention — a **spike-aware
loss** that up-weights the reconstruction error at spikes — was designed precisely to protect weak-unit
separability, and it **fails to**: swept across two orders of magnitude on the best body, no setting
clears the noise floor, aggressive weighting *hurts*, and the weak units it targets do not move
(+0.01–+0.02 d′; Results). That the residual deficit resists even a loss aimed straight at it suggests
it is **intrinsic to the blind-spot objective** — the estimator cannot report a peak it is structurally
forbidden from seeing — rather than a tuning oversight. One lever does remain unexhausted: **training
length** — d′ is still rising at 3.3 M updates (om1 by +0.30 past 14 k, steepest at its final
checkpoint), so the short-budget rankings are a convergence-speed-biased screen and a fully-converged
model may recover more. Whether that closes the last −0.09 to −0.36 d′, or whether a residual cost is
permanent, is the open question this manuscript leaves.

## Recommended configuration

The recommendation is now settled by the full sweep: pick **capacity** — the `base64` / `arch` family
carries the only clear, replicated detection gain — and add **`omission=0`** when waveform fidelity on
weak units matters (it lifts amplitude to ~0.94 for a detection cost inside the noise floor); the best
all-round body is `arch_l2_om0`. L2 is a harmless default, and **spike-aware weighting is not
recommended** — it does not help detection and, past small weights, degrades it. Every one of these is
a large gain over the original architecture; the residual sub-raw deficit is, on current evidence, a
property of the blind-spot objective, addressable (if at all) only by longer training or a change to
the objective itself.

For the **training recipe**, the efficiency sweep adds one clear recommendation: **batch 256 with lr
2e-3 and 5 % warmup** is 4.4× faster to the d′ = 4.30 operating point than the AdamW/cosine baseline
with no cost to the final ceiling. Lion, one-cycle, and the tuned AdamW variants are either slower or
cap below the target — prefer the large-batch AdamW recipe for any new training run.
