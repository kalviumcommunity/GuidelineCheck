"""Section-aware chunking built on LangChain's RecursiveCharacterTextSplitter."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")


@dataclass
class RawChunk:
    text: str
    section: str | None
    chunk_index: int


def _split_into_sections(text: str) -> list[tuple[str | None, str]]:
    """Split markdown-ish text into (heading, body) blocks based on `#` headings."""
    lines = text.splitlines()
    sections: list[tuple[str | None, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in lines:
        match = _HEADING_RE.match(line.strip())
        if match:
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    return [(heading, "\n".join(body).strip()) for heading, body in sections if "\n".join(body).strip()]


def chunk_document_text(
    text: str,
    chunk_size: int = 900,
    chunk_overlap: int = 130,
) -> list[RawChunk]:
    """Chunk document text while preserving section-heading context per chunk."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    sections = _split_into_sections(text) or [(None, text)]

    raw_chunks: list[RawChunk] = []
    index = 0
    for heading, body in sections:
        if not body.strip():
            continue
        pieces = splitter.split_text(body)
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            raw_chunks.append(RawChunk(text=piece, section=heading, chunk_index=index))
            index += 1

    return raw_chunks


def stable_chunk_id(document_id: str, chunk_index: int, text: str) -> str:
    """Deterministic chunk ID: stable across re-ingestion runs for duplicate detection."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{document_id}::chunk-{chunk_index:03d}::{digest}"
