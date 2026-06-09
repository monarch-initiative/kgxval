import csv
import json
import logging
from pathlib import Path
from typing import Any, Iterable, Optional

from kgxval.dir.kgxval_types import KGX_EDGE, KGX_NODE


def JSONLDictGen(
    file_loc: Optional[Path], attach_original_json: bool = False
) -> Iterable[KGX_NODE | KGX_EDGE]:
    if file_loc is None:
        return
    with open(file_loc) as edgejsonl:
        for row in edgejsonl:
            d: dict[str, Any] = json.loads(row)
            if type(d) != dict:
                logging.warning(f"{file_loc} has an incorrectly formatted row --- {d}")
                continue
            if attach_original_json:
                d["original_json"] = row
            yield d


def TSVDictGen(
    file_loc: Optional[Path], _: bool = False
) -> Iterable[KGX_NODE | KGX_EDGE]:
    if file_loc is None:
        return
    with open(file_loc) as edgetsv:
        dReader = csv.DictReader(edgetsv, delimiter="\t")
        for d in dReader:
            # d2 = {k.replace("biolink:","").lower():v for (k,v) in d.items()}
            yield d


# TODO: make this a test.
if __name__ == "__main__":
    print("Not printing anything for None")
    for x in JSONLDictGen(None):
        print(x)
