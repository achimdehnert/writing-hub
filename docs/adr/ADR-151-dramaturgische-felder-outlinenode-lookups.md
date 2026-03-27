# ADR-151: Dramaturgische Felder auf OutlineNode und Lookup-Tabellen

**Status:** Accepted  
**Datum:** 2026-03-27  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150

---

## Kontext

`OutlineNode` ist das Kernmodell für Szenen und Kapitel. Es fehlen die
für professionelles Schreiben essenziellen dramaturgischen Felder:

- **Szenen-Outcome** (YES/NO/YES-BUT/NO-AND) — bestimmt die Spannungskurve
- **POV-Charakter** — wessen Perspektive wird erzählt?
- **Emotions-Delta** — wo beginnt die Szene emotional, wo endet sie?
- **Spannungsniveau** — numerisch 1–10 für die Spannungskurven-Visualisierung
- **NarrativeVoice** — Erzählperspektive ist pro Projekt definiert

Zusätzlich fehlt `ProjectTurningPoint` — ein Modell für die semantischen
Wendepunkte (Inciting Incident, Midpoint, etc.), die unabhängig von
`OutlineFrameworkBeat`-Positionen pro Projekt definiert werden.

---

## Entscheidung

### 1. Neue Datei: `apps/projects/models_lookups_drama.py`

Lookup-Tabellen sind DB-getrieben (Admin-verwaltbar), nicht als Enum
hardcodiert. Kompatibel mit `iil-outlinefw` ActPhase/TensionLevel.

```python
class SceneOutcomeLookup(models.Model):
    """
    YES/NO/YES-BUT/NO-AND — das wichtigste einzelne Strukturelement
    für die Spannungskurve.

    Seed-Werte:
        yes      | Ja               | Figur erreicht ihr Ziel
        no       | Nein             | Figur scheitert, Dinge werden schlimmer
        yes_but  | Ja, aber...      | Teilsieg mit Preis
        no_and   | Nein, und dazu.. | Scheitern + neue Komplikation
    """
    code          = models.SlugField(max_length=20, unique=True)
    label         = models.CharField(max_length=80)
    description   = models.TextField(blank=True)
    tension_delta = models.SmallIntegerField(default=0)
    sort_order    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_scene_outcome_lookup"
        ordering = ["sort_order"]


class POVTypeLookup(models.Model):
    """
    Seed: first | third_limited | third_omniscient | second
    """
    code            = models.SlugField(max_length=30, unique=True)
    label           = models.CharField(max_length=80)
    authoringfw_key = models.CharField(max_length=20, blank=True)
    sort_order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_pov_type_lookup"


class TempusLookup(models.Model):
    """
    Seed: past | present
    """
    code            = models.SlugField(max_length=20, unique=True)
    label           = models.CharField(max_length=50)
    authoringfw_key = models.CharField(max_length=20, blank=True)
    sort_order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_tempus_lookup"


class NarrativeDistanceLookup(models.Model):
    """
    Seed: close | medium | distant
    """
    code       = models.SlugField(max_length=20, unique=True)
    label      = models.CharField(max_length=50)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_narrative_distance_lookup"


class CharacterArcTypeLookup(models.Model):
    """
    Seed: positive | negative | flat
    """
    code       = models.SlugField(max_length=20, unique=True)
    label      = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_character_arc_type_lookup"
```

### 2. OutlineNode-Erweiterung (in `apps/projects/models.py`)

Neue Felder auf `OutlineNode`:

```python
# --- DRAMATURGISCHE FELDER (ADR-151) ---
outcome = models.ForeignKey(
    "projects.SceneOutcomeLookup",
    null=True, blank=True, on_delete=models.SET_NULL,
    verbose_name="Szenen-Outcome",
)
pov_character_id = models.UUIDField(
    null=True, blank=True,
    verbose_name="POV-Charakter (WeltenHub UUID)",
)
pov_type = models.ForeignKey(
    "projects.POVTypeLookup",
    null=True, blank=True, on_delete=models.SET_NULL,
)
emotion_start     = models.CharField(max_length=100, blank=True, default="")
emotion_end       = models.CharField(max_length=100, blank=True, default="")
tension_numeric   = models.SmallIntegerField(null=True, blank=True)  # 1–10
timeline_position = models.DateTimeField(null=True, blank=True)
sequel_needed     = models.BooleanField(default=False)
```

### 3. NarrativeVoice (neue Datei: `apps/projects/models_narrative.py`)

```python
class NarrativeVoice(models.Model):
    """
    Erzählperspektive eines Buchprojekts. 1:1 zu BookProject.
    Kompatibel mit authoringfw.StyleProfile.
    """
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="narrative_voice",
    )
    pov_type            = models.ForeignKey(POVTypeLookup, null=True, blank=True, on_delete=models.SET_NULL)
    tense               = models.ForeignKey(TempusLookup, null=True, blank=True, on_delete=models.SET_NULL)
    narrative_distance  = models.ForeignKey(NarrativeDistanceLookup, null=True, blank=True, on_delete=models.SET_NULL)
    sentence_length     = models.CharField(max_length=20, blank=True, default="",
        choices=[("short","Kurz"),("medium","Mittel"),("long","Lang"),("mixed","Gemischt")])
    vocabulary_level    = models.CharField(max_length=20, blank=True, default="",
        choices=[("simple","Einfach"),("standard","Standard"),("elevated","Gehoben"),("literary","Literarisch")])
    imagery_density     = models.CharField(max_length=20, blank=True, default="",
        choices=[("sparse","Sparsam"),("moderate","Moderat"),("rich","Reich")])
    irony_level         = models.CharField(max_length=20, blank=True, default="",
        choices=[("none","Keine"),("light","Leicht"),("heavy","Durchgehend")])
    notes               = models.TextField(blank=True, default="")

    class Meta:
        db_table = "wh_narrative_voice"
        verbose_name = "Erzählstimme"
```

### 4. ProjectTurningPoint (in `apps/projects/models_narrative.py`)

```python
class ProjectTurningPoint(models.Model):
    """
    Semantischer Wendepunkt eines Buchprojekts.
    Unabhängig von OutlineFrameworkBeat — hier werden die tatsächlichen
    Wendepunkte des konkreten Projekts dokumentiert.
    """
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="turning_points",
    )
    name                  = models.CharField(max_length=200)   # "Inciting Incident"
    position_percent      = models.SmallIntegerField()         # 0–100
    position_word         = models.IntegerField(null=True, blank=True)
    what_happens          = models.TextField(blank=True, default="")
    character_state_inner = models.TextField(blank=True, default="")
    character_state_outer = models.TextField(blank=True, default="")
    dramatic_function     = models.TextField(blank=True, default="")
    outline_node          = models.ForeignKey(
        "projects.OutlineNode",
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    class Meta:
        db_table  = "wh_project_turning_points"
        ordering  = ["position_percent"]
        verbose_name = "Wendepunkt"
        verbose_name_plural = "Wendepunkte"
```

### 5. Migration und Seeding

Migration `projects/0004_dramaturgic_fields`:
- Neue Tabellen: alle Lookup-Tabellen, `wh_narrative_voice`, `wh_project_turning_points`
- Neue Felder auf `OutlineNode`

Management Command `seed_drama_lookups`:
```python
SCENE_OUTCOMES = [
    ("yes",     "Ja",               +2),
    ("no",      "Nein",             -2),
    ("yes_but", "Ja, aber...",      +1),
    ("no_and",  "Nein, und dazu..", -3),
]
POV_TYPES = ["first", "third_limited", "third_omniscient", "second"]
TEMPUS    = ["past", "present"]
DISTANCES = ["close", "medium", "distant"]
ARC_TYPES = ["positive", "negative", "flat"]
```

---

## Begründung

- **Outcome YES/NO/YES-BUT/NO-AND** ist das wichtigste einzelne Strukturelement
  für die Spannungskurve — ohne es kann das LLM keine kohärente Dramaturgie
  erzeugen und das Drama-Dashboard (ADR-154) kann nicht visualisieren.
- **DB-Lookups statt Enum-Hardcoding:** Erweiterbar ohne Migration, Admin-verwaltbar,
  Mapping auf `authoringfw`-Keys ermöglicht typsichere iil-Package-Integration.
- **NarrativeVoice als eigenes Modell:** Erzählperspektive ist ein vollständiges
  Konfigurationsobjekt mit 7 Dimensionen — kein einzelnes CharField auf BookProject.
- **ProjectTurningPoint entkoppelt von OutlineFrameworkBeat:** Das Framework
  gibt ideale Positionen vor (z. B. Midpoint bei 50%) — der echte Wendepunkt
  des Projekts kann davon abweichen und wird separat dokumentiert.

---

## Abgelehnte Alternativen

**Outcome als CharField mit choices:** Nicht erweiterbar, kein `tension_delta`,
keine Admin-Verwaltung ohne Code-Änderung.

**NarrativeVoice als JSONField auf BookProject:** Keine Typsicherheit,
kein Mapping auf authoringfw.StyleProfile, keine Admin-Inline-Verwaltung.

**POV/Tempus als Enums im Code:** Enums sind nicht admin-verwaltbar und
erfordern Migration für neue Werte. DB-Lookups sind flexibler.

---

## Konsequenzen

- Migration `projects/0004_dramaturgic_fields` (ca. 30 min Aufwand)
- `seed_drama_lookups` Management Command mit 5 Lookup-Serien
- Drama-Dashboard (ADR-154) kann nach dieser Migration implementiert werden
- LLM-Prompts erhalten `NarrativeVoice`-Kontext automatisch via `iil-promptfw`
- Admin-Inlines für alle neuen Modelle erforderlich

---

**Referenzen:** ADR-150, `docs/adr/input/p1a_outlinenode_dramaturgic.md`,  
`docs/adr/input/p1c_narrative_voice.md`, `docs/adr/input/schritt_02_makrostruktur.md`
