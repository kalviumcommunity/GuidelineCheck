"""Shared FastAPI dependency providers for clean service construction."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.repositories.vector_store import VectorStoreRepository
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService


@lru_cache
def get_vector_store_repo() -> VectorStoreRepository:
    return VectorStoreRepository(get_settings())


def get_ingestion_service() -> IngestionService:
    return IngestionService(get_settings(), get_vector_store_repo())


def get_retrieval_service() -> RetrievalService:
    return RetrievalService(get_settings(), get_vector_store_repo())


def get_llm_service() -> LLMService:
    return LLMService(get_settings())


def get_rag_service() -> RAGService:
    return RAGService(get_settings(), get_retrieval_service(), get_llm_service())


def get_document_service() -> DocumentService:
    return DocumentService(get_settings(), get_vector_store_repo())
