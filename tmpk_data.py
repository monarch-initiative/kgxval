
def cntPMIDsInTMKP():
    import time
    now = time.time()
    load_dotenv()
    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
    if ingest_dir == None:
        raise ValueError("Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    tmkp_ingest = Ingest(
                    "tmkg",
                    Path("/home/dkorn/Projects/KGXVal/kgxval/ignore/translator-ingests/data/tmkp/tmkp-2023-03-05/transform_6dadae40/normalization_2025sep1/merged_nodes.jsonl"),
                    Path("/home/dkorn/Projects/KGXVal/kgxval/ignore/translator-ingests/data/tmkp/tmkp-2023-03-05/transform_6dadae40/normalization_2025sep1/merged_edges.jsonl"),
                    "normalized",
                )
    uniq_pubs = set[str]()
    #print(ingest_dict["tmkp"])
    for i,edge_dict in enumerate(tmkp_ingest.iter_edges(validate=False)):
        #print(i)
        print(edge_dict)
        return
        if("publications" in edge_dict):
            uniq_pubs.update(edge_dict["publications"])
        if((i%100000)==0):print(f"i={i} --- {len(uniq_pubs)} --- {int(time.time() - now) } secs have passed")
    print(len(uniq_pubs))

def cntAbstInTMKP():
    import time
    now = time.time()
    from_abs_cnt = 0
    from_abs = set[str]()
    from_pub_cnt = 0
    from_pub = set[str]()

    from_abs_also_in_publist_cnt = 0
    from_pub_also_in_publist_cnt = 0
    from_abs_also_in_publist = set[str]()
    from_pub_also_in_publist = set[str]()
    inscrutable_cnt = 0
    inscrutable = set[str]()


#    ingest_dir = os.getenv("INGEST_TOP_LEVEL_DIR")
#    if ingest_dir == None:
#        raise ValueError("Can't find environment variable $INGEST_TOP_LEVEL_DIR")
    tmkp_ingest = Ingest(
                    "tmkg",
                    Path("/home/dkorn/Projects/KGXVal/kgxval/ignore/translator-ingests/data/tmkp/tmkp-2023-03-05/transform_6dadae40/normalization_2025sep1/merged_nodes.jsonl"),
                    Path("/home/dkorn/Projects/KGXVal/kgxval/ignore/translator-ingests/data/tmkp/tmkp-2023-03-05/transform_6dadae40/normalization_2025sep1/merged_edges.jsonl"),
                    "normalized",
                )
    uniq_xrefs = set[str]()
    for i,edge_dict in enumerate(tmkp_ingest.iter_edges(validate=False)):
        edge_dict_pubs:set[str] = set()
        edge_dict_abs:set[str] = set()
        for study in edge_dict["has_supporting_studies"]:
            for study_result in edge_dict["has_supporting_studies"][study]["has_study_results"]:
                text_type = study_result["supporting_text_section_type"]
                #ABSTRACT means it's a fulltext paper
                is_abstract = "abstract" in text_type or "title" in text_type
                #if("TITLE" in text_type):print("AIGHT GOOD")
                    
                xref_list = study_result["xref"]
                assert len(xref_list)==1, f"Weird xref --- {i}\n {edge_dict}"
                xref = xref_list[0]

                if(is_abstract):
                    from_abs_cnt+=1
                    from_abs.add(xref)
                    edge_dict_abs.add(xref)
                else:
                    from_pub_cnt+=1
                    from_pub.add(xref)
                    edge_dict_pubs.add(xref)
                uniq_xrefs.add(xref)
        for pub in edge_dict["publications"]:
            if(pub in edge_dict_pubs):
                   if(pub in from_abs_also_in_publist):
                       print(f"WACK --- {i} --- {pub} --- this pub is an abstract in one and a pub in this one\n{edge_dict}")
                       return
                   from_pub_also_in_publist.add(pub)
                   from_pub_also_in_publist_cnt+=1
                   
            elif(pub in edge_dict_abs):
                    if(pub in from_pub_also_in_publist):
                        print(f"WACK --- {i} --- {pub} --- this pub is an publication in one and an abstract in this one\n{edge_dict}")
                        return
                    from_abs_also_in_publist.add(pub)
                    from_abs_also_in_publist_cnt+=1
        if((i%100000)==0):print(f"i={i} --- {from_abs_cnt} --- {int(time.time() - now) } secs have passed")\
        

    for i,edge_dict in enumerate(tmkp_ingest.iter_edges(validate=False)):
        for pub in edge_dict["publications"]:
            if(pub not in from_pub_also_in_publist and pub not in from_abs_also_in_publist):
                inscrutable_cnt+=1
                inscrutable.add(pub)


    inter1:set[str] = from_abs.intersection(from_pub)
    inter2:set[str] = from_pub.intersection(from_abs)
    print(len(inter1))
    print(len(inter2))
    print("Unique-Xrefs-from_abs",len(from_abs))
    print("from_abs_cnt",from_abs_cnt)
    print("Unique-Xrefs-From_Full_Text_Pub",len(from_pub))
    print("from_pub_cnt",from_pub_cnt)
    print("unique-xref_cnt",len(uniq_xrefs))

    print("unique-from_pub_also_in_publist",len(from_pub_also_in_publist))
    print("from_pub_also_in_publist_cnt",from_pub_also_in_publist_cnt)
    print("unique-from_abs_also_in_publist",len(from_abs_also_in_publist))
    print("from_abs_also_in_publist_cnt",from_abs_also_in_publist_cnt)

    print("inscrutable_cnt",inscrutable_cnt)
    print("unique_inscrutable_publist", len(inscrutable))    

    print(list(inscrutable)[0:100])

