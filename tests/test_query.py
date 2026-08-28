from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_empty_question():
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]

def test_query_valid_question():
    # Note: Requires ingestion to have happened in the DB.
    # We assume test_ingestion ran first, or ChromaDB has persistence.
    response = client.post("/api/query", json={"question": "What is the guidance for Aurelia Fever?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data

def test_query_historical_guidance():
    # If the word 'historical' is in the query, it should return a 200
    response = client.post("/api/query", json={"question": "What is the historical guidance for Aurelia Fever?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
