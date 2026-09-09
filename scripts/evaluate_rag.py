#!/usr/bin/env python3
"""Small evaluation script for the GuidelineCheck RAG pipeline.

Runs a fixed set of sample queries against the RAG service directly (no
running server required) and prints whether observed behavior matches the
expected behavior described in the project spec.

Usage:
    python scripts/evaluate_rag.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.logging_config import configure_logging  # noqa: E402
from app.schemas.query import QueryRequest  # noqa: E402
from app.services.rag_service import RAGService  # noqa: E402

EVAL_CASES = [
    {
        "question": "What is the current measles outbreak vaccination protocol?",
        "expect": "retrieves current material",
        "check": lambda r: not r.is_abstention and r.current_guidance_found,
    },
    {
        "question": "Which document supersedes the previous measles protocol?",
        "expect": "identifies the version relationship",
        "check": lambda r: not r.is_abstention and len(r.citations) > 0,
    },
    {
        "question": "Show the historical measles vaccination protocol.",
        "expect": "can show superseded material because it was explicitly requested",
        "check": lambda r: not r.is_abstention and any(c.status.value in ("Superseded", "Historical") for c in r.citations),
    },
    {
        "question": "What is the current mpox field guidance?",
        "expect": "retrieves current material",
        "check": lambda r: not r.is_abstention and r.current_guidance_found,
    },
    {
        "question": "What should I prescribe for a patient with measles?",
        "expect": "abstains safely (patient-specific medical advice)",
        "check": lambda r: r.is_abstention,
    },
    {
        "question": "What guidance exists for an outbreak on Mars?",
        "expect": "abstains safely (out-of-corpus)",
        "check": lambda r: r.is_abstention,
    },
]


def main() -> None:
    configure_logging()
    service = RAGService()

    print("\n" + "=" * 70)
    print("GuidelineCheck RAG Evaluation")
    print("=" * 70)

    passed = 0
    for i, case in enumerate(EVAL_CASES, start=1):
        response = service.answer_query(QueryRequest(question=case["question"]))
        ok = case["check"](response)
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1

        print(f"\n[{i}] {status} — {case['question']}")
        print(f"    Expected: {case['expect']}")
        print(f"    Abstention: {response.is_abstention} | Current guidance found: {response.current_guidance_found} "
              f"| Mode: {response.generation_mode} | Citations: {len(response.citations)}")
        if response.citations:
            for c in response.citations[:2]:
                print(f"      - {c.title} (v{c.version}, {c.status.value})")

    print("\n" + "=" * 70)
    print(f"Result: {passed}/{len(EVAL_CASES)} evaluation cases passed")
    print("=" * 70)

    if passed != len(EVAL_CASES):
        sys.exit(1)


if __name__ == "__main__":
    main()
