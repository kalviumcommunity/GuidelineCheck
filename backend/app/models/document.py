"""Core domain models for GuidelineCheck documents and chunks."""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class GuidanceStatus(str, Enum):
    CURRENT = "Current"
    SUPERSEDED = "Superseded"
    HISTORICAL = "Historical"
    DRAFT = "Draft"


# Priority used for ranking: lower number = higher priority.
STATUS_PRIORITY: dict[GuidanceStatus, int] = {
    GuidanceStatus.CURRENT: 0,
    GuidanceStatus.DRAFT: 1,
    GuidanceStatus.SUPERSEDED: 2,
    GuidanceStatus.HISTORICAL: 3,
}


class DocumentMetadata(BaseModel):
    """Required and optional metadata that must be preserved for every document."""

    document_id: str
    title: str
    topic: str
    document_type: str
    version: str
    publication_date: date
    effective_date: date
    status: GuidanceStatus
    supersedes: str | None = None
    region: str = "National (Synthetic)"
    source_filename: str
    source_url: str | None = None
    last_ingested_at: datetime | None = None

    @field_validator("title", "topic", "document_type", "version", mode="before")
    @classmethod
    def _strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class DocumentChunk(BaseModel):
    """A single chunk of text with full inherited document metadata."""

    chunk_id: str
    document_id: str
    text: str
    section: str | None = None
    chunk_index: int
    metadata: DocumentMetadata

    def to_chroma_metadata(self) -> dict:
        """Flatten metadata into a Chroma-compatible (scalar-only) dict."""
        m = self.metadata
        return {
            "document_id": m.document_id,
            "title": m.title,
            "topic": m.topic,
            "document_type": m.document_type,
            "version": m.version,
            "publication_date": m.publication_date.isoformat(),
            "effective_date": m.effective_date.isoformat(),
            "status": m.status.value,
            "supersedes": m.supersedes or "",
            "region": m.region,
            "source_filename": m.source_filename,
            "source_url": m.source_url or "",
            "last_ingested_at": (m.last_ingested_at or datetime.now(timezone.utc)).isoformat(),
            "section": self.section or "",
            "chunk_index": self.chunk_index,
        }
