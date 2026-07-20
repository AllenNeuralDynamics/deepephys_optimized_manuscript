# Scoring and loss calibration (HPC)

The SLURM scripts score a checkpoint against the frozen AP-band benchmark (recording, 10 GT units,
`seed=0` — see [](../../data/provenance.md)). They currently live on the HPC and should be vendored
here verbatim.

| script | call | output |
|---|---|---|
| `run_ckpt.sbatch` | `sbatch run_ckpt.sbatch <ckpt_abs> <out_dprime.csv> [inference_code]` | d′ CSV: `unit_id, …, dprime_deep, dprime_deep_fixed, …` |
| `template_diag.sbatch` | `sbatch template_diag.sbatch <ckpt_abs> <prefix> [inference_code]` | `<prefix>_diag.csv`: `…, amp_ratio, fwhm_ratio, temporal_cos, spatial_cos, …` |
| `validation_loss_headroom.sbatch` | `sbatch validation_loss_headroom.sbatch <analysis.py> <ckpt_abs> <out.csv>` | exploratory GT-support/off-GT residual contrast; not a manuscript analysis |

Both hardcode the S3 benchmark path (`aind-benchmark-data/…ProbeC-AP_recording1_3`) and use the
inference model definition from `aind-ephys-deepinterpolation-inference` (keep it in sync with the
training `model.py`). For schedule-aware checkpoints, pass the clean inference checkout explicitly;
`run_with_inference.py` pins both inference modules before the legacy scoring drivers modify
`sys.path`. `validation_loss_headroom.py` additionally reconstructs the checkpoint's fixed
validation sampler and rejects a result if its aggregate loss does not match the stored checkpoint.
Its off-GT reference conflates independent noise, correlated background, and unlabeled native spikes;
the retained outputs are an audit artifact, not a four-component loss decomposition.

## Vendor from HPC

```bash
rsync -t --no-perms -e "ssh -o BatchMode=yes" \
  jeromel@hpc-login:/allen/aind/scratch/jeromel/ephys_denoising/run_ckpt.sbatch \
  jeromel@hpc-login:/allen/aind/scratch/jeromel/ephys_denoising/template_diag.sbatch \
  ./
```

Aggregate = arithmetic mean over the 10 GT units. Per-unit
rows are retained to build the per-unit × model matrices (appendix B/C).
