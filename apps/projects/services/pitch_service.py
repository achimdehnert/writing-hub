"""
PitchGeneratorService — ADR-159

Generiert Logline, Exposé, Synopsis und Query Letter via LLM.
"""
from __future__ import annotations

from apps.core.prompt_utils import render_prompt


def generate_logline(project):
    protagonist = _get_character(project, "protagonist")
    antagonist = _get_character(project, "antagonist")
    theme = getattr(project, "theme", None)

    messages = render_prompt(
        "projects/pitch_logline",
        title=project.title,
        genre=project.genre or "",
        protagonist_want=protagonist.want if protagonist else "",
        protagonist_need=protagonist.need if protagonist else "",
        protagonist_flaw=protagonist.flaw if protagonist else "",
        antagonist_logic=antagonist.antagonist_logic if antagonist else "",
        inner_story=getattr(project, "inner_story", ""),
        theme=theme.core_question if theme else "",
    )
    if not messages:
        messages = [
            {"role": "system", "content": "Du schreibst professionelle Loglines. Max. 35 Woerter."},
            {"role": "user", "content": f"Logline fuer: {project.title}"},
        ]

    result = _call_llm_messages(
        action_code="logline_generate",
        messages=messages,
    )
    return _save_pitch(project, "logline", result, is_ai=True)


def generate_expose_de(project):
    from apps.projects.models import ComparableTitle
    comps = ComparableTitle.objects.filter(project=project).order_by("sort_order")[:3]
    comps_text = "; ".join(c.to_comp_string() for c in comps) or "—"

    protagonist = _get_character(project, "protagonist")
    antagonist = _get_character(project, "antagonist")
    theme = getattr(project, "theme", None)

    genre = project.genre or ""
    if not genre and hasattr(project, "genre_lookup") and project.genre_lookup:
        genre = project.genre_lookup.name

    messages = render_prompt(
        "projects/pitch_expose_de",
        title=project.title,
        genre=genre,
        target_audience=getattr(project, "target_audience", None) or "Erwachsene Leser",
        comps=comps_text,
        word_count=f"{project.target_word_count:,}" if project.target_word_count else "?",
        outer_story=getattr(project, "outer_story", ""),
        inner_story=getattr(project, "inner_story", ""),
        theme=theme.core_question if theme else "",
        protagonist=f"{protagonist.want} / {protagonist.need}" if protagonist else "\u2014",
        antagonist=antagonist.antagonist_logic if antagonist else "\u2014",
    )
    if not messages:
        messages = [
            {"role": "system", "content": "Du schreibst Verlagsexpos\u00e9s."},
            {"role": "user", "content": f"Expos\u00e9 fuer: {project.title}"},
        ]

    result = _call_llm_messages(
        action_code="expose_generate",
        messages=messages,
    )
    return _save_pitch(project, "expose_de", result, is_ai=True)


def generate_query(project):
    from apps.projects.models import ComparableTitle, PitchDocument
    comps = ComparableTitle.objects.filter(project=project).order_by("sort_order")[:2]
    logline_doc = PitchDocument.objects.filter(
        project=project, pitch_type="logline", is_current=True
    ).first()

    messages = render_prompt(
        "projects/pitch_query",
        title=project.title,
        genre=project.genre or "",
        word_count=f"{project.target_word_count:,}" if project.target_word_count else "?",
        logline=logline_doc.content if logline_doc else "",
        comp1=comps[0].to_comp_string() if len(comps) > 0 else "\u2014",
        comp2=comps[1].to_comp_string() if len(comps) > 1 else "\u2014",
    )
    if not messages:
        messages = [
            {"role": "system", "content": "You write query letters for literary agents."},
            {"role": "user", "content": f"Query letter for: {project.title}"},
        ]

    result = _call_llm_messages(
        action_code="query_generate",
        messages=messages,
    )
    return _save_pitch(project, "query", result, is_ai=True)


def _call_llm_messages(action_code: str, messages: list[dict]) -> str:
    try:
        from aifw.service import sync_completion
        result = sync_completion(
            action_code=action_code,
            messages=messages,
        )
        if not result.success:
            raise RuntimeError(f"LLM-Fehler ({action_code}): {result.error}")
        return result.content.strip()
    except ImportError:
        raise RuntimeError("aifw nicht installiert — LLM-Generierung nicht verfügbar.")


def _get_character(project, role: str):
    try:
        return project.character_links.filter(narrative_role=role).first()
    except Exception:
        return None


def _save_pitch(project, pitch_type: str, content: str, is_ai: bool = False):
    from apps.projects.models import PitchDocument
    PitchDocument.objects.filter(
        project=project, pitch_type=pitch_type, is_current=True
    ).update(is_current=False)

    last = PitchDocument.objects.filter(
        project=project, pitch_type=pitch_type
    ).order_by("-version").first()

    return PitchDocument.objects.create(
        project=project,
        pitch_type=pitch_type,
        content=content,
        is_ai_generated=is_ai,
        ai_agent=f"{pitch_type}_generate",
        version=(last.version + 1) if last else 1,
        is_current=True,
    )
