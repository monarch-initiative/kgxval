To download latest 
KGX-Storage-Download-Helper/get_json_of_node-and-edges_v2.ipynb
KGX-Storage-Download-Helper/download_before_may_8.sh

Run 
      sbatch slurm_run_kgx_summary.sbatch
   Which will build individual ingest files for every ingest.
   In parallel run 
      sbatch slurm_run_kgx_mega_merge_summary.sbatch
   Which will build a harmonized ingest summary.
   In parallel also run
      sbatch slurm_run_prevelance_summary.sbatch
   (Which will go into "data/blink_pred_output/biolink_class_level_summary_{datestr}.xlsx")
   Which will look at node classes.


Then once all of these have built run format
   uv run python src/kgxval/utils/concat_kgx_summaries.py

Move file in data/blink_pred_output/biolink_class_level_summary_{datestr}.xlsx to data/output/Sep-18-26

for x in $(find data/output/Sep-18-26 -name "*.xlsx"); do echo $x; done
    FOR $XLSX IN OUTPUT.
        uv run python src/kgxval/utils/format_xlsx.py $XLSX
   
   
   for x in $(find data/output/Aug-04-26); 
       do uv run src/kgxval/utils/format_xlsx.py $x; 
   done

Then zip all files in format dir and send them to Google Drive.
