# Discussion

On this hybrid benchmark, replacing the original temporal-only network with the modern two-branch
package substantially improves matched-filter detection and empirical waveform amplitude. Yet every
short-budget denoised output remains below the raw all-unit d′. The important qualification is that
the answer depends on which units are averaged: width leads the ten-unit mean, whereas the compound
omission0 routing has the larger effect on the four weakest units and on their waveform amplitude.

## The optimization target changes the apparent winner

The replicated `base64` comparison gives the largest fixed-budget gain in the all-unit mean (+0.105
d′). It does not give the largest weak-unit gain: base64 improves that subgroup by +0.034, while
omission0 and `arch_l2_om0` improve it by ~+0.15. Capacity's mean advantage is partly driven by large
positive changes in already-strong units. Conversely, omission0 can help weak units while reducing
the gains of strong units, yielding only +0.035 in the all-unit mean. Because omission0 moves t±1 into
the temporal branch, removes t±31, and changes spatial-branch input, the effect is not attributable to
one frame pair alone.

This is not a contradiction; it is an aggregation issue. A deployment objective that values total
mean d′ favors width in this screen. An objective that protects marginal units favors adjacent-frame
context. Empirical-template amplitude follows raw unit quality across the complete architecture set
(median per-model Spearman ρ = 0.88), consistent with conditional-mean shrinkage, and t±1 context
raises the lower end of that distribution. The four-unit threshold was selected during analysis, so
the subgroup result should be replicated on a larger, prespecified weak-unit cohort.

## Template SNR is not a detection objective

The former "SNR trap" phrasing conflated template SNR with the amount of noise removed. Here template
SNR is peak-to-peak empirical-template amplitude divided by background SD on one channel; it changes
if either numerator or denominator changes. Matched-filter d′ instead separates multichannel temporal
event scores. Across 21 architectures their changes are essentially uncorrelated (Spearman ρ = 0.02),
and `origdi` combines the highest template SNR with the lowest d′. The appropriate conclusion is not
that greater noise suppression necessarily harms detection, but that this SNR ratio cannot select a
model for the matched-filter objective.

## Training optimization remains open

The initial recipe experiment is a single-seed compound screen. R5 has the lowest estimated time to
d′ = 4.30, but it changes physical batch, learning rate, and warmup together, and checkpoint
times are inferred. Replications with exact telemetry and batch-only/fixed-effective-batch controls
are underway. Until those results land, no recipe is established as faster in expectation.

R8 provides a measurement-level reason to test those controls: microbatch gradients are strongly
aligned early but weakly aligned or conflicting late, and late noise-scale estimates sometimes exceed
the physical batch. The estimates are intermittent and unstable with four microbatches, so they
motivate rather than determine the controller. An adaptive integration run now holds its prior horizon
when a measurement is unresolved; fixed effective batch, physical batch, and corrected importance
sampling provide the corresponding controls. The rank-three sample covariance cannot establish that
Shampoo, K-FAC, or another non-diagonal preconditioner is warranted.

The duration evidence is narrower still: it consists of one om0 and one om1 `support_all` + L2
trajectory. In those runs amplitude stabilizes early while d′ remains duration-sensitive, and om1 is
still rising at 3.3 M updates. This motivates long-budget validation, but does not show that `arch`,
`base64`, or R5 has the same trajectory. Equality of the two d′ means at their last checkpoint also
does not establish equal asymptotes.

## Limitations

First, architecture and recipe choices were developed and evaluated on one recording with ten
injected units. Fixed extraction makes comparisons reproducible but does not protect against adaptive
overfitting of design decisions to this benchmark. Second, matched-filter d′ is a detection surrogate
measured before common-median referencing; it is not sorter-level precision, recall, unit yield, or
waveform stability. Third, many Tier 2 rows have one training seed, exploratory Welch tests are not
multiple-comparison corrected, and the weak-unit analysis contains four post hoc selected units.
Finally, long-duration evidence uses a different body from the architecture and recipe candidates.

## Practical interpretation

For this benchmark and short budget, `base64` is the best replicated choice for the all-unit mean;
omission0 is the clearest tested configuration for preserving weak-unit amplitude and detectability;
`arch_l2_om0` is a balanced candidate that combines those properties but does not dominate every unit.
The modern package outperforms `origdi` under the matched-filter proxy on this benchmark. Stronger claims
require a prespecified held-out recording, exact replicated recipe
timing, long-budget validation of the selected body, and end-to-end spike-sorter evaluation.
