
import os
from datetime import datetime

from kgxval.dir.KGXSummarizer import KGXSummarizer
from dotenv import load_dotenv
import pandas as pd
from tqdm import tqdm

from kgxval.dir.Ingest import makeIngestObjsDict, Ingest
from kgxval.dir.pandas_outputter import ExcelDFFlags, makeExcelSheetForSource, makeSummaryDF


def pickMostRecentDownloadDir(ingest_dir):
    """The ingest directories are """
    fmt = "%b-%d-%y"
    l = list(zip([datetime.strptime(x,fmt) for x in os.listdir(ingest_dir)],os.listdir(ingest_dir)))
    latest_dir = max(l)[1]
    #print(f"Latest run was made on - {latest_dir}")
    return os.path.join(ingest_dir,latest_dir)

def main():
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    if ingest_dir == None:
        raise ValueError("Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)
    
    print(ingest_dict)
    return
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

def makeMegaSummary():
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    if ingest_dir == None:
        raise ValueError("Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)

    hp_cats:tuple[str,...] = tuple([
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ])

    datestr = datetime.now().strftime("%b-%d-%y")  # ex. Feb-16-2026
    outdir = f"data/output/{datestr}"
    os.makedirs(outdir, exist_ok=True)

    pbar:tqdm[str] = tqdm(sorted(list(ingest_dict)))
    first_key = sorted(list(ingest_dict))[0]
    first_ingest_obj = ingest_dict[first_key]["normalized"]
    norm_summ = KGXSummarizer.initWithIngestObj(first_ingest_obj, [])
    for i, source_name in enumerate(pbar):
        pbar.set_description(source_name)
        ingest_obj = ingest_dict[source_name]["normalized"]
        norm_summ.add_summarize_edges_for_iter(ingest_obj.iter_edges(),ingest_obj,source_name)
        #if(i==2):break
    writer = pd.ExcelWriter(f"data/merged_output/merged_summary_{datestr}.xlsx") 
    norm_df = makeSummaryDF(norm_summ.get_pd_rows(), rollup=False)
    norm_df.to_excel(
            writer, sheet_name=f"normalized_merge_summary", index=False
    )
    writer.close()
if __name__ == "__main__":
    #cntAbstInTMKP()
    #cntPMIDsInTMKP()
    
    main()
    #makeMegaSummary()