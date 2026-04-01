"""
Authors — LLM-Service für Stil-Analyse, Regel-Extraktion und Beispieltext-Generierung.
"""
import json
import logging

from .models import WritingStyle, WritingStyleSample

logger = logging.getLogger(__name__)

SITUATIONS = [
    ("action", "Actionszene"),
    ("dialogue", "Dialog"),
    ("description", "Ortsbeschreibung"),
    ("emotion", "Emotionale Szene"),
    ("intro", "Kapiteleinstieg"),
    ("outro", "Kapitelende / Cliffhanger"),
    ("inner", "Innerer Monolog"),
    ("exposition", "Exposition"),
]


def analyze_style(style: WritingStyle) -> bool:
    """
    Analysiert den Quelltext eines WritingStyle per LLM.
    Speichert style_profile und style_prompt.
    """
    from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

    text = style.source_text.strip()
    if not text:
        style.status = WritingStyle.Status.ERROR
        style.error_message = "Kein Quelltext vorhanden."
        style.save(update_fields=["status", "error_message"])
        return False

    style.status = WritingStyle.Status.ANALYZING
    style.save(update_fields=["status"])

    from apps.core.prompt_utils import render_prompt
    prompt_msgs = render_prompt(
        "authors/analyze_style",
        source_text=text,
    )
    if not prompt_msgs:
        prompt_msgs = [
            {"role": "system", "content": "Du bist ein Literaturkritiker. Erstelle ein Stilprofil."},
            {"role": "user", "content": f"Analysiere:\n\n{text[:4000]}"},
        ]

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
    if not prompt_msgs:
        prompt_msgs = [
            {"role": "system", "content": "Du bist ein Stilanalyst. Antworte NUR mit JSON."},
            {"role": "user", "content": f"Extrahiere Stil-Regeln:\n\n{source[:3000]}"},
        ]

    try:
        router = LLMRouter()
        raw = router.completion(
            action_code="style_check",
            messages=prompt_msgs,
        )
        # Strip possible markdown code fences
        clean = raw.strip().lstrip("`").removeprefix("json").strip().rstrip("`")
        data = json.loads(clean)

        # Persist extracted rules
        style.do_list = data.get("do_list", [])
        style.dont_list = data.get("dont_list", [])
        style.taboo_list = data.get("taboo_list", [])
        style.signature_moves = data.get("signature_moves", [])
        style.save(update_fields=["do_list", "dont_list", "taboo_list", "signature_moves"])

        return True, data

    except (json.JSONDecodeError, LLMRoutingError, Exception) as exc:
        logger.warning("extract_style_rules error style=%s: %s", style.pk, exc)
        return False, {"error": str(exc)}


def generate_samples(style: WritingStyle) -> int:
    """
    Generiert Beispieltexte für alle Situationen.
    Gibt Anzahl der generierten Samples zurück.
    """
    from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

    if not style.style_prompt and not style.style_profile:
        return 0

    style_desc = style.style_prompt or style.style_profile[:500]
    count = 0

    router = LLMRouter()
    from apps.core.prompt_utils import render_prompt

    for situation_key, situation_label in SITUATIONS:
        if style.samples.filter(situation=situation_key).exists():
            continue
        try:
            prompt_msgs = render_prompt(
                "authors/generate_sample",
                style_desc=style_desc,
                situation_label=situation_label,
            )
            if not prompt_msgs:
                prompt_msgs = [
                    {"role": "system", "content": "Du bist ein Romanautor. Antworte nur mit dem Text."},
                    {"role": "user", "content": f"Schreibe einen Beispieltext für: {situation_label}"},
                ]
            result = router.completion(
                action_code="chapter_write",
                messages=prompt_msgs,
            )
            WritingStyleSample.objects.create(
                style=style,
                situation=situation_key,
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
