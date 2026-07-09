from datetime import datetime
import os
from typing import Iterable

import pandas as pd
from kgxval.dir.KGXSummarizer import KGXSummarizer
from kgxval.utils.format_xlsx import formatXlsx
from kgxval.dir.Ingest import Ingest, iter_all_edges, makeIngestObjsDict
from kgxval.dir.kgxval_types import INGEST_MAP
from collections import defaultdict
from tqdm import tqdm

from collections import defaultdict
from itertools import count

class NodeIDsOnly:
    node_ids:set[int]
    def __init__(self):
        self.node_ids = set()
    def add_id(self,node_id:int):
        self.node_ids.add(node_id)
    def get_nodes_len(self) -> int:
        return len(self.node_ids)

class NodeIDAndInfores:
    node_ids:set[int]
    inforeses:set[str]
    node_ids_by_infores:defaultdict[str,set[int]]
    def __init__(self):
        self.node_ids = set[int]()
        self.inforeses = set[str]()
        self.node_ids_by_infores = defaultdict(set)
    def add_id_infores(self,node_id:int,infores:str):
        self.node_ids.add(node_id)
        self.inforeses.add(infores)
        self.node_ids_by_infores[infores].add(node_id)

    def get_nodes_len(self) -> int:
        return len(self.node_ids)
    
    def get_infores_str(self) -> str:
        l = []
        for infores in self.inforeses:
            infores_cnt = len(self.node_ids_by_infores[infores])
            l.append((infores_cnt,infores))
        s = ", ".join([f"{info} ({info_cnt})" for (info_cnt,info) in sorted(l,reverse=True)])
        return s
        #return ", ".join(sorted(self.inforeses))

class CatalogPredSink:
    sink_dict: defaultdict[str,NodeIDAndInfores]
    pred_dict: defaultdict[str,NodeIDsOnly]
    sink_pred_dict: defaultdict[str,defaultdict[str,NodeIDsOnly]] 
    def __init__(self):
        self.sink_dict = defaultdict(NodeIDAndInfores)
        self.pred_dict = defaultdict(NodeIDsOnly)
        self.sink_pred_dict = defaultdict(lambda: defaultdict(NodeIDsOnly))

    def update(self,node_id:int,sink_cat:str,pred:str,infores:str):
        self.sink_dict[sink_cat].add_id_infores(node_id,infores)
        self.pred_dict[pred].add_id(node_id)
        self.sink_pred_dict[sink_cat][pred].add_id(node_id)

    def makePredStringForSink(self,sink_key) -> str:
        l = []
        for pred in self.sink_pred_dict[sink_key]:
            pred_cnt = self.sink_pred_dict[sink_key][pred].get_nodes_len()
            l.append((pred_cnt,pred))
        s = ", ".join([f"{pred} ({pred_cnt})" for (pred_cnt,pred) in sorted(l,reverse=True)])
        return s
    
    def makeSinkDF(self,source_name,tot) -> list[tuple]:
        rows = []
        for sink in self.sink_dict:
            sink_cnt = self.sink_dict[sink].get_nodes_len()
            perc = sink_cnt/tot
            preds = self.makePredStringForSink(sink)
            infores = self.sink_dict[sink].get_infores_str()
            rows.append((source_name,sink,sink_cnt,perc,preds,infores))
        return rows

#Currently bidirectional
def countBiolinkNumberOfOccurs(ingest_map:INGEST_MAP,
                               top_level_cat:bool=True,
                               rollup_cats:Iterable[str]=[],
                               ignore_list:list=[]):
    node_to_int:defaultdict[str,int] = defaultdict(count().__next__)
    node_blink_set:defaultdict[str,set[int]] = defaultdict(set)
    source_to_catalog = defaultdict(CatalogPredSink)
    kgxSumm_d:dict[Ingest,KGXSummarizer] = {}
    for i,(edge,ingest) in tqdm(enumerate(iter_all_edges(ingest_map,"normalized")),total=84130086):
        if(ingest.ingest_name in ignore_list):continue
        if(ingest not in kgxSumm_d):
            kgxSumm_d[ingest] = KGXSummarizer.initWithIngestObj(ingest,rollup_cats)
        ingest = kgxSumm_d[ingest]
        #good_ingest = ["ubergraph","geneticskp","hpoa","semmeddb","icees","cohd"]
        #if(ingest.ingest_name not in good_ingest):continue
        #if(i>100000):break
        #if(i>5000000):break
        sub:int = node_to_int[edge["subject"]]
        obj:int = node_to_int[edge["object"]]
        pred= edge["predicate"]
        scats = ingest.get_node_id_category(edge["subject"])
        ocats = ingest.get_node_id_category(edge["object"])
        if(not top_level_cat):raise ValueError("NOT IMPLEMENTED")
        scat = ingest._getBestCat(scats)
        ocat = ingest._getBestCat(ocats)
        infores = ingest.ingest_name
        node_blink_set[scat].add(sub)
        node_blink_set[ocat].add(obj)
        if(True):
            source_to_catalog[scat].update(sub,ocat,pred,infores)
        bijective = True
        if(bijective):
            source_to_catalog[ocat].update(obj,scat,pred,infores)
    return source_to_catalog, node_blink_set

def makeXLSXOutput(
        source_to_catalog:defaultdict[str,CatalogPredSink],
        node_blink_set:defaultdict[str,set[int]],
        rollup_source_to_catalog:defaultdict[str,CatalogPredSink],
        rollup_node_blink_set:defaultdict[str,set[int]],
        xlsx_file:str
        ):
    writer = pd.ExcelWriter(xlsx_file,engine="openpyxl") 
    rows = []
    for blink_class in source_to_catalog:
        blink_total:int = len(node_blink_set[blink_class])
        catalog = source_to_catalog[blink_class]
        rows+=catalog.makeSinkDF(blink_class,blink_total)

    source_sink_df = pd.DataFrame.from_records(rows,
        columns=["Node1","Node2","Total Unique Node1's","Percent","Predicates","Inforeses"])    
    source_sink_df.to_excel(
        writer, sheet_name="Node->Node",index=False
    )

    blink_cnt_rows = []
    for blink_class in node_blink_set:
        blink_cnt_rows.append([blink_class,len(node_blink_set[blink_class])])
    blink_cnt_df = pd.DataFrame.from_records(blink_cnt_rows,columns=["Biolink Class","Total Node Count"])
    blink_cnt_df.to_excel(
            writer, sheet_name=f"Total Node Counts",index=False
    )
    del source_to_catalog
    del node_blink_set
#ROLLUP
    rows = []
    for blink_class in rollup_source_to_catalog:
        blink_total:int = len(rollup_node_blink_set[blink_class])
        catalog = rollup_source_to_catalog[blink_class]
        rows+=catalog.makeSinkDF(blink_class,blink_total)

    rollup_source_sink_df = pd.DataFrame.from_records(rows,
        columns=["Node1","Node2","Total Unique Node1's","Percent","Predicates","Inforeses"])    
    rollup_source_sink_df.to_excel(
        writer, sheet_name="ROLLUP|Node->Node",index=False
    )

    blink_cnt_rows = []
    for blink_class in rollup_node_blink_set:
        blink_cnt_rows.append([blink_class,len(rollup_node_blink_set[blink_class])])
    rollup_blink_cnt_df = pd.DataFrame.from_records(blink_cnt_rows,columns=["Biolink Class","Total Node Count"])
    rollup_blink_cnt_df.to_excel(
            writer, sheet_name=f"ROLLUP|Total Node Counts",index=False
    )


    
    writer.close()
    #formatXlsx(xlsx_file,formatted_xlsx_file)
    formatXlsx(xlsx_file,xlsx_file)
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
    datestr = datetime.now().strftime("%b-%d-%y")  # ex. Feb-16-2026
    source_to_catalog, node_blink_set  = countBiolinkNumberOfOccurs(ingest_dict,True,[],["ubergraph"])
    rollup_source_to_catalog, rollup_node_blink_set  = countBiolinkNumberOfOccurs(ingest_dict,True,[
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ],["ubergraph"])

    
    xlsx_file = f"data/blink_pred_output/biolink_class_level_summary_{datestr}.xlsx"
    makeXLSXOutput(source_to_catalog, node_blink_set,
                   rollup_source_to_catalog, rollup_node_blink_set,
                   xlsx_file)
    
    
    source_to_catalog, node_blink_set  = countBiolinkNumberOfOccurs(ingest_dict,True,[],["semmeddb","ubergraph"])
    rollup_source_to_catalog, rollup_node_blink_set  = countBiolinkNumberOfOccurs(ingest_dict,True,[
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ],["semmeddb","ubergraph"])

    xlsx_file = f"data/blink_pred_output/NO_SEMMED_biolink_class_level_summary_{datestr}.xlsx"
    makeXLSXOutput(source_to_catalog, node_blink_set,
                   rollup_source_to_catalog, rollup_node_blink_set,
                   xlsx_file)
    
    source_to_catalog, node_blink_set  = countBiolinkNumberOfOccurs(ingest_dict,True,[],["semmeddb","tmkp","ubergraph"])
    rollup_source_to_catalog, rollup_node_blink_set  = countBiolinkNumberOfOccurs(ingest_dict,True,[
        "gene or gene product",
        "disease or phenotypic feature",
        "chemical entity",
    ],["semmeddb","tmkp","ubergraph"])

    xlsx_file = f"data/blink_pred_output/NO_SEMMED_OR_TMKP_biolink_class_level_summary_{datestr}.xlsx"
    makeXLSXOutput(source_to_catalog, node_blink_set,
                   rollup_source_to_catalog, rollup_node_blink_set,
                   xlsx_file)