#!/bin/bash
# Job name:
#SBATCH --job-name=sleep
### scontrol show partitions | grep PartitionName | sed s/PartitionName=//
#
# Number of tasks needed for use case (example):
#SBATCH --ntasks=1
#
# Processors per task:
#SBATCH --cpus-per-task=8
#
# Wall clock limit
#SBATCH --time=2-00:00:00
#
#SBATCH --output=ignore/slurm_output/mega_slurm-%A.out
#SBATCH --array=0-4

echo $SLURM_ARRAY_TASK_ID
sleep 10s
echo "Goodbye"