from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.models.document import GuidanceStatus


class ConfidenceLabel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=6, ge=1, le=20)
    topic: str | None = None
    document_type: str | None = None
    region: str | None = None
    status: GuidanceStatus | None = None
    include_historical: bool = False


class Citation(BaseModel):
    document_id: str
    title: str
    document_type: str
    version: str
    status: GuidanceStatus
    effective_date: date
    section: str | None = None
    chunk_id: str
    source_url: str | None = None
    relevance_explanation: str


class RetrievalDiagnostics(BaseModel):
    candidates_considered: int
    candidates_returned: int
    top_similarity_score: float | None = None
    current_candidates_found: int
    superseded_or_historical_candidates_found: int
    used_historical_override: bool


class QueryResponse(BaseModel):
    question: str
    answer_text: str
    is_abstention: bool
    confidence_label: ConfidenceLabel
    retrieved_context_sufficient: bool
    current_guidance_found: bool
    generation_mode: Literal["llm", "extractive_fallback"]
    safety_notice: str
    citations: list[Citation]
    retrieval_diagnostics: RetrievalDiagnostics
