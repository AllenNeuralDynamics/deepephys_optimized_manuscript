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
results/scores/<label>_dprime.csv   +   <label>_diag.csv      ◄── one pair per run
        │  code/figures/collate.py
        ▼
results/tables/{master_table,perunit_amp,perunit_dprime,perunit_dprime_delta,noise_floor}.{csv,md}
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
Safe to run at any time — runs without score files yet are simply reported as *pending* and skipped.

## Subfolders

- [`scores/`](scores/README.md) — raw per-unit CSVs from HPC scoring (the input schema).
- [`tables/`](tables/README.md) — collated master table + per-unit matrices (the manuscript inputs).
