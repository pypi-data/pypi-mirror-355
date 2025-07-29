from pathlib import Path
import pickle
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Any, Dict, Callable
import logging

import numpy as np
from rapidfuzz import fuzz
from metaphone import doublemetaphone
from sklearn.preprocessing import normalize
from sklearn.neighbors import NearestNeighbors

from canonmap.utils.logger import get_logger
logger = get_logger()


class EntityMatcher:
    """
    Matcher with semantic search (sklearn ANN), and customizable scoring weights.
    Always performs semantic prune first, then scores candidates, allowing
    an override to return an exact number of results.
    """

    def __init__(
        self,
        canonical_entities_path: str,
        embedding_model: Callable[[str], np.ndarray],
        semantic_prune: int = 50,
        n_jobs: int = 4,
        use_semantic_search: bool = False,
        token_prefilter_k: int = 200,
        weights: Optional[Dict[str, float]] = None,
        canonical_entity_embeddings_path: Optional[str] = None,
        schema_path: Optional[str] = None,
        verbose: bool = False,
    ):
        if use_semantic_search and not canonical_entity_embeddings_path:
            raise ValueError("canonical_entity_embeddings_path is required when use_semantic_search=True")

        # Set logging level based on verbose flag
        logger.setLevel(logging.DEBUG if verbose else logging.WARNING)

        logger.info("Initializing EntityMatcher with custom weights and semantic_search=%s", use_semantic_search)
        logger.info(f"  canonical_entities:  {canonical_entities_path}")
        logger.info(f"  canonical_entity_embeddings: {canonical_entity_embeddings_path}")
        if schema_path:
            logger.info(f"  schema:    {schema_path}")
        logger.info(f"  semantic_prune: {semantic_prune}")
        logger.info(f"  n_jobs: {n_jobs}")

        # load metadata
        self.metadata: List[Dict[str, Any]] = pickle.loads(Path(canonical_entities_path).read_bytes())
        self.N = len(self.metadata)

        # embedder for on-the-fly embeddings
        self.embed = embedding_model

        # Default weights
        default_weights = {
            'semantic': 0.45,
            'fuzzy':    0.35,
            'initial':  0.10,
            'keyword':  0.05,
            'phonetic': 0.05,
        }

        # If user provided weights, merge with defaults
        if weights:
            # Start with default weights
            self.weights = default_weights.copy()
            # Override with user weights
            self.weights.update(weights)
            logger.info("Merged user weights with defaults: %s", self.weights)
        else:
            self.weights = default_weights
            logger.info("Using default weights: %s", self.weights)

        # If semantic search is disabled, normalize the remaining weights
        if not use_semantic_search:
            # Get user-provided weights (excluding semantic)
            user_weights = {k: v for k, v in weights.items() if k != 'semantic'} if weights else {}
            # Get remaining weights that need normalization
            remaining_weights = {k: v for k, v in self.weights.items() 
                               if k != 'semantic' and k not in user_weights}
            
            # Calculate total of user weights
            user_total = sum(user_weights.values())
            if user_total >= 1.0:
                logger.warning("User weights sum to >= 1.0, some weights may be ignored")
                # Keep user weights as is, set remaining to 0
                normalized_weights = {**user_weights, **{k: 0.0 for k in remaining_weights}}
            else:
                # Calculate remaining weight to distribute
                remaining_total = 1.0 - user_total
                if remaining_weights and remaining_total > 0:
                    # Normalize remaining weights to sum to the remaining total
                    remaining_sum = sum(remaining_weights.values())
                    normalized_remaining = {k: (v/remaining_sum) * remaining_total 
                                         for k, v in remaining_weights.items()}
                    # Combine user weights with normalized remaining weights
                    normalized_weights = {**user_weights, **normalized_remaining}
                else:
                    normalized_weights = user_weights

            # Add semantic back as 0
            normalized_weights['semantic'] = 0.0
            self.weights = normalized_weights
            logger.info("Normalized weights (preserving user values): %s", self.weights)
        else:
            logger.info("Using weights with semantic search: %s", self.weights)

        # precompute entities and phonetic codes
        self.entities = [m['_canonical_entity_'] for m in self.metadata]
        self.phonetics = [doublemetaphone(ent)[0] for ent in self.entities]

        # semantic ANN via sklearn
        self.semantic_enabled = False
        if use_semantic_search and canonical_entity_embeddings_path and Path(canonical_entity_embeddings_path).exists():
            arr = np.load(canonical_entity_embeddings_path)["embeddings"].astype(np.float32)
            if arr.shape[0] != self.N:
                raise ValueError("Metadata/embeddings mismatch")
            self.embeddings = normalize(arr, axis=1)
            self.nn = NearestNeighbors(
                n_neighbors=min(semantic_prune, self.N),
                metric='cosine',
                n_jobs=n_jobs
            )
            self.nn.fit(self.embeddings)
            self.semantic_prune = min(semantic_prune, self.N)
            self.semantic_enabled = True
            logger.info("Built sklearn KNN index on %d vectors", self.N)
        elif use_semantic_search:
            logger.warning("Requested semantic search but no embeddings found; disabled.")

        # thread pool for scoring
        self.pool = ThreadPoolExecutor(max_workers=n_jobs)

    def match(
        self,
        entity_term: str,
        entity_term_embedding: Optional[np.ndarray] = None,
        top_k: int = 5,
        threshold: float = 0.0,
        field_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Match an entity term against the canonical entities.

        Args:
            entity_term (str): The entity term to match
            entity_term_embedding (Optional[np.ndarray]): Pre-computed embedding for the entity term
            top_k (int): Number of top matches to return
            threshold (float): Minimum score threshold for matches
            field_filter (Optional[List[str]]): List of fields to include in results

        Returns:
            List[Dict[str, Any]]: List of match results with scores and metadata
        """
        # Normalize the entity term
        q = entity_term.strip().lower()
        
        # Compute embedding if needed
        if self.semantic_enabled and entity_term_embedding is None:
            entity_term_embedding = self.embed(entity_term)
        
        # prepare normalized entity term embedding
        q_emb = None
        if self.semantic_enabled and entity_term_embedding is not None:
            q_emb = entity_term_embedding.astype(np.float32)
            q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-12)

        # semantic prune first
        if self.semantic_enabled and q_emb is not None:
            _, nbrs = self.nn.kneighbors(q_emb.reshape(1, -1), return_distance=True)
            cand = list(nbrs[0])
        else:
            cand = list(range(self.N))

        # apply field filter if provided
        if field_filter:
            cand = [i for i in cand if self.metadata[i].get('_field_name_') in field_filter]

        # score and rank
        return self._score_and_rank(cand, q, q_emb, threshold, top_k)

    def _score_and_rank(
        self,
        idxs: List[int],
        q: str,
        q_emb: Optional[np.ndarray],
        threshold: float,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        sem_scores = None
        if self.semantic_enabled and q_emb is not None:
            mat = self.embeddings[idxs]
            sem_scores = mat.dot(q_emb) * 100

        futures = []
        results = []

        def _score(i, sem_val):
            ent = self.entities[i]
            sc = {
                'semantic': sem_val or 0.0,
                'fuzzy': fuzz.token_set_ratio(q, ent),
                'phonetic': 100 if doublemetaphone(q)[0] == self.phonetics[i] else 0,
                'initial': 100 if ''.join(w[0] for w in q.split()) == ''.join(w[0] for w in ent.split()) else 0,
                'keyword': 100 if q == ent.lower().strip() else 0,
            }
            # compute weighted total
            total = sum(sc[k] * self.weights[k] for k in sc)
            # reintroduce cross-metric bonuses from old logic
            if sc['semantic'] > 80 and sc['fuzzy'] > 80:
                total += 10
            if sc['fuzzy'] > 90 and sc['semantic'] < 60:
                total -= 15
            if sc['initial'] == 100:
                total += 10
            if sc['phonetic'] == 100:
                total += 5
            total = min(total, 100)

            passes = sum(1 for v in sc.values() if v >= threshold)
            return {
                'entity': ent,
                'score': total,
                'passes': passes,
                'metadata': self.metadata[i],
            }

        for idx, i in enumerate(idxs):
            sem_val = sem_scores[idx] if sem_scores is not None else 0.0
            futures.append(self.pool.submit(_score, i, sem_val))
        for f in futures:
            results.append(f.result())

        # apply pass-based filtering and top_k
        filtered = [r for r in results if r['passes'] > 0] or results
        filtered.sort(key=lambda r: (-r['passes'], -r['score']))
        return filtered[:top_k]
