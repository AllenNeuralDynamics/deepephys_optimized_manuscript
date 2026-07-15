# Discussion

:::{note}
In-band conclusions from Tier 1 + the SUPPORT-scale runs; the architecture/loss sweep (Tier 2/3) may
refine them.
:::

## Two axes, re-measured in-band

The prior study's framing — detection and amplitude as weakly-coupled axes — **holds in-band, but the
levers change hands.** Detection is moved most by **capacity** (base64 +0.105 d′, ~7σ); the training
loss is neutral (L2 +0.012, NS); and the temporal **omission** design barely moves detection
(+0.035 d′ Charbonnier, nil in L2). Amplitude, by contrast, is moved almost entirely by the omission
design (+0.07) and is flat to capacity and loss. The two axes are real; the earlier ranking of what
drives each was distorted by the train/deploy band mismatch.

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

## Recommended configuration

On the in-band evidence so far, the pragmatic pick is the champion body with **doubled capacity
(base64)** — the only lever with a clear detection gain — optionally with `omission=0` where waveform
fidelity matters. The final recommendation awaits the Tier 2/3 sweep (SUPPORT wiring, fuse width,
enlarged architecture, spike-weighting), which may yet move the detection deficit.
