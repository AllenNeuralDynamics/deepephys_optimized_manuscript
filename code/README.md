# Code

Scripts for the reproducible pipeline, grouped by stage. Some live on the AIND HPC or were run
ad-hoc during the study; this directory is the canonical home and each subfolder's README documents
what to vendor and how.

| subfolder | stage | status |
|---|---|---|
| [`training/`](training/README.md) | launch Code Ocean training runs | documented (capsule-side) |
| [`scoring/`](scoring/README.md) | HPC sbatch d′ / diagnostic scoring | **to vendor from HPC** |
| [`figures/`](figures/README.md) | download, collate, plot, build PDF | **to vendor / re-commit** |

:::{note}
The scoring sbatch scripts currently live on the HPC under `$BASE`; the download/collate/plot
helpers were run locally. Pull commands are in each subfolder README. Once committed here, they are
the single source of truth and the manuscript figures regenerate from them.
:::
