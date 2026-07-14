# Discussion

:::{warning} Placeholder
Framed as the hypotheses under test; conclusions are confirmed or revised once the in-domain scores
land.
:::

## Two decoupled axes (hypothesis)

The prior study proposed that **detection** (`d′_self`) and **amplitude fidelity** (`amp_ratio`) are
distinct axes: within the champion's temporal design, detection was nearly flat to most knobs (only
capacity survived replication), while amplitude was invariant to capacity/loss/wiring. If this holds
in-domain, the practical levers reduce to a small set; if the band correction changes it, the
"denoising hurts detection" framing itself is revisited.

## The omission gap as the dominant lever (hypothesis)

The largest prior effect was architectural, not a loss or capacity change: revealing t±1
(`omission=0`) lifted detection **and** amplitude at once, concentrated on the marginal low-SNR units
that are hardest to sort. This manuscript tests whether that lever survives in-domain and at
SUPPORT-scale training, in both Charbonnier and L2.

## Headroom and training length

Because spikes are a vanishingly small fraction of samples, the validation loss is a poor ruler for
spike quality and the "best" checkpoint drifts. The re-measured in-band headroom decomposition
determines whether this still holds once the LFP is removed, and the saturation trajectories test the
undertraining hypothesis directly.

## Recommended configuration

The emerging recommendation (to be confirmed in-domain) is the champion body with `omission=0`,
optionally with L2. The final recommendation, its effect size, and its per-unit profile are reported
once scoring completes.
