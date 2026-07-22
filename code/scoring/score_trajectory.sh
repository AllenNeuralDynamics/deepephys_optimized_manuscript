#!/bin/bash
# Submit d' + waveform-diagnostic scoring for EVERY checkpoint of a trajectory run.
# Scores in-band on the frozen AP-band benchmark (recording1_3) via the two sbatch
# wrappers in this directory.
#
# Usage:
#   score_trajectory.sh <label> <ckpt_dir> [inference_code_dir] [scoring_code_dir]
#     <label>    output stem, e.g. ib_om0_scale  -> traj_scores/<label>_<tag>_{dprime,diag}.csv
#     <ckpt_dir> directory of *.pt (best_model.pt + ckpt_step_*.pt), absolute path
#
# Emits, per checkpoint: tag = 'best' for best_model.pt, 's<step>' for ckpt_step_<step>.pt
# (last_model.pt is skipped). Run on the AIND HPC login node.
set -eo pipefail
BASE=/allen/aind/scratch/jeromel/ephys_denoising
LABEL="${1:?pass label, e.g. ib_om0_scale}"
CKPT_DIR="${2:?pass checkpoint dir (abs path)}"
INFERENCE_CODE="${3:-$BASE/aind-ephys-deepinterpolation-inference-808d7fa/code}"
SCORING_CODE="${4:-${SCORING_CODE:-$BASE/manuscript_scoring}}"
cd "$BASE"
mkdir -p traj_scores logs
n=0
for f in "$CKPT_DIR"/*.pt; do
  b=$(basename "$f" .pt)
  case "$b" in
    best_model)  tag=best ;;
    last_model)  continue ;;
    ckpt_step_*) tag="s${b#ckpt_step_}" ;;
    *)           tag="$b" ;;
  esac
  lbl="${LABEL}_${tag}"
  sbatch --job-name="dp_${lbl}" "$SCORING_CODE/run_ckpt.sbatch" \
    "$f" "$BASE/traj_scores/${lbl}_dprime.csv" "$INFERENCE_CODE" "$SCORING_CODE"
  sbatch --job-name="dg_${lbl}" "$SCORING_CODE/template_diag.sbatch" \
    "$f" "traj_scores/${lbl}" "$INFERENCE_CODE" "$SCORING_CODE"
  n=$((n + 1))
done
echo "submitted $n checkpoint(s) x2 jobs for $LABEL"
