# O2 — Serie: `BookSeries` ausbauen

> Das bestehende `BookSeries`-Model hat nur `title`, `description`, `genre`.
> Für eine echte Serien-Dramaturgie fehlt: übergreifender Arc,
> Charakter-Kontinuität über Bände, geteiltes Thema, Serien-Chronologie.

---

## O2.1 — Analyse: Was fehlt

```
AKTUELL in apps/series/models.py:
    BookSeries     → title, description, genre (zu wenig)
    SeriesVolume   → series, project, volume_number (nur Reihenfolge)

FEHLT:
    SeriesArc         — übergreifender dramaturgischer Bogen
    SeriesTheme       — geteiltes Thema über alle Bände
    SeriesCharacterContinuity — Figur-Zustand am Ende jedes Bandes
    SeriesWorldState  — Welt-Zustand am Ende jedes Bandes (für Konsistenz)
    SeriesPromiseLog  — Was wird dem Leser versprochen? Was ist eingelöst?
```

---

## O2.2 — Models (neue Datei: `apps/series/models_arc.py`)

```python
"""
Serien-Dramaturgie — SeriesArc, SeriesTheme, CharacterContinuity.

Eine Buchserie ist mehr als eine Liste von Bänden.
Sie ist ein übergreifendes dramaturgisches System mit:
    - Eigenem Arc (Hauptfigur entwickelt sich über ALLE Bände)
    - Eigenem Thema (vertieft sich Band für Band)
    - Kontinuitäts-Tracking (was weiß/hat/ist die Figur am Ende von Band N?)
    - Serien-Versprechen (was erwartet der Leser in Band N+1?)
"""
import uuid
from django.db import models


class SeriesArcTypeLookup(models.Model):
    """
    Lookup: Serien-Arc-Typen.

    Seed-Werte:
        single_arc     | Durchgehender Arc  | Eine Figur, ein Arc über alle Bände
        anthology      | Anthologie         | Jeder Band eigenständig, lose verbunden
        escalating_arc | Eskalierender Arc  | Jeder Band erhöht die Einsätze
        dual_arc       | Doppel-Arc         | Haupt-Arc + Band-eigener Arc parallel
    """
    code = models.SlugField(max_length=30, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_series_arc_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Serien-Arc-Typ"
        verbose_name_plural = "Serien-Arc-Typen"

    def __str__(self):
        return self.label


class SeriesArc(models.Model):
    """
    Übergreifender dramaturgischer Arc einer Buchserie. 1:1 zu BookSeries.

    Der Serien-Arc ist die Geschichte ÜBER den einzelnen Bänden:
        - Die falsche Überzeugung, die über mehrere Bände abgebaut wird
        - Der übergreifende Antagonist / das übergreifende Hindernis
        - Die finale Transformation im letzten Band
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    series = models.OneToOneField(
        "series.BookSeries",
        on_delete=models.CASCADE,
        related_name="arc",
    )
    arc_type = models.ForeignKey(
        SeriesArcTypeLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="series_arcs",
    )

    # Übergreifende Dramaturgie
    series_want = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Want",
        help_text="Was verfolgt die Hauptfigur über ALLE Bände? "
                  "Konkreter als Einzel-Band-Want.",
    )
    series_need = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Need",
        help_text="Was braucht sie wirklich — wird erst im letzten Band klar.",
    )
    series_false_belief = models.TextField(
        blank=True, default="",
        verbose_name="Falsche Überzeugung (Serien-Start)",
    )
    series_true_belief = models.TextField(
        blank=True, default="",
        verbose_name="Wahre Erkenntnis (Serien-Ende)",
    )

    # Übergreifender Antagonist / Konflikt
    overarching_conflict = models.TextField(
        blank=True, default="",
        verbose_name="Übergreifender Konflikt",
        help_text="Das Hindernis / der Antagonist, der über alle Bände aktiv ist.",
    )

    # Serien-Thema
    series_theme_question = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Themen-Frage",
        help_text="Die Frage, die die gesamte Serie stellt — tiefer als die Einzel-Band-Themen.",
    )

    total_volumes_planned = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="Geplante Bände",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_series_arcs"
        verbose_name = "Serien-Arc"
        verbose_name_plural = "Serien-Arcs"

    def __str__(self):
        return f"Arc — {self.series.title}"


class SeriesVolumeRole(models.Model):
    """
    Dramaturgische Rolle eines Bandes innerhalb der Serien-Struktur.

    Erweitert SeriesVolume um:
        - Arc-Position (welchen Teil des Serien-Arcs trägt dieser Band?)
        - Serien-Versprechen (was verspricht dieser Band für den nächsten?)
        - Cliffhanger-Typ

    1:1 zu SeriesVolume.
    """
    VOLUME_ARC_POSITION = [
        ("opening",     "Eröffnung — Welt und Figuren einführen"),
        ("escalation",  "Eskalation — Einsätze erhöhen"),
        ("midpoint",    "Serien-Midpoint — alles dreht sich"),
        ("darkest",     "Dunkelster Band — alles scheint verloren"),
        ("climax_prep", "Climax-Vorbereitung"),
        ("finale",      "Finale — Serien-Arc auflösen"),
        ("standalone",  "Eigenständig (Anthologie)"),
    ]

    CLIFFHANGER_TYPES = [
        ("none",          "Kein Cliffhanger"),
        ("question",      "Offene Frage"),
        ("revelation",    "Enthüllung"),
        ("status_change", "Figurenstatus verändert"),
        ("threat",        "Neue Bedrohung etabliert"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    volume = models.OneToOneField(
        "series.SeriesVolume",
        on_delete=models.CASCADE,
        related_name="role",
    )
    arc_position = models.CharField(
        max_length=20,
        choices=VOLUME_ARC_POSITION,
        default="escalation",
        verbose_name="Arc-Position im Serien-Bogen",
    )

    # Was dieser Band für den Serien-Arc leistet
    series_arc_contribution = models.TextField(
        blank=True, default="",
        verbose_name="Beitrag zum Serien-Arc",
        help_text="Welchen Teil des Serien-Arcs trägt dieser Band?",
    )

    # Serien-Versprechen
    promise_to_reader = models.TextField(
        blank=True, default="",
        verbose_name="Versprechen an den Leser",
        help_text="Was verspricht dieses Buch für den nächsten Band?",
    )
    promise_fulfilled_from = models.TextField(
        blank=True, default="",
        verbose_name="Eingelöstes Versprechen",
        help_text="Welches Versprechen aus dem Vorgänger-Band wird hier eingelöst?",
    )

    # Cliffhanger
    cliffhanger_type = models.CharField(
        max_length=20,
        choices=CLIFFHANGER_TYPES,
        default="none",
    )
    cliffhanger_description = models.TextField(
        blank=True, default="",
        verbose_name="Cliffhanger-Beschreibung",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_series_volume_roles"
        verbose_name = "Serien-Band-Rolle"
        verbose_name_plural = "Serien-Band-Rollen"

    def __str__(self):
        return f"{self.volume} — {self.get_arc_position_display()}"


class SeriesCharacterContinuity(models.Model):
    """
    Figur-Zustand am Ende eines Bandes — für Kontinuität in Folgebänden.

    Problem ohne dieses Model:
        LLM beginnt Band 3 ohne zu wissen, was in Band 2 passiert ist.
        → Figur-Widersprüche, Wissens-Fehler, Arc-Brüche.

    Dieses Model ist der "Übergabe-Vertrag" zwischen Bänden.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    series = models.ForeignKey(
        "series.BookSeries",
        on_delete=models.CASCADE,
        related_name="character_continuities",
    )
    volume = models.ForeignKey(
        "series.SeriesVolume",
        on_delete=models.CASCADE,
        related_name="character_continuities",
        verbose_name="Am Ende von Band",
    )
    character_id = models.UUIDField(
        verbose_name="Figur (WeltenHub UUID)",
        help_text="WeltenHub-Referenz der Figur",
    )
    character_name = models.CharField(
        max_length=200,
        verbose_name="Figurenname (Cache)",
        help_text="Gecacht — vermeidet API-Call bei jeder Anzeige",
    )

    # Zustand am Ende des Bandes
    physical_state = models.TextField(
        blank=True, default="",
        verbose_name="Physischer Zustand",
        help_text="Verletzungen, Fähigkeiten, materielle Situation",
    )
    emotional_state = models.TextField(
        blank=True, default="",
        verbose_name="Emotionaler Zustand",
    )
    arc_progress = models.TextField(
        blank=True, default="",
        verbose_name="Arc-Fortschritt",
        help_text="Wie weit ist die Figur auf ihrem Serien-Arc?",
    )
    knowledge_gained = models.JSONField(
        default=list,
        verbose_name="Neu erworbenes Wissen",
        help_text="Was weiß die Figur jetzt, was sie am Anfang des Bandes nicht wusste?",
    )
    relationships_changed = models.JSONField(
        default=dict,
        verbose_name="Veränderte Beziehungen",
        help_text="{'figur_uuid': 'neue_beziehung'}",
    )
    unresolved_threads = models.JSONField(
        default=list,
        verbose_name="Offene Fäden",
        help_text="Was ist am Ende des Bandes noch nicht aufgelöst?",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_series_character_continuities"
        unique_together = [["series", "volume", "character_id"]]
        ordering = ["series", "volume__volume_number", "character_name"]
        verbose_name = "Figur-Kontinuität"
        verbose_name_plural = "Figur-Kontinuitäten"

    def __str__(self):
        return f"{self.character_name} — Ende Band {self.volume.volume_number}"

    def to_next_volume_context(self) -> str:
        """
        Gibt Kontext als Prompt-String für Band N+1 zurück.
        Direkt in LLM-Prompt injizierbar.
        """
        lines = [
            f"FIGUR: {self.character_name}",
            f"PHYSISCH: {self.physical_state}",
            f"EMOTIONAL: {self.emotional_state}",
            f"ARC-STAND: {self.arc_progress}",
        ]
        if self.knowledge_gained:
            lines.append(f"WEISSPUNKT: {'; '.join(self.knowledge_gained)}")
        if self.unresolved_threads:
            lines.append(f"OFFENE FÄDEN: {'; '.join(self.unresolved_threads)}")
        return "\n".join(lines)
```

---

## O2.3 — Migration: `apps/series/migrations/0003_series_arc.py`

```python
"""Migration 0003: SeriesArc, SeriesVolumeRole, SeriesCharacterContinuity."""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("series", "0002_sharedcharacter_sharedworld"),  # letzte series-Migration
        ("projects", "0007_tension_architecture"),
    ]

    operations = [
        migrations.CreateModel(
            name="SeriesArcTypeLookup",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=30, unique=True)),
                ("label", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_series_arc_type_lookup"},
        ),
        migrations.CreateModel(
            name="SeriesArc",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("series", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="arc", to="series.bookseries")),
                ("arc_type", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="series_arcs", to="series.seriesarctypelookup")),
                ("series_want", models.TextField(blank=True, default="")),
                ("series_need", models.TextField(blank=True, default="")),
                ("series_false_belief", models.TextField(blank=True, default="")),
                ("series_true_belief", models.TextField(blank=True, default="")),
                ("overarching_conflict", models.TextField(blank=True, default="")),
                ("series_theme_question", models.TextField(blank=True, default="")),
                ("total_volumes_planned", models.PositiveSmallIntegerField(default=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_series_arcs"},
        ),
        migrations.CreateModel(
            name="SeriesVolumeRole",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("volume", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="role", to="series.seriesvolume")),
                ("arc_position", models.CharField(default="escalation", max_length=20)),
                ("series_arc_contribution", models.TextField(blank=True, default="")),
                ("promise_to_reader", models.TextField(blank=True, default="")),
                ("promise_fulfilled_from", models.TextField(blank=True, default="")),
                ("cliffhanger_type", models.CharField(default="none", max_length=20)),
                ("cliffhanger_description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_series_volume_roles"},
        ),
        migrations.CreateModel(
            name="SeriesCharacterContinuity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("series", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="character_continuities", to="series.bookseries")),
                ("volume", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="character_continuities", to="series.seriesvolume")),
                ("character_id", models.UUIDField()),
                ("character_name", models.CharField(max_length=200)),
                ("physical_state", models.TextField(blank=True, default="")),
                ("emotional_state", models.TextField(blank=True, default="")),
                ("arc_progress", models.TextField(blank=True, default="")),
                ("knowledge_gained", models.JSONField(default=list)),
                ("relationships_changed", models.JSONField(default=dict)),
                ("unresolved_threads", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_series_character_continuities"},
        ),
        migrations.AddConstraint(
            model_name="seriescharactercontinuity",
            constraint=models.UniqueConstraint(
                fields=["series", "volume", "character_id"],
                name="unique_series_volume_character",
            ),
        ),
    ]
```

---

## O2.4 — Service: `SeriesContinuityService`

```python
# apps/series/services/continuity_service.py
"""
SeriesContinuityService — generiert Kontinuitäts-Kontext für Folgebände.

Wird aufgerufen bei: "Neues Projekt für Band N+1 starten"
Injiziert: Figur-Zustände aus Band N in den Authoring-Kontext.
"""
import json
from aifw.service import sync_completion
from series.models import BookSeries, SeriesVolume, SeriesCharacterContinuity


def build_continuity_context(series: BookSeries, for_volume_number: int) -> str:
    """
    Erstellt Prompt-Kontext für Band `for_volume_number`
    aus den Kontinuitäts-Daten des Vorgänger-Bandes.
    """
    prev_volume = SeriesVolume.objects.filter(
        series=series,
        volume_number=for_volume_number - 1,
    ).first()

    if not prev_volume:
        return ""

    continuities = SeriesCharacterContinuity.objects.filter(
        series=series, volume=prev_volume
    ).order_by("character_name")

    if not continuities.exists():
        return ""

    lines = [f"=== KONTINUITÄT AUS BAND {for_volume_number - 1} ==="]
    for c in continuities:
        lines.append(c.to_next_volume_context())
        lines.append("")

    # Offene Versprechen aus VolumeRole
    try:
        role = prev_volume.role
        if role.promise_to_reader:
            lines.append(f"VERSPRECHEN AN LESER: {role.promise_to_reader}")
        if role.cliffhanger_description:
            lines.append(f"CLIFFHANGER: {role.cliffhanger_description}")
    except SeriesVolume.role.RelatedObjectDoesNotExist:
        pass

    return "\n".join(lines)


def generate_continuity_snapshot(
    series: BookSeries,
    volume: SeriesVolume,
    character_ids: list,
) -> list[SeriesCharacterContinuity]:
    """
    Generiert Kontinuitäts-Snapshots für alle Figuren am Ende eines Bandes.
    Nutzt iil-aifw action: series_continuity_extract
    """
    from projects.models import OutlineNode
    from worlds.models import ProjectCharacterLink

    results = []
    project = volume.project

    # Lade alle Kapitel-Inhalte des Bandes
    nodes_content = "\n\n".join([
        f"Kapitel {n.order}: {n.title}\n{n.content[:500]}"
        for n in OutlineNode.objects.filter(
            outline_version__project=project,
            outline_version__is_active=True,
        ).order_by("order")[:20]
    ])

    for char_id in character_ids:
        link = ProjectCharacterLink.objects.filter(
            project=project,
            weltenhub_character_id=char_id,
        ).first()
        if not link:
            continue

        result = sync_completion(
            action_code="series_continuity_extract",
            messages=[{
                "role": "user",
                "content": f"""
Analysiere den Zustand von Figur '{link.authoringfw_role}' am Ende dieses Bandes.

FIGUR ARC: {link.want} / {link.need} / {link.arc_progress if hasattr(link, 'arc_progress') else ''}
KAPITEL-AUSZÜGE:
{nodes_content}

Antworte als JSON:
{{
  "physical_state": "...",
  "emotional_state": "...",
  "arc_progress": "...",
  "knowledge_gained": ["..."],
  "relationships_changed": {{"char_uuid": "neue_beziehung"}},
  "unresolved_threads": ["..."]
}}"""
            }],
        )

        if result.success:
            data = json.loads(result.content)
            cont, _ = SeriesCharacterContinuity.objects.update_or_create(
                series=series, volume=volume, character_id=char_id,
                defaults={
                    "character_name": getattr(link, "voice_description", "")[:200] or str(char_id)[:20],
                    **data,
                },
            )
            results.append(cont)

    return results
```

---

## O2.5 — Seed: SeriesArcTypeLookup

```python
SERIES_ARC_TYPES = [
    dict(code="single_arc",     label="Durchgehender Arc",   sort_order=1,
         description="Eine Figur, ein Arc über alle Bände."),
    dict(code="anthology",      label="Anthologie",          sort_order=2,
         description="Jeder Band eigenständig, lose verbunden."),
    dict(code="escalating_arc", label="Eskalierender Arc",   sort_order=3,
         description="Jeder Band erhöht die Einsätze."),
    dict(code="dual_arc",       label="Doppel-Arc",          sort_order=4,
         description="Haupt-Arc + band-eigener Arc parallel."),
]
```

---

## O2.6 — Deployment

```bash
python manage.py migrate series 0003_series_arc
python manage.py seed_drama_lookups

# AIActionType anlegen:
#   series_continuity_extract
```

---

*writing-hub · Optimierung O2 · Serie Dramaturgie-Ausbauu*
*Neue Tabellen: wh_series_arcs, wh_series_volume_roles, wh_series_character_continuities*
