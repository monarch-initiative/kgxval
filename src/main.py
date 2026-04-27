
import os
from datetime import datetime

from dotenv import load_dotenv
from tqdm import tqdm

from lib.Ingest import makeIngestObjsDict, Ingest
from lib.pandas_outputter import ExcelDFFlags, makeExcelSheetForSource

def main():
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    if ingest_dir == None:
        raise ValueError("Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)

    #hp_cats = [
    #    "anatomical entity",
    #    "gene or gene product",
    #    "disease or phenotypic feature",
    #    "chemical entity",
    #]
    hp_cats:tuple[str,...] = tuple([
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ])

    datestr = datetime.now().strftime("%b-%d-%y")  # ex. Feb-16-2026
    outdir = f"data/output/{datestr}"
    os.makedirs(outdir, exist_ok=True)

    pbar:tqdm[str] = tqdm(sorted(list(ingest_dict)))
    slurm_job = os.getenv("SLURM_ARRAY_TASK_ID")
    print(f"\n$SLURM_ARRAY_TASK_ID is {slurm_job}\n")
    for i, source_name in enumerate(pbar):
        #If $SLURM_ARRAY_TASK_ID is set; we're subdividing the task between multiple different compute cores.
        #This code will skip/continue past all datasets except dataset i==$SLURM_ARRAY_TASK_ID
        if(slurm_job is not None):
            if(i==int(slurm_job)):
                print(f"\n === Executing build for source {i} - {source_name} === \n")
            else:continue
        pbar.set_description(source_name)
        excel_sheet_flags = ExcelDFFlags(unnorm_samp=False, unnorm_summ=False)

        makeExcelSheetForSource(
            ingest_dict=ingest_dict,
            source_name=source_name,
            hp_cats=hp_cats,
            outpath=f"{outdir}/{source_name}_{datestr}_summary.xlsx",
            pbar=pbar,
            config=excel_sheet_flags,
        )

if __name__ == "__main__":
    #cntAbstInTMKP()
    #cntPMIDsInTMKP()
    main()
