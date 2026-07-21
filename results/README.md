# Results — how scored runs flow into the manuscript

This directory is the **landing zone** for scored runs. Everything the manuscript displays is
generated from here, so the paper "receives" results by dropping score CSVs in and running one
script.

## Flow

```
Code Ocean training run  ──►  checkpoints (best_model.pt, ckpt_step_*.pt)
        │  (download + rsync to HPC; see ../reproducibility/reproduce.md)
        ▼
HPC scoring (run_ckpt.sbatch, template_diag.sbatch)
        │  writes per-unit CSVs
        ▼
results/scores/<label>_{dprime,diag}.csv
or results/scores/<label>/<label>_best_{dprime,diag}.csv      ◄── one endpoint pair per run
        │  code/figures/collate.py
        ▼
results/tables/{master_table,model_family_summary,table_coverage,perunit_*,noise_floor}.{csv,md}
        │  figure scripts (code/figures/make_*.py)  +  {include} of the .md tables
        ▼
figures/*.png   +   manuscript tables      ──►   the HTML site
```

## The run manifest — [`runs.csv`](runs.csv)

One row per run, including later adaptive additions and non-primary experiments. The original
plan is preserved in [the versioned plan](../reproducibility/regeneration-plan.md); `runs.csv` is the
authoritative current ledger. Columns:
`label, tier, config, seed, loss, train_chunks, override, co_id, state, ckpt_downloaded, scored, notes`.

Update `co_id`/`state`/`scored` as runs launch and land. `label` uses the `ib_<config>_s<seed>`
convention and is the key that ties a manifest row to its `results/scores/<label>_*.csv` and its
column in the per-unit matrices.

## Collate

```bash
python code/figures/collate.py     # reads runs.csv + results/scores/*, writes results/tables/*
```
Safe to run at any time: runs without score files are reported as pending and skipped, while a ledger
row explicitly marked `scored=yes` fails loudly if its endpoint pair is missing.

## Subfolders

- [`scores/`](scores/README.md) — raw per-unit CSVs from HPC scoring (the input schema).
- [`tables/`](tables/README.md) — collated master table + per-unit matrices (the manuscript inputs).
- [`qualitative/`](qualitative/README.md) — endpoint-validated compact arrays for Figures 1–3.
- [`template_support/`](template_support/README.md) — in-sample/cross-fitted temporal and spatial
        support sensitivity for Figure 19.
