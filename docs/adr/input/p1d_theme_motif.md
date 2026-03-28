# Prio-1 · Schritt D — `ProjectTheme` & `ProjectMotif` Models

> **Ziel:** Neues `ProjectTheme` (1:1 zu `BookProject`) und `ProjectMotif`
> als DB-Objekte. Thema wird nie ausgesprochen — nur durch Figuren-Entscheidungen
> und Motive verkörpert. LLM-Generierung via `iil-aifw`.

---

## D.1 — Models (neue Datei: `apps/projects/models_theme.py`)

```python
"""
ProjectTheme & ProjectMotif — Thema und Motivsystem eines Buchprojekts.

Romanstruktur-Framework Schritt 7:
    - Thema als Frage + Antwort (nie ausgesprochen, immer gezeigt)
    - Motive als wiederkehrende Elemente mit Entwicklungsbogen

LLM-Generierung via iil-aifw (action_codes: theme_generate, motif_generate).
"""
import uuid
from django.db import models


class ProjectTheme(models.Model):
    """
    Thematisches Fundament eines Buchprojekts. 1:1 zu BookProject.

    Das Thema wird NIEMALS im Roman ausgesprochen.
    Es wird durch Figuren-Entscheidungen, Plot-Punkte und Motive verkörpert.

    these_character_id / antithese_character_id → WeltenHub-Referenzen.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="theme",
        verbose_name="Projekt",
    )

    # ── Kern-Thema ────────────────────────────────────────────────────────────
    core_question = models.TextField(
        verbose_name="Themen-Frage",
        help_text="Die offene Frage, die der Roman stellt. "
                  "Nicht moralisierend. Beispiel: 'Kann man vergeben, wenn man alles verloren hat?'",
    )
    thematic_answer = models.TextField(
        blank=True, default="",
        verbose_name="Themen-Antwort",
        help_text="Was antwortet der Roman durch sein Ende? "
                  "Wird NICHT ausgesprochen — nur durch Ereignisse gezeigt.",
    )

    # ── Verkörperung durch Figuren ────────────────────────────────────────────
    these_character_id = models.UUIDField(
        null=True, blank=True,
        verbose_name="These-Figur (WeltenHub UUID)",
        help_text="Figur, die die Themen-Antwort des Romans verkörpert.",
    )
    antithese_character_id = models.UUIDField(
        null=True, blank=True,
        verbose_name="Antithese-Figur (WeltenHub UUID)",
        help_text="Figur, die die Gegenposition verkörpert.",
    )

    # ── Verkörperung in Plot-Punkten ──────────────────────────────────────────
    inciting_incident_relevance = models.TextField(
        blank=True, default="",
        verbose_name="Thema im Inciting Incident",
        help_text="Wie stellt das Inciting Incident die Themen-Frage?",
    )
    midpoint_relevance = models.TextField(
        blank=True, default="",
        verbose_name="Thema im Midpoint",
        help_text="Wie verschärft der Midpoint die Themen-Frage?",
    )
    climax_relevance = models.TextField(
        blank=True, default="",
        verbose_name="Thema im Climax",
        help_text="Wie beantwortet der Climax-Moment die Themen-Frage?",
    )

    # ── Generierungs-Metadaten ─────────────────────────────────────────────────
    is_ai_generated = models.BooleanField(default=False)
    ai_agent = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_project_themes"
        verbose_name = "Projekt-Thema"
        verbose_name_plural = "Projekt-Themen"

    def __str__(self):
        return f"Thema — {self.project.title}: {self.core_question[:60]}"

    def to_prompt_context(self) -> str:
        """Gibt Thema als Prompt-Kontext zurück — für LLM-Szenen-Generierung."""
        lines = [f"THEMEN-FRAGE: {self.core_question}"]
        if self.thematic_answer:
            lines.append(f"THEMEN-RICHTUNG: {self.thematic_answer}")
        return "\n".join(lines)


class MotifTypeLookup(models.Model):
    """
    Lookup: Motiv-Typen.

    Seed-Werte:
        objekt    | Objekt-Motiv   | Ein konkretes Ding (Spiegel, Brief, Waffe)
        handlung  | Handlungs-Motiv| Eine wiederkehrende Handlung
        natur     | Natur-Motiv    | Wetter, Tiere, Landschaft
        farbe     | Farb-Motiv     | Eine Farbe mit symbolischer Bedeutung
        dialog    | Dialog-Motiv   | Eine wiederkehrende Phrase
        name      | Namen-Motiv    | Ein Name mit Bedeutung
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_motif_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Motiv-Typ"
        verbose_name_plural = "Motiv-Typen"

    def __str__(self):
        return self.label


class ProjectMotif(models.Model):
    """
    Ein wiederkehrendes Motiv im Roman.

    Motive müssen sich entwickeln — jedes Auftreten trägt eine neue Bedeutungsschicht.
    Erster Auftritt: beiläufig. Letzter Auftritt: trägt die volle symbolische Last.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="motifs",
        verbose_name="Projekt",
    )
    theme = models.ForeignKey(
        ProjectTheme,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="motifs",
        verbose_name="Thema",
        help_text="Das Thema, das dieses Motiv trägt.",
    )
    motif_type = models.ForeignKey(
        MotifTypeLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="motifs",
        verbose_name="Motiv-Typ",
    )

    label = models.CharField(
        max_length=200,
        verbose_name="Bezeichnung",
        help_text="z.B. 'Der Spiegel', 'Türen schließen', 'Die Farbe Rot'",
    )
    theme_connection = models.TextField(
        blank=True, default="",
        verbose_name="Thema-Bezug",
        help_text="Wie trägt dieses Motiv das Thema?",
    )
    evolution = models.TextField(
        blank=True, default="",
        verbose_name="Bedeutungsentwicklung",
        help_text="Wie verändert sich die Bedeutung über den Roman?",
    )
    payoff = models.TextField(
        blank=True, default="",
        verbose_name="Payoff",
        help_text="Was bedeutet das Motiv am Ende? Wie wird es eingelöst?",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Hauptmotiv",
        help_text="Hauptmotive tragen das Thema direkt. "
                  "Nebenmotive unterstützen, variieren oder kontrastieren.",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_motifs"
        ordering = ["-is_primary", "sort_order", "label"]
        verbose_name = "Projekt-Motiv"
        verbose_name_plural = "Projekt-Motive"

    def __str__(self):
        primary = " ★" if self.is_primary else ""
        return f"{self.label}{primary} ({self.project.title})"


class MotifAppearance(models.Model):
    """
    Einzelnes Auftreten eines Motivs in einer Szene/Kapitel.

    Jedes Auftreten trägt eine neue Bedeutungsschicht.
    Vier Auftritte = vollständiger Entwicklungsbogen.
    """
    PROMINENCE_CHOICES = [
        ("subtle",   "Beiläufig — Leser registriert es nicht bewusst"),
        ("charged",  "Aufgeladen — Leser beginnt Verbindungen herzustellen"),
        ("symbolic", "Symbolisch — Die Bedeutung wird klar/verändert sich"),
        ("payoff",   "Payoff — Trägt die volle symbolische Last"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    motif = models.ForeignKey(
        ProjectMotif,
        on_delete=models.CASCADE,
        related_name="appearances",
        verbose_name="Motiv",
    )
    node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.CASCADE,
        related_name="motif_appearances",
        verbose_name="Szene / Kapitel",
    )

    prominence = models.CharField(
        max_length=20,
        choices=PROMINENCE_CHOICES,
        default="subtle",
        verbose_name="Prominenz",
    )
    context = models.TextField(
        blank=True, default="",
        verbose_name="Kontext",
        help_text="Wie wird das Motiv in dieser Szene verwendet?",
    )
    meaning_at_this_point = models.TextField(
        blank=True, default="",
        verbose_name="Bedeutung an diesem Punkt",
        help_text="Was bedeutet das Motiv an dieser Stelle im Entwicklungsbogen?",
    )
    appearance_order = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Auftrittsnummer",
        help_text="1 = erste Einführung, 4 = Payoff",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_motif_appearances"
        ordering = ["motif", "appearance_order"]
        unique_together = [["motif", "node"]]
        verbose_name = "Motiv-Auftritt"
        verbose_name_plural = "Motiv-Auftritte"

    def __str__(self):
        return f"{self.motif.label} #{self.appearance_order} in {self.node.title}"
```

---

## D.2 — Migration: `apps/projects/migrations/0006_theme_motif.py`

```python
"""
Migration 0006: ProjectTheme, MotifTypeLookup, ProjectMotif, MotifAppearance.

Neue Tabellen:
    wh_project_themes
    wh_motif_type_lookup
    wh_project_motifs
    wh_motif_appearances
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_narrative_voice"),
    ]

    operations = [
        migrations.CreateModel(
            name="MotifTypeLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=80)),
                ("description", models.TextField(blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_motif_type_lookup", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="ProjectTheme",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("project", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="theme",
                    to="projects.bookproject",
                )),
                ("core_question", models.TextField(verbose_name="Themen-Frage")),
                ("thematic_answer", models.TextField(blank=True, default="")),
                ("these_character_id", models.UUIDField(blank=True, null=True)),
                ("antithese_character_id", models.UUIDField(blank=True, null=True)),
                ("inciting_incident_relevance", models.TextField(blank=True, default="")),
                ("midpoint_relevance", models.TextField(blank=True, default="")),
                ("climax_relevance", models.TextField(blank=True, default="")),
                ("is_ai_generated", models.BooleanField(default=False)),
                ("ai_agent", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_project_themes"},
        ),
        migrations.CreateModel(
            name="ProjectMotif",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("project", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="motifs",
                    to="projects.bookproject",
                )),
                ("theme", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="motifs",
                    to="projects.projecttheme",
                )),
                ("motif_type", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="motifs",
                    to="projects.motiftypelookup",
                )),
                ("label", models.CharField(max_length=200)),
                ("theme_connection", models.TextField(blank=True, default="")),
                ("evolution", models.TextField(blank=True, default="")),
                ("payoff", models.TextField(blank=True, default="")),
                ("is_primary", models.BooleanField(default=False)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_project_motifs",
                     "ordering": ["-is_primary", "sort_order", "label"]},
        ),
        migrations.CreateModel(
            name="MotifAppearance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("motif", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="appearances",
                    to="projects.projectmotif",
                )),
                ("node", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="motif_appearances",
                    to="projects.outlinenode",
                )),
                ("prominence", models.CharField(
                    default="subtle", max_length=20,
                    choices=[("subtle","Beiläufig"),("charged","Aufgeladen"),
                             ("symbolic","Symbolisch"),("payoff","Payoff")],
                )),
                ("context", models.TextField(blank=True, default="")),
                ("meaning_at_this_point", models.TextField(blank=True, default="")),
                ("appearance_order", models.PositiveSmallIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_motif_appearances",
                     "ordering": ["motif", "appearance_order"]},
        ),
        migrations.AddConstraint(
            model_name="motifappearance",
            constraint=models.UniqueConstraint(
                fields=["motif", "node"], name="unique_motif_node"
            ),
        ),
    ]
```

---

## D.3 — Service: `apps/projects/services/theme_service.py`

```python
"""
ThemeService — Generiert ProjectTheme und ProjectMotifs via LLM.

action_codes (in aifw Admin anlegen):
    theme_generate  → Thema aus Roman-Kern ableiten
    motif_generate  → Motivsystem entwickeln
"""
import json
from aifw.service import sync_completion
from projects.models import BookProject, ProjectTheme, ProjectMotif, MotifTypeLookup


THEME_SYSTEM = """
Du leitest das Thema eines Romans aus seinem Kern ab.
Das Thema wird nie ausgesprochen — es zeigt sich durch Ereignisse.
Antworte ausschließlich als valides JSON ohne Markdown-Fencing.
"""

THEME_USER = """
Leite das Thema für diesen Roman ab:

TITEL: {title}
GENRE: {genre}
ÄUSSERE GESCHICHTE: {outer_story}
INNERE GESCHICHTE: {inner_story}
ARC-TYP: {arc_direction}

Erstelle:
{{
  "core_question": "Die offene Fragen-Formulierung (nicht moralisierend)",
  "thematic_answer": "Was antwortet der Roman am Ende durch seine Ereignisse?",
  "inciting_incident_relevance": "Wie stellt das Inciting Incident die Frage?",
  "midpoint_relevance": "Wie verschärft der Midpoint die Frage?",
  "climax_relevance": "Wie beantwortet der Climax die Frage?",
  "motifs": [
    {{
      "label": "Bezeichnung des Motivs",
      "motif_type": "objekt | handlung | natur | farbe | dialog | name",
      "theme_connection": "Wie trägt es das Thema?",
      "evolution": "Wie entwickelt sich seine Bedeutung?",
      "payoff": "Was bedeutet es am Ende?",
      "is_primary": true
    }}
  ]
}}

Erstelle 2 Hauptmotive (is_primary=true) und 2-3 Nebenmotive.
"""


def generate_theme(project: BookProject) -> ProjectTheme:
    """
    Generiert ProjectTheme + ProjectMotifs via LLM.
    Gibt das gespeicherte ProjectTheme zurück.
    """
    result = sync_completion(
        action_code="theme_generate",
        messages=[
            {"role": "system", "content": THEME_SYSTEM},
            {"role": "user", "content": THEME_USER.format(
                title=project.title,
                genre=project.genre or (project.genre_lookup.name if project.genre_lookup else ""),
                outer_story=getattr(project, "outer_story", ""),
                inner_story=getattr(project, "inner_story", ""),
                arc_direction=getattr(project, "arc_direction", ""),
            )},
        ],
    )

    if not result.success:
        raise RuntimeError(f"LLM-Fehler: {result.error}")

    data = json.loads(result.content)

    # Theme speichern
    theme, _ = ProjectTheme.objects.update_or_create(
        project=project,
        defaults={
            "core_question": data["core_question"],
            "thematic_answer": data.get("thematic_answer", ""),
            "inciting_incident_relevance": data.get("inciting_incident_relevance", ""),
            "midpoint_relevance": data.get("midpoint_relevance", ""),
            "climax_relevance": data.get("climax_relevance", ""),
            "is_ai_generated": True,
            "ai_agent": "theme_generate",
        },
    )

    # Motive speichern
    for i, m in enumerate(data.get("motifs", [])):
        motif_type = None
        if m.get("motif_type"):
            motif_type = MotifTypeLookup.objects.filter(
                code=m["motif_type"]
            ).first()

        ProjectMotif.objects.get_or_create(
            project=project,
            label=m["label"],
            defaults={
                "theme": theme,
                "motif_type": motif_type,
                "theme_connection": m.get("theme_connection", ""),
                "evolution": m.get("evolution", ""),
                "payoff": m.get("payoff", ""),
                "is_primary": m.get("is_primary", False),
                "sort_order": i,
            },
        )

    return theme
```

---

## D.4 — Seed: MotifTypeLookup

```python
# In seed_drama_lookups.py ergänzen:
from projects.models import MotifTypeLookup

MOTIF_TYPES = [
    dict(code="objekt",   label="Objekt-Motiv",    sort_order=1,
         description="Ein konkretes Ding (Spiegel, Brief, Waffe)."),
    dict(code="handlung", label="Handlungs-Motiv",  sort_order=2,
         description="Eine wiederkehrende Handlung."),
    dict(code="natur",    label="Natur-Motiv",      sort_order=3,
         description="Wetter, Tiere, Landschaft."),
    dict(code="farbe",    label="Farb-Motiv",       sort_order=4,
         description="Eine Farbe mit symbolischer Bedeutung."),
    dict(code="dialog",   label="Dialog-Motiv",     sort_order=5,
         description="Eine wiederkehrende Phrase oder Aussage."),
    dict(code="name",     label="Namen-Motiv",      sort_order=6,
         description="Ein Name mit tieferer Bedeutung."),
]
self._seed(MotifTypeLookup, MOTIF_TYPES, "MotifTypeLookup")
```

---

## D.5 — Deployment

```bash
python manage.py migrate projects 0006_theme_motif
python manage.py seed_drama_lookups

# AIActionType anlegen:
#   code: theme_generate
#   model: claude-sonnet-4-5 (oder DB-konfiguriert)

# Verify
python manage.py shell -c "
from projects.models import ProjectTheme, ProjectMotif, MotifTypeLookup
print('MotifTypes:', MotifTypeLookup.objects.count())
# Test service
from projects.models import BookProject
p = BookProject.objects.first()
if p:
    from projects.services.theme_service import generate_theme
    print('Service importierbar:', True)
"
```

---

## D.6 — Gesamte Migrations-Reihenfolge (Prio-1 komplett)

```bash
# Schritt A
python manage.py migrate projects 0004_dramaturgic_fields

# Schritt B
python manage.py migrate worlds 0004_character_arc_fields

# Schritt C
python manage.py migrate projects 0005_narrative_voice

# Schritt D
python manage.py migrate projects 0006_theme_motif

# Alle Lookups auf einmal seeden
python manage.py seed_drama_lookups

# AIActionTypes in Admin anlegen:
#   character_arc_generate
#   theme_generate
```

---

## D.7 — Neue DB-Tabellen gesamt (Prio-1)

| Tabelle | Model | Schritt |
|---------|-------|---------|
| `wh_scene_outcome_lookup` | SceneOutcomeLookup | A |
| `wh_pov_type_lookup` | POVTypeLookup | A |
| `wh_tension_level_lookup` | TensionLevelLookup | A |
| `wh_character_arc_type_lookup` | CharacterArcTypeLookup | B |
| `wh_tempus_lookup` | TempusLookup | C |
| `wh_narrative_distance_lookup` | NarrativeDistanceLookup | C |
| `wh_vocabulary_level_lookup` | VocabularyLevelLookup | C |
| `wh_narrative_voices` | NarrativeVoice | C |
| `wh_project_themes` | ProjectTheme | D |
| `wh_motif_type_lookup` | MotifTypeLookup | D |
| `wh_project_motifs` | ProjectMotif | D |
| `wh_motif_appearances` | MotifAppearance | D |

---

*writing-hub · Prio-1 Schritt D von 4 · ProjectTheme & ProjectMotif*
*Packages: iil-aifw 0.9.0 · iil-outlinefw 0.1.1*
