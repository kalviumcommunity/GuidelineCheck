from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_document_service
from app.schemas.documents import DocumentDetail, DocumentListResponse, TopicsResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    topic: str | None = Query(default=None),
    status: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    region: str | None = Query(default=None),
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    docs = service.list_documents(topic=topic, status=status, document_type=document_type, region=region)
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDetail:
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    return doc


@router.get("/topics", response_model=TopicsResponse)
def get_topics(service: DocumentService = Depends(get_document_service)) -> TopicsResponse:
    return service.get_topics_response()
