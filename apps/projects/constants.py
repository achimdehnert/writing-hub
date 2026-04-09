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

# ── Content Types (fallback when DB ContentTypeLookup is empty) ───

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

# ── Slug-Mapping: ContentTypeLookup.slug → BookProject.ContentType ─
#
# ContentTypeLookup (DB) uses German slugs for UI display.
# BookProject.content_type (CharField) uses English enum values.
# This dict bridges the two systems.

LOOKUP_SLUG_TO_MODEL_CONTENT_TYPE = {
    "roman": "novel",
    "sachbuch": "nonfiction",
    "kurzgeschichte": "short_story",
    "drehbuch": "screenplay",
    "essay": "essay",
    "novelle": "novel",
    "graphic-novel": "novel",
    "academic": "academic",
    "scientific": "scientific",
}

# ── Framework → BookProject.ContentType (Quick-Project Pipeline) ──

FRAMEWORK_TO_CONTENT_TYPE = {
    "academic_essay": "academic",
    "scientific_essay": "scientific",
    "imrad": "scientific",
    "dissertation": "academic",
    "expose": "academic",
    "systematic_review": "scientific",
    "research_proposal": "academic",
    "essay": "essay",
    "three_act": "novel",
}

# ── Format-Profile (aus universal_writing_prompt_framework.md) ────
#
# Keyed by BookProject.ContentType values.
# Encodiert die Profil-Metadaten aus dem Universal Writing Prompt Framework.

FORMAT_PROFILES = {
    "novel": {
        "profile": "A",
        "label": "Roman / Kurzgeschichte",
        "structure": "Akt | Kapitel | Szene",
        "pflicht_meta": [
            "genre", "pov", "zeitform", "ton", "hauptfigur",
            "antagonist", "setting", "kernthema", "zielgruppe",
        ],
        "quality_criteria": "show-don't-tell, subtext, sensorische Details",
        "citation": "keine",
        "outline_logic": "Drei-Akt | Heldenreise | Fünf-Akt | Snowflake",
    },
    "short_story": {
        "profile": "A",
        "label": "Kurzgeschichte",
        "structure": "Akt | Szene",
        "pflicht_meta": [
            "genre", "pov", "zeitform", "ton", "hauptfigur",
            "setting", "kernthema", "zielgruppe",
        ],
        "quality_criteria": "show-don't-tell, subtext, sensorische Details",
        "citation": "keine",
        "outline_logic": "Drei-Akt | Heldenreise | Snowflake",
    },
    "essay": {
        "profile": "B",
        "label": "Essay (akademisch / literarisch)",
        "structure": "Einleitung | Hauptteil (Argumente) | Schluss",
        "pflicht_meta": [
            "these", "zielgruppe", "ton", "sprache", "zitationsstil",
        ],
        "quality_criteria": "argumentative Dichte, Originalität, Stilsicherheit",
        "citation": "optional (akademisch: Pflicht)",
        "outline_logic": "These → Argument → Gegenargument → Synthese",
    },
    "scientific": {
        "profile": "C",
        "label": "Wissenschaftlicher Aufsatz / Paper",
        "structure": "IMRaD | Einleitung–Theorie–Methode–Ergebnis–Diskussion–Fazit",
        "pflicht_meta": [
            "forschungsfrage", "methode", "fachgebiet", "zielgruppe",
            "zitationsstil", "wortlimit", "keywords",
        ],
        "quality_criteria": "Präzision, Replizierbarkeit, Belegpflicht, Objektivität",
        "citation": "Pflicht (APA 7 | IEEE | Chicago | Vancouver)",
        "outline_logic": "Forschungsfrage → Lücke → Methode → Befund → Implikation",
        "default_bib_style": "apa",
    },
    "academic": {
        "profile": "E",
        "label": "Dissertation / Monographie / Seminararbeit",
        "structure": "Kapitel (typ. 5–8) + Anhang + Literaturverzeichnis",
        "pflicht_meta": [
            "forschungsfrage", "forschungsluecke", "methode", "fachgebiet",
            "betreuer", "universitaet", "zitationsstil", "sprache",
            "umfang_seiten", "keywords",
        ],
        "quality_criteria": "methodische Strenge, theoretische Tiefe, empirische Fundierung",
        "citation": "Pflicht (konsistentes System)",
        "outline_logic": "Forschungslücke → Theorierahmen → Methodik → Empirie → Diskussion",
        "default_bib_style": "apa",
    },
    "nonfiction": {
        "profile": "F",
        "label": "Sachbuch / Ratgeber / Handbuch",
        "structure": "Kapitel | Unterkapitel | Praxisboxen",
        "pflicht_meta": [
            "thema", "zielgruppe", "ton", "kernbotschaft", "usp",
            "kapitelanzahl", "zitationsstil",
        ],
        "quality_criteria": "Zugänglichkeit, Praxisrelevanz, klare Sprache",
        "citation": "optional (Quellenangaben empfohlen)",
        "outline_logic": "Problem → Lösung → Praxis → Vertiefung",
    },
    "screenplay": {
        "profile": "A",
        "label": "Drehbuch / Skript",
        "structure": "Akte | Szenen | Beats",
        "pflicht_meta": [
            "genre", "ton", "hauptfigur", "antagonist",
            "setting", "kernthema", "zielgruppe",
        ],
        "quality_criteria": "show-don't-tell, Dialog-Authentizität, Visual Storytelling",
        "citation": "keine",
        "outline_logic": "Drei-Akt | Save the Cat | Fünf-Akt",
    },
}

# ── Content-Type Groups (for outline prompt dispatch) ─────────────

CONTENT_TYPE_GROUPS = {
    "novel": "fiction",
    "short_story": "fiction",
    "screenplay": "fiction",
    "academic": "academic",
    "scientific": "academic",
    "essay": "nonfiction",
    "nonfiction": "nonfiction",
}

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
