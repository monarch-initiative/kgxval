from collections import defaultdict
from pathlib import Path
from typing import Any, Collection, Iterable, Optional

import numpy as np
from bmt import Toolkit  # pyright: ignore[reportMissingTypeStubs]
from bmt.utils import parse_name # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]
from pydantic import BaseModel
from tqdm import tqdm

from kgxval.dir import Ingest
from kgxval.dir.kgxval_types import KGX_EDGE, KGX_SUMM, PD_SUMM_ROW, SPQO_TUPLE

NONPROPERTY_KEYS: frozenset[str] = frozenset(
    [
        "subject",
        "predicate",
        "qualified_predicate",
        "object",
        "knowledge_level",
        "agent_type",
        "sources",
    ]
)

MATT_QUALIFIER_ORDER: tuple[str, ...] = (
    "object_specialization_qualifier",
    "object_form_or_variant_qualifier",
    "object_derivative_qualifier",
    "object_part_qualifier",
    "object_aspect_qualifier",
    "object_direction_qualifier",
    "object_role_qualifier",
    "object_role",
    "subject_specialization_qualifier",
    "subject_form_or_variant_qualifier",
    "subject_derivative_qualifier",
    "subject_aspect_qualifier",
    "subject_part_qualifier",
    "subject_direction_qualifier",
    "subject_role_qualifier",
    "subject_role",
    "context_qualifier",
    "species_context_qualifier",
    "anatomical_context_qualifier",
    "disease_or_phenotypic_feature_context_qualifier",
    "population_context_qualifier",
    "causal_mechanism_qualifier",
    "derivative_qualifier",
)


def makePipeJoinedStringIfList(str_or_list: str | list[str]) -> str:
    if type(str_or_list) == str:
        return str_or_list
    elif type(str_or_list) == list:
        return "|".join(str_or_list)
    raise ValueError


def cleanPrefixesFromDictVals(dict: dict[str, Any]) -> dict[str, Any]:
    for key, val in list(dict.items()):
        if type(val) == str:
            if val.startswith("infores:"):
                dict[key] = val.replace("infores:", "")
            if val.startswith("biolink:"):
                dict[key] = val.replace("biolink:", "")
    return dict


def orderQualifiersForMatt(qualifiers: Iterable[str]) -> list[str]:
    ret_list: list[str] = []
    for q in MATT_QUALIFIER_ORDER:
        if q in qualifiers:
            ret_list.append(q)
    for q in qualifiers:
        if q not in MATT_QUALIFIER_ORDER and q not in ret_list:
            # print(f"Qualifier {q} found, but not in Matt's list.")
            ret_list.append(q)
    return ret_list


class SPQO(BaseModel, frozen=True):
    """A class representing a unique tuple of Subject, Predicate, Qualifier, and Object.
    We assume that the set of node categories for subject and object have been collapsed
    down to a single category.
    """

    scat: str
    pred: str
    q_pred: str
    ocat: str

    def makeTuple(self) -> SPQO_TUPLE:
        tup = (self.scat, self.pred, self.q_pred, self.ocat)
        return tup


class SPQOStats:
    spqo: SPQO
    ingest: Ingest.Ingest
    cnt: int
    infores_set: set[str] #Set of all inforeses for this SPQO
    at_set: set[str]  # Set of all agent types seen with this spqo
    kl_set: set[str]  # Set of all knowledge levels
    prop_set: set[
        str
    ]  # Set of all property seen (i.e. keys in a jsonl dict which isn't caught by other) (don't store the values, unchecked size and range of values.)
    pks_set: set[str]
    sks_set: set[str]
    suppds_set: set[str]
    aks_set: set[str]
    qualifier_vals: dict[
        str, set[str]
    ]  # Dict of $qualifier -> {set of vals for $qualifier}
    act_scats: set[str]  # Actual subject categories
    act_ocats: set[str]  # Actual object categories
    pub_cnts: list[int]
    evidence_cnts: list[int]

    def __init__(self, spqo: SPQO, ingest: Ingest.Ingest):
        self.spqo = spqo
        self.ingest = ingest
        self.cnt = 0
        self.infores_set = set()
        self.at_set = set()
        self.kl_set = set()
        self.prop_set = set()
        self.pks_set = set()
        self.sks_set = set()
        self.suppds_set = set()
        self.aks_set = set()
        self.qualifier_vals = defaultdict(set)
        self.act_scats = set()
        self.act_ocats = set()
        self.pub_cnts = []
        self.evidence_cnts = []

    @staticmethod
    def testQualifier(potential_qual: str) -> bool:
        """Check to see if a key is a qualifier"""
        return (potential_qual.endswith("_qualifier")) or (
            potential_qual.endswith("role")
        )

    @staticmethod
    def testPopulatedVal(val: Optional[str | int]) -> bool:
        """This looks at the field that's attached to a key in an edge dict. These fields can be left null in a few weird ways.
        We just check if it isn't Null and also that it isn't an empty string.
        """
        if val is None:
            return False
        if type(val) == str and len(val) == 0:
            return False
        return True

    def _getPropertyKeys(self, edge: KGX_EDGE) -> set[str]:
        props = set[str]()
        for potential_prop, val in edge.items():
            if potential_prop in NONPROPERTY_KEYS:
                continue  # This isn't a property
            if self.testQualifier(potential_prop):
                continue  # This is a qualifier or role, not a property
            if potential_prop in self.prop_set:
                continue  # We've already seen this property, no reason to check if it's populated.

            if self.testPopulatedVal(val):
                props.add(potential_prop)
        return props

    def _updateQualifiers(self, edge: KGX_EDGE):
        """If a key appears in the edge dict ending in either _qualifier or role - check if the value is properly populated.
        If it is, add it into our big dictionary of qualifiers with their values.
        """
        for potential_qual, val in edge.items():
            if self.testQualifier(potential_qual) and self.testPopulatedVal(val):
                self.qualifier_vals[potential_qual].add(makePipeJoinedStringIfList(val))

    def _updatePubCount(self, edge: KGX_EDGE):
        if "publications" in edge:
            pub_cnt = len(edge["publications"])
            self.pub_cnts.append(pub_cnt)

    def _updateEvidenceCount(self, edge: KGX_EDGE):
        if "evidence_count" in edge:
            self.evidence_cnts.append(int(edge["evidence_count"]))

    def _updatePKS(self, edge: KGX_EDGE):
        if "sources" in edge:
            self.pks_set.update(
                [
                    s["resource_id"]
                    for s in edge["sources"]
                    if s["resource_role"] == "primary_knowledge_source"
                ]
            )
        elif "primary_knowledge_source" in edge:
            self.pks_set.add(edge["primary_knowledge_source"])

    def _updateSKS(self, edge: KGX_EDGE):
        if "sources" in edge:
            self.sks_set.update(
                [
                    s["resource_id"]
                    for s in edge["sources"]
                    if s["resource_role"] == "secondary_knowledge_source"
                ]
            )
        elif "secondary_knowledge_source" in edge:
            self.sks_set.add(edge["secondary_knowledge_source"])

    def _updateSuppDS(self, edge: KGX_EDGE):
        if "sources" in edge:
            self.suppds_set.update(
                [
                    s["resource_id"]
                    for s in edge["sources"]
                    if s["resource_role"] == "supporting_data_source"
                ]
            )
        elif "supporting_data_source" in edge:
            self.suppds_set.add(edge["supporting_data_source"])

    def _updateAKS(self, edge: KGX_EDGE):
        if "sources" in edge:
            self.aks_set.update(
                [
                    s["resource_id"]
                    for s in edge["sources"]
                    if s["resource_role"] == "aggregator_knowledge_source"
                ]
            )
        elif "aggregator_knowledge_source" in edge:
            self.aks_set.add(edge["aggregator_knowledge_source"])

    def _updateActualSCats(self, edge: KGX_EDGE):
        """We have a set which tracks all of the subject categories which actually end up being mapped to data."""
        all_scats = self.ingest.get_node_id_category(edge["subject"])
        self.act_scats.update(all_scats)

    def _updateActualOCats(self, edge: KGX_EDGE):
        """We have a set which tracks all of the subject categories which actually end up being mapped to data."""
        obj_name = edge["object"]
        if type(obj_name) != str:
            raise ValueError(
                f"The field 'object' was of type {type(obj_name)} instead of str --- {KGX_EDGE} --- "
            )
        all_ocats = self.ingest.get_node_id_category(obj_name)
        self.act_ocats.update(all_ocats)

    def _updateInfores(self, infores_name:str):
        self.infores_set.add(infores_name)

    def incrementStats(self, edge: KGX_EDGE, infores_name: str):
        self.cnt += 1
        kl_str = makePipeJoinedStringIfList(edge.get("knowledge_level", ""))
        if len(kl_str) > 0:
            self.kl_set.add(kl_str)
        at_str = makePipeJoinedStringIfList(edge.get("agent_type", ""))
        if len(at_str) > 0:
            self.at_set.add(at_str)

        edge_props = self._getPropertyKeys(edge)
        self.prop_set.update(edge_props)

        self._updateInfores(infores_name)

        self._updateQualifiers(edge)

        self._updatePubCount(edge)
        self._updateEvidenceCount(edge)

        self._updatePKS(edge)
        self._updateSKS(edge)
        self._updateSuppDS(edge)
        self._updateAKS(edge)

        self._updateActualSCats(edge)
        self._updateActualOCats(edge)

    @staticmethod
    def _makePercentileStr(vals: list[int]) -> str:
        per_range = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        per = np.percentile(vals, per_range)
        avg = np.average(vals)
        no_pub_cnt = sum(val == 0 for val in vals)
        one_pub_cnt = sum(val == 1 for val in vals)
        twoplus_pub_cnt = sum(val > 1 for val in vals)

        percentile_str = ", ".join(
            [f"{per_range[i]}:{per[i]:.2f}" for i in range(len(per_range))]
        )
        # "0%:{per[0]:.2f}, 25%:{per[1]:.2f}, 50%:{per[2]:.2f}, 75%:{per[3]:.2f}, 100%:{per[4]:.2f}"
        retstr = (
            f"(0 pubs:{no_pub_cnt},1 pub:{one_pub_cnt},>1 pubs:{twoplus_pub_cnt}) - Avg:{avg:.2f} - "
            + percentile_str
        )
        return retstr

    def makePdOutputRow(
        self, normalized: str, total_edge_cnt: int
    ) -> PD_SUMM_ROW:
        output_dict: dict[str, float | int | str | SPQO_TUPLE] = {
            "KGX Infores": ", ".join(sorted(self.infores_set)),
            "Normalized": normalized,
            "Edge Count": self.cnt,
            "Edge Proportion": self.cnt / total_edge_cnt,
            "SPQO Tuple": self.spqo.makeTuple(),
            "SCat": self.spqo.scat,
            "SCat (Actual)": ", ".join(sorted(self.act_scats)),
            "Predicate": self.spqo.pred,
            "Qualified_Predicate": self.spqo.q_pred,
            "OCat": self.spqo.ocat,
            "OCat (Actual)": ", ".join(sorted(self.act_ocats)),
            "Knowledge-Level Terms": ", ".join(sorted(self.kl_set)),
            "Agent-Type Terms": ", ".join(sorted(self.at_set)),
            "Edge Properties": ", ".join(sorted(self.prop_set)),
            "Primary Knowledge Source": ", ".join(sorted(self.pks_set)),
            "Secondary Knowledge Source": ", ".join(sorted(self.sks_set)),
            "Supporting Data Source": ", ".join(sorted(self.suppds_set)),
            "Aggregator Knowledge Source": ", ".join(sorted(self.aks_set)),
        }

        if len(self.pub_cnts) > 0:
            # If there are any publications reported; we want to report the percentiles of all publication counts.
            # To do so, we assume any edge without publications has 0 pubs reported.
            corrected_pub_cnts = self.pub_cnts + [0] * (self.cnt - len(self.pub_cnts))
            output_dict["Publication Counts"] = self._makePercentileStr(
                corrected_pub_cnts
            )

        if len(self.evidence_cnts) > 0:
            # If there are any "evidence_count" fields reported; we want to report the percentiles of these counts.
            # To do so, we assume any edge without "evidence_count" reported has a value of 0.
            corrected_evidence_cnts = self.evidence_cnts + [0] * (
                self.cnt - len(self.evidence_cnts)
            )
            output_dict["Evidence Counts"] = self._makePercentileStr(
                corrected_evidence_cnts
            )

        for qual, qual_set in self.qualifier_vals.items():
            output_dict[qual] = ", ".join(sorted(qual_set))

        output_dict = cleanPrefixesFromDictVals(output_dict)
        return output_dict


class KGXSummarizer(Ingest.Ingest):
    tk: Toolkit
    high_priority_desc_dict: dict[str, set[str]]
    blink_class_to_depth: dict[str, int]
    spqo_to_stats: dict[SPQO, SPQOStats]
    total_edge_cnt: int
    summarize_edges_ran: bool

    def __init__(
        self,
        ingest_name: str,
        node_path: Path,
        edge_path: Optional[Path],
        norm_status: str,
        high_priority_node_cats: Iterable[str],
    ):
        self.tk = Toolkit()
        self.high_priority_desc_dict = {}
        self.spqo_to_stats = {}
        self.summarize_edges_ran = False
        self.total_edge_cnt = 0
        for hp_cat in high_priority_node_cats:
            desc_set = set(self.tk.get_descendants(hp_cat))
            self.high_priority_desc_dict[hp_cat] = desc_set
        self.blink_class_to_depth = {}
        for blink_class in self.tk.get_all_classes():
            self.blink_class_to_depth[blink_class] = self.tk.get_element_depth(
                blink_class
            )
        super().__init__(
            ingest_name=ingest_name,
            node_path=node_path,
            edge_path=edge_path,
            norm_status=norm_status,
        )

    @classmethod
    def initWithIngestObj(
        cls, ingest_obj: Ingest.Ingest, high_priority_node_cats: Iterable[str]
    ):
        ingest_name: str = ingest_obj.ingest_name
        node_path: Path = ingest_obj.node_path
        edge_path: Optional[Path] = ingest_obj.edge_path
        norm_status: str = ingest_obj.norm_status
        return cls(
            ingest_name=ingest_name,
            node_path=node_path,
            edge_path=edge_path,
            norm_status=norm_status,
            high_priority_node_cats=high_priority_node_cats,
        )

    def _getBestCat(self, category_list: Collection[str]) -> str:
        """This function collapses a list of categories down to a single "most important" category.
        It's fairly arbitrary, but if we don't do this, summarization is mostly worthless.
        """
        # First see if we can hit any of the "high priority categories"
        for hp_node_cat, desc_set in self.high_priority_desc_dict.items():
            if len(desc_set.intersection(category_list)) > 0:
                return hp_node_cat
        # We couldn't hit any of those, figure out which category has the deepest depth.
        if len(category_list) == 0:
            return "NO CATEGORY"
        return max(category_list, key=lambda cat: self.blink_class_to_depth[cat])

    def _makeSPQOFromEdgeDict(self, edge: KGX_EDGE) -> SPQO:
        all_scats = self.get_node_id_category(edge["subject"])
        all_ocats = self.get_node_id_category(edge["object"])
        pred = parse_name(edge["predicate"])
        if "qualified_predicate" in edge and len(edge["qualified_predicate"]) > 0:
            q_pred = parse_name(edge["qualified_predicate"])
        else:
            q_pred = "n/a"
        scat = self._getBestCat(all_scats)
        ocat = self._getBestCat(all_ocats)
        return SPQO(scat=scat, pred=pred, q_pred=q_pred, ocat=ocat)

    def summarize_edges(self, infores_name:str) -> list[KGX_SUMM]:
        self.total_edge_cnt = 0
        # spqo_to_stats:dict[SPQO,SPQOStats] = {}
        for edge_dict in tqdm(self.iter_edges()):
            self.total_edge_cnt += 1
            edge_spqo = self._makeSPQOFromEdgeDict(edge_dict)
            if edge_spqo not in self.spqo_to_stats:
                self.spqo_to_stats[edge_spqo] = SPQOStats(edge_spqo, self)
            self.spqo_to_stats[edge_spqo].incrementStats(edge_dict, infores_name)
        self.summarize_edges_ran = True
        return self.get_pd_rows()
    
    def add_summarize_edges_for_iter(self, edge_iter:Iterable[KGX_EDGE], ingest: Ingest.Ingest, infores_name:str):
        # spqo_to_stats:dict[SPQO,SPQOStats] = {}
        self.get_node_id_category = ingest.get_node_id_category
        for edge_dict in tqdm(edge_iter):
            self.total_edge_cnt += 1
            try:
                edge_spqo = self._makeSPQOFromEdgeDict(edge_dict)
            except ValueError as e:
                print(f"Making spqo failed due to {str(e)}")
                raise e
            #    continue
            if edge_spqo not in self.spqo_to_stats:
                self.spqo_to_stats[edge_spqo] = SPQOStats(edge_spqo, self)
            self.spqo_to_stats[edge_spqo].ingest = ingest
            self.spqo_to_stats[edge_spqo].incrementStats(edge_dict, infores_name)
        self.summarize_edges_ran = True

        #return self.get_pd_rows()

    def sample_edges(self) -> list[KGX_EDGE]:
        # Makes it be so that if "sources" is present (which is a dict
        # that is {SOURCE_ROLE->INFORES,...}, that information is
        # instead provided as the edge_dict[source_role] .
        def fixSources(edge_dict: KGX_EDGE) -> KGX_EDGE:
            if "sources" not in edge_dict:
                return edge_dict
            for source_dict in edge_dict.get("sources", []):
                source_infores_id = source_dict["resource_id"].replace("infores:", "")
                source_role = source_dict["resource_role"]
                if source_role in edge_dict:
                    edge_dict[source_role] += f", {source_infores_id}"
                else:
                    edge_dict[source_role] = source_infores_id
            edge_dict.pop("sources")
            return edge_dict

        edge_samples_for_spoq: defaultdict[SPQO, list[KGX_EDGE]] = defaultdict(list)
        for edge_dict in self.iter_edges(attach_original_json=True):
            edge_spqo = self._makeSPQOFromEdgeDict(edge_dict)
            if len(edge_samples_for_spoq[edge_spqo]) > 4:
                continue
            edge_dict["KGX Infores"] = self.ingest_name
            edge_dict["SPQO Tuple"] = edge_spqo.makeTuple()
            edge_dict["sub name"] = self.get_node_id_name(edge_dict["subject"])
            edge_dict["obj name"] = self.get_node_id_name(edge_dict["object"])
            edge_dict = fixSources(edge_dict)
            edge_dict = cleanPrefixesFromDictVals(edge_dict)
            edge_samples_for_spoq[edge_spqo].append(edge_dict)

        # Gather all samples for each spoq and make one big list.
        list_of_all_samples: list[KGX_EDGE] = []
        for edge_sample_list in edge_samples_for_spoq.values():
            list_of_all_samples.extend(edge_sample_list)
        return list_of_all_samples

    def get_pd_rows(self) -> list[PD_SUMM_ROW]:
        if not self.summarize_edges_ran:
            raise RuntimeError('Need to run "summarize_edges" before "get_pd_rows"')
        return [
            x.makePdOutputRow(
                normalized=self.norm_status,
                total_edge_cnt=self.total_edge_cnt,
            )
            for x in self.spqo_to_stats.values()
        ]
