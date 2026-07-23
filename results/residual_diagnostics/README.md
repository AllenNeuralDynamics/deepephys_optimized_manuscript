# Full96 residual Gaussianity and whiteness artifacts

These compact artifacts support Appendix Figures 23–25 without requiring the
full S3 recording, a model checkpoint, SpikeInterface, or a GPU. They compare
the final scheduled Full96 omission0 and omission1 checkpoints at the same
53,996,288-window exposure on the frozen ProbeC AP-band hybrid recording.
Inference is pinned to commit `808d7fa`.

The residual is defined in calibrated microvolts as `raw - model prediction`.
The export uses:

- 512 deterministic, non-overlapping 4-ms windows whose centers are more than
  4 ms from all 1,070,127 injected GT events;
- 32 recording-spanning, 1,024-sample intervals containing no injected GT event
  for Welch spectra;
- one 30-ms injected-GT-free interval nearest the recording midpoint for the
  probe image; and
- all 384 channels in physical NP1 geometry.

Injected GT exclusion does not remove unlabeled native spikes. Gaussianity and
whiteness are therefore descriptive diagnostics, not necessary success
conditions or substitutes for GT-event and sorter evaluation.

## Export provenance

| route | HPC job | elapsed | node / GPU | checkpoint SHA-256 | NPZ SHA-256 |
|---|---:|---:|---|---|---|
| omission0 | `23303153` | 00:05:42 | `n69` / TITAN X (Pascal) | `f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506` | `72835760d9ce1054a037966dc1b63a3e8b3939f59ec955cb6574bf5e36f3b6a0` |
| omission1 | `23303154` | 00:05:30 | `n69` / TITAN X (Pascal) | `90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a` | `40fa1854e815f9d25a2a9c7baba93ea65f415753d35cf62c383c455a28bd0fe4` |

Each job verified its checkpoint hash before data access and checked the frozen
384-channel/10-unit recording/sorting alignment. The local renderer then
required exact equality of background centers, spectral starts, channel order,
geometry, raw overview, raw autocorrelation, raw spatial correlation, raw PSD,
raw quantiles, raw histogram, and raw per-channel statistics. Both routes have
overview start frame `107171642`, raw-overview hash
`3e8e8c588d88e13622c834f3f37333c058d042f79f285cad1e0256d3ca7ca130`,
and background-center hash
`e51d881c9d98a5bf1b6b61635b7c9ee0b1d3ce34ea01ca51dece072ffc4b535d`.

Auxiliary artifact hashes are:

| file | SHA-256 |
|---|---|
| `full96_om0_channels.csv` | `c2bb646d8ea2d291a92fbb9a5968b194796675cae001230980c8550f5010f605` |
| `full96_om0_summary.csv` | `6b4cd65bb5df5f8557f9a36bd3e2a20d8542dbd64f22c0e5e5bd4995e288121b` |
| `full96_om0_metadata.json` | `409c10549ed91dcd091abc1dbb317b6b3510f393aa37c0dafecb8502e01c6972` |
| `full96_om1_channels.csv` | `3bbb9d7f063d7cc603299ea91b883b0bb261eaf1c2f10acc3fcdf7ff07eb75fb` |
| `full96_om1_summary.csv` | `9fa16d0d9cd7f71b15c2ae2c66d26e6f958fffdddb1056061d40703465da728d` |
| `full96_om1_metadata.json` | `c042507ffaeca103ab9749aa348a09ab3675df2952bc78e16e3969db04a8fcf9` |

## Contents

Each NPZ stores the shared selection/geometry, one raw/prediction/residual probe
interval, per-domain autocorrelation, spatial correlation, Welch power,
normal/empirical quantiles, and marginal histogram. Each channel CSV contains
384 rows per domain for mean, SD, skewness, excess kurtosis, normal-QQ RMSE,
tail fractions, Jarque–Bera and Ljung–Box tests with FDR decisions, mean/maximum
absolute autocorrelation, spectral flatness, and probe location. Each summary
CSV reports channel medians, nominal-test rejection fractions, variance ratios,
and near/far spatial effects.

Jarque–Bera pools temporally dependent samples and Ljung–Box combines repeated
disjoint windows. Their large-sample p-values and FDR flags are nominal
sensitivity diagnostics, not confirmatory error-calibrated inference.

The principal result is improvement without exact whiteness. Omission0 and
omission1 residual variance/raw variance are 0.360 and 0.499; median excess
kurtosis is 0.068 and 0.094 versus 0.588 raw; median mean absolute lag-1–30
autocorrelation is 0.024 and 0.045 versus 0.110 raw; and median near-contact
absolute correlation is 0.058 and 0.081 versus 0.374 raw. Nevertheless,
nominal Jarque–Bera rejects 81.5%/87.0% of residual channels and nominal
Ljung–Box rejects 100% for both routes after 5% FDR.

## Local regeneration

```bash
python code/figures/residual_diagnostics.py
```

The command validates both routes, writes the full and compact summary tables,
and renders all three figures. Final output hashes are:

| output | SHA-256 |
|---|---|
| `figures/residual_probe_overview.png` | `ee0205c30d901bc54c5f72a53c4f43c30bdb64e7cfe01e1106e6f8c1d3a0c2b0` |
| `figures/residual_distribution_temporal.png` | `f426b0d9b74397166d3971a29def44e8b27bb89359c0b711830df9410d08d87f` |
| `figures/residual_spatial_whiteness.png` | `2220c26e9cca0264affba9ca8f64e1943f97586a89c9df3acda4906dcdb98933` |
| `results/tables/residual_diagnostics_summary.csv` | `f8dc46d04821e581fca19e98205ee0632a87db2507376e1f9027dea0cf73e10d` |
| `results/tables/residual_diagnostics_summary.md` | `7aa084fe134fcf452b9f0ba9a9584c02910ce63fd4dc3ddd469d725d74bbcc8f` |

Recreating these compact artifacts from checkpoints and S3 is documented in
[`code/scoring/README.md`](../../code/scoring/README.md).