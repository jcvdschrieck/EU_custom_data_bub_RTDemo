"""Thin wrapper around sentence-transformers for text embedding."""
from __future__ import annotations
import os
from functools import lru_cache

# Force Hugging Face Hub into offline mode before any sentence-transformers
# / transformers import. sentence-transformers >= 5 calls HF Hub on every
# SentenceTransformer() init to check for adapter configs, and
# huggingface_hub >= 1.7 has a bug where an httpx client is closed before
# a retry fires — raising "Cannot send a request, as the client has been
# closed" intermittently, especially from short-lived subprocesses. The
# model is cached locally on first install (installer warms the cache),
# so offline mode is safe and sidesteps the upstream bug for every caller
# of this module — not just the agent subprocess entry point.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL_NAME = "all-MiniLM-L6-v2"

@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)

def embed(texts: list[str]) -> list[list[float]]:
    """Return a list of 384-dim embedding vectors for *texts*."""
    model = _get_model()
    return model.encode(texts, show_progress_bar=False).tolist()

def embed_one(text: str) -> list[float]:
    return embed([text])[0]
