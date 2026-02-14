import functools
from pathlib import Path
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

def validateNodePrefixesForIngest(ingest:Ingest,fail_on_invalid=False) -> list[PREFIX_ERR]:
    def _printError(err_str:str, fail_on_invalid:bool):
        """This is called when there is a syntax error in a node jsonl dict.
        You can immediately stop"""
        if(fail_on_invalid): raise ValueError(err_str)
        else: 
            return
            print(err_str)

    errors:list[PREFIX_ERR] = list()
    def _appendError(err:PREFIX_ERR):
        if(err in errors): return
        errors.append(err)

    blink_class_to_idprefix:dict[str,set[str]] = _getIDPrefixDict()
    for node_dict in ingest.iter_nodes():
        if(":" not in node_dict["id"]): 
            _printError(f"Invalid Node ID found in {ingest.node_path.name} --- {node_dict["id"]} --- {node_dict}",
                        fail_on_invalid)
            _appendError(PREFIX_ERR(prefix=node_dict["id"],cat="BAD NODE ID",source=ingest.ingest_name,norm_status=ingest.norm_status))
            continue
        if("category" not in node_dict):
            _printError(f"Invalid Node ID found in {ingest.node_path.name} --- {node_dict["id"]} --- {node_dict}",
                        fail_on_invalid)
            _appendError(PREFIX_ERR(prefix=node_dict["id"],cat="NODE DOESN'T HAVE CATEGORY",source=ingest.ingest_name,norm_status=ingest.norm_status))
            continue

        id_prefix:str = node_dict["id"].split(":")[0].lower()
        node_cats:tuple[str,...] = ingest.get_node_id_category(node_dict["id"])

        def _checkValidPrefixForClass(id_prefix:str ,blink_class:str):
            id_prefix = id_prefix.lower()
            blink_class = blink_class.lower().replace("biolink:","")
            if(blink_class not in blink_class_to_idprefix): return True #No range constraint to violate
            elif(len(blink_class_to_idprefix[blink_class])==0): return True #No range constraint to violate
            else:
                valid_prefixes:set[str] = blink_class_to_idprefix[blink_class]
                return id_prefix in valid_prefixes

        #This says whether there is a valid mapping for prefix for ANY of the possible node categories assigned to the node.
        for cat in node_cats:
            if(not _checkValidPrefixForClass(id_prefix,cat)):
                _appendError(PREFIX_ERR(prefix=id_prefix,cat=cat,source=ingest.ingest_name,norm_status=ingest.norm_status))
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