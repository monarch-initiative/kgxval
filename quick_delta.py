

import os
from typing import Optional

from Ingest import makeIngestObjsFromTopLevelDir, Ingest
#import Ingest


if(__name__=="__main__"):
    from dotenv import load_dotenv
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
#    print(ingest_dir)
    unnorm:Optional[Ingest] = None
    normed:Optional[Ingest] = None
    for ingest_obj in makeIngestObjsFromTopLevelDir(ingest_dir):
        if(ingest_obj.ingest_name=="hpoa"):
            if(ingest_obj.norm_status=="normalized"):normed=ingest_obj # type: ignore
            else:unnorm = ingest_obj # type: ignore
    
    if(normed==None or unnorm==None):raise ValueError
    print(normed.node_path)

    unnorm_nodes = unnorm.get_node_to_category_dict()
    normed_nodes = normed.get_node_to_category_dict()

    normed_equiv_ids_to_id = normed._make_node_equiv_id_to_id()

    for node_id in unnorm_nodes:
        normed_node_id = normed_equiv_ids_to_id[node_id]
        unnorm_cats = unnorm_nodes[node_id]
        normed_cats = normed_nodes[normed_node_id]
        if(("phenotypic feature" in unnorm_cats) and ("disease" not in unnorm_cats) and ("disease" in normed_cats)):
            print(node_id)



