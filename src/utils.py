import csv
import json
from pathlib import Path
from typing import Iterable


def JSONLDictGen(file_loc: Path) -> Iterable[dict]:
    with open(file_loc) as edgejsonl:
        for row in edgejsonl: 
            d = json.loads(row)
            #d["original_json"] = row
            yield d

def TSVDictGen(file_loc: Path) -> Iterable[dict]:
    with open(file_loc) as edgetsv:
        dReader = csv.DictReader(edgetsv,delimiter='\t')
        for d in dReader: 
            #d2 = {k.replace("biolink:","").lower():v for (k,v) in d.items()}
            yield d