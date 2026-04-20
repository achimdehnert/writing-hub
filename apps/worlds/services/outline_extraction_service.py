"""
Outline Extraction Service
============================

Extrahiert Charakter- und Ort-Hinweise aus Outline-Nodes
und legt sie als lokale ProjectCharacterLink / ProjectLocationLink an.

Optional: LLM-basierte Verfeinerung der extrahierten Grunddaten.
"""

from __future__ import annotations

import logging
import re

from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
from apps.core.prompt_utils import render_prompt

logger = logging.getLogger(__name__)


def extract_from_outline(project) -> dict:
    """
    Parst alle aktiven Outline-Nodes eines Projekts und extrahiert
    Charakter-Namen und Ort-Namen per LLM.

    Returns:
        {"characters": [{"name": ..., "description": ...}],
         "locations": [{"name": ..., "description": ...}]}
    """
    from apps.projects.models import OutlineVersion

    outline = OutlineVersion.objects.filter(project=project, is_active=True).first()
    if not outline:
        return {"characters": [], "locations": []}

    nodes = outline.nodes.all().order_by("order")
    if not nodes.exists():
        return {"characters": [], "locations": []}

    outline_text = _build_outline_text(nodes, project)

    try:
        router = LLMRouter()
        messages = _build_extraction_prompt(outline_text, project)
        raw = router.completion("character_generate", messages)
        from promptfw.parsing import extract_json

        data = extract_json(raw) or {}
        characters = [c for c in data.get("characters", []) if isinstance(c, dict) and c.get("name")]
        locations = [loc for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("name")]
        return {"characters": characters, "locations": locations}
    except (LLMRoutingError, Exception) as exc:
        logger.error("extract_from_outline LLM-Fehler: %s", exc)
        return _extract_fallback(nodes)


def save_extracted_to_project(project, extracted: dict, world_link=None) -> dict:
    """
    Speichert extrahierte Charaktere und Orte als lokale Links.

    Returns:
        {"characters_created": int, "locations_created": int}
    """
    from apps.worlds.models import ProjectCharacterLink, ProjectLocationLink

    char_count = 0
    for char in extracted.get("characters", []):
        name = char.get("name", "").strip()
        if not name:
            continue
        existing = ProjectCharacterLink.objects.filter(project=project, name__iexact=name).exists()
        if existing:
            continue
        ProjectCharacterLink.objects.create(
            project=project,
            name=name,
            description=char.get("description", ""),
            personality=char.get("personality", ""),
            backstory=char.get("backstory", ""),
            is_protagonist=char.get("is_protagonist", False),
            narrative_role="protagonist" if char.get("is_protagonist") else "supporting",
            source="outline",
        )
        char_count += 1

    loc_count = 0
    for loc in extracted.get("locations", []):
        name = loc.get("name", "").strip()
        if not name:
            continue
        existing = ProjectLocationLink.objects.filter(project=project, name__iexact=name).exists()
        if existing:
            continue
        ProjectLocationLink.objects.create(
            project=project,
            name=name,
            description=loc.get("description", ""),
            atmosphere=loc.get("atmosphere", ""),
            significance=loc.get("significance", ""),
            source="outline",
        )
        loc_count += 1

    return {"characters_created": char_count, "locations_created": loc_count}


def refine_character_with_llm(character_link) -> bool:
    """KI-Verfeinerung eines einzelnen Charakters."""
    try:
        router = LLMRouter()
        ctx = (
            f"Charakter: {character_link.name}\n"
            f"Beschreibung: {character_link.description}\n"
            f"Persönlichkeit: {character_link.personality}\n"
            f"Hintergrund: {character_link.backstory}\n"
            f"Projekt: {character_link.project.title}\n"
            f"Genre: {character_link.project.genre}"
        )
        messages = render_prompt("worlds/character_refine", char_ctx=ctx)
        raw = router.completion("character_generate", messages)
        from promptfw.parsing import extract_json

        data = extract_json(raw) or {}
        if data.get("personality"):
            character_link.personality = data["personality"]
        if data.get("backstory"):
            character_link.backstory = data["backstory"]
        if data.get("description"):
            character_link.description = data["description"]
        if data.get("want"):
            character_link.want = data["want"]
        if data.get("need"):
            character_link.need = data["need"]
        if data.get("flaw"):
            character_link.flaw = data["flaw"]
        character_link.save()
        return True
    except Exception as exc:
        logger.error("refine_character_with_llm: %s", exc)
        return False


def refine_location_with_llm(location_link) -> bool:
    """KI-Verfeinerung eines einzelnen Orts."""
    try:
        router = LLMRouter()
        ctx = (
            f"Ort: {location_link.name}\n"
            f"Beschreibung: {location_link.description}\n"
            f"Projekt: {location_link.project.title}\n"
            f"Genre: {location_link.project.genre}"
        )
        messages = render_prompt("worlds/location_refine", char_ctx=ctx)
        raw = router.completion("world_locations", messages)
        from promptfw.parsing import extract_json

        data = extract_json(raw) or {}
        if data.get("description"):
            location_link.description = data["description"]
        if data.get("atmosphere"):
            location_link.atmosphere = data["atmosphere"]
        if data.get("significance"):
            location_link.significance = data["significance"]
        location_link.save()
        return True
    except Exception as exc:
        logger.error("refine_location_with_llm: %s", exc)
        return False


def _build_outline_text(nodes, project) -> str:
    """Konvertiert Outline-Nodes in einen zusammenhängenden Text."""
    parts = [f"Projekt: {project.title}", f"Genre: {project.genre}", ""]
    for node in nodes:
        parts.append(f"## Kapitel {node.order}: {node.title}")
        if node.description:
            parts.append(node.description[:500])
        parts.append("")
    return "\n".join(parts)


def _build_extraction_prompt(outline_text: str, project) -> list[dict]:
    """Baut den Prompt für die LLM-Extraktion."""
    system = (
        "Du bist ein Literatur-Analyst. Extrahiere aus dem folgenden Outline "
        "alle erwähnten Charaktere und Orte. "
        "Antworte als JSON mit genau diesem Format:\n"
        '{"characters": [{"name": "...", "description": "kurze Beschreibung", '
        '"personality": "...", "is_protagonist": true/false}], '
        '"locations": [{"name": "...", "description": "...", '
        '"atmosphere": "...", "significance": "..."}]}'
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": outline_text},
    ]


def _extract_fallback(nodes) -> dict:
    """
    Regex-Fallback: Einfache Namenserkennung aus Outline-Nodes
    wenn LLM nicht verfügbar.
    """
    all_text = " ".join(f"{n.title} {n.description or ''}" for n in nodes)
    name_pattern = re.compile(r"\b([A-ZÄÖÜ][a-zäöüß]{2,})\b")
    raw_names = name_pattern.findall(all_text)
    stop_words = {
        "Der",
        "Die",
        "Das",
        "Ein",
        "Eine",
        "Und",
        "Oder",
        "Aber",
        "Wenn",
        "Dann",
        "Noch",
        "Hier",
        "Dort",
        "Alle",
        "Jede",
        "Szene",
        "Kapitel",
        "Ort",
        "Geschichte",
        "Roman",
        "Buch",
        "Projekt",
        "Handlung",
        "Beschreibung",
        "Titel",
    }
    from collections import Counter

    counts = Counter(n for n in raw_names if n not in stop_words)
    characters = [
        {"name": name, "description": "", "is_protagonist": i == 0}
        for i, (name, _) in enumerate(counts.most_common(10))
        if _ >= 2
    ]

    loc_pattern = re.compile(r"\(Ort:\s*([^)]+)\)")
    loc_names = set()
    for n in nodes:
        for match in loc_pattern.finditer(n.description or ""):
            loc_names.add(match.group(1).strip())
    locations = [{"name": name, "description": ""} for name in sorted(loc_names)]

    return {"characters": characters, "locations": locations}
