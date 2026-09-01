"""Optional LLM provider integration.

If no provider/API key is configured, `LLMService.is_enabled` is False and the
RAG service automatically uses the deterministic extractive fallback instead.
No API key is ever hard-coded; everything comes from environment variables.
"""
from __future__ import annotations

import json
import logging

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the GuidelineCheck answer generator for an educational, \
synthetic-data public-health RAG demo. You must answer ONLY using the provided context \
chunks. Never use outside knowledge. Never give patient-specific medical advice or a \
diagnosis. Prefer information from chunks whose status is Current. If the context is \
insufficient, contradictory, or missing, you must abstain rather than guess.

Respond with ONLY a JSON object (no markdown fences, no preamble) matching this shape:
{
  "answer_text": string,
  "is_abstention": boolean,
  "confidence_label": "High" | "Medium" | "Low",
  "retrieved_context_sufficient": boolean,
  "current_guidance_found": boolean
}
"""


class LLMService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def is_enabled(self) -> bool:
        return self.settings.llm_enabled

    def generate_structured_answer(self, question: str, context_block: str) -> dict | None:
        """Call the configured LLM provider and parse a structured JSON answer.

        Returns None if the provider is unavailable or the call fails, so the
        caller can fall back to the deterministic extractive path.
        """
        if not self.is_enabled:
            return None

        try:
            if self.settings.llm_provider == "anthropic":
                return self._call_anthropic(question, context_block)
            if self.settings.llm_provider == "openai":
                return self._call_openai(question, context_block)
        except Exception:  # noqa: BLE001
            logger.exception("LLM call failed; falling back to extractive mode")
            return None
        return None

    def _call_anthropic(self, question: str, context_block: str) -> dict | None:
        import anthropic

        client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        response = client.messages.create(
            model=self.settings.llm_model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nContext chunks:\n{context_block}",
                }
            ],
        )
        text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        raw_text = "".join(text_parts).strip()
        return self._parse_json(raw_text)

    def _call_openai(self, question: str, context_block: str) -> dict | None:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nContext chunks:\n{context_block}",
                },
            ],
            temperature=0.0,
        )
        raw_text = response.choices[0].message.content or ""
        return self._parse_json(raw_text)

    @staticmethod
    def _parse_json(raw_text: str) -> dict | None:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM response as JSON: %s", raw_text[:200])
            return None
