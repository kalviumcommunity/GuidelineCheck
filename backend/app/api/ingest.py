from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_ingestion_service
from app.schemas.system import IngestRequest, IngestSummary
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ingestion"])


@router.post("/ingest", response_model=IngestSummary)
def ingest(
    request: IngestRequest | None = None,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestSummary:
    """Trigger ingestion of the synthetic document corpus (development/demo use)."""
    reset = request.reset if request else False
    try:
        return service.run(reset=reset)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc
