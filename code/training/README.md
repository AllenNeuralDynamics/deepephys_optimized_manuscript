# Training (Code Ocean)

Training is launched in the `aind-ephys-deepinterpolation` capsule
([](../../data/provenance.md)) via the API. Each parameter `key=val` becomes the env var
`DI_<KEY>` in the capsule.

## Champion base config

`base_channels=32, depth=3, bs_frames=3, bs_channels=64, bs_depth=5, fuse_channels=64,`
`loss=charbonnier (eps=0.4), omission=1`; `batch_size=64, lr=0.001, cosine, float16`.

Shared, in-band for every run:
`train_recording_path = hybrid_np1/…ProbeC-AP_recording1_3/recording.zarr`,
`slice_start_s=60, slice_dur_s=150`, `val_slice 0–60`, `checkpoint_steps=12`.
Short runs use `train_chunks=4` (~0.28 M updates); SUPPORT-scale uses `train_chunks=47` (~3.3 M).

## Overrides

The complete job list (39 runs across three tiers + the two SUPPORT-scale runs), with the exact
override, seeds, and training loss for each, is the pre-registered table in
[](../../reproducibility/regeneration-plan.md) §4. Config keys relevant to overrides:

- `loss` — `charbonnier` (default) or `l2`.
- `omission` — `1` (hide t±1) or `0` (reveal t±1; forces `bs_frames=1`).
- capacity — `base_channels`, `depth`, `bs_channels`, `bs_depth`; `fuse_channels`.
- SUPPORT wiring — `bs_stage`, `bs_dense`, `bs_multiscale`.
- spike-weighting — `spike_weight`, `spike_weight_gamma`, `spike_weight_thresh`,
  `spike_weight_car`, `spike_weight_hard`.
- `norm` — `group` (default) or `none`; `temporal_mult`.

## Launch body

See [](../../reproducibility/reproduce.md) §2 for the `POST /api/v1/computations` body and the
status-check pattern (read `end_status`, not `state`).
