import functools
from pathlib import Path
from typing import Union
from Ingest import Ingest, makeIngestObjsDict
from pydantic import BaseModel
from bmt import Toolkit
from linkml_runtime.linkml_model.meta import NCName

class PREFIX_ERR(BaseModel,frozen=True):
    source:str
    norm_status:str
    prefix:str
    cat:str

@functools.cache
def _getIDPrefixDict() -> dict[str,set[str]]:
    tk = Toolkit()

    class_to_id_prefixes = {}
    for class_name in tk.get_all_classes():
        el = tk.get_element(class_name)
        if(el==None):continue
        prefixes = el.id_prefixes
        if(prefixes is NCName or prefixes is str): prefixes = [prefixes]

        if(prefixes is not None and len(prefixes)>0):
            class_to_id_prefixes[class_name] = set(prefixes)
    return class_to_id_prefixes

def _printError(err_str:str, fail_on_invalid:bool):
    """This is called when there is a syntax error in a node jsonl dict.
    You can immediately stop"""
    if(fail_on_invalid): raise ValueError(err_str)
    else: 
        return
        print(err_str)

def getNodeStructuralErrors(ingest,fail_on_invalid:bool) -> list[PREFIX_ERR]:
    errors:list[PREFIX_ERR] = list()
    for node_dict in ingest.iter_nodes():
        if(":" not in node_dict["id"]): 
            _printError(f"Invalid Node ID found in {ingest.node_path.name} --- {node_dict["id"]} --- {node_dict}",
                    fail_on_invalid)
            errors.append(PREFIX_ERR(prefix=node_dict["id"],cat="BAD NODE ID",source=ingest.ingest_name,norm_status=ingest.norm_status))
        if("category" not in node_dict):
            _printError(f"Invalid Node ID found in {ingest.node_path.name} --- {node_dict["id"]} --- {node_dict}",
                        fail_on_invalid)
            errors.append(PREFIX_ERR(prefix=node_dict["id"],cat="NODE DOESN'T HAVE CATEGORY",source=ingest.ingest_name,norm_status=ingest.norm_status))
    return errors

def getUniqueNodePrefixCats(ingest:Ingest) -> set[tuple[str,str]]:
    prefix_cat_set:set[tuple[str,str]] = set()
    for node_dict in ingest.iter_nodes():
        if(":" not in node_dict["id"]): continue
        if("category" not in node_dict): continue
        id_prefix:str = node_dict["id"].split(":")[0].lower()
        node_cats:tuple[str,...] = ingest.get_node_id_category(node_dict["id"])
        for node_cat in node_cats:
            prefix_cat_tup:tuple[str,str] = (id_prefix,node_cat)
            prefix_cat_set.add(prefix_cat_tup)
    return prefix_cat_set

def _checkValidPrefixForClass(id_prefix:str ,blink_class:str):
    blink_class_to_idprefix:dict[str,set[str]] = _getIDPrefixDict()
    if(blink_class not in blink_class_to_idprefix): return True #No range constraint to violate
    elif(len(blink_class_to_idprefix[blink_class])==0): return True #No range constraint to violate
    else:
        valid_prefixes:set[str] = blink_class_to_idprefix[blink_class]
        return id_prefix in valid_prefixes


def validateNodePrefixesForIngest(ingest:Ingest,fail_on_invalid:bool=False) -> list[PREFIX_ERR]:
    errors:list[PREFIX_ERR] = list()
    errors+= getNodeStructuralErrors(ingest,fail_on_invalid)

    for id_prefix,node_cat in sorted(getUniqueNodePrefixCats(ingest)):
        if(not _checkValidPrefixForClass(id_prefix,node_cat)):
            errors.append(PREFIX_ERR(prefix=id_prefix,cat=node_cat,source=ingest.ingest_name,norm_status=ingest.norm_status))
    return errors

def writeErrorsToFile(error_dict : dict[tuple[str,str],set[str]],output_path:Path):
    import csv
    with open(output_path,'w') as f:
        writer = csv.writer(f)
        writer.writerow(["INVALID_ID_PREFIX","BIOLINK_CLASS","BIOLINK_URL","SOURCES_APPEARS_IN"])
        for (id_prefix,category),sources in error_dict.items():
            blink_url = f"https://biolink.github.io/biolink-model/{category.split(":")[1]}/#valid-id-prefixes"
            writer.writerow([id_prefix,category,blink_url,', '.join(sorted(sources))])

def main():
    from dotenv import load_dotenv
    import os
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)
    for source_name in ingest_dict:
        if("not_normalized" in ingest_dict[source_name]):
            l = validateNodePrefixesForIngest(ingest_dict[source_name]["not_normalized"])
            print(l)

if(__name__=="__main__"):
    main()