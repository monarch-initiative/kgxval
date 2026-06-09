from datetime import datetime
import os

import pandas as pd
from kgxval.dir.Ingest import iter_all_edges, makeIngestObjsDict
from kgxval.dir.kgxval_types import INGEST_MAP
from collections import defaultdict
from tqdm import tqdm

from collections import defaultdict
from itertools import count

class NodeIDAndInfores:
    node_ids:set[int]
    inforeses:set[str]
    def __init__(self):
        self.node_ids = set[int]()
        self.inforeses = set[str]()
    def add_id_infores(self,node_id:int,infores:str):
        self.node_ids.add(node_id)
        self.inforeses.add(infores)
    def get_nodes_len(self) -> int:
        return len(self.node_ids)
    def get_infores_str(self) -> str:
        return ", ".join(sorted(self.inforeses))


#Currently bidirectional
def countBiolinkNumberOfOccurs(blink_class:str,ingest_map:INGEST_MAP,top_level_cat:bool=True):
    node_to_int = defaultdict(count().__next__)
    node_blink_set = defaultdict(set)
    def updateDicts(node_id:str,scat:str,ocat:str,pred:str,infores:str):
        node_key = node_to_int[node_id]
        node_blink_set[scat].add(node_key)
        node_ids_for_pred[scat][pred].add_id_infores(node_key,infores)
        node_ids_for_ocat[scat][ocat].add_id_infores(node_key,infores)
        node_ids_for_pred_plus_ocat[scat][pred][ocat].add_id_infores(node_key,infores)

    node_ids_for_pred:defaultdict[str,defaultdict[str,NodeIDAndInfores]] = defaultdict(lambda: defaultdict(NodeIDAndInfores))
    node_ids_for_ocat:defaultdict[str,defaultdict[str,NodeIDAndInfores]] = defaultdict(lambda: defaultdict(NodeIDAndInfores))
    node_ids_for_pred_plus_ocat:defaultdict[str,defaultdict[str,defaultdict[str,NodeIDAndInfores]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(NodeIDAndInfores)))
    for i,(edge,ingest) in tqdm(enumerate(iter_all_edges(ingest_map,"normalized"))):
        #if(i>5000000):break
        sub = edge["subject"]
        obj = edge["object"]
        pred= edge["predicate"]
        scats = ingest.get_node_id_category(sub)
        ocats = ingest.get_node_id_category(obj)
        if(not top_level_cat):raise ValueError("NOT IMPLEMENTED")
        scat = scats[0]
        ocat = ocats[0]
        if(blink_class==scat):
            updateDicts(sub,scat,ocat,pred,ingest.ingest_name)
        if(blink_class==ocat):
            updateDicts(obj,ocat,scat,pred,ingest.ingest_name)
    return node_ids_for_pred, node_ids_for_ocat, node_ids_for_pred_plus_ocat, node_blink_set

def makeDFSheet(blink:str,total_from_blink_class:int,column_var:str,node_dict:defaultdict[str,NodeIDAndInfores]):
    rows = []
    for key in node_dict:
        t: NodeIDAndInfores = node_dict[key]
        cnt = t.get_nodes_len()
        perc = f"{cnt/total_from_blink_class:.2f}"
        infores_str = t.get_infores_str()
        rows.append((blink,key,cnt,perc,infores_str))
    df = pd.DataFrame.from_records(rows,columns=["Root Class",column_var,"Count","Proportion","Infores"]).sort_values("Count",ascending=False)
    return df

def makePredOCatDFSheet(blink:str,total_from_blink_class:int,column_var1:str,column_var2:str,node_dict:defaultdict[str,defaultdict[str,NodeIDAndInfores]]):
    rows = []
    for key1 in node_dict:
        for key2 in node_dict[key1]:
            t: NodeIDAndInfores = node_dict[key1][key2]
            cnt = t.get_nodes_len()
            perc = f"{cnt/total_from_blink_class:.2f}"
            infores_str = t.get_infores_str()
            rows.append((blink,key1,key2,cnt,perc,infores_str))
    df = pd.DataFrame.from_records(rows,columns=["Root Class",column_var1,column_var2,"Count","Proportion","Infores"]).sort_values("Count",ascending=False)
    return df

def makeXLSXOutput(
        node_ids_for_pred:defaultdict[str,defaultdict[str,NodeIDAndInfores]],
        node_ids_for_ocat:defaultdict[str,defaultdict[str,NodeIDAndInfores]],
        node_ids_for_pred_plus_ocat:defaultdict[str,defaultdict[str,defaultdict[str,NodeIDAndInfores]]],
        node_blink_set:defaultdict[str,set[str]]):
    datestr = datetime.now().strftime("%b-%d-%y")  # ex. Feb-16-2026
    writer = pd.ExcelWriter(f"data/blink_pred_output/summary_{datestr}.xlsx") 
    
    for blink_class in node_ids_for_pred:
        blink_total:int = len(node_blink_set[blink_class])
        pred_obj = node_ids_for_pred[blink_class]
        ocat_obj = node_ids_for_ocat[blink_class]
        pred_ocat_obj = node_ids_for_pred_plus_ocat[blink_class]
        pred_df = makeDFSheet(blink_class,blink_total,"Predicate",pred_obj)
        pred_df.to_excel(
            writer, sheet_name=f"{blink_class}-Pred",index=False
        )

        ocat_df =  makeDFSheet(blink_class,blink_total,"OCat",ocat_obj)
        ocat_df.to_excel(
            writer, sheet_name=f"{blink_class}-OCat",index=False
        )

        pred_ocat_df = makePredOCatDFSheet(blink_class,blink_total,"Predicate","OCat",pred_ocat_obj)
        pred_ocat_df.to_excel(
            writer, sheet_name=f"{blink_class}-Pred-OCat",index=False
        )


    blink_cnt_rows = []
    for blink_class in node_blink_set:
        blink_cnt_rows.append([blink_class,len(node_blink_set[blink_class])])
    blink_cnt_df = pd.DataFrame.from_records(blink_cnt_rows,columns=["Biolink Class","Total Node Count"])
    blink_cnt_df.to_excel(
            writer, sheet_name=f"Total Node Counts",index=False
    )
    writer.close()
    """for x in sorted(node_ids_for_pred):
        print(blink,x,len(node_ids_for_pred[x]))
        for y in sorted(node_ids_for_pred_plus_ocat[x]):
            print(blink,x,"---",y,len(node_ids_for_pred_plus_ocat[x][y]))"""

if(__name__=="__main__"):
    from dotenv import load_dotenv
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    if ingest_dir == None:
        raise ValueError("Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)


    blink = "chemical entity"
    node_ids_for_pred, node_ids_for_ocat, node_ids_for_pred_plus_ocat, node_blink_set  = countBiolinkNumberOfOccurs(blink,ingest_dict)
    makeXLSXOutput(node_ids_for_pred, node_ids_for_ocat, node_ids_for_pred_plus_ocat, node_blink_set)
    
    
    """for x in sorted(node_ids_for_pred):
        print(blink,x,len(node_ids_for_pred[x]))
        for y in sorted(node_ids_for_pred_plus_ocat[x]):
            print(blink,x,"---",y,len(node_ids_for_pred_plus_ocat[x][y]))""" 