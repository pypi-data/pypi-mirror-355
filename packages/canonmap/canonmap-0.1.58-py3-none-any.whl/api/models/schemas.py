from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    """Request model for artifact generation."""
    csv_path: str = Field(..., description="Path to the input CSV file")
    output_path: Optional[str] = Field(None, description="Directory to save artifacts")
    name: str = Field("data", description="Base name for output files")
    entity_fields: Optional[List[str]] = Field(None, description="List of column names to treat as entity fields")
    use_other_fields_as_metadata: bool = Field(False, description="Include all non-entity columns as metadata")
    num_rows: Optional[int] = Field(None, description="Number of rows to process")
    return_schema: bool = Field(False, description="Whether to generate and return schema information")
    return_embeddings: bool = Field(False, description="Whether to compute and return embeddings for entities")

class MatchRequest(BaseModel):
    """Request model for entity matching."""
    entity_term: str = Field(..., description="The entity term to match")
    canonical_entities_path: str = Field(..., description="Path to the canonical_entities.pkl file")
    canonical_entity_embeddings_path: Optional[str] = Field(None, description="Path to the canonical_entity_embeddings.npz file (required if use_semantic_search=True)")
    schema_path: Optional[str] = Field(None, description="Path to the schema.pkl file (not used in matching)")
    top_k: int = Field(5, description="Maximum number of results to return")
    threshold: float = Field(0, description="Minimum score threshold for matches")
    field_filter: Optional[List[str]] = Field(None, description="List of field names to restrict matching to")
    use_semantic_search: bool = Field(False, description="Whether to enable semantic search")
    weights: Optional[Dict[str, float]] = Field(None, description="Custom weights for different matching strategies")
    verbose: bool = Field(False, description="Whether to show detailed logging")

class MatchResult(BaseModel):
    """Response model for a single match result."""
    entity: str = Field(..., description="The matched entity string")
    score: float = Field(..., description="Match score (0-100)")
    passes: int = Field(..., description="Number of individual matching strategies that passed")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata for the matched entity")

class MatchResponse(BaseModel):
    """Response model for entity matching."""
    results: List[MatchResult] = Field(..., description="List of match results")

class GenerateResponse(BaseModel):
    """Response model for artifact generation."""
    canonical_entities: List[Dict[str, Any]] = Field(..., description="List of entity objects with their metadata")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Nested dictionary of data types and formats (if return_schema=True)")
    embeddings: Optional[List[float]] = Field(None, description="Optional list of entity embeddings (if return_embeddings=True)") 