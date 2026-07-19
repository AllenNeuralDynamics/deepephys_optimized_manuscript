# Raw scores (input schema)

One pair of per-unit CSVs per run, written by the HPC scoring scripts
([`../../code/scoring/`](../../code/scoring/README.md)) against the frozen AP-band benchmark
(10 GT units, `seed=0`). File names use the manifest `label`. Original screen endpoints use
`<label>_{dprime,diag}.csv` at this directory root; trajectory and control endpoints use
`<label>/<label>_best_{dprime,diag}.csv`. `collate.py` resolves both layouts as one endpoint per run.

## `<label>_dprime.csv` — from `run_ckpt.sbatch`

One row per GT unit:

| column | meaning |
|---|---|
| `unit_id` | ground-truth unit id |
| `dprime_deep` | matched-filter d′, denoised template (**primary**) |
| `dprime_deep_fixed` | matched-filter d′, raw/true template (artifact control) |
| `dprime_raw` | d′ on the raw (undenoised) recording (baseline) |
| `snr_deep` | SNR of the denoised spike |

## `<label>_diag.csv` — from `template_diag.sbatch`

One row per GT unit:

| column | meaning |
|---|---|
| `unit_id` | ground-truth unit id |
| `amp_ratio` | denoised ÷ true peak-to-peak on the peak channel |
| `fwhm_ratio` | trough-width ratio |
| `temporal_cos` | waveform temporal-shape correlation |
| `spatial_cos` | spatial-footprint correlation |

## Trajectory runs

Trajectory directories may also contain paired checkpoint files tagged by saved optimizer step.
`collate_trajectory.py` combines those repeated states with checkpoint telemetry; `collate.py`
deliberately reads only the `best` pair so checkpoints are never counted as independent models in
the all-model tables.

Column names beyond `unit_id` may include extras; `collate.py` reads only the columns above and
ignores the rest.
