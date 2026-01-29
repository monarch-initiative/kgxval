
from collections import defaultdict
import csv
from typing import Iterable, Optional
from src.Ingest import Ingest
from pydantic import BaseModel
from bmt import Toolkit
from linkml_runtime.linkml_model.meta import SlotDefinition, ClassDefinition, Element

class SOPC(BaseModel):
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
    seen_sopcs = defaultdict()
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
        writer.writerow(["NODE_SUBJECTS","NODE_OBJECTS","PREDICATE","EDGE_CATEGORIES","COUNT"])
        for sopc, cnt in _getUniqueSOPCsForIngest(ingest):
            writer.writerow(sopc.to_csv_list() + [cnt])

class _ValidationError(BaseModel):
    pred:str
    error:str
    valid_cats:list[str]
    actual_cats:tuple[str,...]

def _checkValidBiolink(pred:str) -> list[_ValidationError]:
    tk = Toolkit()
    if(tk.get_element(pred)==None):
        return [_ValidationError(pred=pred,
                                error="BAD BIOLINK",
                                valid_cats=[],
                                actual_cats=tuple())]
    return []
        
def _checkSubForPred(pred:str,node_sub_cats:tuple[str,...]) -> list[_ValidationError]:
    def getSubRange(el:Element) -> Optional[str]:
        if(type(el)==SlotDefinition): 
            if el:
                if el.domain: return el.domain
        if(type(el)==ClassDefinition): 
            slot_dict:dict[str,Any] = el.slot_usage # type: ignore
            if("subject" in slot_dict and slot_dict["subject"].range!=None):
                return slot_dict["subject"].range
        return None
    
    tk = Toolkit()
    el = tk.get_element(pred)
    if(el==None):raise ValueError
    pred_sub_range = getSubRange(el)
    all_valid_pred_subs = set(tk.get_descendants(name=pred_sub_range))
    inter = all_valid_pred_subs.intersection(node_sub_cats)
    if(len(inter)==0): return [_ValidationError(pred=pred,
                        error="BAD SUBJECT",
                        valid_cats=sorted(tk.get_descendants(name=pred_sub_range)),
                        actual_cats=node_sub_cats)]
    else: return []


def _checkObjForPred(pred:str,node_obj_cats:tuple[str,...]):
    def getObjRange(el:Element) -> Optional[str]:
        if(type(el)==SlotDefinition): 
            if el:
                if el.range: return el.range
        if(type(el)==ClassDefinition): 
            slot_dict:dict[str,Any] = el.slot_usage # type: ignore
            if("object" in slot_dict and slot_dict["object"].range!=None):
                return slot_dict["object"].range
        return None
    
    tk = Toolkit()
    el = tk.get_element(pred)
    if(el==None):raise ValueError
    pred_obj_range = getObjRange(el)
    all_valid_pred_objs = set(tk.get_descendants(name=pred_obj_range))
    inter = all_valid_pred_objs.intersection(node_obj_cats)
    if(len(inter)==0): return [_ValidationError(pred=pred,
                        error="BAD OBJECT",
                        valid_cats=sorted(tk.get_descendants(name=pred_obj_range)),
                        actual_cats=node_obj_cats)]
    else: return []

def inspectSubObjErrorsForIngest(ingest:Ingest) -> list[_ValidationError]:
    error_list:list[_ValidationError] = []
    for sopc,_ in _getUniqueSOPCsForIngest(ingest):
        error_list+= _checkValidBiolink(sopc.predicate)
        error_list+= _checkSubForPred(sopc.predicate,sopc.node_sub_cats)
        error_list+= _checkObjForPred(sopc.predicate,sopc.node_obj_cats)
        for edge_cat in sopc.edge_cats:
            error_list+= _checkValidBiolink(edge_cat)
            error_list+= _checkSubForPred(edge_cat,sopc.node_sub_cats)
            error_list+= _checkObjForPred(edge_cat,sopc.node_obj_cats)
    return error_list