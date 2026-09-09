from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_version: str
    vector_store_ready: bool
    document_count: int
    chunk_count: int


class IngestRequest(BaseModel):
    reset: bool = False


class IngestSummary(BaseModel):
    documents_scanned: int
    documents_ingested: int
    documents_skipped_duplicate: int
    documents_failed: int
    chunks_created: int
    reset_performed: bool
    warnings: list[str] = []
    errors: list[str] = []


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
