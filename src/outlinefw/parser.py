"""
outlinefw.parser — JSON-Parser für LLM-Outline-Antworten

Extrahiert OutlineNode-Liste aus rohem LLM-Text.
Robust gegen Markdown-Fencing, <think>-Tags, führenden Text.
"""
from __future__ import annotations

import json
import logging
import re

from .schemas import OutlineNode

logger = logging.getLogger(__name__)


def parse_nodes(raw: str) -> list[OutlineNode]:
    """
    JSON-Array aus LLM-Antwort parsen → list[OutlineNode].

    Behandelt:
    - ```json ... ``` Fencing
    - <think>...</think> Tags (Reasoning-Modelle)
    - Führender Text vor dem JSON-Array
    """
    # Reasoning-Tags entfernen
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
    # Markdown-Fencing entfernen
    raw = re.sub(r"```json\s*|```", "", raw).strip()
    # Zum ersten [ springen
    start = raw.find("[")
    if start != -1:
        raw = raw[start:]
    # Trailing garbage nach letztem ]
    end = raw.rfind("]")
    if end != -1:
        raw = raw[: end + 1]

    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]
        nodes = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            nodes.append(
                OutlineNode(
                    order=item.get("order", i + 1),
                    title=item.get("title", f"Kapitel {i + 1}"),
                    description=item.get("description", ""),
                    beat_type=item.get("beat_type", "chapter"),
                    beat=item.get("beat", ""),
                    act=item.get("act", ""),
                    notes=item.get("notes", ""),
                    emotional_arc=item.get("emotional_arc", ""),
                    tension_level=item.get("tension_level", ""),
                    target_words=int(item.get("target_words", 0) or 0),
                )
            )
        return nodes
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("outlinefw.parser: JSON-Fehler: %s | raw[:200]=%s", exc, raw[:200])
        return []
