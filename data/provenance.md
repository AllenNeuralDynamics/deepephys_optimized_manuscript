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
  `checkpoint_steps=12` (`24` for the width/schedule/depth follow-up; `11` for the Full96 duration pair).

## HPC (AIND scratch)

| item | path |
|---|---|
| Base | `/allen/aind/scratch/jeromel/ephys_denoising` |
| Conda env | `/allen/aind/scratch/jeromel/ephys_denoising/env` |
| Conda init | `/allen/aind/scratch/jeromel/astro_voltage_deepinterp/miniforge3/etc/profile.d/conda.sh` |
| Login | `ssh -o BatchMode=yes hpc-login.corp.alleninstitute.org` (SSH config selects `jeromel`) |

## Full96 duration diagnostic (Figure 16)

| run | computation id | budget | checkpoints | runtime |
|---|---|---:|---:|---:|
| Full96 om0 | `307fe678-bd24-48e8-90e8-bc41b6314ec2` | 53,996,544 windows | 11 scheduled + validation-best | 48,377 s |
| Full96 om1 | `d8d53304-974e-4980-84a1-10286252af71` | 53,996,544 windows | 11 scheduled + validation-best | 49,363 s |

Both use the full `96→192→384→768` body, batch 256, Charbonnier, seed 0, and the R5 optimizer
recipe. Omission0 uses `bs_frames=1`; omission1 uses `bs_frames=3`. Checkpoints are stored under
`models/ib_w96_om{0,1}_scale/`, hash-verified locally and after HPC transfer, and scored with pinned
inference commit `808d7fa`. Figure 16 uses the 11 scheduled states and exact `samples_seen` telemetry.
HPC scoring jobs were `23276157–23276204`; strict paired-state validation job `23276217` completed
with 12 d′/diagnostic state pairs × 10 units for each route.

## Legacy SUPPORT duration diagnostic (provenance only)

| run | computation id | override | loss |
|---|---|---|---|
| RUN3 (om0) | `ccf82c60-43c4-4829-9984-8d41e4639fc2` | support_all, `omission=0 bs_frames=1`, `train_chunks=47` | L2 |
| RUN4 (om1) | `5eec6d19-f063-4f9d-a17a-b11da5a65869` | support_all, `omission=1 bs_frames=3`, `train_chunks=47` | L2 |

Both computations completed and their trajectories remain in the complete evidence inventory, but
they are no longer displayed in Figure 16. Live and staged runs are tracked in `results/runs.csv`,
which supersedes static status prose here.

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

The opening raw/denoised and unit-attenuation figures compare three compact
exports: the matched Full96 omission routes and seed-0 original DI. The d′
distribution figure remains focused on Full96 omission0. These are post-screen
diagnostic selections, not held-out evidence.

| item | value |
|---|---|
| inference checkout | `aind-ephys-deepinterpolation-inference` commit `808d7fa` |
| scoring extraction | seed 0; at most 100 GT events/unit; 200 spike-excluded backgrounds |
| detail units | 2143, 1143, 720, 1129 |
| exemplar | unit 1143, frame 107200608, nearest other injected event 14.667 ms away |

| model | checkpoint SHA-256 | export job | NPZ SHA-256 |
|---|---|---|---|
| `ib_w96_om0_s0` | `1087a75b878fa82745f33581095f5d54a7f69bbb68ce83fd99893b62d778c4d1` | `23244894` (00:12:36, GTX 1080 Ti) | `5be9ca2cbb07a62b626b87ac56495fde490ae2d64a02c1bf92af8d305163e93e` |
| `ib_w96_om1_s0` | `6683c5880ac0c6c6a95e72b09fdb29398bd91218d66e2379f9db6b2b5924f146` | `23246072` (00:10:51, TITAN Xp) | `433582303a763e273b0f972f67502149f78e3336f8150b580081323ad63b2122` |
| `ib_origdi_s0` | `d047ea9fda59c5ba74fa28a88b7b4347b84b087111a4db8fe5632851a63610c0` | `23246073` (00:10:54, TITAN Xp) | `39af42d4029c44b07a3ed44780d2d6ff021a54604c986face0bb14915ac14393` |

Before writing each artifact, the exporter recomputed all ten committed per-unit
SNR and d′ rows and required maximum absolute error below `1e-6`; the observed
error was exactly 0 for all three. The renderer additionally verified exact
agreement in shared raw/event/template inputs. The 30-ms all-probe and 4-ms local
displays remove only each channel's median for visualization. Scoring uses the
native calibrated windows without that display centering. CSV and metadata hashes
are recorded in `results/qualitative/README.md`.

## Learning-stage qualitative export (Figures 20–22)

The learning-stage collection applies the same exporter to steps 135, 459, 1565,
61903, and 210923 of both Full96 duration runs. The checkpoints correspond to
34.6k, 117.5k, 400.6k, 15.85M, and 54.0M cumulative training windows. All stages
reuse the qualitative benchmark's fixed event, contact set, and four detail units.

| route | step | export job | node | checkpoint SHA-256 | NPZ SHA-256 |
|---|---:|---:|---|---|---|
| om0 | 135 | `23281634` | `n202` | `9a29206746aec7645dfb0c6feddf0fa84fc0ff9708e76ff25fa6e381b6f8a806` | `1dd424a0f465d34fda780671a12648069c658cad375352aefca8764fcf820402` |
| om0 | 459 | `23281635` | `n203` | `84677244c7c7ce3b98b8411b994727946e6d945da8a4ba36694966c901b2c31d` | `e710d097db17dca254c53c59d863f70b7228b83860337c9e188e779085ac9f1d` |
| om0 | 1565 | `23281636` | `n69` | `456f68d1930160e00a40580e6474e0d5f6510ca4e37dd4ab2228f3d9aab0ba87` | `dde13b73a136e44612644f8ce67991b60927a962d925e714ee389547f38d39fd` |
| om0 | 61903 | `23281637` | `n202` | `1802490a9831d0cadf04d0775a20596c3b279a262b6308d6c383c748dd1757de` | `d9d4e0845215e77f70364c027b38d89725b6b29c53712d6f113686052334943a` |
| om0 | 210923 | `23281638` | `n203` | `f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506` | `ecf17a2f07bd4107297ca2973b32334bd93dca202fd78fa8be2fe93f088602fd` |
| om1 | 135 | `23281639` | `n69` | `2aad7a8281a4f6e0e983481d34912c049c1a5c1a720d99599cbd8a8b81291657` | `1ce7a9f03bb7adc412b50dfc53266f429cdbb7d727eaecc8f670f9b93505f3d8` |
| om1 | 459 | `23281688` | `n69` | `67e599839a38da86eb46f2e11a88869f88dafb992cd2ff3509004cda4e6ab232` | `098caa48cf337bb88b8d5152473f271314941b31255dceb87e0e1b62c19cf6f2` |
| om1 | 1565 | `23281641` | `n69` | `35539113812b1787bf38798f52daba13584224c7634a1b4f4ad3ab6ab91e85dd` | `0d9ef59025148b49330512aae72eacf4fc20c7db5a33a666f5491e6bfcc685f0` |
| om1 | 61903 | `23281642` | `n202` | `4d32a22a455a67c8ecb5c84b2ee5af1c450c8df5adc3622734d54760ceac214f` | `d83194d261cd9e964d81ad173c032896dd476c9cf3318112d3d555b5b8a030b6` |
| om1 | 210923 | `23281643` | `n203` | `90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a` | `56b7e76a9b51b4f5525c443a2cb6a3b869066389319f5f38568beb564a440628` |

Nodes `n69`, `n202`, and `n203` use Pascal-generation TITAN X, GTX 1080 Ti, and
TITAN Xp GPUs. A first om1 step-459 attempt (`23281640`) on A100 node `n04` was
rejected by the unchanged `1e-6` replay gate (`snr_deep` error
`0.0012331008911132812`); replacement `23281688` passed on `n69`. Every retained
artifact passed the exporter gate, and the renderer then verified the shared
raw/event/template domain and committed aggregate d′. Complete CSV/metadata
hashes and final figure hashes are recorded in
[`results/qualitative/learning_stages/README.md`](../results/qualitative/learning_stages/README.md).

## Template-support sensitivity

The post hoc linear-filter support diagnostic used the same inference commit,
recording/sorting URLs, seed-0 event selection, 100 GT events/unit, and 200
background centers as the frozen endpoint. It swept 0.5/1/2/3/4-ms crops and
top-1/2/4/8/16/24 raw-ranked channels plus the endpoint rule, both in-sample and
with deterministic two-fold event-level cross-fitting.

| model | HPC job | elapsed | GPU |
|---|---:|---:|---|
| `ib_w96_om0_s0` | `23258586` | 00:08:46 | TITAN Xp |
| `ib_w96_om1_s0` | `23258587` | 00:08:41 | TITAN Xp |
| `ib_origdi_s0` | `23258588` | 00:08:40 | TITAN X (Pascal) |

All jobs completed with exit 0. Each 4-ms in-sample endpoint reproduced committed
raw/denoised d′ within `1e-6` and its per-unit channel count. Exact result-file
hashes and schemas are in
[`results/template_support/README.md`](../results/template_support/README.md).

## Checkpoint schedule (`n_ckpt=12`)

Log-spaced steps: 1, 4, 15, 60, 235, 919, 3597, 14078, 55103, 215688, 844255, 3304616 —
files `ckpt_step_########.pt` plus `best_model.pt`.

## Local model store (weights — not in git)

Trained checkpoints live in the **git-ignored** `models/<label>/` store, one folder per run, each
with a `manifest.json` (config, loss, `co_id`, and a per-file sha256 for integrity). Populate it
with `python code/store_model.py <label> <ckpt_dir>` after downloading a run's checkpoints
(`code/figures/co_dl.py`). Weights are also always recoverable from each run's Code Ocean
computation via the `co_id` recorded in `results/runs.csv`.
