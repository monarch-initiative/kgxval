#!/bin/bash
# Job name:
#SBATCH --job-name=file-formatter
#
# Partition:
#SBATCH --partition=batch
### scontrol show partitions | grep PartitionName | sed s/PartitionName=//
#
# Number of tasks needed for use case (example):
#SBATCH --ntasks=1
#
# Processors per task:
#SBATCH --cpus-per-task=1
#
# Wall clock limit
#SBATCH --time=2-00:00:00
#
#SBATCH --output=ignore/slurm_output/%A-file-formatter.out

cd ..
. .env

INGEST_DIR_NAME=$(basename $INGEST_TOP_LEVEL_DIR)
format_dir="data/output/$INGEST_DIR_NAME"
for x in $(find $format_dir -name "*.xlsx"); 
       do uv run src/kgxval/utils/format_xlsx.py $x; 
done

mkdir -p data/zipped
zip data/zipped/$INGEST_DIR_NAME.zip FORMATTED/data/output/$INGEST_DIR_NAME/* -r