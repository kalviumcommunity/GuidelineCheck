"""Utilities for loading raw text and sidecar metadata from data/documents."""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.models.document import DocumentMetadata, GuidanceStatus

logger = logging.getLogger(__name__)

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


class DocumentLoadError(Exception):
    """Raised when a source document or its metadata cannot be loaded/validated."""


def load_raw_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8")
    if suffix in SUPPORTED_PDF_EXTENSIONS:
        return _load_pdf_text(path)
    raise DocumentLoadError(f"Unsupported file extension: {suffix}")


def _load_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise DocumentLoadError(
            "pypdf is required to read PDF documents. Install it via requirements.txt."
        ) from exc

    reader = PdfReader(str(path))
    pages_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(f"[page {i + 1}]\n{text}")
    return "\n\n".join(pages_text)


def load_metadata_sidecar(source_path: Path) -> dict:
    """Look for a `<stem>.json` sidecar file next to the source document."""
    sidecar_path = source_path.with_suffix(".json")
    if not sidecar_path.exists():
        raise DocumentLoadError(
            f"Missing required metadata sidecar file: {sidecar_path.name} for {source_path.name}"
        )
    try:
        return json.loads(sidecar_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DocumentLoadError(f"Invalid JSON in metadata sidecar {sidecar_path.name}: {exc}") from exc


def build_document_metadata(source_path: Path) -> DocumentMetadata:
    raw = load_metadata_sidecar(source_path)
    raw = dict(raw)  # copy
    raw["source_filename"] = source_path.name
    raw["last_ingested_at"] = datetime.now(timezone.utc)
    try:
        return DocumentMetadata(**raw)
    except ValidationError as exc:
        raise DocumentLoadError(
            f"Metadata validation failed for {source_path.name}: {exc}"
        ) from exc


def discover_documents(documents_dir: Path) -> list[Path]:
    """Return all supported source document paths (excluding .json sidecars)."""
    if not documents_dir.exists():
        return []
    exts = SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS
    return sorted(p for p in documents_dir.iterdir() if p.is_file() and p.suffix.lower() in exts)
