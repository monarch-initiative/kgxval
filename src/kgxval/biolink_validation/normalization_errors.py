from collections import defaultdict
import csv
from tqdm import tqdm
from kgxval.dir.Ingest import Ingest
from kgxval.dir.kgxval_types import INGEST_MAP


def makeNormedToUnnormedDict(unnorm_ingest:Ingest, normed_ingest:Ingest) -> dict[str,set[str]]:
    all_unnorm_node_ids = set[str]()
    all_unnorm_node_ids_cleaned = set()
    d = {}
    for node in unnorm_ingest.iter_nodes():
        node_id = node['id']
        """
        node_id.replace(":0",":")
        node_id.replace(":0",":")
        node_id.replace(":0",":")
        node_id.replace(":0",":")
        node_id.replace(":0",":")
        node_id.replace(":0",":")
        node_id.replace(":0",":")"""
        all_unnorm_node_ids.add(node_id)
        all_unnorm_node_ids_cleaned.add(node_id.strip().upper())
        d[node_id.strip().upper()] = node_id
    
    normed_to_unnorm:dict[str,set] = {}
    for node in tqdm(normed_ingest.iter_nodes()):
        equiv_ids = node["equivalent_identifiers"]
        canon_id = node["id"]
        unnorm_ids = [d[x.strip().upper()] for x in equiv_ids if x.strip().upper() in all_unnorm_node_ids_cleaned]
        if(len(unnorm_ids)==0):
            print("NORM PATH",normed_ingest.node_path)
            print("UNNORM PATH",unnorm_ingest.node_path)
            raise ValueError(f"Cannot find any nodes matching {node["id"]} and {equiv_ids} in pre-normalization nodes.")
        normed_to_unnorm[canon_id] = set(unnorm_ids)
    return normed_to_unnorm


ID_TO_RES = defaultdict[tuple[str,tuple[str,...]],set[tuple[str,str]]]
def findNormalizationMismatch(unnorm_ingest:Ingest, normed_ingest:Ingest) -> tuple[ID_TO_RES,ID_TO_RES]:
    normed_to_unnorm = makeNormedToUnnormedDict(unnorm_ingest,normed_ingest)
    miss_matches:set[tuple[str,tuple[str,...]]] = set()
    miss_matches_examples:ID_TO_RES = defaultdict(set)

    correct_matches = set()
    correct_matches_examples:ID_TO_RES = defaultdict(set)
    for node in tqdm(normed_ingest.iter_nodes()):
        normed_id = node["id"]
        norm_cats = normed_ingest.get_node_id_category(normed_id)
        unnorm_ids = normed_to_unnorm[normed_id]
        #if(len(unnorm_ids)>1):
        #    raise ValueError()
        #    #TODO
        for unnorm_id in unnorm_ids:
    #        unnorm_id = unnorm_ids.pop()
            unnorm_cats = unnorm_ingest.get_node_id_category(unnorm_id)
            if(len(unnorm_cats)!=1):
                raise ValueError()
            unnorm_cat = unnorm_cats[0]
            inter_cats = set(unnorm_cats).intersection(norm_cats)
            tup = (unnorm_cat,norm_cats)
            if(len(inter_cats)==0):
    #            print(inter_cats,tup)
    #            exit()
                miss_matches.add(tup)
                miss_matches_examples[tup].add((unnorm_id,normed_id))
            else:
                correct_matches.add(tup)
                correct_matches_examples[tup].add((unnorm_id,normed_id))

    return miss_matches_examples,correct_matches_examples

def callNodeNorm(curies:list[str]) -> dict[str,str]:
    import requests
    req_d = {
     "curies": list(sorted(curies)),
     "conflate": True,
     "description": False,
     "drug_chemical_conflate": True
    }
    node_norm = "https://nodenormalization-sri.renci.org/1.5/get_normalized_nodes"
    r = requests.post(node_norm,json=req_d)
    node_norm_resp = r.json()
    idx_to_label = {}
    for key in node_norm_resp:
        idx = node_norm_resp[key]["id"]["identifier"]
        label = node_norm_resp[key]["id"].get("label","n/a")
        idx_to_label[idx] = label
        for idx_dict in node_norm_resp[key]["equivalent_identifiers"]:
            idx = idx_dict["identifier"]
            label = idx_dict.get("label","n/a")
            if(idx not in idx_to_label): idx_to_label[idx] = label
    return idx_to_label

def getNames(ids:list[tuple[str,str]]) -> list[str]:
    norm_ids = []
    for unnorm,normed in ids: 
        norm_ids.append(normed)
        norm_ids.append(unnorm)
    idx_to_label = callNodeNorm(norm_ids)
    return_strs = []
    for unnorm,normed in ids:
        s = f"{unnorm} ({idx_to_label[unnorm]})|{normed} ({idx_to_label[normed]})"
        return_strs.append(s)
    return return_strs

def main():
    pass

def find_normalization_errors(ingest_dict:INGEST_MAP, misses_csv_path:str, matches_csv_path:str,sample_cnt=50):
    def getNormUnnnorm(ingest_dict,key) -> tuple[Ingest,Ingest]:
        return (ingest_dict[key]["normalized"], ingest_dict[key]["not_normalized"])
    with open(matches_csv_path) as matches_csv, open(misses_csv_path) as misses_csv:
        match_out_writer = csv.writer(matches_csv)
        misses_out_writer = csv.writer(misses_csv)

        for infores in ingest_dict:
            (normed,unnorm) = getNormUnnnorm(ingest_dict,infores)
            misses,matches = findNormalizationMismatch(unnorm,normed)
            for unnorm_cat,normed_cats in matches.keys():
                id_list = matches[(unnorm_cat,normed_cats)]
                num_matches = len(id_list)
                normed_cat_str = '|'.join(sorted(normed_cats)) 
                match_out_writer.writerow([infores,num_matches,unnorm,normed_cat_str])
            for unnorm_cat,normed_cats in misses:
                id_list = misses[(unnorm_cat,normed_cats)]
                miss_cnt = len(id_list)
                normed_cat_str = '|'.join(sorted(normed_cats))
                example_list = getNames(sorted(id_list)[0:sample_cnt])
                misses_out_writer.writerow([infores,miss_cnt,unnorm_cat,normed_cat_str] + example_list)



if(__name__=="__main__"):
    import dotenv
    import os
    from kgxval.dir.Ingest import makeIngestObjsDict
    dotenv.load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    if ingest_dir == None:
        raise ValueError("Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    ingest_dict = makeIngestObjsDict(ingest_dir)
    miss_out_path = 'data/misses.csv'
    match_out_path = 'data/matches.csv'
    find_normalization_errors(ingest_dict,miss_out_path,match_out_path)