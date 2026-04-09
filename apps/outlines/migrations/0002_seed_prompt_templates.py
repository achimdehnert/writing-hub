"""
Seed data: Initial prompt templates for all 3 content-type groups × 2 template keys.
These match the current .jinja2 file templates but are now DB-backed,
versionable, and can be tuned per content-type without redeploying.
"""
from django.db import migrations


# ── Academic / Scientific prompts ───────────────────────────────────
ACADEMIC_ENRICH_SYSTEM = """\
Du bist ein erfahrener wissenschaftlicher Lektor und Strukturberater.
Du verbesserst und strukturierst Kapitel-Gliederungen fuer akademische/wissenschaftliche Texte.
Schreibe NIEMALS Fliesstext oder Prosa. Verwende Stichpunkte und Nummerierung.
Fokus: Forschungsfrage, Argumentation, Methodik, Quellen, logischer Aufbau.
Antworte AUSSCHLIESSLICH als JSON: {"description": "...", "emotional_arc": "..."}"""

ACADEMIC_ENRICH_USER = """\
Projekt-Kontext:
{{ context_block }}

{% if beat_phase %}Beat/Phase: {{ beat_phase }}{% endif %}
Abschnitt {{ order }}: {{ title }}
Ziel-Woerter: {{ target_words | default(3000) }}

Bisheriger Inhalt (VERBESSERE und STRUKTURIERE diesen, erfinde NICHTS Neues):
{{ description | default('(noch kein Inhalt)') }}

Erstelle eine STRUKTURIERTE Gliederung fuer diesen wissenschaftlichen Abschnitt (KEIN Fliesstext):
- 1) Zentrale These / Forschungsfrage dieses Abschnitts
- 2) Unterabschnitte (2-4 Stichpunkte mit Inhalt und Argumentationslinie)
- 3) Methodik / Vorgehen (falls relevant)
- 4) Erwartete Ergebnisse / Ueberleitung zum naechsten Abschnitt
- 5) Wichtige Quellen/Referenzen (falls im bisherigen Inhalt erwaehnt)

Antwort als JSON:
{"description": "1) These: ... 2) Unterabschnitte: a) ... b) ... 3) Methodik: ... 4) Ueberleitung: ... 5) Quellen: ...", "emotional_arc": "Argumentativer Bogen: von X ueber Y zu Z"}"""

ACADEMIC_DETAIL_SYSTEM = """\
Du bist ein erfahrener wissenschaftlicher Lektor und Strukturberater.
Du erstellst STRUKTURIERTE Gliederungen fuer akademische/wissenschaftliche Texte.
Schreibe NIEMALS Fliesstext oder Prosa. Verwende Stichpunkte und Nummerierung.
Fokus: Forschungsfrage, Argumentation, Methodik, Quellen, logischer Aufbau.
Antworte AUSSCHLIESSLICH als JSON."""

ACADEMIC_DETAIL_USER = """\
{{ context_block }}

{% if beat_phase %}Beat/Phase: {{ beat_phase }}{% endif %}
Abschnitt {{ order }}: {{ title }}
Ziel-Woerter: {{ target_words | default(3000) }}

Bisheriger Inhalt (VERBESSERE und STRUKTURIERE diesen, erfinde NICHTS Neues):
{{ description | default('(leer)') }}

Erstelle eine STRUKTURIERTE Gliederung fuer diesen wissenschaftlichen Abschnitt (KEIN Fliesstext):
- 1) Zentrale These / Forschungsfrage dieses Abschnitts
- 2) Unterabschnitte (2-4 Stichpunkte mit Inhalt und Argumentationslinie)
- 3) Methodik / Vorgehen (falls relevant)
- 4) Erwartete Ergebnisse / Ueberleitung zum naechsten Abschnitt
- 5) Wichtige Quellen/Referenzen (falls im bisherigen Inhalt erwaehnt)

Antwort als JSON:
{"description": "1) These: ... 2) Unterabschnitte: a) ... b) ... 3) Methodik: ... 4) Ueberleitung: ... 5) Quellen: ...", "emotional_arc": "Argumentativer Bogen: von X ueber Y zu Z"}"""


# ── Fiction prompts ─────────────────────────────────────────────────
FICTION_ENRICH_SYSTEM = """\
Du bist ein erfahrener Story-Planer und Lektor.
Du erstellst STRUKTURIERTE Kapitel-Outlines als Planungsdokument.
Schreibe NIEMALS Prosa, ausgeschriebene Szenen oder erzaehlenden Text.
Verwende: Stichpunkte, Szenen-Nummern, Kernkonflikte, Plot-Punkte.
Antworte AUSSCHLIESSLICH als JSON: {"description": "...", "emotional_arc": "..."}"""

FICTION_ENRICH_USER = """\
Projekt-Kontext:
{{ context_block }}

{% if beat_phase %}Beat/Phase: {{ beat_phase }}
Akt: {{ act }}{% endif %}
Kapitel {{ order }}: {{ title }}
Ziel-Woerter: {{ target_words | default(3000) }}

Bisheriger Inhalt (VERBESSERE und STRUKTURIERE diesen, erfinde NICHTS Neues):
{{ description | default('(noch kein Inhalt)') }}

Erstelle ein STRUKTURIERTES Kapitel-Outline (KEIN Prosa-Text, KEINE ausgeschriebene Szene):
- 1) Kernkonflikt des Kapitels
- 2) Szenen-Aufteilung (2-4 Szenen als Stichpunkte mit Ort und Handlung)
- 3) Wichtige Plot-Punkte
- 4) Kapitel-Ziel / Cliffhanger

Antwort als JSON:
{"description": "1) Kernkonflikt: ... 2) Szenen: ... 3) Plot-Punkte: ... 4) Kapitel-Ziel: ...", "emotional_arc": "Emotionaler Bogen in max 2 Saetzen"}"""

FICTION_DETAIL_SYSTEM = FICTION_ENRICH_SYSTEM.replace(
    '{"description": "...", "emotional_arc": "..."}',
    "",
).strip() + "\nAntworte AUSSCHLIESSLICH als JSON."

FICTION_DETAIL_USER = """\
{{ context_block }}

{% if beat_phase %}Beat/Phase: {{ beat_phase }}
Akt: {{ act }}{% endif %}
Kapitel {{ order }}: {{ title }}
Ziel-Woerter: {{ target_words | default(3000) }}

Bisheriger Inhalt (VERBESSERE und STRUKTURIERE diesen, erfinde NICHTS Neues):
{{ description | default('(leer)') }}

Erstelle ein STRUKTURIERTES Kapitel-Outline (KEIN Prosa-Text):
- 1) Kernkonflikt des Kapitels
- 2) Szenen-Aufteilung (2-4 Szenen als Stichpunkte mit Ort und Handlung)
- 3) Wichtige Plot-Punkte
- 4) Kapitel-Ziel / Ueberleitung zum naechsten Kapitel

Antwort als JSON:
{"description": "1) Kernkonflikt: ... 2) Szenen: ... 3) Plot-Punkte: ... 4) Kapitel-Ziel: ...", "emotional_arc": "Emotionaler Bogen in max 2 Saetzen"}"""


# ── Nonfiction prompts ──────────────────────────────────────────────
NONFICTION_ENRICH_SYSTEM = """\
Du bist ein erfahrener Sachbuch-Lektor und Strukturberater.
Du verbesserst und strukturierst Kapitel-Gliederungen fuer Sachtexte und Essays.
Schreibe NIEMALS Fliesstext oder Prosa. Verwende Stichpunkte und Nummerierung.
Fokus: Kernaussage, Argumentationsstruktur, Belege, Lesernutzen, roter Faden.
Antworte AUSSCHLIESSLICH als JSON: {"description": "...", "emotional_arc": "..."}"""

NONFICTION_ENRICH_USER = """\
Projekt-Kontext:
{{ context_block }}

{% if beat_phase %}Beat/Phase: {{ beat_phase }}{% endif %}
Abschnitt {{ order }}: {{ title }}
Ziel-Woerter: {{ target_words | default(3000) }}

Bisheriger Inhalt (VERBESSERE und STRUKTURIERE diesen, erfinde NICHTS Neues):
{{ description | default('(noch kein Inhalt)') }}

Erstelle eine STRUKTURIERTE Gliederung fuer diesen Sachtext-Abschnitt (KEIN Fliesstext):
- 1) Kernaussage / Leitfrage des Abschnitts
- 2) Unterabschnitte (2-4 Stichpunkte mit Inhalt und Argumentationslinie)
- 3) Beispiele / Belege / Daten (falls relevant)
- 4) Ueberleitung / Verbindung zum naechsten Abschnitt
- 5) Lesernutzen: Was lernt der Leser in diesem Abschnitt?

Antwort als JSON:
{"description": "1) Kernaussage: ... 2) Unterabschnitte: a) ... b) ... 3) Belege: ... 4) Ueberleitung: ... 5) Lesernutzen: ...", "emotional_arc": "Argumentativer Bogen: von X ueber Y zu Z"}"""

NONFICTION_DETAIL_SYSTEM = NONFICTION_ENRICH_SYSTEM.replace(
    '{"description": "...", "emotional_arc": "..."}',
    "",
).strip() + "\nAntworte AUSSCHLIESSLICH als JSON."

NONFICTION_DETAIL_USER = """\
{{ context_block }}

{% if beat_phase %}Beat/Phase: {{ beat_phase }}{% endif %}
Abschnitt {{ order }}: {{ title }}
Ziel-Woerter: {{ target_words | default(3000) }}

Bisheriger Inhalt (VERBESSERE und STRUKTURIERE diesen, erfinde NICHTS Neues):
{{ description | default('(leer)') }}

Erstelle eine STRUKTURIERTE Gliederung fuer diesen Sachtext-Abschnitt (KEIN Fliesstext):
- 1) Kernaussage / Leitfrage des Abschnitts
- 2) Unterabschnitte (2-4 Stichpunkte mit Inhalt und Argumentationslinie)
- 3) Beispiele / Belege / Daten (falls relevant)
- 4) Ueberleitung / Verbindung zum naechsten Abschnitt
- 5) Lesernutzen: Was lernt der Leser in diesem Abschnitt?

Antwort als JSON:
{"description": "1) Kernaussage: ... 2) Unterabschnitte: a) ... b) ... 3) Belege: ... 4) Ueberleitung: ... 5) Lesernutzen: ...", "emotional_arc": "Argumentativer Bogen: von X ueber Y zu Z"}"""


# ── Seed data ───────────────────────────────────────────────────────
SEED_TEMPLATES = [
    # Academic × enrich_node
    ("academic", "enrich_node", ACADEMIC_ENRICH_SYSTEM, ACADEMIC_ENRICH_USER),
    # Academic × detail_pass
    ("academic", "detail_pass", ACADEMIC_DETAIL_SYSTEM, ACADEMIC_DETAIL_USER),
    # Fiction × enrich_node
    ("fiction", "enrich_node", FICTION_ENRICH_SYSTEM, FICTION_ENRICH_USER),
    # Fiction × detail_pass
    ("fiction", "detail_pass", FICTION_DETAIL_SYSTEM, FICTION_DETAIL_USER),
    # Nonfiction × enrich_node
    ("nonfiction", "enrich_node", NONFICTION_ENRICH_SYSTEM, NONFICTION_ENRICH_USER),
    # Nonfiction × detail_pass
    ("nonfiction", "detail_pass", NONFICTION_DETAIL_SYSTEM, NONFICTION_DETAIL_USER),
]


def seed_templates(apps, schema_editor):
    OutlinePromptTemplate = apps.get_model("outlines", "OutlinePromptTemplate")
    for group, key, system, user in SEED_TEMPLATES:
        OutlinePromptTemplate.objects.create(
            content_type_group=group,
            template_key=key,
            system_prompt=system,
            user_prompt_template=user,
            version=1,
            is_active=True,
            notes="Initial seed from .jinja2 templates (v1)",
        )


def unseed_templates(apps, schema_editor):
    OutlinePromptTemplate = apps.get_model("outlines", "OutlinePromptTemplate")
    OutlinePromptTemplate.objects.filter(version=1, notes__startswith="Initial seed").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("outlines", "0001_prompt_templates_and_quality_ratings"),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]
