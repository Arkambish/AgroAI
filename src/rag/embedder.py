"""Sentence-transformer embeddings for RAG retrieval."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        print(f'[rag] Loading embedding model: {_MODEL_NAME}')
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def encode_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def encode_query(query: str) -> list[float]:
    return encode_texts([query])[0]
