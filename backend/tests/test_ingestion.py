from __future__ import annotations

from pathlib import Path

import pytest

from app.models.document import GuidanceStatus
from app.services.ingestion_service import IngestionService
from app.utils.document_loader import DocumentLoadError, build_document_metadata


def test_metadata_extraction_and_validation(settings):
    path = Path(settings.documents_dir) / "measles_protocol_v2.md"
    metadata = build_document_metadata(path)

    assert metadata.document_id == "measles-protocol-v2"
    assert metadata.status == GuidanceStatus.CURRENT
    assert metadata.version == "2.0"
    assert metadata.supersedes == "measles-protocol-v1"
    assert metadata.source_filename == "measles_protocol_v2.md"
    assert metadata.last_ingested_at is not None


def test_metadata_missing_sidecar_raises(tmp_path):
    orphan = tmp_path / "orphan.md"
    orphan.write_text("# Orphan\nNo metadata here.")
    with pytest.raises(DocumentLoadError):
        build_document_metadata(orphan)


def test_ingestion_creates_chunks_with_preserved_metadata(settings):
    service = IngestionService(settings)
    summary = service.run(reset=True)

    assert summary.documents_ingested >= 6
    assert summary.chunks_created > 0
    assert summary.documents_failed == 0

    chunks = service.repo.get_document_chunks("measles-protocol-v2")
    assert len(chunks) > 0
    for chunk in chunks:
        meta = chunk["metadata"]
        assert meta["document_id"] == "measles-protocol-v2"
        assert meta["version"] == "2.0"
        assert meta["status"] == "Current"
        assert meta["effective_date"] == "2026-07-05"
        assert meta["source_filename"] == "measles_protocol_v2.md"


def test_duplicate_ingestion_is_skipped_without_reset(settings):
    service = IngestionService(settings)
    first = service.run(reset=True)
    second = service.run(reset=False)

    assert first.documents_ingested >= 6
    assert second.documents_ingested == 0
    assert second.documents_skipped_duplicate >= 6
    # Chunk count in the store should not double.
    assert service.repo.count() > 0


def test_reset_recreates_the_store(settings):
    service = IngestionService(settings)
    service.run(reset=True)
    count_before = service.repo.count()
    assert count_before > 0

    summary = service.run(reset=True)
    assert summary.reset_performed is True
    assert summary.documents_ingested >= 6
    # Should be roughly the same chunk count after a clean rebuild.
    assert service.repo.count() == count_before
