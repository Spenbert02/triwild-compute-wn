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
module load openmpi/gcc/5.0.9

