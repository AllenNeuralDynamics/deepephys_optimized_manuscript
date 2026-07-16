# Discussion

:::{note}
Conclusions from Tier 1 + Tier 2 + the SUPPORT-scale runs; the spike-weighting sweep (Tier 3) may
refine them.
:::

Optimising DeepInterpolation for spike detection turns on a small number of levers, and measuring them
directly against injected ground truth — in the band the denoiser is deployed in — sorts them cleanly.
Detection and waveform amplitude are two weakly-coupled axes driven by different knobs; denoising
leaves a hard residual detection deficit; and the validation loss is effectively blind to spikes. The
practical upshot is a short list of what actually moves detection versus what only moves amplitude —
and where the remaining deficit lives (the weak units).

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

Across every configuration, denoised output is less detectable than raw (−0.11 to −0.22 d′), even
though SNR improves throughout. "Denoising helps SNR but hurts detection" is thus a genuine property
of the blind-spot denoiser in its deployment band — and closing that gap is the real open problem,
with SNR a misleading target for sorting.

## What would move the ceiling

The detection deficit is not spread evenly — it is concentrated on the marginal, low-SNR units that
the shrinkage estimator flattens (the same units that dominate the amplitude undershoot). Capacity
helps because it gives the network more power to separate those units; the omission gap helps their
*amplitude* but not, at convergence, their *detectability*. That points the search for the remaining
−0.11 to −0.22 d′ at interventions that specifically protect weak-unit separability — spike-aware
losses and larger receptive fields — which is exactly what Tier 2/3 probes. The trajectories add a
further lever: **d′ is still rising at 3.3 M updates** (om1 by +0.30 past 14 k, steepest at its final
checkpoint), so **training length itself is a detection lever** — and the short-budget rankings are a
convergence-speed-biased screen, not converged values. Whether any of these clears the band, or
whether a residual denoising cost is intrinsic to the blind-spot objective, is the open question this
manuscript sets up.

## Recommended configuration

On the evidence so far, the pragmatic pick is **capacity** — the `base64` / `arch` family carries the
only clear, replicated detection gain — optionally with `omission=0` where waveform fidelity on weak
units matters more than the last fraction of detectability. L2 is a harmless default. The final
recommendation awaits the spike-weighting sweep (Tier 3), which targets weak-unit detection directly
and will either move the deficit or confirm it as a property of the blind-spot objective.
