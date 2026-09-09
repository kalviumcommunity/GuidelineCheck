from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_rag_service
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    try:
        return service.answer_query(request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc
