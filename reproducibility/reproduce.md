# Reproduce

End-to-end: **environment → launch training → score checkpoints → collate → figures → HTML site.**
All identifiers (capsules, data assets, recording paths, HPC locations) are in
[](../data/provenance.md).

:::{danger} Secrets
Never commit or print credentials. Code Ocean access uses a token sourced from
`~/.codeocean.env` (git-ignored). Authenticate with `curl -u "$CODEOCEAN_TOKEN:"` — do not echo the
token.
:::

## 1. Environments

**Code Ocean (training).** Training runs in the `aind-ephys-deepinterpolation` capsule
(id in [](../data/provenance.md)); no local setup required beyond API credentials.

**AIND HPC (scoring).**
```bash
ssh -o BatchMode=yes jeromel@hpc-login
source /allen/aind/scratch/jeromel/astro_voltage_deepinterp/miniforge3/etc/profile.d/conda.sh
conda activate /allen/aind/scratch/jeromel/ephys_denoising/env
BASE=/allen/aind/scratch/jeromel/ephys_denoising
```

**Manuscript (local).**
```bash
pip install mystmd      # or npm install -g mystmd
```

## 2. Launch a training run (Code Ocean API)

Each parameter `key=val` becomes the env var `DI_<KEY>` inside the capsule. Body template:
```json
{
  "capsule_id": "<training-capsule-id>",
  "parameters": ["key=val", "..."],
  "data_assets": [{"id": "<hybrid-asset-id>", "mount": "hybrid_np1"}]
}
```
```bash
set -a; source ~/.codeocean.env; set +a
curl -s -u "$CODEOCEAN_TOKEN:" -H 'Content-Type: application/json' \
  -d @body.json "$CODEOCEAN_DOMAIN/api/v1/computations"
```
The original job plan and subsequent adaptive changes are documented in [](regeneration-plan.md);
the authoritative current ledger and exact overrides are in `results/runs.csv`. Every reported run
trains and is scored on the same AP-band recording (`train_recording_path` in the plan).

Check status (look at `end_status`, not `state`):
```bash
curl -s -u "$CODEOCEAN_TOKEN:" "$CODEOCEAN_DOMAIN/api/v1/computations/<id>"
```

## 3. Download checkpoints

`best_model.pt` (+ the 12 log-spaced `ckpt_step_*.pt` for trajectory runs) via the download helper
in [`code/figures/`](../code/figures/README.md), then stage to HPC:
```bash
rsync -t --no-perms --chmod=u+rwx -e "ssh -o BatchMode=yes" \
  <local_ckpt> jeromel@hpc-login:$BASE/checkpoints_sweep/ib/<label>/
```

## 4. Score on HPC (AP-band, frozen substrate)

```bash
sbatch code/scoring/run_ckpt.sbatch      <ckpt_abs> <out_dprime.csv>     # d′ metrics
sbatch code/scoring/template_diag.sbatch <ckpt_abs> <prefix>            # amp/fwhm/cos diagnostics
```
Both are pinned to the benchmark recording, 10 GT units, `seed=0` (see
[](../data/provenance.md)). See [`code/scoring/`](../code/scoring/README.md).

## 5. Collate + figures

Collate mean-over-10-units into the complete endpoint master table and per-unit matrices, then render
the figure collection (§6 of the plan). The collator resolves both root-level screen scores and
nested `best` scores from trajectory/control runs, and writes a ledger coverage audit. Scripts and
their exact inputs/outputs are documented in
[`code/figures/`](../code/figures/README.md).

```bash
python code/figures/collate.py
python code/figures/width_schedule_followup.py
python code/figures/make_figures.py
```

## 6. Build the manuscript (local HTML site)

```bash
myst start          # live preview at http://localhost:3000
myst build --html   # static site in _build/
```

## 7. Active and staged experiments

Current computation IDs and states are tracked in `results/runs.csv`. All training and scoring jobs
underlying the 87 current endpoints are complete. Two matched √2 schedule runs were added after the
coverage audit and have completed training, checkpoint validation, and frozen scoring. The
matched depth-2 base96 omission0/omission1 controls subsequently completed the same pipeline. The
regenerated coverage table therefore shows 87 scored endpoints and the intentionally aborted R7
PCGrad row as the sole exclusion.
