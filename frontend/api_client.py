"""Thin httpx-based client for the GuidelineCheck FastAPI backend."""
from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BACKEND_URL = os.environ.get("GUIDELINECHECK_API_URL", "http://localhost:8000")


class APIClientError(Exception):
    """Raised when the backend cannot be reached or returns an error."""


class GuidelineCheckAPIClient:
    def __init__(self, base_url: str = DEFAULT_BACKEND_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health(self) -> dict[str, Any]:
        try:
            resp = httpx.get(self._url("/health"), timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise APIClientError(f"Could not reach backend health endpoint: {exc}") from exc

    def is_backend_reachable(self) -> bool:
        try:
            self.health()
            return True
        except APIClientError:
            return False

    def ingest(self, reset: bool = False) -> dict[str, Any]:
        try:
            resp = httpx.post(
                self._url("/api/v1/ingest"), json={"reset": reset}, timeout=120.0
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise APIClientError(f"Ingestion request failed: {exc}") from exc

    def query(
        self,
        question: str,
        top_k: int = 6,
        topic: str | None = None,
        document_type: str | None = None,
        region: str | None = None,
        status: str | None = None,
        include_historical: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "question": question,
            "top_k": top_k,
            "topic": topic,
            "document_type": document_type,
            "region": region,
            "status": status,
            "include_historical": include_historical,
        }
        try:
            resp = httpx.post(self._url("/api/v1/query"), json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                detail = exc.response.json().get("detail", "")
            except Exception:  # noqa: BLE001
                pass
            raise APIClientError(f"Query failed: {detail or exc}") from exc
        except httpx.HTTPError as exc:
            raise APIClientError(f"Query request failed: {exc}") from exc

    def list_documents(
        self,
        topic: str | None = None,
        status: str | None = None,
        document_type: str | None = None,
        region: str | None = None,
    ) -> dict[str, Any]:
        params = {k: v for k, v in {
            "topic": topic, "status": status, "document_type": document_type, "region": region,
        }.items() if v}
        try:
            resp = httpx.get(self._url("/api/v1/documents"), params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise APIClientError(f"Could not list documents: {exc}") from exc

    def get_topics(self) -> dict[str, Any]:
        try:
            resp = httpx.get(self._url("/api/v1/topics"), timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise APIClientError(f"Could not fetch topics: {exc}") from exc
