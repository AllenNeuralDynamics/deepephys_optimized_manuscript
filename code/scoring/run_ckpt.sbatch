#!/bin/bash
# Score one checkpoint's detection sensitivity (d') on the frozen AP-band benchmark.
# Usage: sbatch run_ckpt.sbatch <checkpoint.pt> <out_dprime.csv> [inference_code] [scoring_code]
# Output CSV columns: unit_id, ..., dprime_deep, dprime_deep_fixed, ... (mean over 10 GT units = aggregate).
# Stage this repository directory at $BASE/manuscript_scoring before submission.
#SBATCH --partition=aind
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --output=/allen/aind/scratch/jeromel/ephys_denoising/logs/%x_%j.out
#SBATCH --error=/allen/aind/scratch/jeromel/ephys_denoising/logs/%x_%j.err
set -eo pipefail
BASE=/allen/aind/scratch/jeromel/ephys_denoising
FORGE=/allen/aind/scratch/jeromel/astro_voltage_deepinterp/miniforge3
CKPT_ARG="${1:?pass checkpoint path as arg 1}"
OUT_ARG="${2:?pass output csv as arg 2}"
INFERENCE_CODE_ARG="${3:-}"
SCORING_CODE_ARG="${4:-}"
[[ "$CKPT_ARG" = /* ]] && CKPT="$CKPT_ARG" || CKPT="${SLURM_SUBMIT_DIR:-$PWD}/$CKPT_ARG"
[[ "$OUT_ARG" = /* ]] && OUT="$OUT_ARG" || OUT="$BASE/$OUT_ARG"
mkdir -p "$BASE/logs"
mkdir -p "$(dirname "$OUT")"
source "$FORGE/etc/profile.d/conda.sh"
conda activate "$BASE/env"
echo "host=$(hostname) job=$SLURM_JOB_ID ckpt=$CKPT date=$(date -Is)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
S="aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3"
INFERENCE_CODE="${INFERENCE_CODE_ARG:-${INFERENCE_CODE:-$BASE/aind-ephys-deepinterpolation-inference-808d7fa/code}}"
SCORING_CODE="${SCORING_CODE_ARG:-${SCORING_CODE:-$BASE/manuscript_scoring}}"
for SCRIPT in run_with_inference.py run_hybrid_s3.py detection_metrics.py; do
    [[ -f "$SCORING_CODE/$SCRIPT" ]] || { echo "missing $SCORING_CODE/$SCRIPT" >&2; exit 2; }
done
echo "inference_code=$INFERENCE_CODE scoring_code=$SCORING_CODE"
cd "$INFERENCE_CODE"
srun env INFERENCE_CODE="$INFERENCE_CODE" \
    PYTHONPATH="$SCORING_CODE:$INFERENCE_CODE${PYTHONPATH:+:$PYTHONPATH}" \
    python "$SCORING_CODE/run_with_inference.py" "$SCORING_CODE/run_hybrid_s3.py" \
    --rec-url "s3://$S/recording.zarr" \
    --gt-url  "s3://$S/sorting.zarr" \
    --checkpoint "$CKPT" \
    --n-spikes 100 --n-bg 200 --batch-size 512 \
    --out "$OUT"
echo "DONE"
