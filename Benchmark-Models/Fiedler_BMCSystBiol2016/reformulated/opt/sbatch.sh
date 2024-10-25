#!/bin/bash
#SBATCH --job-name fied
#SBATCH --output log/%j.log
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 48
#SBATCH --time 07-00:00:00
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=maren.philipps@uni-bonn.de

source home/maren/prerequisites.sh
source /home/maren/devenv/bin/activate
python calibrate.py
