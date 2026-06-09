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
#--array=0-31
#SBATCH --output=ignore/slurm_output/slurm-%A_%a.out
## Command(s) to run (example):

#--begin=now+4hour

mkdir -p ignore/slurm_output
uv sync
. .env
uv run many_sources $INGEST_TOP_LEVEL_DIR --task_number $SLURM_ARRAY_TASK_ID
