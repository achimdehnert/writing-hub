"""
Projects — Zentrale Konstanten (SSoT).

Alle UI-Choices, Agent-Definitionen, Farben und Validierungs-Sets
werden hier definiert und von Views/Services importiert.
Keine Duplikate in View-Dateien!
"""

# ── Research & Citations ──────────────────────────────────────────

BIBLIOGRAPHY_STYLES = [
    ("apa", "APA 7"),
    ("mla", "MLA 9"),
    ("chicago", "Chicago 17"),
    ("harvard", "Harvard"),
    ("ieee", "IEEE"),
    ("vancouver", "Vancouver"),
]

SEARCH_SOURCES = [
    ("arxiv", "arXiv", "#f59e0b"),
    ("semantic_scholar", "Semantic Scholar", "#a78bfa"),
    ("pubmed", "PubMed", "#34d399"),
    ("openalex", "OpenAlex", "#60a5fa"),
]

VALID_SEARCH_SOURCES = frozenset(src_id for src_id, _, _ in SEARCH_SOURCES)

SUMMARY_STYLES = [
    ("scientific", "Wissenschaftlich", "#7dd3fc"),
    ("complex", "Komplex / Fachpublikum", "#a78bfa"),
    ("medium", "Allgemein informiert", "#86efac"),
    ("simple", "Einfache Sprache", "#fbbf24"),
]

SUMMARY_CITATION_FORMATS = [
    ("inline", "Inline [Autor Jahr]"),
    ("bibliography", "Literaturliste [1][2]"),
    ("none", "Keine Zitate"),
]

# ── Publishing ────────────────────────────────────────────────────

LANGUAGE_CHOICES = [
    ("de", "Deutsch"),
    ("en", "Englisch"),
    ("fr", "Französisch"),
    ("es", "Spanisch"),
    ("it", "Italienisch"),
    ("nl", "Niederländisch"),
    ("pt", "Portugiesisch"),
]

AGE_CHOICES = [
    ("0", "Allgemein (ab 0)"),
    ("6", "Kinder (ab 6)"),
    ("10", "Kinder (ab 10)"),
    ("12", "Jugendliche (ab 12)"),
    ("16", "Jugendliche (ab 16)"),
    ("18", "Erwachsene (ab 18)"),
]

BISAC_CHOICES = [
    ("FIC000000", "Fiction / General"),
    ("FIC002000", "Fiction / Action & Adventure"),
    ("FIC009000", "Fiction / Fantasy"),
    ("FIC010000", "Fiction / Historical"),
    ("FIC022000", "Fiction / Mystery & Detective"),
    ("FIC028000", "Fiction / Science Fiction"),
    ("FIC027000", "Fiction / Romance"),
    ("FIC031000", "Fiction / Thrillers / General"),
    ("NON000000", "Nonfiction / General"),
    ("SEL000000", "Self-Help"),
    ("BIO000000", "Biography & Autobiography"),
    ("JUV000000", "Juvenile Fiction"),
    ("YAF000000", "Young Adult Fiction"),
]

PUBLISHING_STATUS_CHOICES = [
    ("draft", "Entwurf"),
    ("review", "In Review"),
    ("ready", "Druckfertig"),
    ("published", "Veröffentlicht"),
]

PUBLISHING_STATUS_COLORS = {
    "draft": "#f59e0b",
    "review": "#6366f1",
    "ready": "#22c55e",
    "published": "#0ea5e9",
}

# ── AI Review Agents ──────────────────────────────────────────────

AI_REVIEW_AGENTS = [
    {"key": "style_critic", "name": "Stil-Kritiker", "icon": "bi-brush",
     "description": "Analysiert Schreibstil, Sprache und Ausdrucksweise"},
    {"key": "story_editor", "name": "Story-Editor", "icon": "bi-diagram-3",
     "description": "Prüft Handlung, Charakterkonsistenz und Pacing"},
    {"key": "lector", "name": "Lektor", "icon": "bi-check2-square",
     "description": "Findet Fehler, Widersprüche und Schwachstellen"},
    {"key": "beta_reader", "name": "Beta-Leser", "icon": "bi-person-raised-hand",
     "description": "Gibt Leserperspektive und emotionale Reaktion"},
    {"key": "genre_expert", "name": "Genre-Experte", "icon": "bi-award",
     "description": "Bewertet Genre-Konventionen und Erwartungen"},
]

# ── Peer Review (Scientific) ─────────────────────────────────────

PEER_REVIEW_AGENTS = [
    {
        "key": "methodology",
        "name": "Methodik-Prüfer",
        "icon": "bi-clipboard-data",
        "description": "Prüft Forschungsdesign, Validität, Reliabilität und Reproduzierbarkeit",
        "prompt_template": "projects/peer_review_methodology",
    },
    {
        "key": "argumentation",
        "name": "Argumentations-Prüfer",
        "icon": "bi-diagram-3",
        "description": "Prüft Logik, Evidenz, Kausalität und Bias",
        "prompt_template": "projects/peer_review_argumentation",
    },
    {
        "key": "sources",
        "name": "Quellen-Prüfer",
        "icon": "bi-journal-bookmark",
        "description": "Prüft Quellenabdeckung, Aktualität und Zitierethik",
        "prompt_template": "projects/peer_review_sources",
    },
    {
        "key": "structure",
        "name": "Struktur-Prüfer",
        "icon": "bi-list-nested",
        "description": "Prüft Gliederung, Kohärenz und akademische Konventionen",
        "prompt_template": "projects/peer_review_structure",
    },
]

VALID_FINDING_TYPES = frozenset({"strength", "weakness", "suggestion", "concern"})
VALID_SEVERITIES = frozenset({"minor", "major", "critical"})
SCIENTIFIC_CONTENT_TYPES = frozenset({"scientific", "academic", "essay"})

# ── Content Types (fallback when DB lookups unavailable) ──────────

DEFAULT_CONTENT_TYPES = [
    {"slug": "roman", "name": "Roman", "icon": "bi-book",
     "subtitle": "Erzählung mit Charakteren & Weltenbau",
     "workflow_hint": "Konzept → Charaktere → Outline → Schreiben"},
    {"slug": "sachbuch", "name": "Sachbuch", "icon": "bi-journal-text",
     "subtitle": "Ratgeber, Biographie, How-To oder Sachtext",
     "workflow_hint": "Thema → Struktur → Kapitel → Schreiben"},
    {"slug": "kurzgeschichte", "name": "Kurzgeschichte", "icon": "bi-file-text",
     "subtitle": "Kurze Erzählung mit klarer Pointe",
     "workflow_hint": "Idee → Outline → Schreiben"},
    {"slug": "drehbuch", "name": "Drehbuch", "icon": "bi-camera-video",
     "subtitle": "Skript für Film, Serie oder Theater",
     "workflow_hint": "Konzept → Struktur → Szenen → Schreiben"},
    {"slug": "essay", "name": "Essay", "icon": "bi-pencil-square",
     "subtitle": "Argumentativer Text zu einem Thema",
     "workflow_hint": "These → Recherche → Gliederung → Schreiben"},
    {"slug": "novelle", "name": "Novelle", "icon": "bi-journal",
     "subtitle": "Mittellange Erzählung mit einem Wendepunkt",
     "workflow_hint": "Konzept → Outline → Schreiben"},
    {"slug": "graphic-novel", "name": "Graphic Novel", "icon": "bi-image",
     "subtitle": "Bild-Text-Erzählung, Comic-Format",
     "workflow_hint": "Story → Panels → Dialoge → Zeichnung"},
    {"slug": "academic", "name": "Akademische Arbeit", "icon": "bi-mortarboard",
     "subtitle": "Monographie, Dissertation, Abschlussarbeit",
     "workflow_hint": "Thema → Recherche → Gliederung → Schreiben"},
    {"slug": "scientific", "name": "Wissenschaftliches Paper", "icon": "bi-journals",
     "subtitle": "IMRaD-Struktur, Fachartikel",
     "workflow_hint": "Hypothese → Methodik → Ergebnisse → Diskussion"},
]

# ── Framework Fallbacks ───────────────────────────────────────────

FW_BEATS_FALLBACK = {
    "three_act": 6, "save_the_cat": 15, "heros_journey": 12,
    "five_act": 5, "dan_harmon": 8, "blank": 0,
}

FW_LABELS_FALLBACK = {
    "three_act": "Drei-Akt-Struktur",
    "save_the_cat": "Save the Cat",
    "heros_journey": "Heldenreise",
    "five_act": "Fünf-Akt-Struktur",
    "dan_harmon": "Dan Harmon Story Circle",
    "blank": "Leere Kapitel",
}
