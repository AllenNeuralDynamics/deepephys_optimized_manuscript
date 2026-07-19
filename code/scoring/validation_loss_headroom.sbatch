#!/bin/bash
# Usage: sbatch validation_loss_headroom.sbatch <analysis.py> <checkpoint.pt> <out.csv>
#SBATCH --partition=aind
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/allen/aind/scratch/jeromel/ephys_denoising/logs/%x_%j.out
#SBATCH --error=/allen/aind/scratch/jeromel/ephys_denoising/logs/%x_%j.err
set -eo pipefail

BASE=/allen/aind/scratch/jeromel/ephys_denoising
FORGE=/allen/aind/scratch/jeromel/astro_voltage_deepinterp/miniforge3
SCRIPT_ARG="${1:?pass analysis script as arg 1}"
CHECKPOINT_ARG="${2:?pass checkpoint as arg 2}"
OUT_ARG="${3:?pass output CSV as arg 3}"
SUBMIT_DIR="${SLURM_SUBMIT_DIR:-$PWD}"
[[ "$SCRIPT_ARG" = /* ]] && SCRIPT="$SCRIPT_ARG" || SCRIPT="$SUBMIT_DIR/$SCRIPT_ARG"
[[ "$CHECKPOINT_ARG" = /* ]] && CHECKPOINT="$CHECKPOINT_ARG" || CHECKPOINT="$SUBMIT_DIR/$CHECKPOINT_ARG"
[[ "$OUT_ARG" = /* ]] && OUT="$OUT_ARG" || OUT="$SUBMIT_DIR/$OUT_ARG"
S="aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3"

mkdir -p "$BASE/logs" "$(dirname "$OUT")"
source "$FORGE/etc/profile.d/conda.sh"
conda activate "$BASE/env"
INFERENCE_CODE="$BASE/aind-ephys-deepinterpolation-inference/code"
export PYTHONPATH="$INFERENCE_CODE${PYTHONPATH:+:$PYTHONPATH}"
cd "$INFERENCE_CODE"

echo "host=$(hostname) job=$SLURM_JOB_ID checkpoint=$CHECKPOINT date=$(date -Is)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
srun --chdir="$INFERENCE_CODE" python "$SCRIPT" \
    --checkpoint "$CHECKPOINT" \
    --rec-url "s3://$S/recording.zarr" \
    --gt-url "s3://$S/sorting.zarr" \
    --label ib_r5_bs256 \
    --batch-size 256 \
    --out "$OUT"
echo "DONE"