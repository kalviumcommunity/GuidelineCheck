"""GuidelineCheck FastAPI application entrypoint.

Educational demonstration using synthetic guidance only. Not for clinical,
patient-specific, or real-world operational decisions.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import documents, health, ingest, query
from app.core.config import get_settings
from app.core.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="GuidelineCheck API",
    description=(
        "RAG-based public health guidance assistant. Educational demonstration using "
        "synthetic guidance only. Not for clinical, patient-specific, or real-world "
        "operational decisions."
    ),
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "An unexpected error occurred."},
    )


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs",
        "disclaimer": (
            "Educational demonstration using synthetic guidance only. Not for clinical, "
            "patient-specific, or real-world operational decisions."
        ),
    }
