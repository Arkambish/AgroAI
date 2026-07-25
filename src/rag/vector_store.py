"""ChromaDB vector store for AgriSense knowledge chunks."""

from __future__ import annotations

import os
from typing import Any

import chromadb

from rag.chunk_loader import Chunk
from rag.embedder import encode_texts

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_PERSIST_DIR = os.path.join(ROOT, 'data', 'rag', 'chroma')
COLLECTION_NAME = 'agrisense_knowledge'


class VectorStore:
    def __init__(self, persist_dir: str | None = None) -> None:
        self.persist_dir = persist_dir or DEFAULT_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={'hnsw:space': 'cosine'},
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    def index_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        embeddings = encode_texts(texts)
        self._collection.upsert(
            ids=[c.id for c in chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                {
                    'source_type': c.source_type,
                    'district': c.district or '',
                    'season': c.season or '',
                    'source_file': c.source_file or '',
                }
                for c in chunks
            ],
        )
        print(f'[rag] Indexed {len(chunks)} chunks into ChromaDB')

    def _build_where(self, district: str | None, season: str | None) -> dict[str, Any] | None:
        clauses: list[dict[str, Any]] = []
        if district:
            clauses.append({'district': {'$eq': district}})
        if season:
            clauses.append({'season': {'$eq': season}})
        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {'$and': clauses}

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        district: str | None = None,
        season: str | None = None,
    ) -> list[dict[str, Any]]:
        where = self._build_where(district, season)
        kwargs: dict[str, Any] = {
            'query_embeddings': [query_embedding],
            'n_results': top_k,
            'include': ['documents', 'metadatas', 'distances'],
        }
        if where is not None:
            kwargs['where'] = where

        try:
            results = self._collection.query(**kwargs)
        except Exception:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances'],
            )

        if not results['documents'] or not results['documents'][0]:
            if where is not None:
                return self.query(query_embedding, top_k=top_k)
            return []

        hits: list[dict[str, Any]] = []
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0],
        ):
            hits.append({
                'content': doc,
                'source_type': meta.get('source_type', 'UNKNOWN'),
                'district': meta.get('district', ''),
                'season': meta.get('season', ''),
                'source_file': meta.get('source_file', ''),
                'distance': dist,
            })
        return hits
