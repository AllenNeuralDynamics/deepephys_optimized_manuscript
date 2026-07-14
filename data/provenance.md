# Data & compute provenance

All identifiers needed to reproduce the study. **No credentials are stored here** — the Code Ocean
token is sourced at runtime from `~/.codeocean.env` (git-ignored).

## Code Ocean capsules

| role | capsule id | repo |
|---|---|---|
| Training (DeepInterpolation ephys) | `cb03dc8b-be21-42fe-aec0-e60607ff1bfe` | `aind-ephys-deepinterpolation` |
| Inference / surrogate scoring | — | `aind-ephys-deepinterpolation-inference` |
| Benchmark pipeline (KS4 + DARTsort, no-generation) | `5a096db9` | `aind-ephys-deepinterp-benchmark` |

Parameters are passed as `key=val` and appear in the capsule as env var `DI_<KEY>`.

## Data assets

| role | asset id | mount | notes |
|---|---|---|---|
| **In-domain training (AP-band hybrid)** | `384bf77c-f37b-4ab1-a008-03f10a0c49c9` | `hybrid_np1` | used for all in-band runs |
| Superseded training (wide-band) | `51f9b4df…` (`ecephys_np1_benchmark`) | — | out-of-band; the source of the prior error |

## Recordings

- **Training (in-band), per run:**
  `hybrid_np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3/recording.zarr`
- **Scoring substrate (S3, AP-band):**
  `aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3`
- **Ground truth:** 10 injected hybrid units; extraction `seed=0`.
- Training slice `slice_start_s=60`, `slice_dur_s=150`; validation `0–60 s`; `checkpoint_steps=12`.

## HPC (AIND scratch)

| item | path |
|---|---|
| Base | `/allen/aind/scratch/jeromel/ephys_denoising` |
| Conda env | `/allen/aind/scratch/jeromel/ephys_denoising/env` |
| Conda init | `/allen/aind/scratch/jeromel/astro_voltage_deepinterp/miniforge3/etc/profile.d/conda.sh` |
| Login | `ssh -o BatchMode=yes jeromel@hpc-login` |

## Runs in flight (in-domain SUPPORT-scale omission A/B)

| run | computation id | override | loss |
|---|---|---|---|
| RUN3 (om0) | `ccf82c60-43c4-4829-9984-8d41e4639fc2` | support_all, `omission=0 bs_frames=1`, `train_chunks=47` | L2 |
| RUN4 (om1) | `5eec6d19-f063-4f9d-a17a-b11da5a65869` | support_all, `omission=1 bs_frames=3`, `train_chunks=47` | L2 |

## Checkpoint schedule (`n_ckpt=12`)

Log-spaced steps: 1, 4, 15, 60, 235, 919, 3597, 14078, 55103, 215688, 844255, 3304616 —
files `ckpt_step_########.pt` plus `best_model.pt`.

## Local model store (weights — not in git)

Trained checkpoints live in the **git-ignored** `models/<label>/` store, one folder per run, each
with a `manifest.json` (config, loss, `co_id`, and a per-file sha256 for integrity). Populate it
with `python code/store_model.py <label> <ckpt_dir>` after downloading a run's checkpoints
(`code/figures/co_dl.py`). Weights are also always recoverable from each run's Code Ocean
computation via the `co_id` recorded in `results/runs.csv`.
