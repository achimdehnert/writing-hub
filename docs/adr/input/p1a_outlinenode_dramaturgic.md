# Prio-1 · Schritt A — `OutlineNode` dramaturgische Felder

> **Ziel:** `OutlineNode` bekommt die dramaturgischen Pflichtfelder aus dem Romanstruktur-Framework.
> Kompatibel mit `iil-outlinefw` (ActPhase / TensionLevel Enums).
> DB-getrieben via neue Lookup-Tabellen.

---

## A.1 — Neue Lookup-Models (neue Datei: `apps/projects/models_lookups_drama.py`)

```python
"""
Dramaturgische Lookup-Tabellen — DB-getrieben, Admin-verwaltbar.
Kompatibel mit iil-outlinefw ActPhase / TensionLevel.
"""
from django.db import models


class SceneOutcomeLookup(models.Model):
    """
    Lookup: Szenen-/Kapitel-Outcome nach dem YES/NO-System.
    Wird DB-getrieben befüllt — kein Hardcoding im Code.

    Seed-Werte (management command):
        yes       | Ja               | Figur erreicht ihr Ziel
        no        | Nein             | Figur scheitert, Dinge werden schlimmer
        yes_but   | Ja, aber...      | Teilsieg mit Preis
        no_and    | Nein, und dazu.. | Scheitern + neue Komplikation
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    tension_delta = models.SmallIntegerField(
        default=0,
        help_text="Typische Spannungsveränderung (+/-) nach diesem Outcome"
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_scene_outcome_lookup"
        ordering = ["sort_order"]
        verbose_name = "Szenen-Outcome"
        verbose_name_plural = "Szenen-Outcomes"

    def __str__(self):
        return f"{self.code} — {self.label}"


class POVTypeLookup(models.Model):
    """
    Lookup: Erzählperspektive.
    Kompatibel mit authoringfw.StyleProfile.pov.

    Seed-Werte:
        first              | Ich-Erzähler
        third_limited      | Dritte Person limitiert (empfohlen)
        third_omniscient   | Dritte Person allwissend
        second             | Du-Form (experimentell)
    """
    code = models.SlugField(max_length=30, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    authoringfw_key = models.CharField(
        max_length=30, blank=True,
        help_text="Mapping zu authoringfw.StyleProfile.pov"
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_pov_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "POV-Typ"
        verbose_name_plural = "POV-Typen"

    def __str__(self):
        return self.label


class TensionLevelLookup(models.Model):
    """
    Lookup: Spannungsniveaus — gespiegelt aus outlinefw.TensionLevel.

    Seed-Werte (exakt aus iil-outlinefw TensionLevel enum):
        low    | Niedrig  | 1-3  | outlinefw: 'low'
        medium | Mittel   | 4-6  | outlinefw: 'medium'
        high   | Hoch     | 7-8  | outlinefw: 'high'
        peak   | Maximum  | 9-10 | outlinefw: 'peak'
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=50)
    numeric_min = models.PositiveSmallIntegerField(default=1)
    numeric_max = models.PositiveSmallIntegerField(default=10)
    outlinefw_key = models.CharField(
        max_length=20, blank=True,
        help_text="Mapping zu outlinefw.TensionLevel enum value"
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_tension_level_lookup"
        ordering = ["sort_order"]
        verbose_name = "Spannungsniveau"
        verbose_name_plural = "Spannungsniveaus"

    def __str__(self):
        return f"{self.label} ({self.numeric_min}–{self.numeric_max})"
```

---

## A.2 — `OutlineNode` erweitern (in `apps/projects/models.py`)

Füge die folgenden Felder zur bestehenden `OutlineNode`-Klasse hinzu:

```python
# --- DRAMATURGISCHE FELDER (Romanstruktur-Framework Schritt 4) ---

# Szenen-Outcome (YES/NO-System)
outcome = models.ForeignKey(
    "projects.SceneOutcomeLookup",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="outline_nodes",
    verbose_name="Outcome",
    help_text="YES | NO | YES_BUT | NO_AND — dramaturgisches Ergebnis",
)

# Emotionaler Deltawert
emotion_start = models.CharField(
    max_length=100, blank=True, default="",
    verbose_name="Emotion Anfang",
    help_text="Emotionaler Ausgangswert der POV-Figur (z.B. 'hoffnungsvoll')",
)
emotion_end = models.CharField(
    max_length=100, blank=True, default="",
    verbose_name="Emotion Ende",
    help_text="Emotionaler Endwert — muss sich von emotion_start unterscheiden",
)

# Spannungsniveau
tension_level = models.ForeignKey(
    "projects.TensionLevelLookup",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="outline_nodes",
    verbose_name="Spannungsniveau",
    help_text="Mapping zu outlinefw.TensionLevel",
)
tension_numeric = models.PositiveSmallIntegerField(
    null=True, blank=True,
    verbose_name="Spannung (1–10)",
    help_text="Numerischer Spannungswert für Kurven-Visualisierung",
)

# POV
pov_character_id = models.UUIDField(
    null=True, blank=True,
    verbose_name="POV-Figur (WeltenHub UUID)",
    help_text="WeltenHub-Referenz der POV-Figur für diese Szene/Kapitel",
)
pov_type = models.ForeignKey(
    "projects.POVTypeLookup",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="outline_nodes",
    verbose_name="POV-Typ",
)

# Sequel
sequel_needed = models.BooleanField(
    default=False,
    verbose_name="Sequel nötig",
    help_text="Braucht es nach dieser Szene eine Reaktions-Szene?",
)

# Zeitstruktur
story_timeline_position = models.CharField(
    max_length=100, blank=True, default="",
    verbose_name="Story-Zeitpunkt",
    help_text="Position in der Story-Chronologie (z.B. 'Tag 3, 14:00')",
)
story_duration = models.CharField(
    max_length=100, blank=True, default="",
    verbose_name="Story-Dauer",
    help_text="Wie lange dauert diese Szene/dieses Kapitel in der Story? (z.B. '2 Stunden')",
)

# outlinefw-Mapping
outlinefw_beat_name = models.CharField(
    max_length=80, blank=True, default="",
    verbose_name="outlinefw Beat Name",
    help_text="Mapping zu outlinefw.BeatDefinition.name (z.B. 'inciting_incident')",
)
outlinefw_position = models.DecimalField(
    max_digits=4, decimal_places=3,
    null=True, blank=True,
    verbose_name="outlinefw Position (0.0–1.0)",
    help_text="Normierte Position im Framework (aus outlinefw.BeatDefinition.position)",
)
```

---

## A.3 — Migration: `apps/projects/migrations/0004_dramaturgic_fields.py`

```python
"""
Migration 0004: Dramaturgische Felder für OutlineNode + neue Lookup-Tabellen.

Neue Tabellen:
    wh_scene_outcome_lookup
    wh_pov_type_lookup
    wh_tension_level_lookup

Neue Felder auf wh_outline_nodes:
    outcome_id, emotion_start, emotion_end,
    tension_level_id, tension_numeric,
    pov_character_id, pov_type_id, sequel_needed,
    story_timeline_position, story_duration,
    outlinefw_beat_name, outlinefw_position
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_publishingprofile"),   # ← anpassen an letzte Migration
    ]

    operations = [
        # ── 1. Lookup-Tabellen anlegen ──────────────────────────────────────
        migrations.CreateModel(
            name="SceneOutcomeLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=80)),
                ("description", models.TextField(blank=True)),
                ("tension_delta", models.SmallIntegerField(default=0)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_scene_outcome_lookup", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="POVTypeLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=30, unique=True)),
                ("label", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("authoringfw_key", models.CharField(max_length=30, blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_pov_type_lookup", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="TensionLevelLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=50)),
                ("numeric_min", models.PositiveSmallIntegerField(default=1)),
                ("numeric_max", models.PositiveSmallIntegerField(default=10)),
                ("outlinefw_key", models.CharField(max_length=20, blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_tension_level_lookup", "ordering": ["sort_order"]},
        ),

        # ── 2. OutlineNode: FK-Felder ────────────────────────────────────────
        migrations.AddField(
            model_name="outlinenode",
            name="outcome",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="outline_nodes",
                to="projects.sceneoutcomelookup",
                verbose_name="Outcome",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="tension_level",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="outline_nodes",
                to="projects.tensionlevellookup",
                verbose_name="Spannungsniveau",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="pov_type",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="outline_nodes",
                to="projects.povtypelookup",
                verbose_name="POV-Typ",
            ),
        ),

        # ── 3. OutlineNode: einfache Felder ─────────────────────────────────
        migrations.AddField(
            model_name="outlinenode",
            name="emotion_start",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Emotion Anfang"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="emotion_end",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Emotion Ende"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="tension_numeric",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Spannung (1–10)"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="pov_character_id",
            field=models.UUIDField(blank=True, null=True, verbose_name="POV-Figur (WeltenHub UUID)"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="sequel_needed",
            field=models.BooleanField(default=False, verbose_name="Sequel nötig"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="story_timeline_position",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Story-Zeitpunkt"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="story_duration",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Story-Dauer"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="outlinefw_beat_name",
            field=models.CharField(blank=True, default="", max_length=80, verbose_name="outlinefw Beat Name"),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="outlinefw_position",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True, verbose_name="outlinefw Position (0.0–1.0)"),
        ),
    ]
```

---

## A.4 — Seed Management Command: `apps/projects/management/commands/seed_drama_lookups.py`

```python
"""
python manage.py seed_drama_lookups

Befüllt die dramaturgischen Lookup-Tabellen.
Idempotent (get_or_create).
Kompatibel mit outlinefw.TensionLevel und authoringfw.StyleProfile.pov.
"""
from django.core.management.base import BaseCommand
from projects.models import SceneOutcomeLookup, POVTypeLookup, TensionLevelLookup


SCENE_OUTCOMES = [
    dict(code="yes",     label="Ja",              tension_delta=-1, sort_order=1,
         description="Figur erreicht ihr Ziel vollständig."),
    dict(code="no",      label="Nein",             tension_delta=+2, sort_order=2,
         description="Figur scheitert, Situation verschlimmert sich."),
    dict(code="yes_but", label="Ja, aber...",       tension_delta=+1, sort_order=3,
         description="Teilsieg — Ziel erreicht, aber mit Preis oder Komplikation."),
    dict(code="no_and",  label="Nein, und dazu...", tension_delta=+3, sort_order=4,
         description="Scheitern plus neue, zusätzliche Komplikation."),
]

POV_TYPES = [
    dict(code="first",            label="Ich-Erzähler",                    authoringfw_key="first",           sort_order=1,
         description="Maximale Intimität, eingeschränkte Wissensbasis."),
    dict(code="third_limited",    label="Dritte Person (limitiert)",        authoringfw_key="third_limited",   sort_order=2,
         description="Empfohlen: Intimität + Flexibilität, ein POV pro Szene."),
    dict(code="third_omniscient", label="Dritte Person (allwissend)",       authoringfw_key="third_omniscient",sort_order=3,
         description="Gott-Perspektive, kann mehrere Köpfe gleichzeitig zeigen."),
    dict(code="second",           label="Du-Form (experimentell)",          authoringfw_key="second",          sort_order=4,
         description="Extrem ungewöhnlich, sehr intensiv."),
]

# Exakt aus outlinefw.TensionLevel enum (low/medium/high/peak)
TENSION_LEVELS = [
    dict(code="low",    label="Niedrig",  numeric_min=1, numeric_max=3, outlinefw_key="low",    sort_order=1),
    dict(code="medium", label="Mittel",   numeric_min=4, numeric_max=6, outlinefw_key="medium", sort_order=2),
    dict(code="high",   label="Hoch",     numeric_min=7, numeric_max=8, outlinefw_key="high",   sort_order=3),
    dict(code="peak",   label="Maximum",  numeric_min=9, numeric_max=10,outlinefw_key="peak",   sort_order=4),
]


class Command(BaseCommand):
    help = "Seed dramaturgische Lookup-Tabellen (idempotent)"

    def handle(self, *args, **options):
        self._seed(SceneOutcomeLookup, SCENE_OUTCOMES, "SceneOutcomeLookup")
        self._seed(POVTypeLookup, POVTypes := POV_TYPES, "POVTypeLookup")
        self._seed(TensionLevelLookup, TENSION_LEVELS, "TensionLevelLookup")

    def _seed(self, model, data, name):
        created = 0
        for item in data:
            _, was_created = model.objects.get_or_create(
                code=item["code"], defaults=item
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"  {name}: {created} neu, {len(data) - created} bereits vorhanden"
        ))
```

---

## A.5 — Admin: `apps/projects/admin.py` — Ergänzungen

```python
from django.contrib import admin
from .models import SceneOutcomeLookup, POVTypeLookup, TensionLevelLookup

@admin.register(SceneOutcomeLookup)
class SceneOutcomeLookupAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "tension_delta", "sort_order"]
    ordering = ["sort_order"]

@admin.register(POVTypeLookup)
class POVTypeLookupAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "authoringfw_key", "sort_order"]
    ordering = ["sort_order"]

@admin.register(TensionLevelLookup)
class TensionLevelLookupAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "numeric_min", "numeric_max", "outlinefw_key"]
    ordering = ["sort_order"]
```

---

## A.6 — outlinefw-Sync-Service: `apps/projects/services/outline_sync_service.py`

```python
"""
OutlineSyncService — synchronisiert outlinefw-Beat-Daten in OutlineNode-Felder.

Wird aufgerufen nach LLM-generierter Outline (outlinefw.OutlineGenerator).
Mapped outlinefw.TensionLevel → TensionLevelLookup (DB).
"""
from outlinefw.schemas import OutlineNode as FWNode, TensionLevel
from projects.models import OutlineNode, TensionLevelLookup


# Mapping outlinefw TensionLevel → DB-Lookup (lazy, gecacht)
_TENSION_CACHE: dict[str, TensionLevelLookup] = {}


def _get_tension(fw_key: str) -> TensionLevelLookup | None:
    if not fw_key:
        return None
    if fw_key not in _TENSION_CACHE:
        try:
            _TENSION_CACHE[fw_key] = TensionLevelLookup.objects.get(outlinefw_key=fw_key)
        except TensionLevelLookup.DoesNotExist:
            return None
    return _TENSION_CACHE[fw_key]


def sync_fw_node_to_db(db_node: OutlineNode, fw_node: FWNode) -> OutlineNode:
    """
    Schreibt outlinefw-Felder (beat_name, position, tension) in OutlineNode.
    Gibt den (ungespeicherten) Node zurück — Caller macht bulk_update.
    """
    db_node.outlinefw_beat_name = fw_node.beat_name or ""
    db_node.outlinefw_position = fw_node.position

    if fw_node.tension:
        fw_key = fw_node.tension.value  # z.B. 'high'
        db_node.tension_level = _get_tension(fw_key)
        # Numerischen Mittelwert setzen
        if db_node.tension_level:
            db_node.tension_numeric = (
                db_node.tension_level.numeric_min + db_node.tension_level.numeric_max
            ) // 2

    if fw_node.character_arcs:
        # Ersten Arc-String als emotional_arc übernehmen (wenn leer)
        if not db_node.emotional_arc:
            db_node.emotional_arc = fw_node.character_arcs[0] if fw_node.character_arcs else ""

    return db_node
```

---

## A.7 — Deployment-Reihenfolge

```bash
# 1. Migration ausführen
python manage.py migrate projects 0004_dramaturgic_fields

# 2. Lookups seeden
python manage.py seed_drama_lookups

# 3. Verify
python manage.py shell -c "
from projects.models import SceneOutcomeLookup, TensionLevelLookup
print('Outcomes:', SceneOutcomeLookup.objects.count())
print('TensionLevels:', TensionLevelLookup.objects.count())
"
```

---

## A.8 — Imports ergänzen in `apps/projects/models.py`

```python
# Am Ende der imports-Sektion ergänzen:
from apps.projects.models_lookups_drama import (
    SceneOutcomeLookup,
    POVTypeLookup,
    TensionLevelLookup,
)
```

> **Alternativ:** Modelle direkt in `models.py` ans Ende anfügen — abhängig von eurem Style.

---

*writing-hub · Prio-1 Schritt A von 4 · OutlineNode dramaturgische Felder*
*Packages: iil-outlinefw 0.1.1 · iil-authoringfw 0.8.0*
