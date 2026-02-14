import csv
import json
from pathlib import Path
from typing import Iterable, Optional


def JSONLDictGen(file_loc: Optional[Path],attach_original_json:bool=False) -> Iterable[dict]:
    if(file_loc is None):
        return
    with open(file_loc) as edgejsonl:
        for row in edgejsonl: 
            d = json.loads(row)
            if(attach_original_json):d["original_json"] = row
            yield d

def TSVDictGen(file_loc: Optional[Path],_:bool=False) -> Iterable[dict]:
    if(file_loc is None):
        return
    with open(file_loc) as edgetsv:
        dReader = csv.DictReader(edgetsv,delimiter='\t')
        for d in dReader: 
            #d2 = {k.replace("biolink:","").lower():v for (k,v) in d.items()}
            yield d

if(__name__=="__main__"):
    print("Not printing anything for None")
    for x in JSONLDictGen(None):
        print(x)
