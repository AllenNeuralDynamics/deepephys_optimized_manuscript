# Figures & collation

Helpers that turn scored CSVs into the manuscript tables and figure collection (§5–§6 of
[](../../reproducibility/regeneration-plan.md)). These were run ad-hoc during the study and must be
re-committed here so the figures regenerate deterministically.

| script | purpose |
|---|---|
| `co_dl.py` | download checkpoints plus exact optimization telemetry from a Code Ocean computation |
| `collate.py` | collate per-unit CSVs → master table + per-unit amp / Δd′ matrices (mean over 10 units) |
| `collate_trajectory.py` | merge checkpoint scores with measured elapsed time, LR, samples, optimizer steps, and effective batch |
| `recipe_convergence.py` | compare recipe trajectories and bootstrap paired GT-unit endpoint differences |
| `gradient_diagnostics.py` | plot gradient-noise scale, microbatch alignment, and covariance spectrum over training |
| `make_ranking_fig.py` | F1 d′-ranking vs ±2σ band |
| `make_loss_pairs_fig.py` | F3 the six Charbonnier↔L2 matched pairs |
| `make_perunit_heatmaps.py` | F6/F7 per-unit amplitude and Δd′ heatmaps (units × models) |
| `make_traj_fig.py` | F8 d′/amp vs training-updates trajectories |
| `psd_plot.py` | F10 PSD band-mismatch (train vs eval) — the correction evidence |
| `build_report_pdf.py` | (optional) legacy pandoc/tectonic PDF from the old report; not used — the site is HTML |

## Figure ↔ quantification map

The complete mapping (10 figures + 5 tables, one+ per quantification family) is tabulated in
[](../../reproducibility/regeneration-plan.md) §6. Figures are written to `../../figures/` and
referenced from the manuscript sections.

:::{note} Status
The ad-hoc versions of these scripts were ephemeral and are not yet in the repo. Re-commit them here
(cleaned up) as scoring lands; until then the figure directives in `sections/` are commented out.
:::
