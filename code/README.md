# Code

Scripts for the reproducible pipeline, grouped by stage. This directory is the canonical source;
the AIND HPC receives staged copies for GPU/S3 execution. Each subfolder README documents inputs,
outputs, environment assumptions, and exact commands.

| subfolder | stage | status |
|---|---|---|
| [`training/`](training/README.md) | launch Code Ocean training runs | documented (capsule-side) |
| [`scoring/`](scoring/README.md) | event/background d′, waveform diagnostics, S3/HPC drivers, qualitative export | vendored and tested |
| [`figures/`](figures/README.md) | collate tables and render every committed manuscript figure | vendored and regenerated |

:::{note}
Checkpoint weights and the full S3 recording are intentionally not committed. Endpoint CSVs and
three compact qualitative NPZ artifacts are committed with provenance. Each qualitative exporter
first reproduces its frozen endpoint numerically; all subsequent figure rendering is local and
requires neither a GPU nor S3 access.
:::
