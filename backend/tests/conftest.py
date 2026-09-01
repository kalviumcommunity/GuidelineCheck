"""Shared pytest fixtures.

Tests use a deterministic, lightweight bag-of-words embedding function instead
of downloading the real BAAI/bge-small-en-v1.5 model, so the suite runs fully
offline and fast while still exercising real ChromaDB persistence/query logic.
"""
from __future__ import annotations

import hashlib
import math
import re
import shutil
import tempfile
from pathlib import Path

import pytest
from chromadb import EmbeddingFunction

REPO_ROOT = Path(__file__).resolve().parents[2]

# Common domain-filler words that appear across almost every synthetic
# document. Downweighting them keeps the deterministic fake embedding from
# reporting high similarity for genuinely unrelated queries (e.g. a question
# about "Mars" would otherwise share generic words like "outbreak"/"guidance"
# with every real document).
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "is", "are", "was",
    "be", "must", "should", "will", "may", "with", "that", "this", "these",
    "those", "as", "at", "by", "on", "it", "its", "if", "not", "no", "do",
    "does", "did", "than", "then", "into", "such", "under",
    "fictional", "guidelinecheck", "health", "authority",
    "synthetic", "document", "documents", "operating", "operational",
    "what", "which", "who", "when", "where", "how", "exists", "exist",
    "show", "me", "there", "any",
    # These two appear in almost every synthetic document regardless of
    # topic, so they carry little discriminating signal for this small toy
    # corpus and are filtered to avoid false-positive matches on off-topic
    # queries (e.g. "outbreak on Mars").
    "outbreak", "response",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


class DeterministicFakeEmbeddingFunction(EmbeddingFunction):
    """A tiny, deterministic embedding function with real semantic signal.

    Uses hashed bag-of-words so that texts sharing vocabulary end up with
    higher cosine similarity than unrelated texts -- good enough to validate
    ranking/reranking logic without network access or heavy ML dependencies.
    Subclasses chromadb's EmbeddingFunction so it gets a working default
    `embed_query` (which just calls `__call__`) for free.
    """

    DIM = 4096

    def __init__(self) -> None:  # override to avoid the base-class deprecation warning
        pass

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        # Binary bag-of-words (unique tokens only) rather than raw counts, so
        # a long chunk doesn't dilute a single shared distinctive term's
        # contribution the way pure term-frequency counting would. This is a
        # crude stand-in for real dense sentence embeddings, which capture
        # semantic meaning holistically rather than diluting by document
        # length.
        vec = [0.0] * self.DIM
        for token in set(_tokenize(text)):
            idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.DIM
            vec[idx] = 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def name() -> str:
        return "deterministic-fake-embedding"

    @staticmethod
    def get_config() -> dict:
        return {"dim": DeterministicFakeEmbeddingFunction.DIM}

    @staticmethod
    def build_from_config(config: dict) -> "DeterministicFakeEmbeddingFunction":
        return DeterministicFakeEmbeddingFunction()


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch, tmp_path):
    """Point every test at an isolated temp Chroma dir and the fake embedder.

    Settings are pydantic-settings driven from environment variables, so we set
    env vars (picked up by every fresh `Settings()` construction) rather than
    trying to monkeypatch already-imported `get_settings` references.
    """
    from app.repositories import vector_store as vs_module
    from app.core.config import get_settings

    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()

    # Reset singletons between tests.
    vs_module._client_singleton = None
    vs_module._embedding_fn_singleton = None

    monkeypatch.setattr(
        vs_module, "_get_embedding_function", lambda settings: DeterministicFakeEmbeddingFunction()
    )

    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(chroma_dir))
    monkeypatch.setenv("DOCUMENTS_DIR", str(REPO_ROOT / "data" / "documents"))
    monkeypatch.setenv("CHROMA_COLLECTION_NAME", "test_collection")
    monkeypatch.setenv("LLM_PROVIDER", "none")
    # The lightweight deterministic fake embedding function used in tests
    # produces systematically lower raw cosine scores than a real dense
    # sentence embedding model would for genuinely relevant matches (it has
    # no semantic understanding, only literal token overlap), so tests use a
    # lower sufficiency bar calibrated to this fixture instead of production's
    # default of 0.30.
    monkeypatch.setenv("MIN_SUFFICIENT_SIMILARITY", "0.20")

    get_settings.cache_clear()
    test_settings = get_settings()

    # api.deps caches a VectorStoreRepository via lru_cache; clear it too so
    # each test gets a repo bound to its own temp Chroma directory.
    try:
        from app.api import deps as deps_module

        deps_module.get_vector_store_repo.cache_clear()
    except Exception:  # noqa: BLE001 - deps module may not be imported yet
        pass

    yield test_settings

    get_settings.cache_clear()
    try:
        from app.api import deps as deps_module

        deps_module.get_vector_store_repo.cache_clear()
    except Exception:  # noqa: BLE001
        pass
    vs_module._client_singleton = None
    vs_module._embedding_fn_singleton = None


@pytest.fixture
def settings(_isolated_settings):
    return _isolated_settings
