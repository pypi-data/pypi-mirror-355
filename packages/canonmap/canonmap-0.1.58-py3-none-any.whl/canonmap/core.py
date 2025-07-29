# File: canonmap/core.py

import json
import tempfile
from pathlib import Path
from typing import Optional, List, Any, Dict

from canonmap.services.artifact_generator import ArtifactGenerator
from canonmap.services.entity_matcher.entity_matcher import EntityMatcher
from canonmap.utils.logger import get_logger

logger = get_logger()


class CanonMap:
    """
    Main interface for generating and saving artifacts, and performing entity matching.
    
    This class provides high-level methods for:
    1. Generating artifacts from CSV files (metadata, schema, embeddings)
    2. Matching entities against generated artifacts using various matching strategies
    
    The entity matching process uses a combination of:
    - Semantic search (using transformer embeddings)
    - Fuzzy string matching
    - Phonetic matching
    - Initial matching
    - Keyword matching
    - Full string matching
    """

    def __init__(self, verbose: bool = False):
        """Initialize the CanonMap with an ArtifactGenerator instance."""
        self.artifact_generator = ArtifactGenerator(verbose=verbose)
        self.verbose = verbose

    def generate_artifacts(
        self,
        csv_path: str,
        output_path: Optional[str] = None,
        name: str = "data",
        entity_fields: Optional[List[str]] = None,
        use_other_fields_as_metadata: bool = False,
        num_rows: Optional[int] = None,
        return_schema: bool = False,
        return_embeddings: bool = False,
        return_processed_data: bool = False,
        unload: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate artifacts from a CSV file.

        Args:
            csv_path (str): Path to the input CSV file
            output_path (Optional[str]): Directory to save artifacts. If None, uses a temporary directory
            name (str): Base name for output files (default: "data")
            entity_fields (Optional[List[str]]): List of column names to treat as entity fields.
                If None, automatically detects entity fields
            use_other_fields_as_metadata (bool): If True, includes all non-entity columns as metadata
            num_rows (Optional[int]): Number of rows to process. If None, processes all rows
            return_schema (bool): Whether to generate and return schema information
            return_embeddings (bool): Whether to compute and return embeddings for entities
            return_processed_data (bool): Whether to save the processed DataFrame with cleaned column names
            unload (bool): Whether to convert artifact files to JSON/CSV (except .npz files)

        Returns:
            Dict[str, Any]: Dictionary containing:
                - "canonical_entities": List of entity objects with their metadata
                - "schema": Optional nested dictionary of data types and formats (if return_schema=True)
                - "embeddings": Optional numpy array of entity embeddings (if return_embeddings=True)
                - "paths": Dictionary of paths to generated artifacts
        """
        out_dir = Path(output_path) if output_path else Path(tempfile.mkdtemp())
        return self.artifact_generator.generate_artifacts_from_csv(
            csv_path=csv_path,
            output_path=out_dir,
            name=name,
            entity_fields=entity_fields,
            use_other_fields_as_metadata=use_other_fields_as_metadata,
            num_rows=num_rows,
            return_schema=return_schema,
            return_embeddings=return_embeddings,
            return_processed_data=return_processed_data,
            unload=unload,
        )

    def match_entity(
        self,
        entity_term: str,
        canonical_entities_path: str,
        canonical_entity_embeddings_path: Optional[str] = None,
        schema_path: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.0,
        field_filter: Optional[List[str]] = None,
        use_semantic_search: bool = False,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Match an entity term against entities in the generated artifacts.

        Args:
            entity_term (str): The entity term to match
            canonical_entities_path (str): Path to the canonical_entities.pkl file
            canonical_entity_embeddings_path (Optional[str]): Path to the canonical_entity_embeddings.npz file
            schema_path (Optional[str]): Path to the schema.json file
            top_k (int): Number of top matches to return
            threshold (float): Minimum score threshold for matches
            field_filter (Optional[List[str]]): List of fields to include in results
            use_semantic_search (bool): Whether to enable semantic search
            weights (Optional[Dict[str, float]]): Custom weights for different matching strategies

        Returns:
            List[Dict[str, Any]]: List of match results with scores and metadata
        """
        try:
            # Load the matcher
            matcher = EntityMatcher(
                canonical_entities_path=canonical_entities_path,
                canonical_entity_embeddings_path=canonical_entity_embeddings_path,
                use_semantic_search=use_semantic_search,
                embedding_model=lambda txt: self.artifact_generator._embed_texts([txt])[0],
                verbose=self.verbose
            )
            
            # Log the entity term
            logger.info(f"Entity term: '{entity_term}'")
            
            # Compute entity term embedding if semantic search is enabled
            q_emb = None
            if use_semantic_search:
                try:
                    q_emb = self.artifact_generator._embed_texts([entity_term])[0]
                except Exception as e:
                    logger.warning("Failed to compute entity term embedding; proceeding without semantic scores")
            
            # Perform matching
            matches = matcher.match(
                entity_term=entity_term,
                entity_term_embedding=q_emb,
                top_k=top_k,
                threshold=threshold
            )

            logger.info(f"Entity match completed: found {len(matches)} results")
            if matches:
                logger.info("Top matches:")
                for i, r in enumerate(matches[:top_k], 1):
                    logger.info(f"  {i}. '{r['entity']}' (score: {r['score']:.1f})")
            return matches
        except Exception as e:
            logger.error(f"Error in match_entity: {e}")
            return []
