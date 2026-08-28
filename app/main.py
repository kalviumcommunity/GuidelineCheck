from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.schemas import IngestRequest, QueryRequest, QueryResponse
from app.core.documents import process_and_ingest_documents
from app.core.rag import generate_rag_response
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GuidelineCheck Backend", description="RAG API for public health guidelines")

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/ingest")
def ingest_documents(request: IngestRequest):
    try:
        if not request.documents:
            raise HTTPException(status_code=400, detail="No documents provided for ingestion.")
        
        chunks_count = process_and_ingest_documents(request)
        return {"message": "Ingestion successful", "chunks_stored": chunks_count}
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
def query_guidelines(request: QueryRequest):
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")
            
        response = generate_rag_response(request)
        return response
    except Exception as e:
        logger.error(f"Error during query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
