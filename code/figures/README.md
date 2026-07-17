# Figures & collation

Helpers that turn scored CSVs into manuscript tables and figures (§5–§6 of the
[](../../reproducibility/regeneration-plan.md)). The current generators are committed here so figures
regenerate deterministically.

| script | purpose |
|---|---|
| `co_dl.py` | download checkpoints plus exact optimization telemetry from a Code Ocean computation |
| `collate.py` | collate per-unit CSVs → master table + per-unit amp / Δd′ matrices (mean over 10 units) |
| `collate_trajectory.py` | merge checkpoint scores with measured elapsed time, LR, samples, optimizer steps, and effective batch |
| `recipe_convergence.py` | compare recipe trajectories and bootstrap paired GT-unit endpoint differences |
| `gradient_diagnostics.py` | plot gradient-noise scale, microbatch alignment, and covariance spectrum over training |
| `make_figures.py` | architecture ranking, template-SNR/d′, unit-quality, heatmap, duration, and legacy-audit figures |

## Figure ↔ quantification map

The original figure plan is documented in [](../../reproducibility/regeneration-plan.md) §6. The
authoritative current collection is the set of figure directives in `sections/`; figures are written
to `../../figures/`.
