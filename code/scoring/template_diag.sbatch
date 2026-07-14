#!/bin/bash
# Score one checkpoint's waveform diagnostics (amp_ratio, fwhm_ratio, temporal/spatial cos, snr)
# on the frozen AP-band benchmark. Usage: sbatch template_diag.sbatch <checkpoint.pt> <prefix>
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
CKPT="${1:?pass checkpoint path}"
PREFIX="${2:?pass output prefix}"
mkdir -p "$BASE/logs"
source "$FORGE/etc/profile.d/conda.sh"
conda activate "$BASE/env"
echo "host=$(hostname) job=$SLURM_JOB_ID ckpt=$CKPT prefix=$PREFIX date=$(date -Is)"
nvidia-smi --query-gpu=name --format=csv,noheader
S="aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3"
cd "$BASE/aind-ephys-deepinterpolation-inference/code"
srun python "$BASE/template_diag.py" \
    --rec-url "s3://$S/recording.zarr" \
    --gt-url  "s3://$S/sorting.zarr" \
    --checkpoint "$CKPT" --n-spikes 200 --batch-size 512 \
    --out "$BASE/${PREFIX}_diag.csv" --npz "$BASE/${PREFIX}_diag.npz"
echo "DONE"
