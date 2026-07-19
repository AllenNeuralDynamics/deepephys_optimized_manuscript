# DeepEphys Optimized — Manuscript & Reproducible Pipeline

A [MyST Markdown](https://mystmd.org) publication: an optimisation of the DeepInterpolation ephys
denoiser for Neuropixels spike detection — with a focus on protecting the weaker, low-amplitude
units — together with a fully reproducible **train → score → figure** pipeline.

> **Status:** all planned Code Ocean training and all 610 HPC scoring jobs are complete. The report
> includes the architecture and recipe screens, matched replications, gradient and integration
> controls, validation-loss headroom calibration, capacity-matched NAF control, corrected weighting
> screen, and duration trajectories.

## Why this repo exists

DeepInterpolation can raise peak-channel template SNR while reducing matched-filter detectability.
This repository evaluates architecture and training choices against an injected hybrid benchmark,
with special attention to weak units. Because the denoiser is self-supervised, models are trained and
scored in the AP band; benchmark-specific conclusions still require held-out-recording and sorter-level
validation.

## Repository map

| path | contents |
|---|---|
| `index.md` | the manuscript (abstract + `{include}` of `sections/`) |
| `sections/` | manuscript sections (introduction, methods, results, discussion, appendix) |
| `reproducibility/reproduce.md` | step-by-step: environment → launch → score → figures → PDF |
| `reproducibility/regeneration-plan.md` | versioned experimental and analysis plan (including adaptive reprioritization) |
| `data/provenance.md` | Code Ocean capsule/asset IDs, recording paths, HPC locations |
| `code/` | scoring (HPC sbatch), figure-generation, and training-launch scripts + docs |
| `figures/` | manuscript figure assets |
| `references.bib` | bibliography |

## Build

```bash
# one-time: install the MyST CLI
pip install mystmd            # or: npm install -g mystmd

# live preview of the website (http://localhost:3000)
myst start

# build the static HTML site (output in _build/)
myst build --html
```

The manuscript is read as a **local HTML website** (MyST book theme). No PDF or LaTeX toolchain is
required.

## Reproducing the results

See [`reproducibility/reproduce.md`](reproducibility/reproduce.md). In short: training runs on
Code Ocean (capsule + data asset in [`data/provenance.md`](data/provenance.md)); checkpoints are
scored on the AIND HPC with the sbatch scripts in `code/scoring/`; tables and figures are
collated by the scripts in `code/figures/`.

## Citation

See [`CITATION.cff`](CITATION.cff). Licensed CC-BY-4.0 (content) / MIT (code).
