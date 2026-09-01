"""Retrieval service implementing metadata-aware, current-guidance-prioritized search."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date

from app.core.config import Settings, get_settings
from app.models.document import STATUS_PRIORITY, GuidanceStatus
from app.repositories.vector_store import VectorStoreRepository

logger = logging.getLogger(__name__)

# Keywords that signal the user is explicitly asking about historical/older/superseded
# guidance, in which case superseded/historical material should be surfaced rather
# than filtered out.
_HISTORICAL_QUERY_PATTERN = re.compile(
    r"\b(historical|history|previous|prior|old|older|superseded|supersede|"
    r"version 1|v1\.0|earlier|past|what changed|version history|used to)\b",
    re.IGNORECASE,
)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: dict
    similarity_score: float  # 0..1, higher is better
    status_score: float
    recency_score: float
    topic_boost: float
    final_score: float
    explanation: str = ""


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    candidates_considered: int = 0
    used_historical_override: bool = False


def _distance_to_similarity(distance: float) -> float:
    """Convert Chroma cosine distance to a similarity score in [0, 1].

    Chroma's "cosine" space reports distance = 1 - cosine_similarity, so
    cosine_similarity = 1 - distance. We clamp to [0, 1] since embeddings for
    genuinely unrelated text can occasionally yield a small negative cosine
    similarity, which we treat the same as "no similarity" for ranking and
    abstention purposes.
    """
    similarity = 1.0 - distance
    return max(0.0, min(1.0, similarity))


def query_signals_historical_intent(question: str) -> bool:
    return bool(_HISTORICAL_QUERY_PATTERN.search(question))


class RetrievalService:
    def __init__(self, settings: Settings | None = None, repo: VectorStoreRepository | None = None):
        self.settings = settings or get_settings()
        self.repo = repo or VectorStoreRepository(self.settings)

    def _build_where_clause(
        self,
        topic: str | None,
        document_type: str | None,
        region: str | None,
        status: str | None,
    ) -> dict | None:
        clauses = []
        if topic:
            clauses.append({"topic": topic})
        if document_type:
            clauses.append({"document_type": document_type})
        if region:
            clauses.append({"region": region})
        if status:
            clauses.append({"status": status})
        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    def retrieve_guidance(
        self,
        question: str,
        topic: str | None = None,
        document_type: str | None = None,
        region: str | None = None,
        status: str | None = None,
        include_historical: bool = False,
        top_k: int = 6,
    ) -> RetrievalResult:
        """Retrieve and rerank chunks, prioritizing Current guidance.

        Scoring = semantic similarity + status priority + recency + topic boost,
        unless the query explicitly signals historical intent, in which case
        superseded/historical material is allowed to surface.
        """
        historical_intent = query_signals_historical_intent(question)
        allow_historical = include_historical or historical_intent

        where = self._build_where_clause(topic, document_type, region, status)

        # Over-fetch candidates so reranking has real signal to work with.
        candidate_n = max(top_k * 4, 20)
        raw = self.repo.query(question, n_results=candidate_n, where=where)

        ids = raw.get("ids", [[]])[0]
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        candidates: list[RetrievedChunk] = []
        for cid, doc, meta, dist in zip(ids, documents, metadatas, distances):
            status_value = meta.get("status", GuidanceStatus.HISTORICAL.value)
            try:
                status_enum = GuidanceStatus(status_value)
            except ValueError:
                status_enum = GuidanceStatus.HISTORICAL

            if not allow_historical and status_enum in (
                GuidanceStatus.SUPERSEDED,
                GuidanceStatus.HISTORICAL,
            ):
                continue

            similarity = _distance_to_similarity(dist)
            status_priority = STATUS_PRIORITY.get(status_enum, 3)

            if historical_intent:
                # The user explicitly asked about historical/superseded/older
                # guidance (e.g. "show the historical protocol", "version 1.0",
                # "what changed"). Invert the priority so the specifically
                # requested older material is favored over unrelated current
                # material, rather than being buried by the default current-
                # guidance bias.
                if status_enum in (GuidanceStatus.SUPERSEDED, GuidanceStatus.HISTORICAL):
                    status_score = 1.0
                elif status_enum == GuidanceStatus.CURRENT:
                    status_score = 0.4
                else:
                    status_score = 0.5
            else:
                # Default behavior: Current=1.0 ... Historical=0.0
                status_score = 1.0 - (status_priority / 3.0)

            recency_score = self._recency_score(meta.get("effective_date"))

            topic_boost = 0.05 if topic and meta.get("topic") == topic else 0.0

            final_score = (
                0.55 * similarity
                + 0.25 * status_score
                + 0.15 * recency_score
                + topic_boost
            )

            explanation_parts = [f"semantic match {similarity:.2f}"]
            explanation_parts.append(f"status={status_enum.value}")
            if status_enum == GuidanceStatus.CURRENT:
                explanation_parts.append("prioritized as current guidance")
            elif status_enum in (GuidanceStatus.SUPERSEDED, GuidanceStatus.HISTORICAL):
                explanation_parts.append("shown due to historical/version-history request")

            candidates.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=meta.get("document_id", ""),
                    text=doc,
                    metadata=meta,
                    similarity_score=similarity,
                    status_score=status_score,
                    recency_score=recency_score,
                    topic_boost=topic_boost,
                    final_score=final_score,
                    explanation="; ".join(explanation_parts),
                )
            )

        candidates.sort(key=lambda c: c.final_score, reverse=True)

        # Prefer the most recent Current version per document "family" (by title)
        # so we don't show two current-labelled chunks of an outdated pairing.
        deduped = self._prefer_latest_current_per_title(candidates)

        top_chunks = deduped[:top_k]

        return RetrievalResult(
            chunks=top_chunks,
            candidates_considered=len(ids),
            used_historical_override=historical_intent and not include_historical,
        )

    @staticmethod
    def _recency_score(effective_date_str: str | None) -> float:
        if not effective_date_str:
            return 0.0
        try:
            eff = date.fromisoformat(effective_date_str)
        except ValueError:
            return 0.0
        today = date.today()
        days_old = max((today - eff).days, 0)
        # Decays over ~3 years; recent documents score near 1.0
        return max(0.0, 1.0 - (days_old / 1095))

    @staticmethod
    def _prefer_latest_current_per_title(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """If multiple Current-status chunks share a title (i.e. same guidance family),
        keep only chunks from the most-recently-effective version among Current results.
        Non-current statuses (shown intentionally for historical queries) are untouched.
        """
        best_current_effective: dict[str, str] = {}
        for c in chunks:
            if c.metadata.get("status") == GuidanceStatus.CURRENT.value:
                title = c.metadata.get("title", "")
                eff = c.metadata.get("effective_date", "")
                if title not in best_current_effective or eff > best_current_effective[title]:
                    best_current_effective[title] = eff

        result = []
        for c in chunks:
            if c.metadata.get("status") == GuidanceStatus.CURRENT.value:
                title = c.metadata.get("title", "")
                if c.metadata.get("effective_date", "") == best_current_effective.get(title):
                    result.append(c)
            else:
                result.append(c)
        return result
