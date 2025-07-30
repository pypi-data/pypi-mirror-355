# pr_agent/core/embedder.py

import numpy as np
from sentence_transformers import SentenceTransformer

#from pr_agent.settings import EMBEDDING_MODEL
from pr_agent.core.summarizer import extract_summary

from pr_agent.settings import settings

embed_model = settings.EMBEDDING_MODEL

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(embed_model)
    return _model

def generate_embedding(text: str) -> list[float]:
    """
    Generate a vector embedding for the summarized version of `text`.
    If `text` is empty or None, return an empty list. Otherwise:
      1. Run extract_summary(...) to get a shorter, context‐preserving summary.
      2. Pass that summary into the SentenceTransformer to obtain the embedding.
    """
    if not text:
        return []


    model = _get_model()
    vec = model.encode([text], show_progress_bar=False)[0]
    return vec.tolist()

def save_embedding(vector: list[float], doc_id: str, output_dir: str) -> str:
    """
    Save a numeric vector to disk as a .npy file. Create output_dir if needed.
    Returns the file path of the saved vector.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{doc_id}_emb.npy")
    np.save(path, np.array(vector))
    return path
