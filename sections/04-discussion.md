# Discussion

:::{note}
In-band conclusions from Tier 1 + the SUPPORT-scale runs; the architecture/loss sweep (Tier 2/3) may
refine them.
:::

Re-running the study in the denoiser's own band leaves the *structure* of the prior conclusions intact
— two decoupled axes, a hard detection deficit, a spike-blind validation loss — while overturning the
single claim the earlier report built its recommendation on. The lever that supposedly broke the
detection wall (the omission gap) is, in-band, an amplitude lever whose detection advantage vanishes
with training; the modest lever the earlier report had already found (capacity) is in fact the only
reproducible way to raise detection. The correction is not cosmetic — it changes which knob a
practitioner should turn.

## Two axes, re-measured in-band

The prior study's framing — detection and amplitude as weakly-coupled axes — **holds in-band, but the
levers change hands.** Detection is moved most by **capacity** (base64 +0.105 d′, ~7σ); the training
loss is neutral (L2 +0.012, NS); and the temporal **omission** design barely moves detection
(+0.035 d′ Charbonnier, nil in L2). Amplitude, by contrast, is moved almost entirely by the omission
design (+0.07) and is flat to capacity and loss. The two axes are real, and the decoupling has a
concrete mechanism: amplitude is governed by a per-unit **shrinkage estimator** (Spearman 0.94 with
unit quality; see Results), so it moves only under interventions that change what the blind spot can
see *locally* — the adjacent t±1 frames — whereas detection tracks the model's overall capacity to
separate spike from background. The earlier ranking of what drives each axis was distorted by the
train/deploy band mismatch.

## The omission gap was over-credited out of band

The earlier report's headline — `omission=0` as "the largest single lever," +0.204 d′ — does **not**
survive the in-band correction. In-band its detection effect shrinks ~6× and, at SUPPORT scale, the
d′ gap **closes entirely** (om0 = om1 = 4.361 at 3.3 M updates): revealing t±1 mainly **accelerates
convergence** and **improves amplitude**, rather than raising the detection ceiling. This is the
clearest single consequence of scoring in the correct band.

## Denoising still costs detection

Across every in-band configuration, DI output is less detectable than raw (−0.11 to −0.22 d′). The
"denoising helps SNR but hurts detection" puzzle is therefore a genuine property of the denoiser in
its own band, not an out-of-domain artifact — and closing that gap (rather than the omission design)
is the real open problem. SNR improves throughout, reinforcing that SNR is a misleading target for
sorting.

## What would move the ceiling

The detection deficit is not spread evenly — it is concentrated on the marginal, low-SNR units that
the shrinkage estimator flattens (the same units that dominate the amplitude undershoot). Capacity
helps because it gives the network more power to separate those units; the omission gap helps their
*amplitude* but not, at convergence, their *detectability*. That points the search for the remaining
−0.11 to −0.22 d′ at interventions that specifically protect weak-unit separability — spike-aware
losses and larger receptive fields — which is exactly what Tier 2/3 probes. Whether any of them clears
the band, or whether a residual denoising cost is intrinsic to the blind-spot objective, is the open
question this manuscript sets up.

## Recommended configuration

On the in-band evidence so far, the pragmatic pick is the base32 body with **doubled capacity
(`base64`)** — the only lever with a clear, replicated detection gain (+0.105 d′) — optionally with
`omission=0` where waveform fidelity matters more than the last fraction of detectability. L2 is a
harmless default. The final recommendation awaits the Tier 2/3 sweep (SUPPORT wiring, fuse width, the
15× architecture, spike-weighting), which may yet move the detection deficit or confirm it as a
property of the method.
