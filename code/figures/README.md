# Figures & collation

Helpers that turn scored CSVs into manuscript tables and figures (§5–§6 of the
[](../../reproducibility/regeneration-plan.md)). The current generators are committed here so figures
regenerate deterministically.

| script | purpose |
|---|---|
| `co_dl.py` | download checkpoints plus exact optimization telemetry from a Code Ocean computation |
| `collate.py` | resolve root and nested best endpoints → complete master/family/coverage tables + per-unit amp / Δd′ matrices (mean over 10 units) |
| `collate_trajectory.py` | merge checkpoint scores with measured elapsed time, LR, samples, optimizer steps, and effective batch |
| `architecture_evolution.py` | render the three-panel current topology, architecture evolution, and NAF-stage comparison |
| `recipe_convergence.py` | compare recipe trajectories and bootstrap paired GT-unit endpoint differences |
| `recipe_replication.py` | compare R0/R1/R5 across three matched training seeds, sample budgets, and waveform metrics |
| `integration_controls.py` | compare R9–R12 adaptive, sampling, physical-batch, and accumulated-batch controls with matched R1 endpoints, trajectories, units, and compute |
| `naf_control.py` | compare the capacity-matched R13 NAF temporal block with the three R5 DoubleConv seeds, loss curves, units, and runtime |
| `weighting_controls.py` | compare corrected matched-L2 weighting endpoints, waveform fidelity, seed context, and paired unit effects |
| `validation_loss_headroom.py` | calibrate measured spike-support loss headroom against seed, NAF, and method-control validation-loss changes |
| `gradient_diagnostics.py` | plot gradient-noise scale, microbatch alignment, and covariance spectrum over training |
| `adaptive_accumulation.py` | plot adaptive noise measurements, integration decisions, alignment, and optimizer-update compression |
| `make_figures.py` | architecture ranking, template-SNR/d′, unit-quality, heatmap, and duration figures |

## Figure ↔ quantification map

The original figure plan is documented in [](../../reproducibility/regeneration-plan.md) §6. The
authoritative current collection is the set of figure directives in `sections/`; figures are written
to `../../figures/`.
