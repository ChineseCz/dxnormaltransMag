"""Embedding service for local sentence-transformers models."""
import os
import asyncio
from typing import List

import numpy as np

# Prefer a domestic mirror when HF endpoint is not configured.
if not os.getenv("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


class EmbeddingService:
    """Generate text embeddings with local sentence-transformers."""

    def __init__(self):
        self._model = None
        self.model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
        self.dimension = 512
        self._available = None
        self._init_error = None

    def _lazy_init(self):
        """Lazy-load model to avoid startup I/O stalls."""
        if self._available is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            # sentence-transformers renamed this API in newer versions.
            if hasattr(self._model, "get_embedding_dimension"):
                self.dimension = self._model.get_embedding_dimension()
            else:
                self.dimension = self._model.get_sentence_embedding_dimension()
            self._available = True
            print(f"[Embedding] Local model loaded: {self.model_name} ({self.dimension} dim)")
        except Exception as e:
            self._model = None
            self._available = False
            self._init_error = str(e)
            print(f"[Embedding] Local model load failed: {e}")

    @property
    def available(self) -> bool:
        if self._available is None:
            self._lazy_init()
        return self._available or False

    async def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Batch embed text list."""
        if not texts:
            return []
        self._lazy_init()
        if self._model is None:
            msg = self._init_error or "Embedding model not loaded"
            raise RuntimeError(msg)

        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=False,
            ),
        )
        return vectors.tolist()

    async def embed_query(self, query: str) -> List[float]:
        vectors = await self.embed_texts([query])
        return vectors[0]

    def normalize(self, vectors: List[List[float]]) -> np.ndarray:
        """L2 normalize vectors for FAISS inner-product search."""
        arr = np.array(vectors, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms


embedding_service = EmbeddingService()
