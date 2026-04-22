"""
Authors — LLM-Service für Stil-Analyse, Regel-Extraktion und Beispieltext-Generierung.
"""

import logging

from promptfw.parsing import extract_json

from .models import SituationType, WritingStyle, WritingStyleSample

logger = logging.getLogger(__name__)

# Legacy fallback situations (used when no genre_profile is set)
LEGACY_SITUATIONS = [
    ("action", "Actionszene"),
    ("dialogue", "Dialog"),
    ("description", "Ortsbeschreibung"),
    ("emotion", "Emotionale Szene"),
    ("intro", "Kapiteleinstieg"),
    ("outro", "Kapitelende / Cliffhanger"),
    ("inner", "Innerer Monolog"),
    ("exposition", "Exposition"),
]


def get_situations_for_style(style: WritingStyle) -> list[tuple[str, str, str]]:
    """
    Returns list of (slug, label, llm_prompt_hint) for the style's genre.
    Falls back to LEGACY_SITUATIONS if no genre_profile set.
    """
    if style.genre_profile:
        return [
            (st.slug, st.label, st.llm_prompt_hint or "")
            for st in style.genre_profile.situation_types.filter(is_active=True).order_by("sort_order")
        ]
    return [(key, label, "") for key, label in LEGACY_SITUATIONS]


def analyze_style(style: WritingStyle) -> bool:
    """
    Analysiert den Quelltext eines WritingStyle per LLM.
    Speichert style_profile und style_prompt.
    Wird typisch in einem Background-Thread aufgerufen.
    """
    from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

    style.refresh_from_db()
    text = style.source_text.strip()
    if not text:
        style.status = WritingStyle.Status.ERROR
        style.error_message = "Kein Quelltext vorhanden."
        style.save(update_fields=["status", "error_message"])
        return False

    from apps.core.prompt_utils import render_prompt

    prompt_msgs = render_prompt(
        "authors/analyze_style",
        source_text=text,
    )

    try:
        router = LLMRouter()
        result = router.completion(
            action_code="style_check",
            messages=prompt_msgs,
        )

        style_prompt = ""
        if "## Stil-Prompt" in result:
            parts = result.split("## Stil-Prompt")
            style_prompt = parts[-1].strip().lstrip(":").strip()

        style.style_profile = result
        style.style_prompt = style_prompt
        style.status = WritingStyle.Status.READY
        style.error_message = ""
        style.save(update_fields=["style_profile", "style_prompt", "status", "error_message"])
        return True

    except LLMRoutingError as exc:
        logger.warning("analyze_style LLMRoutingError style=%s: %s", style.pk, exc)
        style.status = WritingStyle.Status.ERROR
        style.error_message = f"LLM nicht verfügbar: {exc}"
        style.save(update_fields=["status", "error_message"])
        return False
    except Exception as exc:
        logger.exception("analyze_style error style=%s: %s", style.pk, exc)
        style.status = WritingStyle.Status.ERROR
        style.error_message = str(exc)
        style.save(update_fields=["status", "error_message"])
        return False


def extract_style_rules(style: WritingStyle) -> tuple[bool, dict]:
    """
    Extrahiert DO/DONT/Taboo/Signature-Moves aus dem Quelltext per LLM.
    Gibt (True, {do_list, dont_list, taboo_list, signature_moves}) oder
    (False, {error}) zurück.
    """
    from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

    text = (style.source_text or "").strip()
    profile = (style.style_profile or "").strip()

    if not text and not profile:
        return False, {"error": "Kein Quelltext oder Stil-Profil vorhanden."}

    source = text[:3000] if text else profile[:2000]

    from apps.core.prompt_utils import render_prompt

    prompt_msgs = render_prompt(
        "authors/extract_rules",
        source_text=source,
    )

    try:
        router = LLMRouter()
        raw = router.completion(
            action_code="style_check",
            messages=prompt_msgs,
        )
        data = extract_json(raw)
        if not data:
            return False, {"error": "Keine JSON-Antwort vom LLM"}

        # Persist extracted rules
        style.do_list = data.get("do_list", [])
        style.dont_list = data.get("dont_list", [])
        style.taboo_list = data.get("taboo_list", [])
        style.signature_moves = data.get("signature_moves", [])
        style.save(update_fields=["do_list", "dont_list", "taboo_list", "signature_moves"])

        return True, data

    except (ValueError, LLMRoutingError, Exception) as exc:
        logger.warning("extract_style_rules error style=%s: %s", style.pk, exc)
        return False, {"error": str(exc)}


def generate_samples(style: WritingStyle) -> int:
    """
    Generiert Beispieltexte fuer alle Situationen des Genres.
    Gibt Anzahl der generierten Samples zurueck.
    """
    from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

    if not style.style_prompt and not style.style_profile:
        return 0

    style_desc = style.style_prompt or style.style_profile[:500]
    count = 0

    router = LLMRouter()
    from apps.core.prompt_utils import render_prompt

    situations = get_situations_for_style(style)

    for situation_key, situation_label, llm_hint in situations:
        if style.samples.filter(situation=situation_key).exists():
            continue
        try:
            prompt_msgs = render_prompt(
                "authors/generate_sample",
                style_desc=style_desc,
                situation_label=situation_label,
                llm_prompt_hint=llm_hint,
            )
            result = router.completion(
                action_code="chapter_write",
                messages=prompt_msgs,
            )
            # Resolve SituationType FK if genre_profile is set
            situation_type = None
            if style.genre_profile:
                situation_type = SituationType.objects.filter(
                    genre_profile=style.genre_profile,
                    slug=situation_key,
                ).first()

            WritingStyleSample.objects.create(
                style=style,
                situation=situation_key,
                situation_type=situation_type,
                text=result,
            )
            count += 1
        except (LLMRoutingError, Exception) as exc:
            logger.warning("generate_samples skip situation=%s: %s", situation_key, exc)
            continue

    return count


def get_style_prompt_for_writing(style: WritingStyle) -> str:
    """
    Gibt den Stil-Prompt-Baustein zurück der beim Schreiben verwendet wird.
    Enthält DO/DONT/Taboo wenn vorhanden.
    """
    parts = []
    if style.style_prompt:
        parts.append(style.style_prompt)
    elif style.style_profile:
        parts.append(style.style_profile[:300])
    if style.do_list:
        parts.append("DO: " + "; ".join(style.do_list[:5]))
    if style.dont_list:
        parts.append("DONT: " + "; ".join(style.dont_list[:5]))
    if style.taboo_list:
        parts.append("TABOO (niemals): " + "; ".join(style.taboo_list[:5]))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Query helpers (ADR-041)
# ---------------------------------------------------------------------------


def get_active_genres():
    """Return all active GenreProfiles."""
    from apps.authors.models import GenreProfile

    return GenreProfile.objects.filter(is_active=True)


def get_genre_by_pk(pk: int):
    """Return a single active GenreProfile by pk, or None."""
    from apps.authors.models import GenreProfile

    return GenreProfile.objects.filter(pk=pk, is_active=True).first()


def create_author(owner, name: str, bio: str = ""):
    """Create and return a new Author."""
    from apps.authors.models import Author

    return Author.objects.create(owner=owner, name=name, bio=bio)


def get_situation_type(genre_profile, slug: str):
    """Return SituationType for genre_profile + slug, or None."""
    from apps.authors.models import SituationType

    if not genre_profile:
        return None
    return SituationType.objects.filter(genre_profile=genre_profile, slug=slug).first()


def save_sample(style, situation: str, text: str, situation_type=None, notes: str = ""):
    """Create or update a WritingStyleSample."""
    from apps.authors.models import WritingStyleSample

    obj, _ = WritingStyleSample.objects.update_or_create(
        style=style,
        situation=situation,
        defaults={"text": text, "notes": notes, "situation_type": situation_type},
    )
    return obj


def create_sample(style, situation: str, text: str, situation_type=None):
    """Create a new WritingStyleSample (no upsert)."""
    from apps.authors.models import WritingStyleSample

    return WritingStyleSample.objects.create(
        style=style,
        situation=situation,
        situation_type=situation_type,
        text=text,
    )
