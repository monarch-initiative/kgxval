#!/bin/bash
# Job name:
#SBATCH --job-name=cleanup
#
# Partition:
#SBATCH --partition=general
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

cd ..
. .env
date_dir=$(uv run python -c 'import datetime;datestr = datetime.datetime.now().strftime("%b
-%d-%y");print(datestr);')