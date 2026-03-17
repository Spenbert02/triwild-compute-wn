#!/bin/bash
#SBATCH --job-name=mesh_tagging
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --account=torch_pr_870_general
#SBATCH --output=tagging_%j.out  # This captures your print statements/progress bar

module purge
$SCRATCH/offsets_testing_triwild/triwild-compute-wn/build/compute_wn $SCRATCH/linear_results/ $SCRATCH/out_fix/ $SCRATCH/offsets_testing_triwild/tagged_mshs_redone/
