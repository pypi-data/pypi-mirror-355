from fastapi import APIRouter, HTTPException
from typing import List
from ..models.schemas import MatchRequest, MatchResult, MatchResponse
from canonmap import CanonMap
from fastapi import BackgroundTasks
from canonmap.services.entity_matcher.entity_matcher import EntityMatcher
import logging

router = APIRouter()

@router.post("/match")
async def match_entities(
    request: MatchRequest,
    background_tasks: BackgroundTasks
) -> MatchResponse:
    """Match entities against canonical entities."""
    try:
        # Set logging level based on verbose flag
        logging.getLogger('canonmap').setLevel(logging.DEBUG if request.verbose else logging.WARNING)
        
        # Initialize CanonMap for embedding model
        canonmap = CanonMap()
        
        # Load the matcher
        matcher = EntityMatcher(
            canonical_entities_path=request.canonical_entities_path,
            canonical_entity_embeddings_path=request.canonical_entity_embeddings_path,
            use_semantic_search=request.use_semantic_search,
            embedding_model=lambda txt: canonmap.artifact_generator._embed_texts([txt])[0]
        )
        
        # Perform matching
        matches = matcher.match(
            entity_term=request.entity_term,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        return MatchResponse(
            results=[
                MatchResult(
                    entity=result["entity"],
                    score=result["score"],
                    passes=result["passes"],
                    metadata=result["metadata"]
                )
                for result in matches
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 