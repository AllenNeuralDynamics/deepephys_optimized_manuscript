#!/bin/bash
# Score one checkpoint's waveform diagnostics (amp_ratio, fwhm_ratio, temporal/spatial cos, snr)
# on the frozen AP-band benchmark.
# Usage: sbatch template_diag.sbatch <checkpoint.pt> <prefix> [inference_code]
# Writes $BASE/<prefix>_diag.csv (+ .npz). Per-unit rows; mean over 10 GT units = aggregate.
# Vendored copy of the HPC script at $BASE/template_diag.sbatch (source of truth).
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
CKPT_ARG="${1:?pass checkpoint path}"
PREFIX_ARG="${2:?pass output prefix}"
INFERENCE_CODE_ARG="${3:-}"
[[ "$CKPT_ARG" = /* ]] && CKPT="$CKPT_ARG" || CKPT="${SLURM_SUBMIT_DIR:-$PWD}/$CKPT_ARG"
[[ "$PREFIX_ARG" = /* ]] && PREFIX="$PREFIX_ARG" || PREFIX="$BASE/$PREFIX_ARG"
mkdir -p "$BASE/logs"
mkdir -p "$(dirname "$PREFIX")"
source "$FORGE/etc/profile.d/conda.sh"
conda activate "$BASE/env"
echo "host=$(hostname) job=$SLURM_JOB_ID ckpt=$CKPT prefix=$PREFIX date=$(date -Is)"
nvidia-smi --query-gpu=name --format=csv,noheader
S="aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3"
INFERENCE_CODE="${INFERENCE_CODE_ARG:-${INFERENCE_CODE:-$BASE/aind-ephys-deepinterpolation-inference/code}}"
echo "inference_code=$INFERENCE_CODE"
cd "$INFERENCE_CODE"
srun env INFERENCE_CODE="$INFERENCE_CODE" \
    PYTHONPATH="$INFERENCE_CODE${PYTHONPATH:+:$PYTHONPATH}" \
    python "$BASE/run_with_inference.py" "$BASE/template_diag.py" \
    --rec-url "s3://$S/recording.zarr" \
    --gt-url  "s3://$S/sorting.zarr" \
    --checkpoint "$CKPT" --n-spikes 200 --batch-size 512 \
    --out "${PREFIX}_diag.csv" --npz "${PREFIX}_diag.npz"
echo "DONE"
