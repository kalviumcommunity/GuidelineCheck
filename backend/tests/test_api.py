from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(settings):
    # Import app AFTER the isolated settings fixture has set env vars, so the
    # dependency-injected services in app.api.deps pick up the test settings.
    from app.main import app

    return TestClient(app)


def test_health_endpoint_returns_ok_shape(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "app_version" in body
    assert "vector_store_ready" in body
    assert "document_count" in body
    assert "chunk_count" in body


def test_ingest_endpoint_returns_summary(client):
    response = client.post("/api/v1/ingest", json={"reset": True})
    assert response.status_code == 200
    body = response.json()
    assert body["documents_ingested"] >= 6
    assert body["reset_performed"] is True


def test_query_endpoint_schema_and_grounded_answer(client):
    client.post("/api/v1/ingest", json={"reset": True})
    response = client.post(
        "/api/v1/query",
        json={"question": "What is the current measles outbreak vaccination protocol?", "top_k": 5},
    )
    assert response.status_code == 200
    body = response.json()
    for key in [
        "question", "answer_text", "is_abstention", "confidence_label",
        "retrieved_context_sufficient", "current_guidance_found", "generation_mode",
        "safety_notice", "citations", "retrieval_diagnostics",
    ]:
        assert key in body
    assert body["is_abstention"] is False
    assert len(body["citations"]) > 0
    citation = body["citations"][0]
    for field in ["document_id", "title", "version", "status", "effective_date", "chunk_id", "relevance_explanation"]:
        assert field in citation


def test_query_endpoint_answers_broad_prompt_in_demo_mode(client):
    client.post("/api/v1/ingest", json={"reset": True})
    response = client.post(
        "/api/v1/query",
        json={"question": "What guidance exists for an outbreak on Mars?", "top_k": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_abstention"] is False
    assert body["confidence_label"] == "Low"
    assert "best-effort" in body["answer_text"].lower()


def test_documents_endpoint_lists_indexed_documents(client):
    client.post("/api/v1/ingest", json={"reset": True})
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 6
    doc_ids = {d["document_id"] for d in body["documents"]}
    assert "measles-protocol-v2" in doc_ids
    assert "measles-protocol-v1" in doc_ids


def test_document_detail_endpoint(client):
    client.post("/api/v1/ingest", json={"reset": True})
    response = client.get("/api/v1/documents/measles-protocol-v2")
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "measles-protocol-v2"
    assert body["supersedes"] == "measles-protocol-v1"


def test_document_detail_404_for_unknown_id(client):
    client.post("/api/v1/ingest", json={"reset": True})
    response = client.get("/api/v1/documents/does-not-exist")
    assert response.status_code == 404


def test_topics_endpoint(client):
    client.post("/api/v1/ingest", json={"reset": True})
    response = client.get("/api/v1/topics")
    assert response.status_code == 200
    body = response.json()
    assert "Measles" in body["topics"]
    assert "Mpox" in body["topics"]
