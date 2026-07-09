from datetime import datetime
from typing import Final, Iterable, Optional

import pandas as pd
from pydantic import BaseModel
from tqdm import tqdm

from kgxval.biolink_validation.check_kgx_blink_prefix import (
    PREFIX_ERR,
    validateNodePrefixesForIngest,
)
from kgxval.biolink_validation.check_kgx_sub_obj_pred import (
    SPOCValidationError,
    findSubObjErrorsForIngest,
)
from kgxval.dir.KGXSummarizer import KGXSummarizer, SPQOStats, orderQualifiersForMatt
from kgxval.dir.kgxval_types import INGEST_MAP, KGX_EDGE, KGX_SUMM


def getQualifiersFromDictList(kgx_summ_dicts: list[KGX_SUMM]) -> set[str]:
    quals = set[str]()
    for d in kgx_summ_dicts:
        for key in d.keys():
            if SPQOStats.testQualifier(key):
                quals.add(key)
    return quals


def getSourceRolesFromDictList(kgx_summ_dicts: list[KGX_SUMM]) -> list[str]:
    populated_roles = list[str]()
    for role in [
        "Primary Knowledge Source",
        "Secondary Knowledge Source",
        "Supporting Data Source",
        "Aggregator Knowledge Source",
    ]:
        # This gets all of the string lengths for all of the dictionaries[$ROLE] values.
        role_val_lens = [len(d.get(role, "")) for d in kgx_summ_dicts]
        # If *any* of the values recorded for $ROLE have any text in them, make $ROLE a column in the csv.
        # This rigamorale is necessary in case a knowledge provider gives a dict with "SuppKS" as a key
        # but all of the them are populated with empty strings.
        if len(role_val_lens) > 0 and max(role_val_lens) > 0:
            populated_roles.append(role)
    return populated_roles


def getAllOtherKeys(sample_list: list[KGX_EDGE], current_cols: list[str]) -> list[str]:
    not_covered_keys: set[str] = set()
    for keys in [set(x.keys()) for x in sample_list]:
        not_covered_keys.update(keys.difference(current_cols))
    return sorted(not_covered_keys)


def getShouldReportPublicationCount(kgx_summ_dicts: list[KGX_SUMM]) -> list[str]:
    if any(["Publication Counts" in d for d in kgx_summ_dicts]):
        return ["Publication Counts"]
    else:
        return []


def getShouldReportEvidenceCount(kgx_summ_dicts: list[KGX_SUMM]) -> list[str]:
    if any(["Evidence Counts" in d for d in kgx_summ_dicts]):
        return ["Evidence Counts"]
    else:
        return []


def makeSummaryDF(kgx_summ_dicts: list[KGX_SUMM], rollup: bool = True):
    output_quals = getQualifiersFromDictList(kgx_summ_dicts)
    output_roles = getSourceRolesFromDictList(kgx_summ_dicts)
    output_pub_cnt = getShouldReportPublicationCount(kgx_summ_dicts)
    output_evidence_cnt = getShouldReportEvidenceCount(kgx_summ_dicts)

    output_columns = (
        [
            "KGX Infores",
            "Normalized",
            "Edge Count",
            "Edge Proportion",
            "SPQO Tuple",
            "SCat",
            "SCat (Actual)",
            "Predicate",
            "OCat",
            "OCat (Actual)",
            "Qualified_Predicate",
        ]
        + orderQualifiersForMatt(output_quals)
        + ["Knowledge-Level Terms", "Agent-Type Terms"]
        + output_roles
        + output_pub_cnt
        + output_evidence_cnt
        + ["Edge Properties"]
    )

    if not rollup:
        output_columns.remove("SCat (Actual)")
        output_columns.remove("OCat (Actual)")

    df = pd.DataFrame.from_records(kgx_summ_dicts, columns=output_columns).sort_values(
        ["Predicate", "SCat", "OCat", "Qualified_Predicate"]
    )
    return df


def makeSampleDF(kgx_samples: list[KGX_SUMM]):
    output_quals = getQualifiersFromDictList(kgx_samples)
    output_roles = getSourceRolesFromDictList(kgx_samples)

    known_cols = (
        [
            "KGX Infores",
            "SPQO Tuple",
            "id",
            "category",
            "subject",
            "sub name",
            "predicate",
            "object",
            "obj name",
            "qualified_predicate",
        ]
        + orderQualifiersForMatt(output_quals)
        + output_roles
        + ["original_subject", "original_object", "original_json"]
    )

    other_keys = getAllOtherKeys(kgx_samples, known_cols)

    final_col_list = (
        [
            "KGX Infores",
            "SPQO Tuple",
            "id",
            "category",
            "subject",
            "sub name",
            "predicate",
            "object",
            "obj name",
            "qualified_predicate",
        ]
        + orderQualifiersForMatt(output_quals)
        + output_roles
        + other_keys
        + ["original_subject", "original_object", "original_json"]
    )

    df = pd.DataFrame.from_records(kgx_samples, columns=final_col_list).fillna("")
    df.sort_values(["predicate", "subject", "object", "qualified_predicate"])

    return df


def makePrefixErrorDF(err_list: list[PREFIX_ERR]):
    if len(err_list) > 0:
        df = pd.DataFrame(s.__dict__ for s in err_list)
    else:
        df = pd.DataFrame.from_records(
            [["NO ERRORS FOUND", "", "", ""]],
            columns=["source", "norm_status", "prefix", "cat"],
        )

    return df


def makeSubObjErrorDF(spoc_errs: list[SPOCValidationError]):
    columns: Final[list[str]] = [
        "INGEST NAME",
        "NORMALIZED",
        "PREDICATE",
        "ERROR",
        "VALID CATEGORIES",
        "PROVIDED CATEGORIES",
    ]
    if len(spoc_errs) > 0:
        df = pd.DataFrame.from_records(
            [x.to_csv_list() for x in spoc_errs], columns=columns
        )
    else:
        df = pd.DataFrame.from_records(
            [["NO ERRORS FOUND", "", "", "", "", ""]], columns=columns
        )
    return df


class ExcelDFFlags(BaseModel):
    unnorm_summ: bool = True
    """If set will return attach a sheet with a summary of the unnormalized ingest."""
    unnorm_samp: bool = True
    """If set will return attach a sheet with sample of the unnormalized ingest (5 per unique SPQO)."""
    norm_summ: bool = True
    """If set will return attach a sheet with a summary of the normalized ingest."""
    norm_samp: bool = True
    """If set will return attach a sheet with sample of the normalized ingest (5 per unique SPQO)."""
    blink_prefix: bool = True
    """If set will return attach a sheet with error in biolink curie prefixes in normalized and unnormalized ingests."""
    blink_subobj: bool = True
    """If set will return attach a sheet with error in biolink subject, object, predicates in normalized and unnormalized ingests."""
    include_rollup: bool = True
    """If set, will make a sheet where the categories are rolled up to the hp_cats."""


def makeExcelSheetForSource(
    ingest_dict: INGEST_MAP,
    source_name: str,
    hp_cats: Iterable[str],
    outpath: str,
    config: ExcelDFFlags = ExcelDFFlags(),
    pbar: Optional["tqdm[str]"] = None, 
):
    #Flag marking if unnormalized data is present in the source.
    unnorm_exists = (source_name in ingest_dict) and (
        "not_normalized" in ingest_dict[source_name]
    )

    #Flag marking if normalized data is present in the source.
    norm_exists = (source_name in ingest_dict) and (
        "normalized" in ingest_dict[source_name]
    )

    if (not unnorm_exists) and (not norm_exists):
        writer = pd.ExcelWriter(outpath)
        blank_df = pd.DataFrame()
        blank_df.to_excel(writer, sheet_name="NO_FILES_FOR_INGEST", index=False)
        writer.close()
        return
    class CurrentTime:
        def __init__(self):
            self.currenttime = datetime.now()
    currentTime = CurrentTime()

    def updatePBar(step: str,time_print=True):
        if pbar is not None:
            last_step_name = pbar.desc
            old_time = currentTime.currenttime
            currentTime.currenttime = datetime.now()
            if(time_print):
                print(f"{last_step_name} took {str(currentTime.currenttime-old_time)}")
            pbar.set_description(f"{source_name} -- {step}")

    prefix_errs: list[PREFIX_ERR] = list()
    sub_obj_errs: list[SPOCValidationError] = list()

    writer = pd.ExcelWriter(outpath,engine="openpyxl")  # Creating Excel Writer Object from Pandas

    if unnorm_exists:
        unnorm_ingest_obj = ingest_dict[source_name]["not_normalized"]
        unnorm_summ = KGXSummarizer.initWithIngestObj(unnorm_ingest_obj, hp_cats)
        if config.unnorm_summ:
            updatePBar("unnorm summarization")
            unnorm_df = makeSummaryDF(unnorm_summ.summarize_edges(source_name))
            unnorm_df.to_excel(
                writer, sheet_name=f"{source_name}_unnorm_summary", index=False
            )
        if config.unnorm_samp:
            updatePBar("unnorm sampling")
            unnorm_samples_df = makeSampleDF(unnorm_summ.sample_edges())
            unnorm_samples_df.to_excel(
                writer, sheet_name=f"{source_name}_unnorm_samples", index=False
            )
        if config.blink_prefix:
            updatePBar("unnorm biolink curie/cat validation")
            prefix_errs += validateNodePrefixesForIngest(unnorm_ingest_obj)
        if config.blink_subobj:
            updatePBar("unnorm biolink spoq validation")
            sub_obj_errs += findSubObjErrorsForIngest(unnorm_ingest_obj)

    if norm_exists:
        norm_ingest_obj = ingest_dict[source_name]["normalized"]
        norm_summ = KGXSummarizer.initWithIngestObj(norm_ingest_obj, [])
        if config.norm_summ:
            updatePBar("normalize summarization")
            norm_summ.summarize_edges(source_name)
            norm_df = makeSummaryDF(norm_summ.get_pd_rows(), rollup=False)
            norm_df.to_excel(
                writer, sheet_name=f"{source_name}_normalized_summary", index=False
            )
        if config.norm_summ:
            updatePBar("normalize sampling")
            norm_samples_df = makeSampleDF(norm_summ.sample_edges())
            norm_samples_df.to_excel(
                writer, sheet_name=f"{source_name}_normalized_samples", index=False
            )
        if config.blink_prefix:
            updatePBar("normalize biolink curie/cat validation")
            prefix_errs += validateNodePrefixesForIngest(norm_ingest_obj)
        if config.blink_subobj:
            updatePBar("normalize biolink spoq validation")
            sub_obj_errs += findSubObjErrorsForIngest(norm_ingest_obj)

    if norm_exists and config.include_rollup:
        norm_ingest_obj = ingest_dict[source_name]["normalized"]
        rollup_summ = KGXSummarizer.initWithIngestObj(norm_ingest_obj, hp_cats)
        updatePBar("rolled-up normalize summarization")
        rollup_summ.summarize_edges(source_name)
        rollup_df = makeSummaryDF(rollup_summ.get_pd_rows(), rollup=True)
        rollup_df.to_excel(
            writer, sheet_name=f"{source_name}_rollup_summary", index=False
        )
        updatePBar("rollup sampling")
        rollup_samples_df = makeSampleDF(rollup_summ.sample_edges())
        rollup_samples_df.to_excel(
            writer, sheet_name=f"{source_name}_rollup_samples", index=False
        )

    if config.blink_prefix:
        prefix_df = makePrefixErrorDF(prefix_errs)
        prefix_df.to_excel(
            writer, sheet_name=f"{source_name}_BIOLINK_PREFIX_ERRORS", index=False
        )
    if config.blink_subobj:
        sub_obj_df = makeSubObjErrorDF(sub_obj_errs)
        sub_obj_df.to_excel(
            writer, sheet_name=f"{source_name}_BIOLINK_SUBOBJ_ERRORS", index=False
        )
    writer.close()
