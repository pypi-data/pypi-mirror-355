# canonmap/services/artifact_generator/_run_pipeline.py

from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Dict

import pandas as pd
import pickle
import spacy
import json

from canonmap.services.artifact_generator._structure_parser_helper import StructureParserHelper
from canonmap.utils.logger import get_logger

logger = get_logger()

def _metadata_objects_equal(obj1: Dict[str, Any], obj2: Dict[str, Any]) -> bool:
    """Check if two metadata objects are exactly equal in all their attributes."""
    if set(obj1.keys()) != set(obj2.keys()):
        return False
    return all(obj1[k] == obj2[k] for k in obj1.keys())

def run_artifact_generation_pipeline(
    num_cores: int = 1,
    df: pd.DataFrame = None,
    output_path: Union[str, Path] = None,
    name: str = "data",
    entity_fields: Optional[List[str]] = None,
    use_other_fields_as_metadata: bool = False,
    nlp: Optional[spacy.Language] = None,
    max_uniqueness_ratio: float = 0.95,
    max_avg_length: int = 100,
    normalize_entities: bool = True,
    return_schema: bool = False,
    return_processed_data: bool = False,
    unload: bool = False,
) -> Dict[str, Any]:
    output_path = _ensure_output_dir(output_path)
    artifact_paths = _get_artifact_paths(output_path, name)

    # 1) Clean & format columns, then infer schema
    logger.info("Cleaning & formatting columns; inferring schema")
    parser = StructureParserHelper(num_cores=num_cores, nlp=nlp)
    cleaned_df, column_map, raw_schema_map = parser.parse_dataframe(df)

    # Save processed data if requested
    if return_processed_data:
        processed_data_path = Path(output_path) / f"{name}_processed_data.pkl"
        logger.info(f"Saving processed data to {processed_data_path}")
        cleaned_df.to_pickle(processed_data_path)
        artifact_paths["processed_data"] = processed_data_path

    # 1.a) Wrap the raw schema into nested { source_name: { table_name: { … } } }
    nested_schema: Dict[str, Any] = {
        name: {
            name: {}
        }
    }

    # For each column, collect data_type, optional date_format, and example_data
    for col, col_info in raw_schema_map.items():
        entry: Dict[str, Any] = {"data_type": col_info["data_type"]}

        # If this is a DATE or DATETIME, include the detected format
        if col_info["data_type"] in ("DATE", "DATETIME"):
            entry["date_format_in_database"] = col_info.get("date_format_in_database")

        # Build example_data: up to 10 non-null, unique values from cleaned_df[col]
        series = cleaned_df[col].dropna()
        if len(series) > 0:
            unique_vals = pd.Series(series).drop_duplicates().head(10).tolist()
            example_list: List[Any] = []
            for v in unique_vals:
                if isinstance(v, (pd.Timestamp, pd.Timedelta)):
                    example_list.append(str(v))
                else:
                    example_list.append(v)
            entry["example_data"] = example_list
        else:
            entry["example_data"] = []

        nested_schema[name][name][col] = entry

    # 2) Build metadata_list
    metadata_list: List[Dict[str, Any]] = []

    valid_entity_fields: List[str] = []
    if entity_fields:
        logger.info(f"Using provided entity_fields: {entity_fields}")
        for fld in entity_fields:
            if fld in cleaned_df.columns:
                if raw_schema_map[fld]["data_type"] == "STRING":
                    valid_entity_fields.append(fld)
                else:
                    logger.info(
                        f"Skipping '{fld}' (data_type={raw_schema_map[fld]['data_type']} is not STRING)."
                    )
            else:
                logger.info(f"Skipping '{fld}' (column not found).")

        if not valid_entity_fields:
            logger.info(
                "No valid entity_fields remain after filtering to STRING columns. "
                "Falling back to auto‐extraction."
            )
        logger.info(f"Entity fields that will actually be used: {valid_entity_fields}")

    # 2.a) If entity_fields were provided and valid
    if valid_entity_fields:
        for _, row in cleaned_df.iterrows():
            for fld in valid_entity_fields:
                entity_value = row[fld]
                if pd.isna(entity_value):
                    continue
                text = str(entity_value).strip()
                if text == "" or text.lower() in ("nan", "none", "null"):
                    continue

                entity_obj: Dict[str, Any] = {
                    "_canonical_entity_": entity_value,
                    "_field_name_": fld,
                    "_source_name_": name,
                    "_table_name_": name
                }

                if use_other_fields_as_metadata:
                    for other_col in cleaned_df.columns:
                        if other_col == fld:
                            continue
                        val = row[other_col]
                        if pd.isna(val):
                            continue
                        val_str = str(val).strip()
                        if val_str == "" or val_str.lower() in ("nan", "none", "null"):
                            continue
                        entity_obj[other_col] = val

                # Check if this exact metadata object already exists
                if not any(_metadata_objects_equal(entity_obj, existing) for existing in metadata_list):
                    metadata_list.append(entity_obj)

    # 2.b) Otherwise, run full spaCy + heuristic extraction
    if not valid_entity_fields:
        logger.info("No entity_fields specified; running automatic entity extraction")
        row_dicts = cleaned_df.to_dict(orient="records")

        string_cols = {
            col
            for col, info in raw_schema_map.items()
            if info["data_type"] == "STRING"
        }
        logger.info(
            f"Limiting auto‐extraction to these STRING columns: {sorted(string_cols)}"
        )
        entities_by_field = parser.build_known_entities(
            metadata=row_dicts,
            table_name=name,
            allowed_fields=string_cols,
            max_uniqueness_ratio=max_uniqueness_ratio,
            max_avg_length=max_avg_length,
            normalize=normalize_entities
        )

        for record in row_dicts:
            for fld, candidate_list in entities_by_field.items():
                for entity_value in candidate_list:
                    text = str(entity_value).strip()
                    if text == "" or text.lower() in ("nan", "none", "null"):
                        continue

                    entity_obj: Dict[str, Any] = {
                        "_canonical_entity_": entity_value,
                        "_field_name_": fld,
                        "_source_name_": name,
                        "_table_name_": name
                    }
                    # Check if this exact metadata object already exists
                    if not any(_metadata_objects_equal(entity_obj, existing) for existing in metadata_list):
                        metadata_list.append(entity_obj)

    logger.info("Saving canonical_entities.pkl")
    with open(artifact_paths["canonical_entities"], "wb") as f:
        pickle.dump(metadata_list, f)

    if return_schema:
        logger.info("Saving schema.pkl")
        with open(artifact_paths["schema"], "wb") as f:
            pickle.dump(nested_schema, f)

    logger.info(f"All artifacts saved under: {output_path}")

    # Unload artifacts if requested
    if unload:
        from concurrent.futures import ThreadPoolExecutor
        def unload_task(args):
            key, path = args
            if str(path).endswith('.npz'):
                return  # skip embeddings
            if not Path(path).exists():
                return
            try:
                obj = pickle.load(open(path, 'rb'))
                if key == "schema":
                    # Save schema as JSON only
                    json_path = str(path).replace('.pkl', '.json')
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(obj, f, default=str, indent=2)
                elif key == "processed_data":
                    # Save processed_data as CSV only
                    if isinstance(obj, pd.DataFrame):
                        csv_path = str(path).replace('.pkl', '.csv')
                        obj.to_csv(csv_path, index=False)
                elif key == "canonical_entities":
                    # Save canonical_entities as JSON only
                    json_path = str(path).replace('.pkl', '.json')
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(obj, f, default=str, indent=2)
            except Exception as e:
                logger.warning(f"Could not unload {path}: {e}")
        with ThreadPoolExecutor() as executor:
            executor.map(unload_task, artifact_paths.items())

    return {
        "metadata": metadata_list,
        "schema": nested_schema if return_schema else None,
        "paths": artifact_paths
    }

def _ensure_output_dir(output_path: Union[str, Path]) -> Path:
    p = Path(output_path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def _get_artifact_paths(output_path: Union[str, Path], name: str) -> Dict[str, Path]:
    p = Path(output_path)
    return {
        "canonical_entities": p / f"{name}_canonical_entities.pkl",
        "canonical_entity_embeddings": p / f"{name}_canonical_entity_embeddings.npz",
        "schema": p / f"{name}_schema.pkl",
        "processed_data": p / f"{name}_processed_data.pkl"
    }

