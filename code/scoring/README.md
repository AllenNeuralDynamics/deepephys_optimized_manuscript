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
| `score_trajectory.sh` | submits paired d′ and waveform jobs for every saved state in a trajectory |
| `validate_trajectory_outputs.py` | verifies trajectory state counts, required columns, and 10 GT-unit rows before collation |
| `export_qualitative_examples.py` | reproduces a committed endpoint, then exports compact raw/denoised traces, templates, and score distributions |
| `export_qualitative_examples.sbatch` | GPU/S3 wrapper for that qualitative export |
| `template_support_sweep.py` | in-sample and two-fold event-level cross-fitted temporal/channel support sensitivity |
| `template_support_sweep.sbatch` | frozen GPU/S3 wrapper for one checkpoint's support sweep |
| `residual_statistics.py` | per-channel Gaussianity, temporal, spectral, and spatial residual statistics |
| `export_residual_diagnostics.py` | hash-checked compact raw/prediction/residual export from deterministic off-injected-event intervals |
| `export_residual_diagnostics.sbatch` | frozen GPU/S3 wrapper for one checkpoint's residual export |

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

Each GPU/S3 export validates that its d′ values reproduce the corresponding
committed endpoint within `1e-6` before writing anything. For omission0:

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
   "$INFERENCE" \
   ib_w96_om0_s0
```

Repeat the same command with these checkpoint, reference, output, and label
substitutions for the contextual models:

| model | checkpoint | reference | output stem | label |
|---|---|---|---|---|
| Full96 omission1 | `$BASE/checkpoints_sweep/ib/ib_w96_om1_s0/best_model.pt` | `$BASE/traj_scores/ib_w96_om1_s0_dprime.csv` | `$BASE/qualitative/full96_om1_examples` | `ib_w96_om1_s0` |
| original DI seed 0 | `$BASE/models/ib_origdi_s0/best_model.pt` | `$BASE/traj_scores/ib_origdi_s0_dprime.csv` | `$BASE/qualitative/origdi_s0_examples` | `ib_origdi_s0` |

Once all three compact artifacts exist, figure regeneration is local and does
not require S3, SpikeInterface, a checkpoint, or a GPU. The renderer verifies
that their raw/event/template domains match before writing Figures 1–2:

```bash
python code/figures/qualitative_examples.py
```

Figures 20–22 use the same exporter at five scheduled states of each Full96
duration run: steps 135, 459, 1565, 61903, and 210923 (34.6k, 117.5k, 400.6k,
15.85M, and 54.0M cumulative windows). For each omission route, substitute the
trajectory checkpoint and its matching committed score file:

```bash
OUTDIR=$BASE/qualitative_learning
for route in 0 1; do
   label="ib_w96_om${route}_scale"
   for step in 00000135 00000459 00001565 00061903 00210923; do
      stem="${label}_s${step}_examples"
      sbatch "$SCORING/export_qualitative_examples.sbatch" \
         "$SCORING/export_qualitative_examples.py" \
         "$SCORING/detection_metrics.py" \
         "$BASE/checkpoints_sweep/ib/$label/ckpt_step_${step}.pt" \
         "$BASE/traj_scores/${label}_s${step}_dprime.csv" \
         "$OUTDIR/${stem}.npz" \
         "$OUTDIR/${stem}_metadata.json" \
         "$INFERENCE" "${label}_s${step}"
   done
done
```

After copying the 10 NPZ/CSV/metadata triplets to
`results/qualitative/learning_stages/`, regeneration is local:

```bash
python code/figures/learning_evolution.py
```

The renderer requires one shared event/raw/template domain and reproduces every
selected checkpoint's committed aggregate d′ before writing the figures.

## Export residual Gaussianity and whiteness diagnostics

Figures 23–25 use the final scheduled state of each Full96 duration route. The
exporter verifies the requested checkpoint hash, exact 384-channel/10-unit
benchmark, and frame alignment before selecting 512 deterministic non-overlapping
4-ms windows away from injected GT events, 32 strictly injected-GT-free spectral
segments, and one 30-ms overview interval. For omission0:

```bash
sbatch --job-name=resid_om0 "$SCORING/export_residual_diagnostics.sbatch" \
   "$BASE/models/ib_w96_om0_scale/ckpt_step_00210923.pt" \
   f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506 \
   "$BASE/residual_diagnostics/full96_om0" \
   "$INFERENCE" ib_w96_om0_scale "$SCORING"
```

For omission1, substitute `om1` in the job name, checkpoint path, output stem,
and model label, and use checkpoint hash
`90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a`.
Each stem contains an NPZ, per-channel CSV, summary CSV, and metadata JSON. After
copying both stems to `results/residual_diagnostics/`, rendering is local:

```bash
python code/figures/residual_diagnostics.py
```

The renderer requires exact shared raw windows, spectral segments, overview,
geometry, and calibration between routes. Jobs, hashes, output schema, and the
important native-spike caveat are recorded in
[`results/residual_diagnostics/`](../../results/residual_diagnostics/README.md).

## Run the template-support sensitivity

The post hoc support diagnostic rescans 0.5–4 ms and top 1–24 raw-ranked
channels while preserving the frozen events and backgrounds. It writes detail,
fold-averaged per-unit, and model-summary CSVs and aborts unless the 4-ms
in-sample endpoint reproduces committed d′ and channel counts:

```bash
sbatch "$SCORING/template_support_sweep.sbatch" \
   <checkpoint.pt> <reference_dprime.csv> \
   "$BASE/support_sweep/<label>" "$INFERENCE" <label> "$SCORING"
```

The manuscript runs this for `ib_w96_om0_s0`, `ib_w96_om1_s0`, and
`ib_origdi_s0`. Exact commands, jobs, hashes, named cells, and interpretation are
in [`results/template_support/`](../../results/template_support/README.md).

## Tests

```bash
python code/tests/test_detection_metrics.py
python code/tests/test_template_support_sweep.py
python code/tests/test_residual_statistics.py
python -m py_compile \
   code/scoring/detection_metrics.py \
   code/scoring/run_hybrid_s3.py \
   code/scoring/template_diag.py \
   code/scoring/validate_trajectory_outputs.py \
   code/scoring/export_qualitative_examples.py \
   code/scoring/template_support_sweep.py \
   code/scoring/residual_statistics.py \
   code/scoring/export_residual_diagnostics.py
bash -n code/scoring/*.sbatch code/scoring/score_best.sh
```

The focused tests verify the exact pooled-variance equation, invariance to a
shared affine voltage transform, and recording/sorting frame alignment.

`validation_loss_headroom.py` is a separate exploratory audit. Its off-GT set
mixes independent noise, correlated background, and unlabeled native spikes and
is not used for the primary endpoint conclusions.
