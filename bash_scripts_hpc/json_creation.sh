#!/bin/bash
#SBATCH --job-name=mesh_tagging
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=1:00:00
#SBATCH --account=torch_pr_870_general
#SBATCH --output=json_%j.out  # This captures your print statements/progress bar

module purge
module load anaconda3/2025.06
source /share/apps/anaconda3/2025.06/etc/profile.d/conda.sh
export PATH_TO_ENV=/home/seb9449/.conda/envs/offset_test_triwild_venv
source activate $PATH_TO_ENV
python -u $SCRATCH/offsets_testing_triwild/triwild-compute-wn/create_job_jsons.py -m $SCRATCH/offsets_testing_triwild/tagged_mshs_under10mb
