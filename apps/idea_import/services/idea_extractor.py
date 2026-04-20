"""
IdeaExtractorService — Sync-Variante des IdeaExtractorAgent.

Portiert aus bfagent — LLM-Calls ausschliesslich via LLMRouter (ADR-095).
"""

from __future__ import annotations

import logging

from promptfw.parsing import extract_json

from apps.core.prompt_utils import render_prompt
from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

logger = logging.getLogger(__name__)

_ACTION_CODE = "idea_extraction"
_MAX_CHARS = 8_000


def extract_ideas(document_text: str) -> dict:
    """
    Ruft die KI synchron auf und gibt das Extraktionsergebnis als dict zurück.
    Wirft keine Exception — gibt bei Fehler ein leeres Ergebnis zurück.
    """
    if not document_text.strip():
        return _empty_result("Leerer Eingabe-Text.")

    truncated = document_text[:_MAX_CHARS]
    if len(document_text) > _MAX_CHARS:
        truncated += f"\n\n[... Text auf {_MAX_CHARS} Zeichen gekürzt ...]"

    messages = render_prompt(
        "idea_import/idea_extraction",
        document_text=truncated,
    )

    try:
        router = LLMRouter()
        raw = router.completion(action_code=_ACTION_CODE, messages=messages)
    except (LLMRoutingError, Exception) as exc:
        logger.exception("IdeaExtractor: LLM-Fehler: %s", exc)
        return _empty_result(f"KI-Fehler: {exc}")

    return _parse(raw)


def _parse(raw: str) -> dict:
    data = extract_json(raw)
    if data:
        return data
    logger.error("IdeaExtractor: JSON-Parse-Fehler | raw[:200]=%s", raw[:200])
    return _empty_result("Parse-Fehler: Keine JSON-Antwort vom LLM")


def _empty_result(error_msg: str = "") -> dict:
    return {
        "title": None,
        "description": None,
        "content_type": None,
        "core_thesis": None,
        "target_audience": None,
        "genre": None,
        "outline_beats": [],
        "chapters": [],
        "characters": [],
        "world_elements": [],
        "confidence_scores": {"metadata": 0.0, "outline": 0.0, "characters": 0.0, "world": 0.0},
        "detected_language": "de",
        "_error": error_msg,
    }


def section_summary(data: dict) -> dict:
    return {
        "metadata_fields": sum(1 for f in [data.get("title"), data.get("description"), data.get("genre")] if f),
        "outline_beats": len(data.get("outline_beats", [])),
        "chapters": len(data.get("chapters", [])),
        "characters": len(data.get("characters", [])),
        "world_elements": len(data.get("world_elements", [])),
    }


def available_sections(data: dict) -> list[str]:
    sections = []
    if data.get("title") or data.get("description") or data.get("genre"):
        sections.append("metadata")
    if data.get("outline_beats") or data.get("chapters"):
        sections.append("outline")
    if data.get("characters"):
        sections.append("characters")
    if data.get("world_elements"):
        sections.append("world")
    return sections
