"""
GenreConventionService — ADR-160

Prüft Projekt gegen Genre-Konventionen (maschinenlesbar).
Regelbasiert — kein LLM.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def check_genre_conventions(project) -> list[dict]:
    """
    Prüft Projekt gegen Genre-Konventionen.
    Gibt Check-Liste zurück — kann in DramaturgicHealthScore integriert werden.
    """
    genre_lookup = getattr(project, "genre_lookup", None)
    if not genre_lookup:
        return []
    profile = getattr(genre_lookup, "convention_profile", None)
    if not profile:
        return []

    results = []
    for conv in profile.conventions:
        passed = _evaluate_convention(project, conv)
        results.append(
            {
                "label": conv.get("label", ""),
                "description": conv.get("description", ""),
                "passed": passed,
                "weight": conv.get("weight", "recommended"),
            }
        )
    return results


def _evaluate_convention(project, conv: dict) -> bool:
    check_type = conv.get("check_type", "")

    if check_type == "turning_point_exists":
        pct = conv.get("check_by_percent", 100)
        return project.turning_points.filter(position_percent__lte=pct).exists()

    if check_type == "b_story_exists":
        return project.subplot_arcs.filter(story_label="b_story").exists()

    if check_type == "happy_end_required":
        return getattr(project, "arc_direction", "") == "positive"

    if check_type == "fair_play":
        entries = getattr(project, "foreshadowing_entries", None)
        if entries is None:
            return True
        planted = entries.filter(is_planted=True)
        return all(e.setup_node and getattr(e.setup_node, "position_start", 0) <= 75 for e in planted)

    if check_type == "none":
        return True

    logger.warning(
        "GenreConventionProfile: unbekannter check_type '%s' — Convention '%s' wird ignoriert.",
        check_type,
        conv.get("label", "?"),
    )
    return True
