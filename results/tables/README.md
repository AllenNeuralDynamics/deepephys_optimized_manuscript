# Collated tables (manuscript inputs)

Generated from versioned scripts under [`../../code/`](../../code/README.md). The all-model tables
come from `figures/collate.py`; specialized control tables come from their named
generators. Each is written as `.csv` data and, where useful, a `.md` view. **Do not edit by hand** —
rerun the owning script.

| file | contents | used by |
|---|---|---|
| `master_table.{csv,md}` | all completed endpoints: family, budget, config, loss, seed, and mean-over-units metrics (currently 87 runs) | Results / complete inventory |
| `model_family_summary.{csv,md}` | run/config counts and d′ range by experiment family and budget | Appendix A / comparison boundaries |
| `table_coverage.{csv,md}` | every ledger row, resolved endpoint layout, inclusion status, and exclusion reason | coverage audit |
| `perunit_amp.{csv,md}` | `amp_ratio`, units (rows, by baseline d′) × all completed endpoint models (cols) | Appendix B (T4) |
| `perunit_dprime.{csv,md}` | `dprime_deep`, units × all completed endpoint models | Appendix C (T5) |
| `perunit_dprime_delta.{csv,md}` | `dprime_deep − dprime_raw`, units × all completed endpoint models | Appendix C heatmap |
| `noise_floor.{csv,md}` | σ of d′ and amp over seed replicates, per config | Methods / T2 |
| `width_schedule_summary.{csv,md}` | matched R5 base64/base96 width/depth/schedules: parameters, Code Ocean runtime, d′, weak-unit d′, and waveform metrics | Results / width-depth-schedule follow-up |
| `width_schedule_paired_effects.{csv,md}` | paired unit-level d′ contrasts and deterministic descriptive bootstrap intervals | Results / width-schedule follow-up |
| `width_schedule_perunit_amp.{csv,md}` | all 10 units × matched R5 reference/nine follow-ups for amplitude | Appendix B |
| `width_schedule_perunit_dprime_delta.{csv,md}` | all 10 units × matched R5 reference/nine follow-ups for Δd′ | Appendix C |

The `validation_loss_*` files are retained as exploratory audit artifacts and are not manuscript
inputs. Their off-GT reference combines independent noise, correlated background, and unlabeled
native spikes, so they must not be interpreted as a spike-reconstruction floor.

`channel_schedule_gpu_benchmark.csv`, its metadata JSON, and
`channel_schedule_gpu_summary.{csv,md}` are exploratory synthetic-batch compute measurements for
alternative temporal U-Net channel pyramids. They quantify parameters, training-step throughput,
and peak GPU allocation only; they provide no evidence that a schedule preserves validation loss,
waveform fidelity, or d′. The separately generated `width_schedule_*` tables provide those endpoint
measurements for the schedules that were actually trained and scored, including the matched
omission0/omission1 √2 endpoints. The synthetic benchmark remains a separate throughput and memory
measurement rather than endpoint evidence.

The global master table is an evidence inventory, not an omnibus causal ranking. Filter on
`experiment_family` and `budget_group`, then use the dedicated matched-control summaries for recipe,
integration, NAF, and corrected-weighting conclusions.
