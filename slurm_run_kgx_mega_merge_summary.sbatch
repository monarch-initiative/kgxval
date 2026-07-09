#!/bin/bash
# Job name:
#SBATCH --job-name=kgx-mega-summarization
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
#SBATCH --output=ignore/slurm_output/mega_slurm-%A.out

#--begin=now+4hour

mkdir -p ignore/slurm_output
uv sync
. .env
uv run merge_sources_together $INGEST_TOP_LEVEL_DIR --ignore_sem_icees_uber True
uv run merge_sources_together $INGEST_TOP_LEVEL_DIR --ignore_sem_icees_uber False