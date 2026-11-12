#!/bin/bash
# Job name:
#SBATCH --job-name=kgx-summarization
#
# Partition:
#SBATCH --partition=largemem
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
#SBATCH --mem=250GB
#SBATCH --array=0-31
#SBATCH --output=ignore/slurm_output/%A_%a-kgx_summ.out
## Command(s) to run (example):

#--begin=now+4hour
cd ..
mkdir -p ignore/slurm_output
uv sync
. .env
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"
uv run ingest_summary $INGEST_TOP_LEVEL_DIR --task_number $SLURM_ARRAY_TASK_ID
