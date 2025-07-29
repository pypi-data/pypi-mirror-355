from fastapi import APIRouter, HTTPException
from ..models.schemas import GenerateRequest, GenerateResponse
from canonmap import CanonMap

router = APIRouter(tags=["generation"])

@router.post("/generate-artifacts/", response_model=GenerateResponse)
async def generate_artifacts(request: GenerateRequest):
    """
    Generate artifacts from a CSV file.
    
    This endpoint processes a CSV file to:
    1. Extract and clean entities
    2. Infer data types and formats
    3. Generate embeddings (if enabled)
    4. Save artifacts to disk
    
    The process includes:
    - Entity extraction with optional comma-splitting
    - Schema inference for all columns
    - Metadata generation for each entity
    - Optional embedding generation using sentence-transformers
    """
    try:
        canonmap = CanonMap()
        results = canonmap.generate_artifacts(
            csv_path=request.csv_path,
            output_path=request.output_path,
            name=request.name,
            entity_fields=request.entity_fields,
            use_other_fields_as_metadata=request.use_other_fields_as_metadata,
            num_rows=request.num_rows,
            embed=request.embed
        )
        
        return GenerateResponse(
            metadata=results["metadata"],
            data_schema=results["schema"],
            paths=results["paths"],
            embeddings=results.get("embeddings")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 