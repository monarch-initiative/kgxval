#!/bin/bash
# Job name:
#SBATCH --job-name=translator-kgx-build
#
# Partition:
#SBATCH --partition=inter
#--partition=largemem
#
### scontrol show partitions | grep PartitionName | sed s/PartitionName=//
#
#SBATCH --ntasks=1
#
# Processors per task:
#SBATCH --cpus-per-task=8
#
# Wall clock limit
#SBATCH --time=2-00:00:00
#
#SBATCH --mem=25GB
#SBATCH --output=ignore/slurm_output/slurm-%j.out
## Command(s) to run (example):

mkdir -p ignore/slurm_output
rm ignore/translator-ingests/data/* -rf
cd ignore/translator-ingests

make run
