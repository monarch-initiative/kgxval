from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    print("HI")
    from .Ingest import Ingest

KGX_NODE = dict[str, Any]
KGX_EDGE = dict[str, Any]

KGX_SUMM = dict[str, Any]

INGEST_MAP = dict[str, dict[str, "Ingest"]]

SPQO_TUPLE = tuple[str, str, str, str]

PD_SUMM_ROW = dict[str, float | int | str | SPQO_TUPLE]
"""Row which should be passed into a pandas dataframe which contains all information on a particular subset of ingests."""
