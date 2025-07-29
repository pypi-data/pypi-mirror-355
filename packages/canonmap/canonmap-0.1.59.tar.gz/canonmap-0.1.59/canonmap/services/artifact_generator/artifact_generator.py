# File: canonmap/services/artifact_generator/artifact_generator.py

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import json
import numpy as np
import torch
import logging

from canonmap.utils.get_cpu_count import get_cpu_count
from canonmap.services.artifact_generator._from_csv_helper import convert_csv_to_df
from canonmap.services.artifact_generator._run_pipeline import run_artifact_generation_pipeline

# module-level preload of spaCy and transformer models
from canonmap.utils.load_spacy_model import load_spacy_model
from transformers import AutoTokenizer, AutoModel

_spacy_nlp = load_spacy_model()
_EMB_MODEL_NAME = "intfloat/e5-base-v2"
_device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)
_tokenizer = AutoTokenizer.from_pretrained(_EMB_MODEL_NAME)
_embed_model = AutoModel.from_pretrained(_EMB_MODEL_NAME).to(_device)
_embed_model.eval()

# Set logging level based on verbose flag
logger = logging.getLogger(__name__)

class ArtifactGenerator:
    def __init__(
        self,
        nlp: Optional[Any] = None,
        batch_size: int = 64,
        verbose: bool = False,
    ):
        self.num_cores = get_cpu_count()
        # reuse the preloaded spaCy NLP
        self.nlp = nlp or _spacy_nlp
        # reuse the preloaded transformer
        self.tokenizer = _tokenizer
        self.embed_model = _embed_model
        self.device = _device
        self.batch_size = batch_size
        
        # Set logging level based on verbose flag
        logger.setLevel(logging.DEBUG if verbose else logging.WARNING)

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        all_embs = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                out = self.embed_model(**inputs)
            cls_emb = out.last_hidden_state[:, 0, :].cpu().numpy()
            all_embs.append(cls_emb)
        return np.vstack(all_embs)

    def generate_artifacts_from_csv(
        self,
        csv_path: str,
        output_path: Union[str, Path],
        name: str,
        entity_fields: Optional[List[str]] = None,
        use_other_fields_as_metadata: bool = False,
        num_rows: Optional[int] = None,
        return_schema: bool = False,
        return_embeddings: bool = False,
        return_processed_data: bool = False,
        unload: bool = False,
    ) -> Dict[str, Any]:
        # run existing pipeline for metadata & schema
        df = convert_csv_to_df(csv_path=csv_path, num_rows=num_rows)
        result = run_artifact_generation_pipeline(
            num_cores=self.num_cores,
            df=df,
            output_path=output_path,
            name=name,
            entity_fields=entity_fields,
            use_other_fields_as_metadata=use_other_fields_as_metadata,
            nlp=self.nlp,
            return_schema=return_schema,
            return_processed_data=return_processed_data,
            unload=unload,
        )
        
        # rename metadata to canonical_entities in the result
        result["canonical_entities"] = result.pop("metadata")
        
        # optionally compute and save embeddings
        if return_embeddings:
            canonical_entities = result["canonical_entities"]
            flat = [{m["_field_name_"]: m["_canonical_entity_"]} for m in canonical_entities]
            texts = [json.dumps(r, default=str) for r in flat]
            embeddings = self._embed_texts(texts)
            result["embeddings"] = embeddings
            
            # save embeddings to disk
            embeddings_path = Path(output_path) / f"{name}_canonical_entity_embeddings.npz"
            np.savez_compressed(embeddings_path, embeddings=embeddings)
        
        # remove paths from result
        result.pop("paths", None)
        
        return result