# DeepEphys Optimized — Manuscript & Reproducible Pipeline

A [MyST Markdown](https://mystmd.org) publication: a strictly **in-domain** re-evaluation of the
DeepInterpolation ephys denoiser for Neuropixels spike detection, together with a fully
reproducible **train → score → figure** pipeline.

> **Status:** manuscript skeleton + pre-registered design. The in-domain (AP-band) results are
> being regenerated; numbers land as scoring completes. See
> [`reproducibility/regeneration-plan.md`](reproducibility/regeneration-plan.md).

## Why this repo exists

The prior internal report trained DeepInterpolation on **wide-band** data but evaluated it on
**high-passed AP-band** data — the denoiser ran outside its training domain, so every absolute
number and ranking is out-of-band. This repository re-does the study with one rule: **train and
evaluate in the same band, on the same recording the model is deployed on.** It is organized so a
reviewer can reproduce every table and figure from scratch.

## Repository map

| path | contents |
|---|---|
| `index.md` | the manuscript (abstract + `{include}` of `sections/`) |
| `sections/` | manuscript sections (introduction, methods, results, discussion, appendix) |
| `reproducibility/reproduce.md` | step-by-step: environment → launch → score → figures → PDF |
| `reproducibility/regeneration-plan.md` | the pre-registered experimental design (jobs, quantification, figures) |
| `data/provenance.md` | Code Ocean capsule/asset IDs, recording paths, HPC locations |
| `code/` | scoring (HPC sbatch), figure-generation, and training-launch scripts + docs |
| `figures/` | manuscript figure assets (generated in-band) |
| `references.bib` | bibliography |
| `archive/` | the superseded, out-of-band v1 report (kept for provenance) |

## Build

```bash
# one-time: install the MyST CLI
pip install mystmd            # or: npm install -g mystmd

# live preview of the website
myst start

# build the manuscript PDF (typst template; no system LaTeX needed)
myst build --pdf
# -> exports/manuscript.pdf

# list / switch templates
myst templates list --pdf
```

To use a LaTeX/arXiv style instead, change `exports.template` in `index.md` to e.g.
`arxiv_two_column` (requires a LaTeX toolchain such as `tectonic`).

## Reproducing the results

See [`reproducibility/reproduce.md`](reproducibility/reproduce.md). In short: training runs on
Code Ocean (capsule + data asset in [`data/provenance.md`](data/provenance.md)); checkpoints are
scored on the AIND HPC with the sbatch scripts in `code/scoring/`; tables and figures are
collated by the scripts in `code/figures/`.

## Citation

See [`CITATION.cff`](CITATION.cff). Licensed CC-BY-4.0 (content) / MIT (code).
