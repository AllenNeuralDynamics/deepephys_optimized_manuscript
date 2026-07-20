# Frozen endpoint scoring

This directory contains the complete scoring path used for the manuscript, not
only submission wrappers. It evaluates one checkpoint against the frozen AP-band
hybrid benchmark (`recording1_3`, 10 injected GT units, extraction `seed=0`). GT
labels are never used during self-supervised training; they enter only here.

| file | role |
|---|---|
| `detection_metrics.py` | event/background sampling, empirical templates, matched-filter projections, d′, AUC, optional plotting arrays |
| `run_hybrid_s3.py` | executable S3 endpoint driver; writes the per-unit d′ CSV |
| `template_diag.py` | empirical-template amplitude, width, lag, temporal/spatial fidelity, and NPZ template arrays |
| `run_with_inference.py` | ensures inference/model imports come from an explicitly pinned checkout |
| `run_ckpt.sbatch` | frozen GPU job for `run_hybrid_s3.py` |
| `template_diag.sbatch` | frozen GPU job for `template_diag.py` |
| `score_best.sh` | submits one d′ job and one waveform job for a checkpoint |
| `export_qualitative_examples.py` | reproduces a committed endpoint, then exports compact raw/denoised traces, templates, and score distributions |
| `export_qualitative_examples.sbatch` | GPU/S3 wrapper for that qualitative export |

The scoring/model checkout used for the width, schedule, and depth endpoints is
inference commit `808d7fa`. Computation IDs, HPC job IDs, checkpoint hashes, and
the exact benchmark paths are in [`data/provenance.md`](../../data/provenance.md)
and [`results/runs.csv`](../../results/runs.csv).

## Detection calculation

For each GT unit:

1. Select at most 100 GT spike times using NumPy RNG seed 0.
2. Sample 200 background centers with the same RNG and reject centers within one
   4-ms analysis window of **any** injected GT event.
3. Extract 1.5 ms before through 2.5 ms after every center on all 384 channels.
4. Average the raw hit windows. Select channels whose raw empirical-template
   peak-to-peak amplitude is at least 50% of the peak channel, retaining at most
   the 24 strongest channels.
5. Flatten and L2-normalize the empirical template. The score for each event or
   background window is its dot product with that matched filter.
6. Compute

   $$
   d' = \frac{\mu_{\mathrm{GT}}-\mu_{\mathrm{bg}}}
              {\sqrt{\left(\sigma^2_{\mathrm{GT}}+\sigma^2_{\mathrm{bg}}\right)/2}}.
   $$

All 100 GT-event scores and all 200 background scores enter through their means
and population variances. The calculation does **not** slide across the trace,
count threshold crossings, count local extrema, select maxima, or use an
extreme-value statistic. AUC is also reported as the threshold-free probability
that a GT score exceeds a background score.

`dprime_raw` uses the raw empirical template on raw windows. `dprime_deep` uses
the denoised empirical template on denoised windows, approximating a sorter that
learns its templates after denoising. `dprime_deep_fixed` projects denoised
windows onto the raw empirical template to test raw-shape compatibility.

The empirical template and the GT hit scores reuse the same events, making
absolute d′ optimistically in-sample. This bias is identical across the frozen
comparisons; a cross-fitted endpoint remains a planned validation.

### Why can d′ decrease after denoising?

Lower pointwise voltage noise is not sufficient for higher d′. Denoising can
attenuate or reshape the spike, reducing the difference between mean GT and
background projection scores. It can also leave structured background that
projects onto the learned template. d′ improves only if the separation of the
two complete score distributions grows relative to their pooled spread. The
committed score-distribution figure makes these terms visible for a strong and a
weak unit.

## Waveform calculation

`template_diag.py` independently selects up to 200 events per unit with seed 0,
uses the same raw-template channel rule, and writes:

- `amp_ratio`: denoised/raw empirical-template peak-to-peak on the raw peak channel;
- `fwhm_ratio`: trough full width at half minimum;
- `temporal_cos`: cosine between rank-1 temporal profiles;
- `spatial_cos`: cosine between rank-1 spatial footprints;
- lag, peak-channel correlation, spatial-amplitude correlation, footprint spread,
  and rank-1 energy fractions.

The accompanying NPZ retains raw and denoised empirical templates for every GT
unit. These are empirical averages from the noisy hybrid recording, not the
noise-free injected source templates.

## Run one endpoint on HPC

From the manuscript repository, stage this complete directory to its canonical
scratch location:

```bash
rsync -rt --no-perms --chmod=u+rwx -e "ssh -o BatchMode=yes" \
   code/scoring/ \
   jeromel@hpc-login:/allen/aind/scratch/jeromel/ephys_denoising/manuscript_scoring/
```

Then run on HPC. The wrappers fail if any required vendored file is absent;
they do not fall back to older scripts in the scratch root.

```bash
BASE=/allen/aind/scratch/jeromel/ephys_denoising
SCORING=$BASE/manuscript_scoring
INFERENCE=$BASE/aind-ephys-deepinterpolation-inference-808d7fa/code

sbatch "$SCORING/run_ckpt.sbatch" \
   <checkpoint.pt> "$BASE/traj_scores/<label>_dprime.csv" \
   "$INFERENCE" "$SCORING"

sbatch "$SCORING/template_diag.sbatch" \
   <checkpoint.pt> "traj_scores/<label>" \
   "$INFERENCE" "$SCORING"
```

Both jobs use the S3 benchmark recorded in provenance. Aggregate manuscript
values are arithmetic means over the 10 per-unit rows; the rows are retained for
the appendix matrices.

## Rebuild the qualitative figures

The GPU/S3 export validates that its d′ values reproduce the committed full96
omission0 endpoint within `1e-6` before writing anything:

```bash
BASE=/allen/aind/scratch/jeromel/ephys_denoising
SCORING=$BASE/manuscript_scoring
INFERENCE=$BASE/aind-ephys-deepinterpolation-inference-808d7fa/code

sbatch "$SCORING/export_qualitative_examples.sbatch" \
   "$SCORING/export_qualitative_examples.py" \
   "$SCORING/detection_metrics.py" \
   "$BASE/checkpoints_sweep/ib/ib_w96_om0_s0/best_model.pt" \
   "$BASE/traj_scores/ib_w96_om0_s0_dprime.csv" \
   "$BASE/qualitative/full96_om0_examples.npz" \
   "$BASE/qualitative/full96_om0_examples_metadata.json" \
   "$INFERENCE"
```

Once the compact artifact exists, figure regeneration is local and does not
require S3, SpikeInterface, a checkpoint, or a GPU:

```bash
python code/figures/qualitative_examples.py
```

## Tests

```bash
python code/tests/test_detection_metrics.py
python -m py_compile \
   code/scoring/detection_metrics.py \
   code/scoring/run_hybrid_s3.py \
   code/scoring/template_diag.py \
   code/scoring/export_qualitative_examples.py
bash -n code/scoring/*.sbatch code/scoring/score_best.sh
```

The focused tests verify the exact pooled-variance equation, invariance to a
shared affine voltage transform, and recording/sorting frame alignment.

`validation_loss_headroom.py` is a separate exploratory audit. Its off-GT set
mixes independent noise, correlated background, and unlabeled native spikes and
is not used for the primary endpoint conclusions.
