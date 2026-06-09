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
#
#SBATCH --output=ignore/slurm_output/slurm-%j.out

uv run python src/kgxval/dir/analyze_predicate_prevelance.py