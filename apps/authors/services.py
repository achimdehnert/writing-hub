"""
Authors — LLM-Service für Stil-Analyse und Beispieltext-Generierung.
"""
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
    Gibt True bei Erfolg zurück.
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

    system = (
        "Du bist ein erfahrener Literaturkritiker und Schreibcoach.\n"
        "Analysiere den folgenden Text und erstelle ein detailliertes Stilprofil.\n"
        "Antworte auf Deutsch in klar strukturierten Abschnitten."
    )
    user = (
        f"Analysiere folgenden Text und erstelle ein detailliertes Stilprofil:\n\n"
        f"{text[:4000]}\n\n"
        "Erstelle das Stilprofil mit folgenden Abschnitten:\n"
        "## Satzstruktur & Rhythmus\n"
        "## Wortwahl & Vokabular\n"
        "## Perspektive & Erzählstimme\n"
        "## Tonalität & Atmosphäre\n"
        "## Besondere Merkmale\n"
        "## Stil-Prompt (1-2 Sätze für LLM-Instruktion)\n"
    )

    try:
        router = LLMRouter()
        result = router.completion(
            action_code="style_check",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        # Style-Prompt extrahieren (letzter Abschnitt)
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
    system = (
        "Du bist ein professioneller Romanautor.\n"
        "Schreibe kurze Beispieltexte (150-250 Wörter) in einem vorgegebenen Schreibstil.\n"
        "Antworte nur mit dem Text, keine Erklärungen oder Metainformationen."
    )

    for situation_key, situation_label in SITUATIONS:
        # Nur generieren wenn noch kein Sample für diese Situation
        if style.samples.filter(situation=situation_key).exists():
            continue
        try:
            user = (
                f"Schreibstil-Profil:\n{style_desc}\n\n"
                f"Schreibe einen Beispieltext für folgende Situation: {situation_label}\n"
                f"Der Text soll exakt diesen Schreibstil nachahmen. 150-250 Wörter."
            )
            result = router.completion(
                action_code="chapter_write",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
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
    Präferenz: style_prompt > style_profile[:300]
    """
    if style.style_prompt:
        return style.style_prompt
    if style.style_profile:
        return style.style_profile[:300]
    return ""
