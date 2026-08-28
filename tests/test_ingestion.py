from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_ingest_documents():
    payload = {
        "documents": [
            {
                "page_content": "This is a synthetic public health document regarding Aurelia Fever.",
                "metadata": {
                    "document_id": "doc-001",
                    "title": "Aurelia Fever Protocol",
                    "document_type": "Guideline",
                    "topic": "Aurelia Fever",
                    "version": "1.0",
                    "publication_date": "2024-01-01",
                    "effective_date": "2024-01-01",
                    "status": "Current",
                    "supersedes": None
                }
            }
        ]
    }
    
    response = client.post("/api/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Ingestion successful"
    assert data["chunks_stored"] >= 1
