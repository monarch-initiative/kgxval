

import os
from pathlib import Path
from typing import Optional

from Ingest import findEdgeFile, findNodeFile, Ingest, makeIngestObjsFromTopLevelDir
from check_kgx_so import SPOCValidationError, inspectSubObjErrorsForIngest, validationErrorsToFile


if(__name__=="__main__"):
    from dotenv import load_dotenv
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    print(ingest_dir)
    valid_errors:list[SPOCValidationError] = []
    for ingest_obj in makeIngestObjsFromTopLevelDir(ingest_dir):
        valid_errors+=inspectSubObjErrorsForIngest(ingest_obj)
    validationErrorsToFile(valid_errors,"data/spoc_validation_errors.csv")