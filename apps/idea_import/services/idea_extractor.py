"""
IdeaExtractorService — Sync-Variante des IdeaExtractorAgent.

Portiert aus bfagent (kein Celery/async — sync via aifw.sync_completion).
"""
from __future__ import annotations

import logging

from aifw import sync_completion
from promptfw.parsing import extract_json

logger = logging.getLogger(__name__)

_ACTION_CODE = "idea_extraction"
_MAX_CHARS = 8_000

_SYSTEM_PROMPT = (
    "Du bist ein präziser Literatur-Analyst für das Writing Hub Buchprojekt-System.\n\n"
    "Deine Aufgabe: Analysiere den gegebenen Text und extrahiere ALLE erkennbaren "
    "Buchprojekt-Inhalte.\n\n"
    "KRITISCHE REGELN:\n"
    "1. Antworte NUR mit validem JSON — kein Fließtext, keine Erklärungen, keine Markdown-Backticks.\n"
    "2. Fehlende Informationen → null oder leere Liste. NIEMALS Inhalte erfinden.\n"
    "3. Halte dich streng an das vorgegebene JSON-Schema.\n"
    "4. confidence_scores: Schätze pro Sektion 0.0–1.0 (1.0 = sehr sicher)."
)

_TASK_TEMPLATE = """
Analysiere dieses Dokument und extrahiere alle Buchprojekt-Inhalte:

---DOKUMENT START---
{document_text}
---DOKUMENT ENDE---

Extrahiere in folgendes JSON-Schema:

{{
  "title": "Buchtitel oder null",
  "description": "Kurzbeschreibung/Klappentext oder null",
  "content_type": "novel|nonfiction|essay oder null",
  "core_thesis": "Kernthese/Prämisse oder null",
  "target_audience": "Zielgruppe oder null",
  "genre": "Genre oder null",
  "outline_beats": [{{"title": "...", "description": "...", "beat_type": "chapter", "order": 1}}],
  "chapters": [{{"number": 1, "title": "...", "summary": "..."}}],
  "characters": [{{"name": "...", "role": "protagonist|antagonist|supporting", "description": "...", "arc": "..."}}],
  "world_elements": [{{"name": "...", "element_type": "location|object|faction|rule|concept", "description": "..."}}],
  "confidence_scores": {{"metadata": 0.0, "outline": 0.0, "characters": 0.0, "world": 0.0}},
  "detected_language": "de"
}}
"""


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

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _TASK_TEMPLATE.format(document_text=truncated)},
    ]

    try:
        result = sync_completion(action_code=_ACTION_CODE, messages=messages)
    except Exception as exc:
        logger.exception("IdeaExtractor: sync_completion Fehler: %s", exc)
        return _empty_result(f"KI-Fehler: {exc}")

    if not result.success:
        logger.error("IdeaExtractor: aifw-Fehler: %s", result.error)
        return _empty_result(f"KI-Fehler: {result.error}")

    return _parse(result.content)


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
