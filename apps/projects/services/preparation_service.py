"""
Preparation Pipeline Service — flexible Vorbereitung zwischen Outline und Schreiben.

Content-Type-abhängige Vorbereitungsschritte (Recherche, Charaktere, Welten, Fakten)
mit Completion-Check. Kein Schritt ist blockierend.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.authoring.defaults import DEFAULT_CONTENT_TYPE
from apps.projects.constants import CONTENT_TYPE_GROUPS, PREPARATION_STEPS

logger = logging.getLogger(__name__)


def get_preparation_status(
    project: Any,
    chapters: list[Any] | None = None,
) -> dict[str, Any]:
    """
    Ermittelt den Vorbereitungsstatus für ein Projekt.

    Returns dict mit:
        group: str — content-type group (academic/fiction/nonfiction)
        steps: list[dict] — Schritte mit completion-Status + resolved URLs
        completed_count: int
        total_count: int
    """
    from django.urls import reverse, NoReverseMatch

    content_type = getattr(project, "content_type", DEFAULT_CONTENT_TYPE) or DEFAULT_CONTENT_TYPE
    group = CONTENT_TYPE_GROUPS.get(content_type, "fiction")
    step_defs = PREPARATION_STEPS.get(group, [])

    if not step_defs:
        return {"group": group, "steps": [], "completed_count": 0, "total_count": 0}

    steps = []
    for step_def in step_defs:
        step = dict(step_def)
        step["done"] = _check_completion(step["key"], project, chapters)
        step["detail"] = _get_detail(step["key"], project, chapters)
        step["resolved_url"] = ""
        if step.get("url_name"):
            try:
                step["resolved_url"] = reverse(step["url_name"])
            except NoReverseMatch:
                step["resolved_url"] = ""
        steps.append(step)

    completed = sum(1 for s in steps if s["done"])
    return {
        "group": group,
        "steps": steps,
        "completed_count": completed,
        "total_count": len(steps),
    }


def _check_completion(key: str, project: Any, chapters: list | None) -> bool:
    """Prüft ob ein Vorbereitungsschritt abgeschlossen ist."""
    if key == "research":
        if not chapters:
            return False
        return any(bool(getattr(ch, "notes", "")) for ch in chapters)

    if key == "characters":
        from apps.worlds.models import ProjectCharacterLink

        return ProjectCharacterLink.objects.filter(project=project).exists()

    if key == "worlds":
        from apps.worlds.models import ProjectWorldLink

        return ProjectWorldLink.objects.filter(project=project).exists()

    if key == "facts":
        if not chapters:
            return False
        return any(bool(getattr(ch, "notes", "")) for ch in chapters)

    return False


def _get_detail(key: str, project: Any, chapters: list | None) -> str:
    """Liefert Detail-Info für einen Schritt (z.B. '3 Charaktere')."""
    if key == "research":
        if not chapters:
            return ""
        count = sum(1 for ch in chapters if getattr(ch, "notes", ""))
        total = len(chapters)
        if count == 0:
            return ""
        return f"{count}/{total} Kapitel"

    if key == "characters":
        from apps.worlds.models import ProjectCharacterLink

        count = ProjectCharacterLink.objects.filter(project=project).count()
        return f"{count} Charaktere" if count else ""

    if key == "worlds":
        from apps.worlds.models import ProjectWorldLink

        count = ProjectWorldLink.objects.filter(project=project).count()
        return f"{count} Welten" if count else ""

    if key == "facts":
        if not chapters:
            return ""
        count = sum(1 for ch in chapters if getattr(ch, "notes", ""))
        total = len(chapters)
        if count == 0:
            return ""
        return f"{count}/{total} Kapitel"

    return ""
