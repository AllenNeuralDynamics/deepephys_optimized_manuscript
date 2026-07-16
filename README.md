# DeepEphys Optimized — Manuscript & Reproducible Pipeline

A [MyST Markdown](https://mystmd.org) publication: an optimisation of the DeepInterpolation ephys
denoiser for Neuropixels spike detection — with a focus on protecting the weaker, low-amplitude
units — together with a fully reproducible **train → score → figure** pipeline.

> **Status:** Tier 1 + Tier 2 scored; the spike-weighting sweep (Tier 3) is in progress. See
> [`reproducibility/regeneration-plan.md`](reproducibility/regeneration-plan.md).

## Why this repo exists

DeepInterpolation raises SNR but can *reduce* spike detectability, and the cost falls hardest on the
weak units already near the sorting threshold. This repository optimises the ephys architecture to
protect those units — sweeping capacity, loss, temporal design, and spike-aware weighting — measuring
each choice directly against an injected hybrid ground-truth benchmark. Because the denoiser is
self-supervised, every model is **trained and scored in its deployment band** (AP-band), and the whole
pipeline is reproducible from scratch.

## Repository map

| path | contents |
|---|---|
| `index.md` | the manuscript (abstract + `{include}` of `sections/`) |
| `sections/` | manuscript sections (introduction, methods, results, discussion, appendix) |
| `reproducibility/reproduce.md` | step-by-step: environment → launch → score → figures → PDF |
| `reproducibility/regeneration-plan.md` | the pre-registered experimental design (jobs, quantification, figures) |
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
