#!/bin/bash
# Export compact raw/denoised traces, templates, and score distributions for figures.
# Usage: sbatch export_qualitative_examples.sbatch <export.py> <metrics.py> <checkpoint> <reference.csv> <out.npz> <metadata.json> <inference_code>
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
EXPORT_SCRIPT="${1:?pass export script}"
METRICS_SCRIPT="${2:?pass detection_metrics.py}"
CHECKPOINT="${3:?pass checkpoint}"
REFERENCE="${4:?pass reference dprime csv}"
OUTPUT="${5:?pass output npz}"
METADATA="${6:?pass metadata json}"
INFERENCE_CODE="${7:?pass pinned inference code directory}"
mkdir -p "$BASE/logs" "$(dirname "$OUTPUT")"
source "$FORGE/etc/profile.d/conda.sh"
conda activate "$BASE/env"
METRICS_TARGET="$(dirname "$EXPORT_SCRIPT")/detection_metrics.py"
if [[ "$(realpath "$METRICS_SCRIPT")" != "$(realpath -m "$METRICS_TARGET")" ]]; then
    cp "$METRICS_SCRIPT" "$METRICS_TARGET"
fi
S="aind-benchmark-data/ephys-hybrid-evaluation/sorters/np1/ecephys_681532_2023-10-18_13-01-15/experiment1_Record Node 103#Neuropix-PXI-100.ProbeC-AP_recording1_3"
echo "host=$(hostname) job=$SLURM_JOB_ID checkpoint=$CHECKPOINT date=$(date -Is)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
srun env PYTHONPATH="$INFERENCE_CODE${PYTHONPATH:+:$PYTHONPATH}" \
    python "$EXPORT_SCRIPT" \
    --rec-url "s3://$S/recording.zarr" \
    --gt-url "s3://$S/sorting.zarr" \
    --checkpoint "$CHECKPOINT" \
    --inference-code "$INFERENCE_CODE" \
    --reference-scores "$REFERENCE" \
    --out "$OUTPUT" \
    --metadata "$METADATA" \
    --model-label ib_w96_om0_s0 \
    --units 2143,1143,720,1129 \
    --exemplar-unit 1143 \
    --device cuda --batch-size 512
echo "DONE"