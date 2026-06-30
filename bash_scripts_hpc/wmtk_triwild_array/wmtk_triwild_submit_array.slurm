#!/bin/bash
#SBATCH --job-name=wmtk_triwild
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=1:00:00
#SBATCH --account=torch_pr_870_general
#SBATCH --output=logs/job_%A_%a.out 
#SBATCH --error=logs/job_%A_%a.err

export OMP_NUM_THREADS=1
export IGL_NUM_THREADS=1

# UPDATE THIS to match the base directory in your python script
WMTK_EXE="/scratch/seb9449/wildmeshing-toolkit/build/app/wmtk_app"

RUN_LIST=$1

# Grab the json path
LINE_NUM=$((SLURM_ARRAY_TASK_ID + 1))
JSON_PATH=$(sed -n "${LINE_NUM}p" "$RUN_LIST")

echo "=========================================="
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Processing JSON: $JSON_PATH"
echo "=========================================="

# Execute offsets
"$WMTK_EXE" -j "$JSON_PATH"