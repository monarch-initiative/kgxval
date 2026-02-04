import os
from pathlib import Path
from typing import Iterable, Optional
from utils import TSVDictGen, JSONLDictGen
from bmt import Toolkit
from bmt.utils import parse_name

def findNodeFile(ingest_dir, find_normalized=True) -> Optional[str]:
    for (root,_,files) in os.walk(ingest_dir):
        for filename in files:
            if(not find_normalized):
                if(filename.endswith("nodes.jsonl") and not filename.endswith("normalized_nodes.jsonl")):
                    return os.path.join(root,filename)
            if(find_normalized):
                if(filename.endswith("normalized_nodes.jsonl")):
                    return os.path.join(root,filename)

def findEdgeFile(ingest_dir, find_normalized=True) -> Optional[str]:
    for (root,_,files) in os.walk(ingest_dir):
        for filename in files:
            if(not find_normalized):
                if(filename.endswith("edges.jsonl") and not filename.endswith("normalized_edges.jsonl")):
                    return os.path.join(root,filename)
            if(find_normalized):
                if(filename.endswith("normalized_edges.jsonl")):
                    return os.path.join(root,filename)

def expandCategories(cats:tuple[str,...]) -> set[str]:
    tk = Toolkit()
    s = set[str]()
    for cat in cats:
        s.update(tk.get_ancestors(cat))
    return s


class Ingest:
    def __init__(self,ingest_name:str,node_path:Path,edge_path:Path,norm_status:str=""):
        self.ingest_name=ingest_name
        self.node_path:Path=node_path
        self.edge_path:Path=edge_path
        self.norm_status:str=norm_status
        if(node_path.suffix.lower() in [".tsv",".csv"]): self.ingest_gen = TSVDictGen
        elif(node_path.suffix.lower() in [".json",".jsonl"]): self.ingest_gen = JSONLDictGen

        self.node_to_category: Optional[dict[str, tuple[str, ...]]] = None

    def iter_nodes(self) -> Iterable[dict]:
        for node_dict in self.ingest_gen(self.node_path):
            yield node_dict

    def iter_edges(self) -> Iterable[dict]:
        for edge_dict in self.ingest_gen(self.edge_path):
            yield edge_dict

    def _make_node_to_category_dict(self) -> dict[str,tuple[str,...]]:
        node_to_category:dict[str,tuple[str,...]] = {}
        for row_dict in self.iter_nodes():
            node_id:str = row_dict["id"]
            node_cats:str|list[str] = row_dict["category"]

            if(type(node_cats)==str): node_cats = [node_cats]
            
            if(type(node_cats)!=list):raise ValueError(f"{node_cats} === TYPE OF NODE CAT {type(node_cats)}")
            
            node_to_category[node_id] = tuple(sorted([parse_name(x) for x in node_cats]))
        return node_to_category
    
    def _make_node_equiv_id_to_id(self) -> dict[str,str]:
        node_to_node:dict[str,str] = {}
        for row_dict in self.iter_nodes():
            node_id:str = row_dict["id"]
            node_equivs:list[str] = row_dict["category"]
            for eq in node_equivs: node_to_node[eq]=node_id
        return node_to_node

    def get_node_to_category_dict(self) -> dict[str,tuple[str,...]]:
        if(self.node_to_category==None):
            self.node_to_category = self._make_node_to_category_dict()
        return self.node_to_category 
    
    def get_node_id_category(self,node_id):
        node_to_cat = self.get_node_to_category_dict()
        if(node_id not in node_to_cat):
            raise ValueError(f"{self.ingest_name}/{self.norm_status} === {node_id} could not be found in {self.node_path}")
        return node_to_cat[node_id]
    
def makeIngestObjsFromTopLevelDir(top_lvl_dir_path) -> list[Ingest]:
    def makeNotNormalizedIngest(source_name:str,source_dir:str) -> list[Ingest]:
        unnorm_node_path = findNodeFile(source_dir,find_normalized=False)
        unnorm_edge_path = findEdgeFile(source_dir,find_normalized=False)
        if(unnorm_node_path!=None and unnorm_edge_path!=None): 
            return [Ingest(source_name,Path(unnorm_node_path),Path(unnorm_edge_path),"not_normalized")]
        else:
            return []
    def makeNormalizedIngest(source_name:str,source_dir:str) -> list[Ingest]:
        norm_node_path = findNodeFile(source_dir,find_normalized=True)
        norm_edge_path = findEdgeFile(source_dir,find_normalized=True)
        if(norm_node_path!=None and norm_edge_path!=None): 
            return [Ingest(source_name,Path(norm_node_path),Path(norm_edge_path),"normalized")]
        else:
            return []
    ingest_list:list[Ingest] = []
    for subdir in os.listdir(top_lvl_dir_path):
        source_dir = os.path.join(top_lvl_dir_path,subdir)
        source_name = subdir
        ingest_list += makeNotNormalizedIngest(source_name,source_dir)
        ingest_list += makeNormalizedIngest(source_name,source_dir)
    return ingest_list
