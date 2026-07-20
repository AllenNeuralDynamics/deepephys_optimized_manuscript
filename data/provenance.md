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
| Wide-band training asset | `51f9b4df…` (`ecephys_np1_benchmark`) | — | not used for in-band scoring |

## Recordings

- **Training (in-band), per run:**
  `hybrid_np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3/recording.zarr`
- **Scoring substrate (S3, AP-band):**
  `aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3`
- **Ground truth:** 10 injected hybrid units; extraction `seed=0`.
- Training slice `slice_start_s=60`, `slice_dur_s=150`; validation `0–60 s`; default
  `checkpoint_steps=12` (`24` for the width/schedule/depth follow-up).

## HPC (AIND scratch)

| item | path |
|---|---|
| Base | `/allen/aind/scratch/jeromel/ephys_denoising` |
| Conda env | `/allen/aind/scratch/jeromel/ephys_denoising/env` |
| Conda init | `/allen/aind/scratch/jeromel/astro_voltage_deepinterp/miniforge3/etc/profile.d/conda.sh` |
| Login | `ssh -o BatchMode=yes jeromel@hpc-login` |

## Long-duration omission diagnostic

| run | computation id | override | loss |
|---|---|---|---|
| RUN3 (om0) | `ccf82c60-43c4-4829-9984-8d41e4639fc2` | support_all, `omission=0 bs_frames=1`, `train_chunks=47` | L2 |
| RUN4 (om1) | `5eec6d19-f063-4f9d-a17a-b11da5a65869` | support_all, `omission=1 bs_frames=3`, `train_chunks=47` | L2 |

Both computations completed and their trajectories are scored. Live and staged optimization runs
are tracked in `results/runs.csv`, which supersedes static status prose here.

## Matched R5 width, channel-schedule, and depth follow-up

| run | computation id | temporal schedule | omission | Code Ocean runtime |
|---|---|---|---:|---:|
| full base96 | `edb49d0f-ca97-40e6-a0fc-fb0d3305f8f4` | 96→192→384→768 | 0 | 16,672 s |
| full base96 | `50f7d07d-dea1-40fa-8c4b-c8b8a65c5b8b` | 96→192→384→768 | 1 | 16,610 s |
| cap384 | `29f50c37-ce7e-450f-9147-83c0462ae7b1` | 96→192→384→384 | 0 | 14,281 s |
| growth1.5 | `1eb46bac-c88b-4f6a-a358-6fec2b9f7704` | 96→144→216→324 | 0 | 9,915 s |
| growth1.5 | `1d2e85d8-b745-4e72-9570-6a33cb521f87` | 96→144→216→324 | 1 | 10,249 s |
| growth √2 | `ffeeb1d1-bfcf-47d9-9e54-78e9c15f2a9b` | 96→136→192→272 | 0 | 9,553 s |
| growth √2 | `a447dddb-62f6-46ea-994a-59cf9d58c3b3` | 96→136→192→272 | 1 | 9,654 s |
| depth 2, full 2× | `b43cb91d-7547-41e6-bbe7-bb147cb06c61` | 96→192→384 | 0 | 9,596 s |
| depth 2, full 2× | `bc6ba5f8-3757-4851-a42f-6b3ff27e01ce` | 96→192→384 | 1 | 9,800 s |

All nine computations completed successfully. Their checkpoints strict-loaded and were scored
on HPC with the schedule-aware inference checkout pinned to commit `808d7fa`; final d′ and waveform
job IDs are recorded in `results/runs.csv`. The two √2 computations were added after the coverage
audit identified that only their synthetic GPU benchmark existed. The matched depth-2 pair compares
a shallow 96→192→384 pyramid against the nearly parameter-matched depth-3 √2 schedule; its final
d′/diagnostic jobs were `23243308`–`23243311`.

## Qualitative benchmark export

The opening raw/denoised, unit-attenuation, and d′-distribution figures use one
compact export from the highest-d′ omission0 endpoint. This is a post-screen
diagnostic selection, not held-out evidence.

| item | value |
|---|---|
| model | `ib_w96_om0_s0` (`96→192→384→768`, omission0) |
| checkpoint SHA-256 | `1087a75b878fa82745f33581095f5d54a7f69bbb68ce83fd99893b62d778c4d1` |
| inference checkout | `aind-ephys-deepinterpolation-inference` commit `808d7fa` |
| export job | AIND HPC `23244894`, completed in 00:12:36 on a GTX 1080 Ti |
| scoring extraction | seed 0; at most 100 GT events/unit; 200 spike-excluded backgrounds |
| detail units | 2143, 1143, 720, 1129 |
| exemplar | unit 1143, frame 107200608, nearest other injected event 14.667 ms away |
| compact NPZ | `results/qualitative/full96_om0_examples.npz`, 1,657,671 bytes, SHA-256 `5be9ca2cbb07a62b626b87ac56495fde490ae2d64a02c1bf92af8d305163e93e` |
| reproduced CSV | `results/qualitative/full96_om0_examples.csv`, SHA-256 `fb75d4663cbd66fb68bfda27d0ac84010f76bdfa75d51e3be6cc9f8d2992102f` |
| metadata JSON | `results/qualitative/full96_om0_examples_metadata.json`, SHA-256 `f89fc514fdafbc8e3af03a6855596bf9619fb325213a1c13597e31ee97eda1e2` |

Before writing these files, the exporter recomputed all ten committed per-unit
SNR and d′ rows and required maximum absolute error below `1e-6`; the observed
error was exactly 0. The 30-ms all-probe and 4-ms local displays remove only each
channel's median for visualization. Scoring uses the native calibrated windows
without that display centering.

## Checkpoint schedule (`n_ckpt=12`)

Log-spaced steps: 1, 4, 15, 60, 235, 919, 3597, 14078, 55103, 215688, 844255, 3304616 —
files `ckpt_step_########.pt` plus `best_model.pt`.

## Local model store (weights — not in git)

Trained checkpoints live in the **git-ignored** `models/<label>/` store, one folder per run, each
with a `manifest.json` (config, loss, `co_id`, and a per-file sha256 for integrity). Populate it
with `python code/store_model.py <label> <ckpt_dir>` after downloading a run's checkpoints
(`code/figures/co_dl.py`). Weights are also always recoverable from each run's Code Ocean
computation via the `co_id` recorded in `results/runs.csv`.
