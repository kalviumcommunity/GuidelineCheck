"""RAG orchestration: retrieval -> grounded generation (LLM or extractive fallback)."""
from __future__ import annotations

import logging
import re

from app.core.config import Settings, get_settings
from app.models.document import GuidanceStatus
from app.schemas.query import (
    Citation,
    ConfidenceLabel,
    QueryRequest,
    QueryResponse,
    RetrievalDiagnostics,
)
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService, RetrievedChunk

logger = logging.getLogger(__name__)

SAFETY_NOTICE = (
    "Educational demonstration using synthetic guidance only. Not for clinical, "
    "patient-specific, or real-world operational decisions."
)

ABSTENTION_MESSAGE = (
    "I could not find sufficient guidance in the available synthetic GuidelineCheck "
    "corpus to answer that question safely. Please consult the official public-health "
    "authority or response coordinator."
)

# Patient-specific / clinical-decision phrasing that should always trigger abstention,
# even if superficially related content exists in the corpus.
_UNSAFE_PATIENT_SPECIFIC_PATTERN = re.compile(
    r"\b(prescribe|prescription|dosage for my|diagnose|should i give (my|him|her)|"
    r"my (child|patient|son|daughter) has|treat my|what should i give)\b",
    re.IGNORECASE,
)

# Minimum semantic similarity below which retrieval is considered too weak to trust.
# Configurable via settings.min_sufficient_similarity (env: MIN_SUFFICIENT_SIMILARITY).
# The default of 0.30 is calibrated for real dense sentence embeddings
# (e.g. BAAI/bge-small-en-v1.5); test suites using lightweight fake embedding
# functions may configure a different value via the environment.


class RAGService:
    def __init__(
        self,
        settings: Settings | None = None,
        retrieval_service: RetrievalService | None = None,
        llm_service: LLMService | None = None,
    ):
        self.settings = settings or get_settings()
        self.retrieval_service = retrieval_service or RetrievalService(self.settings)
        self.llm_service = llm_service or LLMService(self.settings)

    def answer_query(self, request: QueryRequest) -> QueryResponse:
        if _UNSAFE_PATIENT_SPECIFIC_PATTERN.search(request.question):
            return self._abstain(
                request,
                candidates_considered=0,
                current_found=0,
                other_found=0,
                used_historical_override=False,
                reason=(
                    "This question asks for patient-specific medical advice, which "
                    "GuidelineCheck does not provide."
                ),
            )

        result = self.retrieval_service.retrieve_guidance(
            question=request.question,
            topic=request.topic,
            document_type=request.document_type,
            region=request.region,
            status=request.status.value if request.status else None,
            include_historical=request.include_historical,
            top_k=request.top_k,
        )

        current_found = sum(
            1 for c in result.chunks if c.metadata.get("status") == GuidanceStatus.CURRENT.value
        )
        other_found = len(result.chunks) - current_found
        top_similarity = result.chunks[0].similarity_score if result.chunks else None

        sufficient = bool(result.chunks) and (top_similarity or 0.0) >= self.settings.min_sufficient_similarity

        if not sufficient:
            return self._abstain(
                request,
                candidates_considered=result.candidates_considered,
                current_found=current_found,
                other_found=other_found,
                used_historical_override=result.used_historical_override,
            )

        # Try LLM generation; fall back to deterministic extractive summary.
        llm_result = None
        if self.llm_service.is_enabled:
            context_block = self._build_context_block(result.chunks)
            llm_result = self.llm_service.generate_structured_answer(request.question, context_block)

        if llm_result:
            answer_text = str(llm_result.get("answer_text", "")).strip() or ABSTENTION_MESSAGE
            is_abstention = bool(llm_result.get("is_abstention", False))
            confidence = self._safe_confidence(llm_result.get("confidence_label"))
            context_sufficient = bool(llm_result.get("retrieved_context_sufficient", True))
            current_guidance_found = bool(llm_result.get("current_guidance_found", current_found > 0))
            generation_mode = "llm"
        else:
            answer_text = self._extractive_answer(request.question, result.chunks, current_found > 0)
            is_abstention = False
            confidence = self._extractive_confidence(top_similarity, current_found)
            context_sufficient = True
            current_guidance_found = current_found > 0
            generation_mode = "extractive_fallback"

        citations = [self._to_citation(c) for c in result.chunks]

        return QueryResponse(
            question=request.question,
            answer_text=answer_text,
            is_abstention=is_abstention,
            confidence_label=confidence,
            retrieved_context_sufficient=context_sufficient,
            current_guidance_found=current_guidance_found,
            generation_mode=generation_mode,
            safety_notice=SAFETY_NOTICE,
            citations=citations,
            retrieval_diagnostics=RetrievalDiagnostics(
                candidates_considered=result.candidates_considered,
                candidates_returned=len(result.chunks),
                top_similarity_score=top_similarity,
                current_candidates_found=current_found,
                superseded_or_historical_candidates_found=other_found,
                used_historical_override=result.used_historical_override,
            ),
        )

    # -- helpers -----------------------------------------------------------------

    def _abstain(
        self,
        request: QueryRequest,
        candidates_considered: int,
        current_found: int,
        other_found: int,
        used_historical_override: bool,
        reason: str | None = None,
    ) -> QueryResponse:
        text = ABSTENTION_MESSAGE if not reason else f"{ABSTENTION_MESSAGE} ({reason})"
        return QueryResponse(
            question=request.question,
            answer_text=text,
            is_abstention=True,
            confidence_label=ConfidenceLabel.LOW,
            retrieved_context_sufficient=False,
            current_guidance_found=False,
            generation_mode="extractive_fallback",
            safety_notice=SAFETY_NOTICE,
            citations=[],
            retrieval_diagnostics=RetrievalDiagnostics(
                candidates_considered=candidates_considered,
                candidates_returned=0,
                top_similarity_score=None,
                current_candidates_found=current_found,
                superseded_or_historical_candidates_found=other_found,
                used_historical_override=used_historical_override,
            ),
        )

    @staticmethod
    def _build_context_block(chunks: list[RetrievedChunk]) -> str:
        blocks = []
        for i, c in enumerate(chunks, start=1):
            m = c.metadata
            blocks.append(
                f"[Chunk {i}] document_id={m.get('document_id')} title={m.get('title')} "
                f"version={m.get('version')} status={m.get('status')} "
                f"effective_date={m.get('effective_date')} section={m.get('section') or 'N/A'}\n"
                f"{c.text}"
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _extractive_answer(question: str, chunks: list[RetrievedChunk], has_current: bool) -> str:
        top = chunks[:3]
        lines = []
        prefix = "Extractive summary (no LLM configured) based on the top matching guidance:"
        lines.append(prefix)
        for c in top:
            m = c.metadata
            status_tag = f"[{m.get('status')}]"
            section = f" — {m.get('section')}" if m.get("section") else ""
            snippet = c.text.strip().replace("\n", " ")
            if len(snippet) > 400:
                snippet = snippet[:400].rsplit(" ", 1)[0] + "..."
            lines.append(
                f"\n\n{status_tag} {m.get('title')} (v{m.get('version')}){section}:\n{snippet}"
            )
        if not has_current:
            lines.append(
                "\n\nNote: no Current-status guidance matched this question; the material "
                "above is superseded/historical and is shown because it was explicitly "
                "requested or is the closest available match."
            )
        return "".join(lines)

    @staticmethod
    def _extractive_confidence(top_similarity: float | None, current_found: int) -> ConfidenceLabel:
        sim = top_similarity or 0.0
        if sim >= 0.55 and current_found > 0:
            return ConfidenceLabel.HIGH
        if sim >= 0.35:
            return ConfidenceLabel.MEDIUM
        return ConfidenceLabel.LOW

    @staticmethod
    def _safe_confidence(value: object) -> ConfidenceLabel:
        try:
            return ConfidenceLabel(value)
        except ValueError:
            return ConfidenceLabel.MEDIUM

    @staticmethod
    def _to_citation(chunk: RetrievedChunk) -> Citation:
        m = chunk.metadata
        return Citation(
            document_id=m.get("document_id", ""),
            title=m.get("title", ""),
            document_type=m.get("document_type", ""),
            version=m.get("version", ""),
            status=GuidanceStatus(m.get("status", GuidanceStatus.HISTORICAL.value)),
            effective_date=m.get("effective_date"),
            section=m.get("section") or None,
            chunk_id=chunk.chunk_id,
            source_url=m.get("source_url") or None,
            relevance_explanation=chunk.explanation,
        )
