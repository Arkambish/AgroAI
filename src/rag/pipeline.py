"""RAG pipeline: index, retrieve, and generate grounded answers."""

from __future__ import annotations

import os
from typing import Any

from rag.chunk_loader import get_chunk_loader
from rag.embedder import encode_query
from rag.llm import AnthropicClient
from rag.vector_store import VectorStore

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RAGPipeline:
    def __init__(
        self,
        corpus: str | None = None,
        results_dir: str | None = None,
        top_k: int | None = None,
        force_reindex: bool | None = None,
    ) -> None:
        self.corpus = corpus or os.environ.get('RAG_CORPUS', 'placeholder')
        self.results_dir = results_dir or os.path.join(
            ROOT, 'outputs', 'results'
        )
        self.top_k = top_k or int(os.environ.get('RAG_TOP_K', '3'))
        self.force_reindex = force_reindex or (
            os.environ.get('RAG_FORCE_REINDEX', '').lower() == 'true'
        )
        self._store = VectorStore()
        self._llm = AnthropicClient()
        self._ensure_index()

    def _ensure_index(self) -> None:
        if self._store.count > 0 and not self.force_reindex:
            print(f'[rag] ChromaDB collection has {self._store.count} chunks — skipping reindex')
            return
        loader = get_chunk_loader(self.corpus, self.results_dir)
        chunks = loader.load()
        if not chunks:
            raise RuntimeError(f'No chunks loaded from corpus={self.corpus!r}')
        self._store.index_chunks(chunks)

    def query(
        self,
        question: str,
        district: str | None = None,
        season: str | None = None,
    ) -> dict[str, Any]:
        district = district.strip() if district else None
        season = season.strip() if season else None
        if district:
            district = district[0].upper() + district[1:].lower()
        if season:
            season = season[0].upper() + season[1:].lower()

        query_embedding = encode_query(question)
        hits = self._store.query(
            query_embedding,
            top_k=self.top_k,
            district=district,
            season=season,
        )

        answer = self._llm.generate(question, hits)
        sources = [
            {
                'source_type': hit['source_type'],
                'content': hit['content'],
            }
            for hit in hits
        ]
        return {'answer': answer, 'sources': sources}


_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        print('[rag] Initializing RAG pipeline (first request)...')
        _pipeline = RAGPipeline()
    return _pipeline
