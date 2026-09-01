"""Service for listing and inspecting indexed documents (aggregated from chunk metadata)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.core.config import Settings, get_settings
from app.repositories.vector_store import VectorStoreRepository
from app.schemas.documents import DocumentDetail, DocumentSummary, TopicsResponse


class DocumentService:
    def __init__(self, settings: Settings | None = None, repo: VectorStoreRepository | None = None):
        self.settings = settings or get_settings()
        self.repo = repo or VectorStoreRepository(self.settings)

    def _aggregate(self) -> dict[str, dict]:
        metadatas = self.repo.get_all_metadatas()
        by_doc: dict[str, dict] = {}
        for m in metadatas:
            doc_id = m.get("document_id")
            if doc_id not in by_doc:
                by_doc[doc_id] = {**m, "chunk_count": 0, "sections": set()}
            by_doc[doc_id]["chunk_count"] += 1
            if m.get("section"):
                by_doc[doc_id]["sections"].add(m["section"])
        return by_doc

    def _superseded_by_map(self, by_doc: dict[str, dict]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for doc_id, m in by_doc.items():
            supersedes = m.get("supersedes")
            if supersedes:
                mapping[supersedes] = doc_id
        return mapping

    def list_documents(
        self,
        topic: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        region: str | None = None,
    ) -> list[DocumentSummary]:
        by_doc = self._aggregate()
        superseded_by = self._superseded_by_map(by_doc)

        summaries = []
        for doc_id, m in by_doc.items():
            if topic and m.get("topic") != topic:
                continue
            if status and m.get("status") != status:
                continue
            if document_type and m.get("document_type") != document_type:
                continue
            if region and m.get("region") != region:
                continue

            summaries.append(
                DocumentSummary(
                    document_id=doc_id,
                    title=m.get("title"),
                    topic=m.get("topic"),
                    document_type=m.get("document_type"),
                    version=m.get("version"),
                    publication_date=m.get("publication_date"),
                    effective_date=m.get("effective_date"),
                    status=m.get("status"),
                    supersedes=m.get("supersedes") or None,
                    superseded_by=superseded_by.get(doc_id),
                    region=m.get("region"),
                    source_filename=m.get("source_filename"),
                    source_url=m.get("source_url") or None,
                    chunk_count=m.get("chunk_count", 0),
                    last_ingested_at=self._safe_parse_dt(m.get("last_ingested_at")),
                )
            )
        summaries.sort(key=lambda s: (s.topic, s.title, s.version))
        return summaries

    def get_document(self, document_id: str) -> DocumentDetail | None:
        by_doc = self._aggregate()
        superseded_by = self._superseded_by_map(by_doc)
        m = by_doc.get(document_id)
        if not m:
            return None
        return DocumentDetail(
            document_id=document_id,
            title=m.get("title"),
            topic=m.get("topic"),
            document_type=m.get("document_type"),
            version=m.get("version"),
            publication_date=m.get("publication_date"),
            effective_date=m.get("effective_date"),
            status=m.get("status"),
            supersedes=m.get("supersedes") or None,
            superseded_by=superseded_by.get(document_id),
            region=m.get("region"),
            source_filename=m.get("source_filename"),
            source_url=m.get("source_url") or None,
            chunk_count=m.get("chunk_count", 0),
            last_ingested_at=self._safe_parse_dt(m.get("last_ingested_at")),
            chunk_sections=sorted(m.get("sections", set())),
        )

    def get_topics_response(self) -> TopicsResponse:
        by_doc = self._aggregate()
        topics = sorted({m.get("topic") for m in by_doc.values() if m.get("topic")})
        document_types = sorted({m.get("document_type") for m in by_doc.values() if m.get("document_type")})
        regions = sorted({m.get("region") for m in by_doc.values() if m.get("region")})
        statuses = sorted({m.get("status") for m in by_doc.values() if m.get("status")})
        return TopicsResponse(
            topics=topics, document_types=document_types, regions=regions, statuses=statuses
        )

    @staticmethod
    def _safe_parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
