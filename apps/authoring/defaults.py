"""
Authoring — Zentrale Defaults (SSoT).

Alle numerischen Grenzwerte, Timeouts, Fallback-Defaults und
String-Konstanten für Kapitel-Generierung, Polling und UI.
Von Views, Handlers, Tasks und Templates importiert.
Keine Magic Numbers/Strings in View-/Handler-Dateien!
"""

# ── Domain Defaults ──────────────────────────────────────────────
DEFAULT_CONTENT_TYPE = "novel"
"""Fallback content_type wenn kein Projekt-Typ gesetzt."""

DEFAULT_CITATION_STYLE = "APA"
"""Standard-Zitierstil."""

DEFAULT_AUDIENCE = "Fachpublikum"
"""Standard-Zielgruppe (Quick-Project)."""

DEFAULT_FRAMEWORK = "academic_essay"
"""Standard-Framework (Quick-Project)."""

# ── Word Counts ──────────────────────────────────────────────────
DEFAULT_TARGET_WORD_COUNT = 2000
"""Fallback-Wortanzahl pro Kapitel wenn weder Projekt noch Node einen Wert hat."""

DEFAULT_PROJECT_TARGET_WORDS = 5000
"""Fallback Gesamt-Wortanzahl für ein Projekt (Quick Project etc.)."""

# ── LLM / Token Limits ──────────────────────────────────────────
MAX_TOKENS_WRITE = 4096
"""Max Tokens für Kapitel-Generierung (write_single, chunk)."""

MAX_TOKENS_REFINE = 8000
"""Max Tokens für Kapitel-Verfeinerung (refine_chapter)."""

MIN_TOKENS_WRITE = 2000
"""Minimum Tokens für Einzelkapitel-Generierung."""

# ── Prompt Context Truncation ────────────────────────────────────
CHUNK_CONTEXT_WINDOW = 3000
"""Max Zeichen aus bisherigem Inhalt als Kontext für Chunks."""

RESEARCH_NOTES_MAX_CHARS = 3000
"""Max Zeichen für Recherche-Notizen im Prompt-Kontext."""

PREV_CHAPTER_SUMMARY_MAX_CHARS = 600
"""Max Zeichen für Zusammenfassung des vorherigen Kapitels."""

NEXT_CHAPTER_OUTLINE_MAX_CHARS = 200
"""Max Zeichen für Outline des nächsten Kapitels."""

CHAR_DESC_MAX_CHARS = 200
"""Max Zeichen für Charakter-Beschreibung im Prompt-Kontext."""

CHAR_MOTIVATION_MAX_CHARS = 150
"""Max Zeichen für Charakter-Motivation im Prompt-Kontext."""

WORLD_DESC_MAX_CHARS = 300
"""Max Zeichen für Welt-Beschreibung im Prompt-Kontext."""

WORLD_ATMOSPHERE_MAX_CHARS = 150
"""Max Zeichen für Welt-Atmosphäre im Prompt-Kontext."""

STYLE_PROMPT_MAX_CHARS = 400
"""Max Zeichen für Style-Prompt im Kontext."""

VOICE_PATTERN_MAX_CHARS = 120
"""Max Zeichen für Voice-Pattern im Kontext."""

LOGLINE_MAX_CHARS = 200
"""Max Zeichen für Logline-Fallback aus Beschreibung."""

ADDITIONAL_NOTES_MAX_CHARS = 500
"""Max Zeichen für zusätzliche Notizen im Outline-Kontext."""

RESEARCH_QUESTION_MAX_CHARS = 300
"""Max Zeichen für Forschungsfrage-Fallback."""

CHAPTER_CONTENT_MAX_CHARS = 8000
"""Max Zeichen für Kapitel-Inhalt in LLM-Reviews."""

FEEDBACK_MAX_CHARS = 2000
"""Max Zeichen für LLM-Feedback-Speicherung."""

SUMMARY_MAX_CHARS = 500
"""Max Zeichen für Zusammenfassungen (Peer-Review etc.)."""

TEXT_REF_MAX_CHARS = 500
"""Max Zeichen für Text-Referenzen in Findings."""

CHAPTER_EXCERPT_MAX_CHARS = 1200
"""Max Zeichen für Kapitel-Auszug in Voice-Drift-Analyse."""

NOTES_PREVIEW_MAX_CHARS = 500
"""Max Zeichen für Notizen-Vorschau."""

ABSTRACT_MAX_CHARS = 300
"""Max Zeichen für Paper-Abstract-Vorschau."""

# ── Prompt Context List Limits ───────────────────────────────────
MAX_CHARACTERS_IN_PROMPT = 5
"""Max Anzahl Charaktere im Prompt-Kontext."""

MAX_WORLDS_IN_PROMPT = 2
"""Max Anzahl Welten im Prompt-Kontext."""

MAX_STYLE_DO_ITEMS = 8
"""Max DO-Einträge im Style-Kontext."""

MAX_STYLE_DONT_ITEMS = 5
"""Max DONT-Einträge im Style-Kontext."""

MAX_STYLE_SIGNATURE_MOVES = 5
"""Max Signature-Moves im Style-Kontext."""

MAX_STYLE_TABOO_ITEMS = 10
"""Max Tabu-Wörter im Style-Kontext."""

MAX_REVIEW_FINDINGS = 10
"""Max Findings pro Review-Durchlauf."""

MAX_LEKTORAT_FINDINGS = 10
"""Max Findings pro Lektorat-Durchlauf."""

MAX_STYLE_SUGGESTIONS = 15
"""Max Style-Suggestions pro Durchlauf."""

MAX_QUALITY_ISSUES = 3
"""Max Quality-Issues für Revise-Entscheidung."""

# ── Polling (JS-seitig, via template context) ────────────────────
POLL_INTERVAL_MS = 2500
"""Polling-Intervall in Millisekunden für Job-Status."""

POLL_MAX_COUNT = 120
"""Max Polling-Versuche (120 × 2.5s = 5 min)."""

AUTOSAVE_DELAY_MS = 2000
"""Autosave-Delay in Millisekunden nach letzter Eingabe."""

# ── Generation Counts ────────────────────────────────────────────
DEFAULT_GENERATE_CHARACTER_COUNT = 3
"""Default Anzahl Charaktere bei LLM-Generierung."""

DEFAULT_GENERATE_LOCATION_COUNT = 3
"""Default Anzahl Orte bei LLM-Generierung."""

DEFAULT_BRAINSTORM_COUNT = 5
"""Default Anzahl Ideen bei Brainstorming."""

# ── UI Defaults ──────────────────────────────────────────────────
DEFAULT_CHAPTER_COUNT = 12
"""Default Kapitelanzahl beim Outline-Erstellen."""

TOAST_DISPLAY_MS = 5000
"""Toast-Anzeigdauer in Millisekunden."""

# ── Chunk Continuation ──────────────────────────────────────────
CHUNK_TARGET_RATIO = 0.80
"""Minimum ratio of actual/target words before continuation kicks in."""

CHUNK_MAX_CONTINUATIONS = 3
"""Max continuation rounds for underweight chapters."""

# ── Chapter Word Count Distribution ─────────────────────────────
CHAPTER_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "novel": {"first": 0.80, "last": 0.85},
    "academic": {"first": 0.70, "last": 0.70},
    "essay": {"first": 0.85, "last": 0.85},
    "default": {"first": 0.85, "last": 0.85},
}
"""Position-aware weight multipliers per content type.

'first'/'last' are fractions of the average chapter length.
Middle chapters auto-fill to hit the total target.
"""


def distribute_chapter_targets(
    project_target: int,
    chapter_count: int,
    content_type: str = "novel",
    *,
    round_to: int = 100,
) -> list[int]:
    """Distribute project word target across chapters by position weight.

    Intro/conclusion chapters get less, middle chapters get more.
    Always sums exactly to ``project_target``.

    Returns:
        List of per-chapter targets, length == chapter_count.

    >>> distribute_chapter_targets(55000, 5, "novel")
    [8800, 12800, 12800, 12800, 7800]
    """
    if chapter_count <= 0:
        return []
    if chapter_count == 1:
        return [project_target]

    profile = CHAPTER_WEIGHT_PROFILES.get(
        content_type, CHAPTER_WEIGHT_PROFILES["default"]
    )
    avg = project_target / chapter_count

    def _round(v: float) -> int:
        return int(round(v / round_to) * round_to) if round_to > 0 else int(v)

    first = _round(avg * profile["first"])
    last = _round(avg * profile["last"])

    middle_count = chapter_count - 2
    if middle_count > 0:
        remaining = project_target - first - last
        middle = _round(remaining / middle_count)
        targets = [first] + [middle] * middle_count + [last]
    else:
        targets = [first, last]

    # Adjust last chapter so sum == project_target exactly
    targets[-1] += project_target - sum(targets)
    return targets


# ── Fallback Chapter Titles ──────────────────────────────────────
FALLBACK_CHAPTER_TITLES = (
    "Einleitung",
    "Theoretischer Rahmen",
    "Methodik",
    "Ergebnisse & Analyse",
    "Fazit & Ausblick",
)
"""Standard-Kapiteltitel für akademische Essays ohne Framework."""
