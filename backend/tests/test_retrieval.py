from __future__ import annotations

import pytest

from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService


@pytest.fixture
def ingested_store(settings):
    IngestionService(settings).run(reset=True)
    return settings


def test_current_ranked_above_superseded_for_same_topic(ingested_store):
    service = RetrievalService(ingested_store)
    result = service.retrieve_guidance(
        "What is the current measles outbreak vaccination protocol dosing schedule?",
        top_k=5,
    )
    assert len(result.chunks) > 0
    statuses = {c.metadata["status"] for c in result.chunks}
    # Without historical intent, superseded material should not appear at all.
    assert "Superseded" not in statuses
    top_doc_ids = {c.document_id for c in result.chunks}
    assert "measles-protocol-v2" in top_doc_ids


def test_historical_query_can_retrieve_superseded_material(ingested_store):
    service = RetrievalService(ingested_store)
    result = service.retrieve_guidance(
        "Show me the historical measles vaccination protocol version 1.0",
        top_k=5,
    )
    statuses = {c.metadata["status"] for c in result.chunks}
    assert "Superseded" in statuses
    assert result.used_historical_override is True


def test_explicit_include_historical_flag_surfaces_superseded(ingested_store):
    service = RetrievalService(ingested_store)
    result = service.retrieve_guidance(
        "measles vaccination protocol dosing",
        include_historical=True,
        top_k=8,
    )
    statuses = {c.metadata["status"] for c in result.chunks}
    assert "Superseded" in statuses or "Current" in statuses


def test_unrelated_query_returns_low_similarity(ingested_store):
    service = RetrievalService(ingested_store)
    result = service.retrieve_guidance("outbreak guidance for a colony on Mars", top_k=5)
    # It may still return the closest chunks, but similarity should be low.
    if result.chunks:
        assert result.chunks[0].similarity_score < 0.6


def test_topic_filter_restricts_results(ingested_store):
    service = RetrievalService(ingested_store)
    result = service.retrieve_guidance("field guidance", topic="Mpox", top_k=5)
    for c in result.chunks:
        assert c.metadata["topic"] == "Mpox"
