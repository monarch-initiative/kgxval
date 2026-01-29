import os
from pathlib import Path
from typing import Iterable, Optional
from .utils import TSVDictGen, JSONLDictGen


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

class Ingest:
    def __init__(self,ingest_name:str,node_path:Path,edge_path:Path):
        self.ingest_name=ingest_name
        self.node_path:Path=node_path
        self.edge_path:Path=edge_path
        if(node_path.suffix.lower() in [".tsv",".csv"]): self.ingest_gen = TSVDictGen
        elif(node_path.suffix.lower() in [".json",".jsonl"]): self.ingest_gen = JSONLDictGen

        self.node_to_category:dict[str,tuple[str,...]]

    def iter_edges(self) -> Iterable[dict]:
        for edge_dict in self.ingest_gen(self.edge_path):
            yield edge_dict

    def _make_node_to_category_dict(self):
        self.node_to_category:dict[str,tuple[str,...]] = {}
        for row_dict in self.ingest_gen(self.node_path):
            node_id:str = row_dict["id"]
            node_cat:str|list[str] = row_dict["category"]

            if(type(node_cat)==str): node_cat = [node_cat]
            if(type(node_cat)!=list[str]):raise ValueError
            
            self.node_to_category[node_id] = tuple(sorted(node_cat))

    def get_node_to_category_dict(self) -> dict[str,tuple[str,...]]:
        if(self.node_to_category==None):
            self._make_node_to_category_dict()
        return self.node_to_category 
    
    def get_node_id_category(self,node_id):
        node_to_cat = self.get_node_to_category_dict()
        return node_to_cat[node_id]