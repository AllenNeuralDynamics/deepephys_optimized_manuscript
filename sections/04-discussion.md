# Discussion

On this hybrid benchmark, replacing the original temporal-only network with the modern two-branch
package substantially improves matched-filter detection and empirical waveform amplitude. Yet every
short-budget denoised output remains below the raw all-unit d′ under the frozen 4-ms endpoint. The
support sensitivity shows that this aggregate direction can reverse for compact filters. The more
important qualification is that
the answer depends on which units are averaged: width leads the ten-unit mean, whereas the compound
omission0 routing has the larger effect on the four weakest units and on their waveform amplitude.
The matched R5 follow-up extends that distinction: full base96 raises the ten-unit omission0 mean,
but its gain is concentrated in the six units outside the weak subgroup and costs substantially more
compute.

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
context. Empirical-template amplitude follows raw unit quality across all 31 architecture-comparison
entries (median per-model Spearman ρ = 0.85; 0.88 in the original 21-model screen), consistent with
conditional-mean shrinkage, and t±1 context raises the lower end of that distribution. The four-unit
threshold was selected during analysis, so the subgroup result should be replicated on a larger,
prespecified weak-unit cohort.

The width/schedule/depth follow-up reinforces capacity as an all-unit lever but narrows the
mechanism. The small depth-3 √2 pyramid is −0.018 d′ versus base64 despite its wider first stage, but
the nearly parameter-matched depth-2 `96→192→384` model is tied with base64 and exceeds √2 by +0.014
d′, with a descriptive paired-unit interval above zero. Extra depth is therefore not intrinsically
beneficial at matched parameter count; allocating channels across scales matters. Within the
depth-3 base96 schedules, 1.5× growth is effectively tied with base64, cap384 is intermediate, and
only the full 96→192→384→768 pyramid has a descriptive paired-unit interval above zero versus
base64. That conditional ordering implicates deeper channel capacity rather than base width alone. The
full model's +0.036 d′ gain accompanies a 74.5% increase in Code Ocean runtime over base64, while the
four-weak-unit mean changes by only +0.002. Under omission1, all four paired models raise the all-unit
mean but lower weak-unit d′, amplitude, and temporal waveform cosine. Capacity therefore does not
remove the aggregation tradeoff identified in the original screen.

## Template SNR is not a detection objective

The former "SNR trap" phrasing conflated template SNR with the amount of noise removed. Here template
SNR is peak-to-peak empirical-template amplitude divided by background SD on one channel; it changes
if either numerator or denominator changes. Matched-filter d′ instead separates multichannel temporal
event scores. Across 21 architectures their changes are essentially uncorrelated (Spearman ρ = 0.02),
and `origdi` combines the highest template SNR with the lowest d′. The appropriate conclusion is not
that greater noise suppression necessarily harms detection, but that this SNR ratio cannot select a
model for the matched-filter objective. The matched-R5 follow-up strengthens that qualification:
its ten endpoints have ρ = 0.70 when all units are averaged but ρ = −0.67 for the four weak units.
The relationship can therefore reverse under a deployment-relevant change in aggregation even
within one controlled model family.

The support sweep adds a second qualification: matched-filter d′ is not a support-invariant property
of a recording. Compact 1-ms, one- or two-channel filters remove the aggregate Full96 deficit in both
the in-sample and event-level cross-fitted analyses. This supports the concern that the 4-ms
multichannel endpoint includes dimensions that do not contribute equally to raw and denoised
separability. It does not reduce to raw-template overfitting, because the reversal survives when
templates and channel rankings are learned on separate training events. However, the reversal is
concentrated in strong units; compact support makes the weak-unit gap more negative, and original DI
remains below raw. The defensible interpretation is therefore narrower than either extreme: the
frozen endpoint overstates the modern models' aggregate disadvantage, while the weak-unit problem is
robust and can be hidden by all-unit averaging.

## Training optimization has only a provisional compound-recipe lead

The matched-seed replications narrow the initial recipe result. Warmup alone is not supported as an
endpoint improvement: R1 averages −0.0031 d′ relative to R0 and improves only one of three paired
seeds. R5 averages +0.0043 d′, improves all three paired seeds, has the smallest seed SD, and reaches
d′ = 4.30 after 2.25 M median windows versus 5.38 M for R0. The endpoint effect is nevertheless small
relative to seed spread, and with three pairs the exact two-sided sign-flip result cannot be smaller
than p = 0.25. R5 changes physical batch, learning rate, and warmup together, so it remains a
provisional compound-recipe lead rather than evidence for any component in isolation.

R8 provides a measurement-level reason to test larger late effective batches: microbatch gradients
are strongly aligned early but weakly aligned or conflicting late, and some late noise-scale estimates
exceed the physical batch. The estimates are intermittent and unstable with four microbatches, so
they motivate rather than determine the controller. R9 responds by moving from effective batch 64
through 128 and 512 before settling at 256. It preserves matched seed-0 d′ with 37.5% fewer optimizer
updates, but does not improve the endpoint or durable convergence, and serial accumulation barely
changes wall time. Adaptive accumulation is therefore an update-compression mechanism here, not a
demonstrated detection gain. The rank-three sample covariance cannot establish that Shampoo, K-FAC,
or another non-diagonal preconditioner is warranted.

The completed controls further narrow the interpretation. Corrected importance sampling (R10) is
endpoint-neutral and more than doubles runtime because it screens four candidate batches. Physical
batch 256 (R11) and accumulated effective batch 256 (R12) both use about one quarter as many updates
as R1 and finish within +0.0026 d′ of each other despite different physical batches. This implicates
the effective-batch/update regime, not physical batching itself, in their lower endpoints. All four
method-control endpoints remain inside the observed R1 seed spread, and each has only one seed; none
supplants the replicated R5 recipe.

## Modern blocks and spike weighting are not automatic gains

The capacity-matched NAF control makes a direct architectural point. R13 holds the R5 recipe and all
non-temporal components fixed, yet ends 0.0223 d′ below matched R5 seed 0, below all three R5 seeds,
and takes 41% longer. Its final validation loss is essentially tied with R5. A block successful in
image restoration therefore does not automatically transfer to blind-spot ephys denoising, and a
matched reconstruction loss is not evidence for matched detection.

The corrected weighting screen reaches the same broader conclusion from the objective side. Soft
magnitude λ = 3 is the only arm with a positive d′ delta (+0.0055), but that single-seed endpoint is
inside the unweighted seed spread. Larger magnitude weights and every gated rule lower d′. At high
weights, amplitude can rise while temporal and spatial template fidelity collapse, so emphasizing
large center-excluded neighbours can optimize a waveform statistic while harming event separation.
Soft λ = 3 is worth replication as a lead; the present screen does not establish it as an
improvement, and the stronger weighting rules should not be advanced.

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
waveform stability. The primary self-template d′ estimates each denoised template from the same 100
hit events it scores, making its absolute value in-sample optimistic; the fixed raw-template metric
and paired comparisons provide complementary checks. Event-level cross-fitting and support sweeps
reduce that concern for three representative models, but they remain post hoc, reuse one background
set, and show that aggregate d′ depends on the chosen linear filter. Neither the frozen nor compact
filter reproduces Kilosort's whitening, temporal search, template competition, or clustering.
Third, many Tier 2 rows, every R9–R13 method control, and each weighted arm have one training seed;
the nine width/schedule/depth follow-ups also have one training seed, and their paired-unit bootstrap
intervals resample fixed benchmark units rather than independent recordings;
exploratory Welch tests are not multiple-comparison corrected, the recipe replication has only three
paired seeds, and the weak-unit analysis contains four post hoc selected units. Finally,
long-duration evidence uses a different body from the architecture and recipe candidates.

## Practical interpretation

For this benchmark and short budget, `base64` is the best replicated choice for the all-unit mean;
omission0 is the clearest tested configuration for preserving weak-unit amplitude and detectability;
`arch_l2_om0` is a balanced candidate that combines those properties but does not dominate every unit.
In the matched R5 follow-up, full base96 gives the highest omission0 all-unit d′ (4.394), but requires
6.96 M parameters and 4.63 h end-to-end versus 3.15 M and 2.65 h for base64, with no material
weak-unit gain. Growth1.5 retains base64-level d′ at 40.5% lower runtime than full base96; cap384 is
the intermediate option. Depth2 also retains base64-level d′ with 43% lower runtime than full
base96 and 43% fewer parameters than base64, but its 2.67 h runtime is essentially the same as
base64 because parameter count does not determine convolution cost. Omission1 reaches still higher all-unit means but should not be selected
when weak-unit detection or waveform amplitude is the deployment objective.
Among the replicated training recipes, R5 is the provisional compound-recipe choice and warmup alone
is not supported. Adaptive accumulation and importance sampling do not improve the endpoint; fixed
and physical effective-batch-256 controls both finish lower. The capacity-matched NAF substitution is
slower and lower in d′, while soft λ = 3 weighting remains only an unreplicated lead and stronger
weighting is harmful. The modern package still outperforms `origdi` under the matched-filter proxy on
this benchmark. The 4-ms endpoint is retained for uniform model ranking, but compact-support
sensitivity should accompany claims about absolute raw-versus-denoised detectability. Stronger claims
require a prespecified held-out recording, long-budget validation of the selected body, and
end-to-end spike-sorter evaluation.
