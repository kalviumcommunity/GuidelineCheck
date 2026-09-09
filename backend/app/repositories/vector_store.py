"""Thin repository wrapper around a persistent ChromaDB collection.

Keeps all direct ChromaDB / embedding-function calls in one place so the rest
of the application only deals with plain Python data structures.
"""
from __future__ import annotations

import logging
import threading

import chromadb
from chromadb.utils import embedding_functions

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client_singleton: chromadb.ClientAPI | None = None
_embedding_fn_singleton = None


def _get_client(settings: Settings) -> chromadb.ClientAPI:
    global _client_singleton
    if _client_singleton is None:
        with _lock:
            if _client_singleton is None:
                _client_singleton = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client_singleton


def _get_embedding_function(settings: Settings):
    global _embedding_fn_singleton
    if _embedding_fn_singleton is None:
        with _lock:
            if _embedding_fn_singleton is None:
                logger.info("Loading embedding model: %s", settings.embedding_model_name)
                _embedding_fn_singleton = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.embedding_model_name
                )
    return _embedding_fn_singleton


class VectorStoreRepository:
    """CRUD + query operations against the persistent Chroma collection."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = _get_client(self.settings)
        self.embedding_fn = _get_embedding_function(self.settings)

    def get_or_create_collection(self):
        return self.client.get_or_create_collection(
            name=self.settings.chroma_collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def reset_collection(self):
        try:
            self.client.delete_collection(self.settings.chroma_collection_name)
        except Exception:  # noqa: BLE001 - fine if it doesn't exist yet
            pass
        return self.get_or_create_collection()

    def count(self) -> int:
        try:
            return self.get_or_create_collection().count()
        except Exception:  # noqa: BLE001
            return 0

    def existing_chunk_ids(self) -> set[str]:
        collection = self.get_or_create_collection()
        if collection.count() == 0:
            return set()
        result = collection.get(include=[])
        return set(result.get("ids", []))

    def existing_document_ids(self) -> set[str]:
        collection = self.get_or_create_collection()
        if collection.count() == 0:
            return set()
        result = collection.get(include=["metadatas"])
        return {m["document_id"] for m in result.get("metadatas", []) if m}

    def add_chunks(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        if not ids:
            return
        collection = self.get_or_create_collection()
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, query_text: str, n_results: int, where: dict | None = None):
        collection = self.get_or_create_collection()
        if collection.count() == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        return collection.query(
            query_texts=[query_text],
            n_results=min(n_results, max(collection.count(), 1)),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def get_all_metadatas(self) -> list[dict]:
        collection = self.get_or_create_collection()
        if collection.count() == 0:
            return []
        result = collection.get(include=["metadatas"])
        return result.get("metadatas", [])

    def get_document_chunks(self, document_id: str) -> list[dict]:
        collection = self.get_or_create_collection()
        if collection.count() == 0:
            return []
        result = collection.get(where={"document_id": document_id}, include=["metadatas", "documents"])
        chunks = []
        for i, cid in enumerate(result.get("ids", [])):
            chunks.append({
                "chunk_id": cid,
                "metadata": result["metadatas"][i],
                "text": result["documents"][i],
            })
        return chunks
