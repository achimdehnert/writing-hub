"""
SeriesContinuityService — ADR-155

Erstellt LLM-Prompt-Kontext aus den Figur-Kontinuitätsdaten des Vorgänger-Bands.
"""

from __future__ import annotations


def build_continuity_context(series, for_volume_number: int) -> str:
    """
    Erstellt Prompt-Kontext für Band N aus den Kontinuitäts-Daten von Band N-1.
    Direkt in Layer-4-Kontext (ADR-150) injizierbar.
    """
    from apps.series.models import SeriesVolume
    from apps.series.models_arc import SeriesCharacterContinuity

    prev_volume = SeriesVolume.objects.filter(
        series=series,
        volume_number=for_volume_number - 1,
    ).first()
    if not prev_volume:
        return ""

    continuities = SeriesCharacterContinuity.objects.filter(series=series, volume=prev_volume).order_by(
        "character_name"
    )

    lines = [f"=== KONTINUITÄT AUS BAND {for_volume_number - 1} ==="]
    for c in continuities:
        lines.append(c.to_next_volume_context())
        lines.append("")

    try:
        role = prev_volume.role
        if role.promise_to_reader:
            lines.append(f"VERSPRECHEN AN LESER: {role.promise_to_reader}")
        if role.cliffhanger_description:
            lines.append(f"CLIFFHANGER: {role.cliffhanger_description}")
    except Exception:
        pass

    return "\n".join(lines)


def build_series_arc_context(series) -> str:
    """
    Gibt SeriesArc-Felder als LLM-Prompt-Block zurück (Layer 4a, ADR-155).
    """
    try:
        arc = series.arc
    except Exception:
        return ""

    lines = ["=== SERIEN-ARC ==="]
    if arc.series_want:
        lines.append(f"Serien-Want: {arc.series_want}")
    if arc.series_need:
        lines.append(f"Serien-Need: {arc.series_need}")
    if arc.series_false_belief:
        lines.append(f"Überzeugung Beginn: {arc.series_false_belief}")
    if arc.series_true_belief:
        lines.append(f"Erkenntnis Ende: {arc.series_true_belief}")
    if arc.overarching_conflict:
        lines.append(f"Übergreifender Konflikt: {arc.overarching_conflict}")
    if arc.series_theme_question:
        lines.append(f"Serien-Thema: {arc.series_theme_question}")
    return "\n".join(lines)
