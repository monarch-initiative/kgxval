# kgx-biolink-validator
KGXVal - A python library for validating the biolink in a KGX file

The KGXVal serves as a toolkit for ensuring [KGX](https://github.com/biolink/kgx) files conform to the expected structure of the [Biolink Data Model] (https://github.com/biolink/biolink-model/). It relies upon Biolink interfaces present within the Biolink Modeling Toolkit ([BMT](https://github.com/biolink/biolink-model-toolkit)).

The KGXVal script is generally designed to be run in a directory with the following structure, and will be most easily useful if KGX data is structured this way (this is how both Biomedical Data Translator, Monarch KG, and ROBOKOP store their KGX files at rest).

```
-TOP_LEVEL_KGX_STORAGE
-- INGEST-1_NAME
--- PRE_NORMED_KGX_FILES
----- NODES.JSONL
----- EDGES.JSONL
--- POST_NORMALIZATION_KGX_FILES
----- NODES.JSONL
----- EDGES.JSONL
-- INGEST-2_NAME
...
```


### Commands
The following commands are provided via the pyproject.toml file

`uv run ingest_summary $TOP_LEVEL_INGEST_DIR` - This will generate summary, samples, and Biolink errors for each ingest in the directory.

`uv run norm_errors $TOP_LEVEL_INGEST_DIR` - This will generate normalization/curation errors for each ingest in the directory.
