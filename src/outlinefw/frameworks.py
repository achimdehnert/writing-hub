"""
outlinefw.frameworks — Story Structure Framework Definitions

Zentrale Quelle für alle Beat-Strukturen.
Keine Django-Abhängigkeit.
"""
from __future__ import annotations

from typing import TypedDict


class BeatDefinition(TypedDict):
    name: str
    position: float       # 0.0 – 1.0 relative position in story
    act: str              # act_1 | act_2a | act_2b | act_3
    description: str
    tension: str          # low | medium | high | peak


class FrameworkDefinition(TypedDict):
    name: str
    description: str
    beats: list[str]
    beat_details: list[BeatDefinition]


FRAMEWORKS: dict[str, FrameworkDefinition] = {
    "three_act": {
        "name": "Drei-Akt-Struktur",
        "description": "Klassisch: Setup, Konfrontation, Auflösung",
        "beats": [
            "Setup", "Inciting Incident", "Rising Action",
            "Midpoint", "Crisis", "Climax", "Resolution",
        ],
        "beat_details": [
            {"name": "Setup",            "position": 0.00, "act": "act_1",  "description": "Welt und Charakter etablieren",        "tension": "low"},
            {"name": "Inciting Incident","position": 0.12, "act": "act_1",  "description": "Auslöser der Geschichte",               "tension": "medium"},
            {"name": "Rising Action",    "position": 0.25, "act": "act_2a", "description": "Konflikte eskalieren",                  "tension": "medium"},
            {"name": "Midpoint",         "position": 0.50, "act": "act_2a", "description": "Falscher Sieg oder Niederlage",         "tension": "high"},
            {"name": "Crisis",           "position": 0.75, "act": "act_2b", "description": "Alles scheint verloren",                "tension": "peak"},
            {"name": "Climax",           "position": 0.88, "act": "act_3",  "description": "Höhepunkt und Entscheidung",            "tension": "peak"},
            {"name": "Resolution",       "position": 1.00, "act": "act_3",  "description": "Neue Normalität nach der Reise",        "tension": "low"},
        ],
    },
    "save_the_cat": {
        "name": "Save the Cat",
        "description": "Blake Snyder's 15-Beat Sheet",
        "beats": [
            "Opening Image", "Theme Stated", "Set-Up", "Catalyst",
            "Debate", "Break into Two", "B Story", "Fun and Games",
            "Midpoint", "Bad Guys Close In", "All Is Lost",
            "Dark Night of the Soul", "Break into Three",
            "Finale", "Final Image",
        ],
        "beat_details": [
            {"name": "Opening Image",        "position": 0.00, "act": "act_1",  "description": "Snapshot vor der Transformation",   "tension": "low"},
            {"name": "Theme Stated",         "position": 0.05, "act": "act_1",  "description": "Thema wird angedeutet",             "tension": "low"},
            {"name": "Set-Up",               "position": 0.10, "act": "act_1",  "description": "Charakter in alter Welt",           "tension": "low"},
            {"name": "Catalyst",             "position": 0.12, "act": "act_1",  "description": "Auslöser",                          "tension": "medium"},
            {"name": "Debate",               "position": 0.18, "act": "act_1",  "description": "Innerer Konflikt / Zögern",         "tension": "medium"},
            {"name": "Break into Two",       "position": 0.25, "act": "act_2a", "description": "Entschluss: neue Welt betreten",    "tension": "medium"},
            {"name": "B Story",              "position": 0.30, "act": "act_2a", "description": "B-Story beginnt (oft Liebesgeschichte)", "tension": "medium"},
            {"name": "Fun and Games",        "position": 0.38, "act": "act_2a", "description": "Versprechen der Prämisse",          "tension": "medium"},
            {"name": "Midpoint",             "position": 0.50, "act": "act_2a", "description": "Falscher Sieg / Niederlage",        "tension": "high"},
            {"name": "Bad Guys Close In",    "position": 0.58, "act": "act_2b", "description": "Antagonisten verstärken Druck",     "tension": "high"},
            {"name": "All Is Lost",          "position": 0.75, "act": "act_2b", "description": "Tiefpunkt — alles verloren",        "tension": "peak"},
            {"name": "Dark Night of the Soul","position": 0.80, "act": "act_2b", "description": "Innere Leere vor Wandel",          "tension": "peak"},
            {"name": "Break into Three",     "position": 0.83, "act": "act_3",  "description": "A+B Story verschmelzen",            "tension": "high"},
            {"name": "Finale",               "position": 0.88, "act": "act_3",  "description": "Synthese, Beweis, Showdown, Finale","tension": "peak"},
            {"name": "Final Image",          "position": 1.00, "act": "act_3",  "description": "Spiegelbild zu Opening Image",      "tension": "low"},
        ],
    },
    "heros_journey": {
        "name": "Heldenreise",
        "description": "Joseph Campbell's Monomyth",
        "beats": [
            "Gewöhnliche Welt", "Ruf des Abenteuers", "Weigerung",
            "Mentor", "Schwellenüberschreitung", "Tests und Gefährten",
            "Nähe zur tiefsten Höhle", "Bewährungsprobe",
            "Belohnung", "Rückweg", "Auferstehung", "Rückkehr mit dem Elixier",
        ],
        "beat_details": [
            {"name": "Gewöhnliche Welt",          "position": 0.00, "act": "act_1",  "description": "Held in vertrauter Welt",           "tension": "low"},
            {"name": "Ruf des Abenteuers",         "position": 0.10, "act": "act_1",  "description": "Aufruf zur Veränderung",            "tension": "low"},
            {"name": "Weigerung",                  "position": 0.15, "act": "act_1",  "description": "Held lehnt zunächst ab",            "tension": "medium"},
            {"name": "Mentor",                     "position": 0.20, "act": "act_1",  "description": "Mentor gibt Hilfsmittel",           "tension": "low"},
            {"name": "Schwellenüberschreitung",    "position": 0.25, "act": "act_2a", "description": "Eintritt in unbekannte Welt",       "tension": "medium"},
            {"name": "Tests und Gefährten",        "position": 0.38, "act": "act_2a", "description": "Prüfungen, Feinde und Freunde",     "tension": "medium"},
            {"name": "Nähe zur tiefsten Höhle",    "position": 0.50, "act": "act_2a", "description": "Vorbereitung auf größten Kampf",   "tension": "high"},
            {"name": "Bewährungsprobe",             "position": 0.62, "act": "act_2b", "description": "Größte Krise",                     "tension": "peak"},
            {"name": "Belohnung",                  "position": 0.70, "act": "act_2b", "description": "Held ergreift Preis",              "tension": "high"},
            {"name": "Rückweg",                    "position": 0.78, "act": "act_3",  "description": "Rückweg mit Konsequenzen",         "tension": "high"},
            {"name": "Auferstehung",               "position": 0.88, "act": "act_3",  "description": "Letzte Prüfung / Transformation",  "tension": "peak"},
            {"name": "Rückkehr mit dem Elixier",   "position": 1.00, "act": "act_3",  "description": "Held kehrt verändert zurück",      "tension": "low"},
        ],
    },
    "five_act": {
        "name": "Fünf-Akt-Struktur",
        "description": "Shakespeareanische Struktur",
        "beats": [
            "Exposition", "Steigende Handlung", "Höhepunkt",
            "Fallende Handlung", "Katastrophe/Auflösung",
        ],
        "beat_details": [
            {"name": "Exposition",           "position": 0.00, "act": "act_1",  "description": "Einführung Charaktere und Welt",     "tension": "low"},
            {"name": "Steigende Handlung",   "position": 0.25, "act": "act_2a", "description": "Komplikationen eskalieren",          "tension": "medium"},
            {"name": "Höhepunkt",            "position": 0.50, "act": "act_2b", "description": "Wendepunkt / Klimax",                "tension": "peak"},
            {"name": "Fallende Handlung",    "position": 0.75, "act": "act_3",  "description": "Konsequenzen des Höhepunkts",        "tension": "high"},
            {"name": "Katastrophe/Auflösung","position": 1.00, "act": "act_3",  "description": "Finale Auflösung",                   "tension": "medium"},
        ],
    },
    "dan_harmon": {
        "name": "Dan Harmon Story Circle",
        "description": "8-Schritt-Kreisstruktur (Community/Rick & Morty)",
        "beats": [
            "You", "Need", "Go", "Search",
            "Find", "Take", "Return", "Change",
        ],
        "beat_details": [
            {"name": "You",    "position": 0.00, "act": "act_1",  "description": "Charakter in Komfortzone",              "tension": "low"},
            {"name": "Need",   "position": 0.12, "act": "act_1",  "description": "Charakter will/braucht etwas",          "tension": "low"},
            {"name": "Go",     "position": 0.25, "act": "act_2a", "description": "Betritt unbekannte Situation",          "tension": "medium"},
            {"name": "Search", "position": 0.38, "act": "act_2a", "description": "Adaptiert, sucht, braucht",             "tension": "medium"},
            {"name": "Find",   "position": 0.50, "act": "act_2a", "description": "Bekommt was er wollte",                 "tension": "high"},
            {"name": "Take",   "position": 0.62, "act": "act_2b", "description": "Zahlt einen Preis dafür",              "tension": "peak"},
            {"name": "Return", "position": 0.75, "act": "act_3",  "description": "Kehrt in bekannte Situation zurück",    "tension": "high"},
            {"name": "Change", "position": 1.00, "act": "act_3",  "description": "Ist verändert durch die Erfahrung",    "tension": "low"},
        ],
    },
}


def get_framework(key: str) -> FrameworkDefinition:
    """Framework by key, fallback to three_act."""
    return FRAMEWORKS.get(key, FRAMEWORKS["three_act"])


def list_frameworks() -> list[dict]:
    """Alle Frameworks als Liste für UI-Selects."""
    return [
        {"key": k, "name": v["name"], "description": v["description"]}
        for k, v in FRAMEWORKS.items()
    ]
