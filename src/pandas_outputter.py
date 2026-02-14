from typing import Final, Iterable
from Ingest import Ingest
from KGXSummarizer import KGXSummarizer, SPQOStats, orderQualifiersForMatt
from biolink_validation.check_kgx_blink_prefix import PREFIX_ERR, validateNodePrefixesForIngest
from biolink_validation.check_kgx_sub_obj_pred import SPOCValidationError, findSubObjErrorsForIngest
import pandas as pd

def getQualifiersFromDictList(kgx_summ_dicts:list[dict]) -> set[str]:
    quals = set()
    for d in kgx_summ_dicts:
        for key in d.keys():
            if(SPQOStats.testQualifier(key)): quals.add(key)
    return quals

def getSourceRolesFromDictList(kgx_summ_dicts:list[dict]) -> list[str]:
    populated_roles = []
    for role in ["Primary Knowledge Source",
                  "Secondary Knowledge Source", 
                  "Supporting Knowledge Source", 
                  "Aggregator Knowledge Source"]:
        #This gets all of the string lengths for all of the dictonaries[$ROLE] values.
        role_val_lens = [len(d.get(role,"")) for d in kgx_summ_dicts]
        #If *any* of the values recorded for $ROLE have any text in them, make $ROLE a column in the csv.
        #This rigamorale is necessary in case a knowledge provider gives a dict with "SuppKS" as a key
        #but all of the them are populated with empty strings.
        if(len(role_val_lens)>0 and max(role_val_lens)>0):populated_roles.append(role)
    return populated_roles

def getAllOtherKeys(sample_list:list[dict],current_cols:list[str]) -> list[str]:
    not_covered_keys:set[str] = set()
    for keys in [set(x.keys()) for x in sample_list]:
        not_covered_keys.update(keys.difference(current_cols))
    return sorted(not_covered_keys)

def getShouldReportPublicationCount(kgx_summ_dicts:list[dict]):
    if any(["Publication Counts" in d for d in kgx_summ_dicts]): return ["Publication Counts"]
    else: return []

def makeSummaryDF(kgx_summ_dicts:list[dict]):
    output_quals = getQualifiersFromDictList(kgx_summ_dicts)
    output_roles = getSourceRolesFromDictList(kgx_summ_dicts)
    output_pub_cnt = getShouldReportPublicationCount(kgx_summ_dicts)

    output_columns = ["KGX Infores", "Normalized", "Edge Count", "Edge Proportion", "SPQO_Tuple",  "SCat", "SCat (Actual)",
                     "Predicate",  "OCat", "OCat (Actual)", "Qualified_Predicate",] +\
                      orderQualifiersForMatt(output_quals) +\
                      [ "Knowledge-Level Terms", "Agent-Type Terms"] +\
                      output_roles +\
                      output_pub_cnt +\
                      ["Edge Properties"]
    
    df = pd.DataFrame.from_records(kgx_summ_dicts,columns=output_columns)
    return df

def makeSampleDF(kgx_samples:list[dict]):
    output_quals = getQualifiersFromDictList(kgx_samples)
    output_roles = getSourceRolesFromDictList(kgx_samples)


    known_cols = ["KGX Infores", "SPQO tuple", "id", "category", "subject", "sub name", "predicate", "object", "obj name", "qualified_predicate"] \
        + orderQualifiersForMatt(output_quals) + output_roles + ['original_json']
    
    other_keys = getAllOtherKeys(kgx_samples,known_cols)

    final_col_list = ["KGX Infores", "SPQO tuple", "id", "category", "subject", "sub name", "predicate", "object", "obj name", "qualified_predicate"] \
        + orderQualifiersForMatt(output_quals) + output_roles \
        + other_keys + ["original_json"]
    
    df = pd.DataFrame.from_records(kgx_samples,columns=final_col_list).fillna("")
    return df

def makePrefixErrorDF(err_list:list[PREFIX_ERR]):
    if(len(err_list)>0):
        df = pd.DataFrame(s.__dict__ for s in err_list)
    else:
        df = pd.DataFrame.from_records([["NO ERRORS FOUND","","",""]],
                                       columns=["source","norm_status","prefix","cat"])

    return df

def makeSubObjErrorDF(spoc_errs:list[SPOCValidationError]):
    columns:Final[list[str]] = ["INGEST NAME", "NORMALIZED", "PREDICATE", "ERROR", "VALID CATEGORIES", "PROVIDED CATEGORIES"]
    if(len(spoc_errs)>0):
        df = pd.DataFrame.from_records([x.to_csv_list() for x in spoc_errs],
                                       columns=columns)
    else:
        df = pd.DataFrame.from_records([["NO ERRORS FOUND","","","","",""]],
                                       columns=columns)
    return df

def makeExcelSheetForSource(ingest_dict:dict[str,dict[str,Ingest]],source_name:str,hp_cats:Iterable[str],outpath:str,with_samples:bool=True):
    unnorm_df,unnorm_samples_df,norm_df,norm_samples_df = None,None,None,None
    prefix_errs:list[PREFIX_ERR] = list()
    sub_obj_errs:list[SPOCValidationError] = list()

    if(source_name in ingest_dict and "not_normalized" in ingest_dict[source_name]):
        unnorm_ingest_obj = ingest_dict[source_name]["not_normalized"]
        unnorm_summ = KGXSummarizer.initWithIngestObj(unnorm_ingest_obj,hp_cats)
        unnorm_df = makeSummaryDF(unnorm_summ.summarize_edges())
        unnorm_samples_df = makeSampleDF(unnorm_summ.sample_edges())
        prefix_errs+=validateNodePrefixesForIngest(unnorm_ingest_obj)
        sub_obj_errs+=findSubObjErrorsForIngest(unnorm_ingest_obj)
    if(source_name in ingest_dict and "normalized" in ingest_dict[source_name]):
        norm_ingest_obj = ingest_dict[source_name]["normalized"]
        norm_summ = KGXSummarizer.initWithIngestObj(norm_ingest_obj,hp_cats)
        norm_summ.summarize_edges()
        norm_df = makeSummaryDF(norm_summ.get_pd_rows())
        norm_samples_df = makeSampleDF(norm_summ.sample_edges())
        prefix_errs+=validateNodePrefixesForIngest(norm_ingest_obj)
        sub_obj_errs+=findSubObjErrorsForIngest(norm_ingest_obj)
    writer = pd.ExcelWriter(outpath) #,engine='xlsxwriter'   # Creating Excel Writer Object from Pandas
    if(norm_df is None and unnorm_df is None):
        blank_df = pd.DataFrame()
        blank_df.to_excel(writer,sheet_name="NO_FILES_FOR_INGEST",index=False)
        writer.close()
        return
    if(unnorm_df is not None and unnorm_samples_df is not None):
        unnorm_df.to_excel(writer,sheet_name=f"{source_name}_unnormalized",index=False)
        unnorm_samples_df.to_excel(writer,sheet_name=f"{source_name}_unnormalized_samples",index=False)
    if(norm_df is not None and norm_samples_df is not None):
        norm_df.to_excel(writer,sheet_name=f"{source_name}_normalized",index=False)
        norm_samples_df.to_excel(writer,sheet_name=f"{source_name}_normalized_samples",index=False)
    prefix_df = makePrefixErrorDF(prefix_errs)
    prefix_df.to_excel(writer,sheet_name=f"{source_name}_BIOLINK_PREFIX_ERRORS",index=False)
    sub_obj_df = makeSubObjErrorDF(sub_obj_errs)
    sub_obj_df.to_excel(writer,sheet_name=f"{source_name}_BIOLINK_SUBOBJ_ERRORS",index=False)
    writer.close()