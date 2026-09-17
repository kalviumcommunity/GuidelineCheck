"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root (GuidelineCheck/) — three levels up from this file
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Central application settings.

    All values can be overridden through environment variables or a `.env`
    file placed at the repository root. Nothing here should ever contain a
    hard-coded secret.
    """

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- General ---
    app_name: str = "GuidelineCheck"
    app_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # --- CORS ---
    cors_allow_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    # --- Storage paths ---
    documents_dir: str = str(REPO_ROOT / "data" / "documents")
    chroma_persist_dir: str = str(REPO_ROOT / "storage" / "chroma")
    chroma_collection_name: str = "guidelinecheck_chunks"

    # --- Embeddings ---
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"

    # --- Chunking ---
    chunk_size: int = 900
    chunk_overlap: int = 130

    # --- Retrieval ---
    default_top_k: int = 6
    max_top_k: int = 20
    min_sufficient_similarity: float = 0.30
    # Temporary demo behavior: answer broad non-patient-specific prompts with
    # the closest indexed context instead of abstaining on a low score.
    allow_broad_answers: bool = True

    # --- LLM provider (optional) ---
    # If llm_provider is "none" or no api key is configured, the app runs in
    # deterministic extractive fallback mode automatically.
    llm_provider: Literal["none", "anthropic", "openai"] = "none"
    llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()
