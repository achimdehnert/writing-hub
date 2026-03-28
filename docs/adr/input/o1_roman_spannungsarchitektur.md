# writing-hub — Weitere Optimierungen: Übersicht

> Basis: Prio-1 (A–D) abgeschlossen.
> Zielformate: Roman, Serie, Essay / Sachbuch.

---

## Optimierungs-Roadmap

| Schritt | Bereich | Was | Impact |
|---------|---------|-----|--------|
| O1 | Roman | Spannungsarchitektur — `ForeshadowingEntry` + `ProjectTurningPoint` | 🔴 Hoch |
| O2 | Roman | `OutlineSequence` — Sequenz-Ebene zwischen Akt und Kapitel | 🟡 Mittel |
| O3 | Serie | `BookSeries` ausbauen — SeriesArc, SeriesTheme, CharacterContinuity | 🔴 Hoch |
| O4 | Essay | Essay-Struktur — `ArgumentNode`, `EssayOutline`, Argumentationskette | 🔴 Hoch |
| O5 | Alle | `MasterTimeline` + `CharacterKnowledgeState` — Zeitkonsistenz | 🟡 Mittel |
| O6 | Alle | `ContentTypeProfile` — Format-spezifische Generierungs-Config (DB) | 🟡 Mittel |

---
---

# O1 — Roman: Spannungsarchitektur

> `ForeshadowingEntry` + `ProjectTurningPoint` — die zwei fehlenden
> Spannung-Schichten aus Romanstruktur-Framework Schritt 6.

---

## O1.1 — Warum das jetzt wichtig ist

Nach Prio-1 kennt der Hub Szenen, Emotionen und Tension-Level.
Was noch fehlt: das **Versprechen-Einlösungs-System** (Foreshadowing)
und die **Wendepunkt-Positionen** als eigene persistente Objekte —
beides ist Voraussetzung für konsistente LLM-Generierung über viele Sitzungen.

---

## O1.2 — Models (in `apps/projects/models_tension.py`)

```python
"""
Spannungsarchitektur — ForeshadowingEntry + ProjectTurningPoint.

Romanstruktur-Framework Schritt 6:
    - Foreshadowing: Setup-Payoff-Paare (Chekhov's Gun)
    - TurningPoints: Wendepunkte mit Figur-Zustand als DB-Objekte

LLM: action_codes foreshadow_plan, turning_points_generate
"""
import uuid
from django.db import models


class ForeshadowingTypeLookup(models.Model):
    """
    Lookup: Foreshadowing-Typen.

    Seed-Werte:
        objekt   | Objekt        | Ein Gegenstand, der Bedeutung bekommt
        dialog   | Dialog        | Eine Aussage, die sich erfüllt
        bild     | Bild/Symbol   | Ein visuelles Element
        name     | Name          | Ein Name mit versteckter Bedeutung
        ereignis | Ereignis      | Eine Handlung, die sich wiederholt
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_foreshadowing_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Foreshadowing-Typ"
        verbose_name_plural = "Foreshadowing-Typen"

    def __str__(self):
        return self.label


class ForeshadowingEntry(models.Model):
    """
    Ein Foreshadowing-Payoff-Paar. Chekhov's Gun.

    Setup-Kapitel: beiläufige Einführung
    Payoff-Kapitel: Einlösung — MUSS existieren

    Regel: Kein Payoff ohne Setup. Kein Setup ohne Payoff.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="foreshadowing_entries",
    )
    foreshadow_type = models.ForeignKey(
        ForeshadowingTypeLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="entries",
    )

    label = models.CharField(
        max_length=200,
        verbose_name="Bezeichnung",
        help_text="z.B. 'Die Narbe an seiner Hand', 'Der halbfertige Brief'",
    )
    meaning = models.TextField(
        blank=True, default="",
        verbose_name="Echte Bedeutung",
        help_text="Was bedeutet dieses Element wirklich? (Leser erfährt es im Payoff)",
    )

    # Setup
    setup_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="foreshadowing_setups",
        verbose_name="Setup-Kapitel/-Szene",
    )
    setup_description = models.TextField(
        blank=True, default="",
        verbose_name="Wie einführen?",
        help_text="So unauffällig wie möglich. Leser darf es nicht als wichtig erkennen.",
    )

    # Payoff
    payoff_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="foreshadowing_payoffs",
        verbose_name="Payoff-Kapitel/-Szene",
    )
    payoff_description = models.TextField(
        blank=True, default="",
        verbose_name="Wie einlösen?",
    )

    # Status
    is_planted = models.BooleanField(
        default=False,
        verbose_name="Setup geschrieben",
        help_text="Wurde der Setup bereits in den Text eingebaut?",
    )
    is_paid_off = models.BooleanField(
        default=False,
        verbose_name="Payoff geschrieben",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_foreshadowing_entries"
        ordering = ["project", "sort_order"]
        verbose_name = "Foreshadowing-Eintrag"
        verbose_name_plural = "Foreshadowing-Einträge"

    def __str__(self):
        status = "✓" if self.is_paid_off else ("~" if self.is_planted else "○")
        return f"{status} {self.label} ({self.project.title})"

    @property
    def is_complete(self) -> bool:
        return self.is_planted and self.is_paid_off

    @property
    def gap_warning(self) -> bool:
        """True wenn Setup geschrieben aber kein Payoff-Node definiert."""
        return self.is_planted and not self.payoff_node


class TurningPointTypeLookup(models.Model):
    """
    Lookup: Wendepunkt-Typen — DB-gespiegelt aus outlinefw.FRAMEWORKS.

    Seed-Werte (aus three_act-Framework, erweiterbar):
        inciting_incident    | Inciting Incident      | 12%
        first_turning_point  | End of Act I           | 25%
        midpoint             | Midpoint               | 50%
        second_turning_point | All is Lost            | 75%
        climax               | Climax                 | 88%
        resolution           | Resolution             | 100%
    """
    code = models.SlugField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    default_position = models.DecimalField(
        max_digits=4, decimal_places=3,
        help_text="Standard-Position (0.0–1.0), aus outlinefw.BeatDefinition",
    )
    outlinefw_beat_name = models.CharField(
        max_length=80, blank=True,
        help_text="Mapping zu outlinefw.BeatDefinition.name",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_turning_point_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Wendepunkt-Typ"
        verbose_name_plural = "Wendepunkt-Typen"

    def __str__(self):
        return f"{self.label} ({int(self.default_position * 100)}%)"


class ProjectTurningPoint(models.Model):
    """
    Konkreter Wendepunkt eines Buchprojekts.

    Verbindet TurningPointTypeLookup mit konkretem Inhalt:
        - Was passiert genau?
        - Innerer + äußerer Zustand der Figur
        - Verknüpfung mit OutlineNode

    Wird nach Outline-Generierung automatisch aus outlinefw-Beats befüllt
    und dann manuell oder via LLM angereichert.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="turning_points",
    )
    turning_point_type = models.ForeignKey(
        TurningPointTypeLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="project_instances",
    )
    node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="turning_points",
        verbose_name="Anker-Kapitel/-Szene",
    )

    # Konkrete Position (kann von Default abweichen)
    position_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text="Position im Roman (0–100%)",
    )
    position_word = models.PositiveIntegerField(
        default=0,
        help_text="Entsprechende Wortzahl",
    )

    # Inhalt
    what_happens = models.TextField(
        blank=True, default="",
        verbose_name="Was passiert?",
    )
    character_state_inner = models.TextField(
        blank=True, default="",
        verbose_name="Innerer Zustand der Figur",
        help_text="Emotionen, Überzeugungen, Erkenntnis",
    )
    character_state_outer = models.TextField(
        blank=True, default="",
        verbose_name="Äußere Situation der Figur",
    )
    dramatic_function = models.TextField(
        blank=True, default="",
        verbose_name="Dramaturgische Funktion",
    )

    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_project_turning_points"
        ordering = ["project", "position_percent"]
        unique_together = [["project", "turning_point_type"]]
        verbose_name = "Wendepunkt"
        verbose_name_plural = "Wendepunkte"

    def __str__(self):
        tp_label = self.turning_point_type.label if self.turning_point_type else "?"
        return f"{self.project.title} — {tp_label} ({self.position_percent}%)"
```

---

## O1.3 — Migration: `0007_tension_architecture.py`

```python
"""Migration 0007: ForeshadowingEntry, TurningPoint-Modelle."""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0006_theme_motif")]

    operations = [
        migrations.CreateModel(
            name="ForeshadowingTypeLookup",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=80)),
                ("description", models.TextField(blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_foreshadowing_type_lookup", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="TurningPointTypeLookup",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=50, unique=True)),
                ("label", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("default_position", models.DecimalField(max_digits=4, decimal_places=3)),
                ("outlinefw_beat_name", models.CharField(max_length=80, blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_turning_point_type_lookup", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="ForeshadowingEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="foreshadowing_entries", to="projects.bookproject")),
                ("foreshadow_type", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="entries", to="projects.foreshadowingtypelookup")),
                ("setup_node", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="foreshadowing_setups", to="projects.outlinenode")),
                ("payoff_node", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="foreshadowing_payoffs", to="projects.outlinenode")),
                ("label", models.CharField(max_length=200)),
                ("meaning", models.TextField(blank=True, default="")),
                ("setup_description", models.TextField(blank=True, default="")),
                ("payoff_description", models.TextField(blank=True, default="")),
                ("is_planted", models.BooleanField(default=False)),
                ("is_paid_off", models.BooleanField(default=False)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_foreshadowing_entries"},
        ),
        migrations.CreateModel(
            name="ProjectTurningPoint",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="turning_points", to="projects.bookproject")),
                ("turning_point_type", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="project_instances", to="projects.turningpointtypelookup")),
                ("node", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="turning_points", to="projects.outlinenode")),
                ("position_percent", models.PositiveSmallIntegerField(default=0)),
                ("position_word", models.PositiveIntegerField(default=0)),
                ("what_happens", models.TextField(blank=True, default="")),
                ("character_state_inner", models.TextField(blank=True, default="")),
                ("character_state_outer", models.TextField(blank=True, default="")),
                ("dramatic_function", models.TextField(blank=True, default="")),
                ("is_ai_generated", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_project_turning_points",
                     "ordering": ["project", "position_percent"]},
        ),
        migrations.AddConstraint(
            model_name="projectturningpoint",
            constraint=models.UniqueConstraint(
                fields=["project", "turning_point_type"],
                name="unique_project_turning_point_type",
            ),
        ),
    ]
```

---

## O1.4 — Seed: Turning Points aus outlinefw synchronisieren

```python
# In seed_drama_lookups.py ergänzen:
from outlinefw.frameworks import FRAMEWORKS
from projects.models import TurningPointTypeLookup, ForeshadowingTypeLookup

def seed_turning_point_types():
    """
    Seed TurningPointTypeLookup aus outlinefw three_act-Framework.
    Idempotent — synchronisiert Beat-Positionen.
    """
    fw = FRAMEWORKS["three_act"]
    for i, beat in enumerate(fw.beats):
        TurningPointTypeLookup.objects.update_or_create(
            code=beat.name,
            defaults={
                "label": beat.name.replace("_", " ").title(),
                "description": beat.description,
                "default_position": beat.position,
                "outlinefw_beat_name": beat.name,
                "sort_order": i,
            },
        )

FORESHADOWING_TYPES = [
    dict(code="objekt",   label="Objekt",       sort_order=1),
    dict(code="dialog",   label="Dialog",       sort_order=2),
    dict(code="bild",     label="Bild/Symbol",  sort_order=3),
    dict(code="name",     label="Name",         sort_order=4),
    dict(code="ereignis", label="Ereignis",     sort_order=5),
]
```

---

## O1.5 — Service: `TurningPointSyncService`

```python
# apps/projects/services/turning_point_service.py
"""
TurningPointSyncService — befüllt ProjectTurningPoints
nach outlinefw-Generierung automatisch.
"""
from outlinefw.schemas import OutlineResult
from projects.models import (
    BookProject, ProjectTurningPoint, TurningPointTypeLookup, OutlineNode
)


def sync_turning_points_from_outline(
    project: BookProject,
    outline: OutlineResult,
    outline_nodes: list[OutlineNode],
) -> list[ProjectTurningPoint]:
    """
    Liest Turning Points aus outlinefw-Resultat und speichert sie als DB-Objekte.
    Verknüpft mit dem passenden OutlineNode über outlinefw_beat_name.
    """
    created = []
    node_by_beat = {n.outlinefw_beat_name: n for n in outline_nodes if n.outlinefw_beat_name}

    for fw_node in outline.nodes:
        if not fw_node.beat_name:
            continue
        tp_type = TurningPointTypeLookup.objects.filter(
            outlinefw_beat_name=fw_node.beat_name
        ).first()
        if not tp_type:
            continue

        db_node = node_by_beat.get(fw_node.beat_name)
        tp, _ = ProjectTurningPoint.objects.update_or_create(
            project=project,
            turning_point_type=tp_type,
            defaults={
                "node": db_node,
                "position_percent": int(fw_node.position * 100),
                "position_word": int((fw_node.position or 0) * (project.target_word_count or 90000)),
                "what_happens": fw_node.summary or "",
                "is_ai_generated": True,
            },
        )
        created.append(tp)

    return created
```

---

## O1.6 — Deployment

```bash
python manage.py migrate projects 0007_tension_architecture
python manage.py seed_drama_lookups   # befüllt TurningPointTypeLookup + ForeshadowingTypes

# Verify
python manage.py shell -c "
from projects.models import TurningPointTypeLookup, ForeshadowingTypeLookup
print('TurningPointTypes:', TurningPointTypeLookup.objects.count())   # sollte 7 sein
print('ForeshadowingTypes:', ForeshadowingTypeLookup.objects.count()) # sollte 5 sein
"
```

---

*writing-hub · Optimierung O1 · Roman Spannungsarchitektur*
*Packages: iil-outlinefw 0.1.1 (TurningLevel-Sync)*
