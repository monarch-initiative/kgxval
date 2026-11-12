#!/bin/bash
# Job name:
#SBATCH --job-name=kgx-deploy
cd ..
. .env

NUM_INFORES=$(ls $INGEST_TOP_LEVEL_DIR | wc -l)
ARRAY_VAL="0-"$(($NUM_INFORES-1))

echo $ARRAY_VAL
cd scripts

sbatch slurm_run_kgx_summary.sbatch --array=$ARRAY_VAL
