"""Ingestion service: discover -> load -> validate -> chunk -> embed -> persist."""
from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import Settings, get_settings
from app.models.document import DocumentChunk, DocumentMetadata
from app.repositories.vector_store import VectorStoreRepository
from app.schemas.system import IngestSummary
from app.utils.chunking import chunk_document_text, stable_chunk_id
from app.utils.document_loader import (
    DocumentLoadError,
    build_document_metadata,
    discover_documents,
    load_raw_text,
)

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, settings: Settings | None = None, repo: VectorStoreRepository | None = None):
        self.settings = settings or get_settings()
        self.repo = repo or VectorStoreRepository(self.settings)

    def _build_chunks_for_document(self, metadata: DocumentMetadata, text: str) -> list[DocumentChunk]:
        raw_chunks = chunk_document_text(
            text,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        chunks = []
        for raw in raw_chunks:
            chunk_id = stable_chunk_id(metadata.document_id, raw.chunk_index, raw.text)
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=metadata.document_id,
                    text=raw.text,
                    section=raw.section,
                    chunk_index=raw.chunk_index,
                    metadata=metadata,
                )
            )
        return chunks

    def run(self, reset: bool = False) -> IngestSummary:
        warnings: list[str] = []
        errors: list[str] = []

        if reset:
            logger.info("Resetting vector store collection as requested")
            self.repo.reset_collection()
        else:
            self.repo.get_or_create_collection()

        documents_dir = Path(self.settings.documents_dir)
        source_paths = discover_documents(documents_dir)

        existing_document_ids = self.repo.existing_document_ids()
        existing_chunk_ids = self.repo.existing_chunk_ids()

        documents_ingested = 0
        documents_skipped = 0
        documents_failed = 0
        total_chunks_created = 0
        seen_document_ids: set[str] = set()

        for path in source_paths:
            try:
                metadata = build_document_metadata(path)
            except DocumentLoadError as exc:
                errors.append(str(exc))
                documents_failed += 1
                continue

            if metadata.document_id in seen_document_ids:
                warnings.append(
                    f"Duplicate document_id '{metadata.document_id}' encountered in source "
                    f"directory (file: {path.name}); skipping second occurrence."
                )
                documents_skipped += 1
                continue
            seen_document_ids.add(metadata.document_id)

            if not reset and metadata.document_id in existing_document_ids:
                logger.info("Skipping already-ingested document: %s", metadata.document_id)
                documents_skipped += 1
                continue

            try:
                text = load_raw_text(path)
            except DocumentLoadError as exc:
                errors.append(str(exc))
                documents_failed += 1
                continue

            if not text.strip():
                warnings.append(f"Document '{path.name}' produced no extractable text; skipped.")
                documents_failed += 1
                continue

            chunks = self._build_chunks_for_document(metadata, text)
            if not chunks:
                warnings.append(f"Document '{path.name}' produced zero chunks; skipped.")
                documents_failed += 1
                continue

            new_ids, new_docs, new_metas = [], [], []
            for chunk in chunks:
                if chunk.chunk_id in existing_chunk_ids:
                    continue
                new_ids.append(chunk.chunk_id)
                new_docs.append(chunk.text)
                new_metas.append(chunk.to_chroma_metadata())
                existing_chunk_ids.add(chunk.chunk_id)

            if new_ids:
                self.repo.add_chunks(new_ids, new_docs, new_metas)
                total_chunks_created += len(new_ids)

            documents_ingested += 1
            logger.info(
                "Ingested document '%s' (%s): %d chunks",
                metadata.title, metadata.document_id, len(new_ids),
            )

        summary = IngestSummary(
            documents_scanned=len(source_paths),
            documents_ingested=documents_ingested,
            documents_skipped_duplicate=documents_skipped,
            documents_failed=documents_failed,
            chunks_created=total_chunks_created,
            reset_performed=reset,
            warnings=warnings,
            errors=errors,
        )
        logger.info("Ingestion summary: %s", summary.model_dump())
        return summary
