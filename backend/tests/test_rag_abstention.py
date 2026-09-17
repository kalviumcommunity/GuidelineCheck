from __future__ import annotations

import pytest

from app.schemas.query import QueryRequest
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService


@pytest.fixture
def ingested_store(settings):
    IngestionService(settings).run(reset=True)
    return settings


def test_broad_mode_answers_out_of_corpus_question(ingested_store):
    service = RAGService(ingested_store)
    response = service.answer_query(QueryRequest(question="What guidance exists for an outbreak on Mars?"))
    assert response.is_abstention is False
    assert response.confidence_label.value == "Low"
    assert "best-effort" in response.answer_text.lower()
    assert response.citations


def test_abstains_on_patient_specific_question(ingested_store):
    service = RAGService(ingested_store)
    response = service.answer_query(
        QueryRequest(question="What should I prescribe for a patient with measles?")
    )
    assert response.is_abstention is True
    assert response.citations == []


def test_grounded_answer_for_current_measles_question(ingested_store):
    service = RAGService(ingested_store)
    response = service.answer_query(
        QueryRequest(question="What is the current measles outbreak vaccination protocol?")
    )
    assert response.is_abstention is False
    assert response.current_guidance_found is True
    assert response.generation_mode == "extractive_fallback"  # no LLM key configured in tests
    assert len(response.citations) > 0
    assert any(c.status.value == "Current" for c in response.citations)
    assert response.safety_notice


def test_broad_vaccine_news_question_gets_current_guidance(ingested_store):
    service = RAGService(ingested_store)
    response = service.answer_query(QueryRequest(question="What is the latest news and info about vaccine?"))
    assert response.is_abstention is False
    assert response.current_guidance_found is True
    assert len(response.citations) > 0


def test_extractive_fallback_marks_mode_and_still_cites(ingested_store):
    service = RAGService(ingested_store)
    assert service.llm_service.is_enabled is False
    response = service.answer_query(
        QueryRequest(question="What is the current mpox field guidance?")
    )
    assert response.generation_mode == "extractive_fallback"
    assert "extractive summary" in response.answer_text.lower()
    assert len(response.citations) > 0


def test_version_supersession_question_identifies_relationship(ingested_store):
    service = RAGService(ingested_store)
    response = service.answer_query(
        QueryRequest(question="Which document supersedes the previous measles protocol?")
    )
    assert response.is_abstention is False
    doc_ids = {c.document_id for c in response.citations}
    assert "measles-protocol-v2" in doc_ids or "measles-protocol-v1" in doc_ids


def test_citations_have_required_fields(ingested_store):
    service = RAGService(ingested_store)
    response = service.answer_query(
        QueryRequest(question="What is the current mpox field guidance?")
    )
    assert len(response.citations) > 0
    for c in response.citations:
        assert c.document_id
        assert c.title
        assert c.version
        assert c.status
        assert c.effective_date
        assert c.chunk_id
        assert c.relevance_explanation
