
from collections import defaultdict
import csv
import functools
from typing import Iterable, Optional
from Ingest import Ingest, expandCategories
from pydantic import BaseModel
from bmt import Toolkit
from linkml_runtime.linkml_model.meta import SlotDefinition, ClassDefinition, Element

class SOPC(BaseModel, frozen=True):
    """This class represents the most core information for validating an edge predicate and categories.
    We only need to know what the subject categories were, what the object categories were, the
    predicate, and all of the edge categories."""
    node_sub_cats:tuple[str,...]
    node_obj_cats:tuple[str,...]
    predicate:str 
    edge_cats:tuple[str,...] #The categories/slots assigned to a biolink relationship - might be empty

    def to_csv_list(self):
        return ["|".join(self.node_sub_cats),
                "|".join(self.node_obj_cats),
                self.predicate,
                "|".join(self.edge_cats)]

def _getUniqueSOPCsForIngest(ingest:Ingest) -> Iterable[tuple[SOPC,int]]:
    seen_sopcs = defaultdict(int)
    for edge_dict in ingest.iter_edges():
        subject_node_id = edge_dict["subject"]
        object_node_id = edge_dict["object"]
        predicate = edge_dict["predicate"]
        edge_cats = tuple(sorted(edge_dict["category"]))

        node_sub_cats = ingest.get_node_id_category(subject_node_id)
        node_obj_cats = ingest.get_node_id_category(object_node_id)
        edge_sopc = SOPC(node_sub_cats=node_sub_cats,
                   node_obj_cats=node_obj_cats,
                   predicate=predicate,
                   edge_cats=edge_cats)
        seen_sopcs[edge_sopc]+=1
    for (sopc,cnt) in seen_sopcs.items():
        yield sopc,cnt

def writeSOPCsToFile(ingest:Ingest,outpath:str):
    with open(outpath,'w') as f:
        writer = csv.writer(f)
        writer.writerow(["INGEST_NAME","NORMALIZED","NODE_SUBJECTS","NODE_OBJECTS","PREDICATE","EDGE_CATEGORIES","COUNT"])
        for sopc, cnt in _getUniqueSOPCsForIngest(ingest):
            writer.writerow([ingest.ingest_name, ingest.norm_status] + sopc.to_csv_list() + [cnt])

class SPOCValidationError(BaseModel):
    pred:str
    error:str
    valid_cats:list[str]
    actual_cats:tuple[str,...]
    ingest_name:str
    normalized:str
    def to_csv_list(self):
        return [self.ingest_name,
                self.normalized,
                self.pred,
                self.error,
                "|".join(sorted(self.valid_cats)),
                "|".join(sorted(self.actual_cats))]

def _checkValidBiolink(pred:str,ingest_name:str,normalized:str) -> list[SPOCValidationError]:
    tk = Toolkit()
    if(tk.get_element(pred)==None):
        return [SPOCValidationError(pred=pred,
                                error="BAD BIOLINK",
                                valid_cats=[],
                                actual_cats=tuple(),
                                ingest_name=ingest_name,
                                normalized=normalized)]
    return []
        
def _checkSubForPred(pred:str,node_sub_cats:tuple[str,...],ingest_name:str,normalized:str) -> list[SPOCValidationError]:
    @functools.cache
    def getSubRange(pred:str) -> Optional[str]:
        el = tk.get_element(pred)
        if(type(el)==SlotDefinition): 
            if el:
                if el.domain: return el.domain
        elif(type(el)==ClassDefinition): 
            slot_dict:dict[str,Any] = el.slot_usage # type: ignore
            if("subject" in slot_dict and slot_dict["subject"].range!=None):
                return slot_dict["subject"].range
        else: raise ValueError(f"Checking for subject of {pred} --- getting an element type of {type(el)}")
        return getSubRange(el.is_a)
    
    tk = Toolkit()
    if(tk.get_element(pred)==None): return []
    pred_sub_range = getSubRange(pred)
    if(pred_sub_range==None): 
        print(f"{pred} doesn't have a subject range")
        return []
    all_valid_pred_subs = set(tk.get_descendants(name=pred_sub_range))
    all_valid_node_subs = expandCategories(node_sub_cats)
    inter = all_valid_pred_subs.intersection(all_valid_node_subs)
    if(len(inter)==0): return [SPOCValidationError(pred=pred,
                        error="BAD SUBJECT",
                        valid_cats=sorted(tk.get_descendants(name=pred_sub_range)),
                        actual_cats=node_sub_cats,
                        ingest_name=ingest_name,
                        normalized=normalized)]
    else: return []


def _checkObjForPred(pred:str,node_obj_cats:tuple[str,...],ingest_name:str,normalized:str):
    @functools.cache
    def getObjRange(pred:str) -> Optional[str]:
        el = tk.get_element(pred)
        if(type(el)==SlotDefinition): 
            if el:
                if el.range: return el.range
        elif(type(el)==ClassDefinition): 
            slot_dict:dict[str,Any] = el.slot_usage # type: ignore
            if("object" in slot_dict and slot_dict["object"].range!=None):
                return slot_dict["object"].range
        else: raise ValueError #Throw error if the element isn't a Slot or Class
        return getObjRange(el.is_a)

    
    if(pred=="biolink:affects"):
        print("HI")
    tk = Toolkit()
    if(tk.get_element(pred)==None): return []
    pred_obj_range = getObjRange(pred)
    if(pred_obj_range==None): 
        print(f"{pred} doesn't have a object range")
        return []
    all_valid_pred_objs = set(tk.get_descendants(name=pred_obj_range))
    all_valid_node_objs = expandCategories(node_obj_cats)
    inter = all_valid_pred_objs.intersection(all_valid_node_objs)
    if(len(inter)==0): return [SPOCValidationError(pred=pred,
                        error="BAD OBJECT",
                        valid_cats=sorted(tk.get_descendants(name=pred_obj_range)),
                        actual_cats=node_obj_cats,
                        ingest_name=ingest_name,
                        normalized=normalized)]
    else: return []

def inspectSubObjErrorsForIngest(ingest:Ingest) -> list[SPOCValidationError]:
    error_list:list[SPOCValidationError] = []
    for sopc,_ in _getUniqueSOPCsForIngest(ingest):
        error_list+= _checkValidBiolink(sopc.predicate,ingest.ingest_name,ingest.norm_status)
        error_list+= _checkSubForPred(sopc.predicate,sopc.node_sub_cats,ingest.ingest_name,ingest.norm_status)
        error_list+= _checkObjForPred(sopc.predicate,sopc.node_obj_cats,ingest.ingest_name,ingest.norm_status)
        for edge_cat in sopc.edge_cats:
            error_list+= _checkValidBiolink(edge_cat,ingest.ingest_name,ingest.norm_status)
            error_list+= _checkSubForPred(edge_cat,sopc.node_sub_cats,ingest.ingest_name,ingest.norm_status)
            error_list+= _checkObjForPred(edge_cat,sopc.node_obj_cats,ingest.ingest_name,ingest.norm_status)
    return error_list

def validationErrorsToFile(spoc_errors:list[SPOCValidationError],outfile:str):
    with open(outfile,'w') as f:
        writer = csv.writer(f)
        writer.writerow(["INGEST_NAME","NORMALIZED","PREDICATE","ERROR","VALID_CATEGORIES","ACTUAL_CATEGORIES"])
        for spoc_error in spoc_errors:
            writer.writerow(spoc_error.to_csv_list())