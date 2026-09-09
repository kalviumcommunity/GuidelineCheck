from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_vector_store_repo
from app.core.config import get_settings
from app.repositories.vector_store import VectorStoreRepository
from app.schemas.system import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(repo: VectorStoreRepository = Depends(get_vector_store_repo)) -> HealthResponse:
    settings = get_settings()
    try:
        chunk_count = repo.count()
        document_count = len(repo.existing_document_ids())
        ready = True
    except Exception:  # noqa: BLE001
        chunk_count = 0
        document_count = 0
        ready = False

    return HealthResponse(
        status="ok" if ready else "degraded",
        app_version=settings.app_version,
        vector_store_ready=ready,
        document_count=document_count,
        chunk_count=chunk_count,
    )
