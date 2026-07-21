#!/bin/bash
# Sweep temporal/channel template support with in-sample and cross-fitted d-prime.
# Usage: sbatch template_support_sweep.sbatch <checkpoint> <reference.csv> <out_prefix> <inference_code> <model_label> [scoring_code]
#SBATCH --partition=aind
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:30:00
#SBATCH --output=/allen/aind/scratch/jeromel/ephys_denoising/logs/%x_%j.out
#SBATCH --error=/allen/aind/scratch/jeromel/ephys_denoising/logs/%x_%j.err
set -eo pipefail
BASE=/allen/aind/scratch/jeromel/ephys_denoising
FORGE=/allen/aind/scratch/jeromel/astro_voltage_deepinterp/miniforge3
CHECKPOINT="${1:?pass checkpoint}"
REFERENCE="${2:?pass reference endpoint CSV}"
OUT_PREFIX="${3:?pass output prefix}"
INFERENCE_CODE="${4:?pass pinned inference code directory}"
MODEL_LABEL="${5:?pass model label}"
SCORING_CODE="${6:-$BASE/manuscript_scoring}"
for SCRIPT in run_with_inference.py template_support_sweep.py detection_metrics.py; do
    [[ -f "$SCORING_CODE/$SCRIPT" ]] || { echo "missing $SCORING_CODE/$SCRIPT" >&2; exit 2; }
done
mkdir -p "$BASE/logs" "$(dirname "$OUT_PREFIX")"
source "$FORGE/etc/profile.d/conda.sh"
conda activate "$BASE/env"
S="aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3"
echo "host=$(hostname) job=$SLURM_JOB_ID model=$MODEL_LABEL date=$(date -Is)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
srun env INFERENCE_CODE="$INFERENCE_CODE" \
    PYTHONPATH="$SCORING_CODE:$INFERENCE_CODE${PYTHONPATH:+:$PYTHONPATH}" \
    python "$SCORING_CODE/run_with_inference.py" \
    "$SCORING_CODE/template_support_sweep.py" \
    --rec-url "s3://$S/recording.zarr" \
    --gt-url "s3://$S/sorting.zarr" \
    --checkpoint "$CHECKPOINT" \
    --reference-scores "$REFERENCE" \
    --model-label "$MODEL_LABEL" \
    --out-prefix "$OUT_PREFIX" \
    --device cuda --batch-size 512 --n-spikes 100 --n-background 200 --seed 0
echo "DONE"