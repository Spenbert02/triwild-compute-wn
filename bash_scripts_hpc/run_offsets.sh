#!/bin/bash
#SBATCH --job-name=mesh_tagging
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=1:00:00
#SBATCH --account=torch_pr_870_general
#SBATCH --output=tagging_%j.out  # This captures your print statements/progress bar

module purge
module load anaconda3/2025.06
source /share/apps/anaconda3/2025.06/etc/profile.d/conda.sh
export PATH_TO_ENV=/home/seb9449/.conda/envs/offset_test_triwild_venv
source activate $PATH_TO_ENV
export LD_LIBRARY_PATH=$SCRATCH/gmp_install/lib:$LD_LIBRARY_PATH
python -u $SCRATCH/offsets_testing_triwild/triwild-compute-wn/python_scripts/run_offsets.py -m $SCRATCH/offsets_testing_triwild/tagged_mshs_under_10mb -e $SCRATCH/offsets_testing_triwild/wildmeshing-toolkit/build/app/wmtk_app
