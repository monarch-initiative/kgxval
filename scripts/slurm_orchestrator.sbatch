#!/bin/bash
# Job name:
#SBATCH --job-name=orchestrator
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
#SBATCH --output=ignore/slurm_output/%A-orchestrator.out

echo "10s go"
cd ..
. .env

NUM_INFORES=$(ls $INGEST_TOP_LEVEL_DIR | wc -l)
ARRAY_VAL="0-"$(($NUM_INFORES-1))

echo "FOUND FOLLOWING NUMBER OF INFORES in $INGEST_TOP_LEVEL_DIR:$NUM_INFORES"
cd scripts

kgx_sum_jid=$(sbatch --array=$ARRAY_VAL ./slurm_run_kgx_summary.sbatch | cut -d ' ' -f4)
echo "KGX SUMMARY JOB ID:$kgx_sum_jid"
merged_jid=$(sbatch ./slurm_run_kgx_mega_merge_summary.sbatch | cut -d ' ' -f4)
echo "MERGE ALL SOURCES JOB ID:$merged_jid"
prev_jid=$(sbatch ./slurm_run_prevelance_summary.sbatch | cut -d ' ' -f4)
echo "PREVELANCE SUMMARY JOB ID:$prev_jid"

sbatch --dependency=afterok:$kgx_sum_jid:$merged_jid:$prev_jid ./slurm_format_xlsx_files.sbatch --dependency=afterok:$kgx_sum_jid:$merged_jid:$prev_jid
