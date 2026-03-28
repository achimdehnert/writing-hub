"""
PitchGeneratorService — ADR-159

Generiert Logline, Exposé, Synopsis und Query Letter via LLM.
"""
from __future__ import annotations


LOGLINE_SYSTEM = """
Du schreibst professionelle Loglines für Verlagsanfragen.
Format (Save-the-Cat): "Ein [Figur mit Mangel/Eigenschaft] muss
[äußeres Ziel erreichen], bevor [Stakes/Konsequenz] — aber
[Antagonist/Hindernis] stellt sich entgegen."
Max. 35 Wörter. Keine Metakommentare. Kein Spoiler des Endes.
"""

EXPOSE_DE_SYSTEM = """
Du schreibst deutschsprachige Verlagsexposés im Branchenstandard.
Ton: professionell, präzise, kein Werbesprech.
Kein "In diesem fesselnden Roman..." — Fakten, keine Adjektive.
"""

EXPOSE_DE_USER = (
    "Schreibe ein deutsches Verlagsexposé für diesen Roman.\n\n"
    "STRUKTUR (exakt):\n"
    "1. KURZINHALT (3–4 Sätze, Handlung ohne Ausgang)\n"
    "2. FIGUREN (Protagonist 2–3 Sätze, Antagonist 1–2 Sätze)\n"
    "3. THEMA (1 Satz — nie moralisierend, als Frage formulierbar)\n"
    "4. MARKT\n"
    "   Zielgruppe: {target_audience}\n"
    "   Vergleichstitel: {comps}\n"
    "   Umfang: ca. {word_count} Wörter\n"
    "5. ZUR AUTORIN / ZUM AUTOR\n"
    "   [Platzhalter — hier Kurzbiografie einfügen]\n\n"
    "ROMAN-BIBEL:\n"
    "Titel: {title}\n"
    "Genre: {genre}\n"
    "Äußere Geschichte: {outer_story}\n"
    "Innere Geschichte: {inner_story}\n"
    "Thema: {theme}\n"
    "Protagonist: {protagonist}\n"
    "Antagonist: {antagonist}\n\n"
    "Länge: max. 500 Wörter. Keine Wertungen."
)

QUERY_SYSTEM = """
You write query letters for US/UK literary agents.
Standard format: Hook → Pitch → Comps → Bio → Closing.
Present tense for the pitch. Max 250 words. No adjective inflation.
"""

QUERY_USER = (
    "Write a query letter for this novel.\n\n"
    "Title: {title}\n"
    "Genre: {genre}\n"
    "Word Count: {word_count}\n"
    "Logline: {logline}\n"
    "Comp 1: {comp1}\n"
    "Comp 2: {comp2}\n\n"
    "Bio placeholder: [Author bio here]\n\n"
    "Hook: Start with the most compelling narrative moment or question.\n"
    "Pitch: 2-3 sentences in present tense, include protagonist + stakes.\n"
    'Comps: "For fans of [comp1] and [comp2]..."'
)


def generate_logline(project):
    protagonist = _get_character(project, "protagonist")
    antagonist = _get_character(project, "antagonist")
    theme = getattr(project, "theme", None)

    user_prompt = (
        f"Titel: {project.title}\n"
        f"Genre: {project.genre or ''}\n"
        f"Protagonist Want: {protagonist.want if protagonist else ''}\n"
        f"Protagonist Need: {protagonist.need if protagonist else ''}\n"
        f"Protagonist Flaw: {protagonist.flaw if protagonist else ''}\n"
        f"Antagonist Logik: {antagonist.antagonist_logic if antagonist else ''}\n"
        f"Innere Geschichte: {getattr(project, 'inner_story', '')}\n"
        f"Thema: {theme.core_question if theme else ''}\n"
    )

    result = _call_llm(
        action_code="logline_generate",
        system=LOGLINE_SYSTEM,
        user=user_prompt,
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

    user_prompt = EXPOSE_DE_USER.format(
        title=project.title,
        genre=genre,
        target_audience=getattr(project, "target_audience", None) or "Erwachsene Leser",
        comps=comps_text,
        word_count=f"{project.target_word_count:,}" if project.target_word_count else "?",
        outer_story=getattr(project, "outer_story", ""),
        inner_story=getattr(project, "inner_story", ""),
        theme=theme.core_question if theme else "",
        protagonist=(
            f"{protagonist.want} / {protagonist.need}" if protagonist else "—"
        ),
        antagonist=(
            antagonist.antagonist_logic if antagonist else "—"
        ),
    )

    result = _call_llm(
        action_code="expose_generate",
        system=EXPOSE_DE_SYSTEM,
        user=user_prompt,
    )
    return _save_pitch(project, "expose_de", result, is_ai=True)


def generate_query(project):
    from apps.projects.models import ComparableTitle, PitchDocument
    comps = ComparableTitle.objects.filter(project=project).order_by("sort_order")[:2]
    logline_doc = PitchDocument.objects.filter(
        project=project, pitch_type="logline", is_current=True
    ).first()

    user_prompt = QUERY_USER.format(
        title=project.title,
        genre=project.genre or "",
        word_count=f"{project.target_word_count:,}" if project.target_word_count else "?",
        logline=logline_doc.content if logline_doc else "",
        comp1=comps[0].to_comp_string() if len(comps) > 0 else "—",
        comp2=comps[1].to_comp_string() if len(comps) > 1 else "—",
    )

    result = _call_llm(
        action_code="query_generate",
        system=QUERY_SYSTEM,
        user=user_prompt,
    )
    return _save_pitch(project, "query", result, is_ai=True)


def _call_llm(action_code: str, system: str, user: str) -> str:
    try:
        from aifw.service import sync_completion
        result = sync_completion(
            action_code=action_code,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
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
