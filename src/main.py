

import os
from pathlib import Path
from typing import Optional

from Ingest import findEdgeFile, findNodeFile, Ingest


def makeIngestObjFromPath(data_dir_path):
    sources = os.listdir(data_dir_path)
    #normed_sources = os.listdir(normed_dir_path)
    def makeNotNormalizedIngest(source_name:str,source_dir:str) -> Optional[Ingest]:
        unnorm_node_path = findNodeFile(source_dir,find_normalized=False)
        unnorm_edge_path = findEdgeFile(source_dir,find_normalized=False)
        if(unnorm_node_path!=None and unnorm_edge_path!=None): 
            return Ingest(source_name,Path(unnorm_node_path),Path(unnorm_edge_path))
        else:
            return None
    def makeNormalizedIngest(source_name:str,source_dir:str) -> Optional[Ingest]:
        norm_node_path = findNodeFile(source_dir,find_normalized=True)
        norm_edge_path = findEdgeFile(source_dir,find_normalized=True)
        if(norm_node_path!=None and norm_edge_path!=None): 
            return Ingest(source_name,Path(norm_node_path),Path(norm_edge_path))
        else:
            return None
    for source_name in sources:
        source_dir = os.path.join(data_dir_path,source_name)
#        unnorm_node_path = findNodeFile(source_dir,find_normalized=False)
#        unnorm_edge_path = findEdgeFile(source_dir,find_normalized=False)

        unnorm_ingest = makeNotNormalizedIngest(source_name,source_dir)
        normalized_ingest = makeNormalizedIngest(source_name,source_dir)
        ingest_list.append(source_obj)
    return ingest_list


if(__name__=="__main__"):
    for ingest_obj in makeIngestObjFromPath():
        if(ingest_obj.isComplete()):
            pass
            #print(ingest_obj)
        else: print(f"==={ingest_obj.source_name} is incomplete===")