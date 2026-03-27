from collections import defaultdict
from datetime import datetime
import os
import csv
from pathlib import Path
import pickle
from typing import Optional

from dotenv import load_dotenv

from Ingest import (
    findEdgeFile,
    findNodeFile,
    Ingest,
    makeIngestObjsDict,
    makeIngestObjsFromTopLevelDir,
)
from KGXSummarizer import KGXSummarizer
from biolink_validation.check_kgx_sub_obj_pred import (
    SPOCValidationError,
    findSubObjErrorsForIngest,
    validationErrorsToFile,
)
import pandas as pd
from pandas_outputter import ExcelDFFlags, makeExcelSheetForSource
from tqdm import tqdm


def main():
    from dotenv import load_dotenv

    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    if ingest_dir == None:
        raise ValueError(f"Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)

    hp_cats = [
        "anatomical entity",
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ]
    hp_cats = [
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ]

    datestr = datetime.now().strftime("%b-%d-%y")  # ex. Feb-16-2026
    outdir = f"data/output/{datestr}"
    os.makedirs(outdir, exist_ok=True)

    pbar = tqdm(sorted(list(ingest_dict)))
    slurm_job = os.getenv("SLURM_ARRAY_TASK_ID")
    print(f"\n$SLURM_ARRAY_TASK_ID is {slurm_job}\n")
    for i, source_name in enumerate(pbar):
        #        if(slurm_job is not None):
        #            if(i==int(slurm_job)):
        #                 print(f"\n === Executing build for source {i} - {source_name} === \n")
        #            else:continue
        #        else:
        #             continue
        #        print(i)
        #        continue
        if "cohd" not in source_name:
            continue
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


def compareCTDPrePostNorm():
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)
    hp_cats = [
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ]
    hp_cats = []
    ctd_ingest = KGXSummarizer.initWithIngestObj(
        ingest_dict["ctd"]["normalized"], hp_cats
    )
    unnorm_ctd_ingest = KGXSummarizer.initWithIngestObj(
        ingest_dict["ctd"]["not_normalized"], hp_cats
    )
    seen_subs = set()
    with open("data/output/ctd_normalized_to_genes.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "NODE_ID",
                "NODE_NAME",
                "PRE-NORMALIZATION_ID",
                "PRE-NORMALIZATION_NAME",
                "PRE-NORMALIZATION_CATEGORY",
                "ASSIGNED_CATEGORY",
                "ALL_NODE_CATEGORIES_(from_node_norm)",
            ]
        )
        for node_dict in ctd_ingest.iter_nodes():
            sub_id = node_dict["id"]
            if sub_id in seen_subs:
                continue
            seen_subs.add(sub_id)
            all_subs = ctd_ingest.get_node_id_category(sub_id)
            best_sub = ctd_ingest._getBestCat(all_subs)
            if "gene or gene product" in all_subs:
                sub_name = ctd_ingest.get_node_id_name(sub_id)
                not_norm_sub_cat = "n/a"
                not_norm_ids = []
                not_norm_name = ""
                for equiv in ctd_ingest.get_node_id_to_equiv_ids(sub_id):
                    if equiv in unnorm_ctd_ingest.get_node_to_category_dict():
                        not_norm_ids.append(equiv)
                        not_norm_name = unnorm_ctd_ingest.get_node_id_name(equiv)
                        not_norm_sub_cat = "|".join(
                            unnorm_ctd_ingest.get_node_id_category(equiv)
                        )
                if not_norm_sub_cat == "chemical entity":
                    if best_sub != "protein":
                        print("WACK!!!", all_subs, best_sub, sub_id)
                    writer.writerow(
                        [
                            sub_id,
                            sub_name,
                            ", ".join(not_norm_ids),
                            not_norm_name,
                            not_norm_sub_cat,
                            best_sub,
                            ", ".join(sorted(all_subs)),
                        ]
                    )


if __name__ == "__main__":
    #    compareCTDPrePostNorm()
    main()
