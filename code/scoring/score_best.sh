#!/bin/bash
# Submit d' + waveform-diagnostic scoring for a single best_model checkpoint, writing FLAT
# output names (traj_scores/<label>_dprime.csv and traj_scores/<label>_diag.csv) that
# code/figures/collate.py consumes for the master table / noise floor.
#
# Usage (on the AIND HPC login node):
#   score_best.sh <label> <ckpt_path>
set -eo pipefail
BASE=/allen/aind/scratch/jeromel/ephys_denoising
LABEL="${1:?pass label, e.g. ib_champion_s0}"
CKPT="${2:?pass checkpoint path}"
cd "$BASE"
mkdir -p traj_scores logs
sbatch --job-name="dp_${LABEL}" run_ckpt.sbatch      "$CKPT" "$BASE/traj_scores/${LABEL}_dprime.csv"
sbatch --job-name="dg_${LABEL}" template_diag.sbatch "$CKPT" "traj_scores/${LABEL}"
echo "submitted $LABEL"
