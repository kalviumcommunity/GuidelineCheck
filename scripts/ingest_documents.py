#!/usr/bin/env python3
"""CLI entrypoint for ingesting the GuidelineCheck synthetic document corpus.

Usage:
    python scripts/ingest_documents.py
    python scripts/ingest_documents.py --reset
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.logging_config import configure_logging  # noqa: E402
from app.services.ingestion_service import IngestionService  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest GuidelineCheck synthetic documents into ChromaDB.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the vector store collection before ingesting.",
    )
    args = parser.parse_args()

    configure_logging()

    service = IngestionService()
    summary = service.run(reset=args.reset)

    print("\n" + "=" * 60)
    print("GuidelineCheck Ingestion Summary")
    print("=" * 60)
    print(f"Documents scanned:            {summary.documents_scanned}")
    print(f"Documents ingested:           {summary.documents_ingested}")
    print(f"Documents skipped (dup):      {summary.documents_skipped_duplicate}")
    print(f"Documents failed:             {summary.documents_failed}")
    print(f"Chunks created:               {summary.chunks_created}")
    print(f"Reset performed:              {summary.reset_performed}")

    if summary.warnings:
        print("\nWarnings:")
        for w in summary.warnings:
            print(f"  - {w}")

    if summary.errors:
        print("\nErrors:")
        for e in summary.errors:
            print(f"  - {e}")
        sys.exit(1)

    print("\nDone. Vector store is ready to query.")


if __name__ == "__main__":
    main()
