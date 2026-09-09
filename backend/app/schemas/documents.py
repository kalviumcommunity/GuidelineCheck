from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.models.document import GuidanceStatus


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    topic: str
    document_type: str
    version: str
    publication_date: date
    effective_date: date
    status: GuidanceStatus
    supersedes: str | None = None
    superseded_by: str | None = None
    region: str
    source_filename: str
    source_url: str | None = None
    chunk_count: int
    last_ingested_at: datetime | None = None


class DocumentDetail(DocumentSummary):
    chunk_sections: list[str] = []


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]
    total: int


class TopicsResponse(BaseModel):
    topics: list[str]
    document_types: list[str]
    regions: list[str]
    statuses: list[str]
