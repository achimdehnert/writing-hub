# ADR-151: Dramaturgische Felder auf OutlineNode und Lookup-Tabellen

**Status:** Accepted  
**Datum:** 2026-03-27 (rev. 2026-03-27)  
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

### App-Struktur-Entscheidung: `apps/core` für geteilte Lookups

`CharacterArcTypeLookup` wird von `ProjectCharacterLink` (App `worlds`) referenziert,
liegt aber dramaturgisch in der `projects`-App. Ein FK `worlds → projects` bei
gleichzeitigem FK `projects → worlds` wäre eine **zirkuläre Django-App-Abhängigkeit**.

**Lösung:** Alle dramaturgischen Lookup-Tabellen, die app-übergreifend referenziert
werden, landen in einer neuen App `apps/core`:

```
apps/core/
    models_lookups_drama.py   ← SceneOutcomeLookup, POVTypeLookup, TempusLookup,
                                 NarrativeDistanceLookup, CharacterArcTypeLookup,
                                 EmotionLookup, SentenceLengthLookup,
                                 VocabularyLevelLookup, ImageryDensityLookup,
                                 IronyLevelLookup
```

`projects` und `worlds` importieren aus `core` — keine Zirkularität.

---

## Entscheidung

### 1. Neue Datei: `apps/core/models_lookups_drama.py`

Alle Lookup-Tabellen vollständig spezifiziert mit `__str__`:

```python
from django.db import models


class SceneOutcomeLookup(models.Model):
    """
    YES/NO/YES-BUT/NO-AND — das wichtigste einzelne Strukturelement
    für die Spannungskurve.

    Seed-Werte:
        yes      | Ja               | +2 | Figur erreicht ihr Ziel
        no       | Nein             | -2 | Figur scheitert, Dinge werden schlimmer
        yes_but  | Ja, aber...      | +1 | Teilsieg mit Preis
        no_and   | Nein, und dazu.. | -3 | Scheitern + neue Komplikation
    """
    code          = models.SlugField(max_length=20, unique=True)
    label         = models.CharField(max_length=80)
    description   = models.TextField(blank=True)
    tension_delta = models.SmallIntegerField(default=0)
    sort_order    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_scene_outcome_lookup"
        ordering = ["sort_order"]
        verbose_name = "Szenen-Outcome"
        verbose_name_plural = "Szenen-Outcomes"

    def __str__(self):
        return f"{self.code} — {self.label}"


class POVTypeLookup(models.Model):
    """
    Seed: first | third_limited | third_omniscient | second
    """
    code            = models.SlugField(max_length=30, unique=True)
    label           = models.CharField(max_length=80)
    description     = models.TextField(blank=True)
    authoringfw_key = models.CharField(max_length=20, blank=True)
    sort_order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_pov_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "POV-Typ"
        verbose_name_plural = "POV-Typen"

    def __str__(self):
        return f"{self.code} — {self.label}"


class TempusLookup(models.Model):
    """
    Seed: past | present
    """
    code            = models.SlugField(max_length=20, unique=True)
    label           = models.CharField(max_length=50)
    description     = models.TextField(blank=True)
    authoringfw_key = models.CharField(max_length=20, blank=True)
    sort_order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_tempus_lookup"
        ordering = ["sort_order"]
        verbose_name = "Tempus"
        verbose_name_plural = "Tempora"

    def __str__(self):
        return f"{self.code} — {self.label}"


class NarrativeDistanceLookup(models.Model):
    """
    Seed: close | medium | distant
    """
    code        = models.SlugField(max_length=20, unique=True)
    label       = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    sort_order  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_narrative_distance_lookup"
        ordering = ["sort_order"]
        verbose_name = "Narrative Distanz"
        verbose_name_plural = "Narrative Distanzen"

    def __str__(self):
        return f"{self.code} — {self.label}"


class CharacterArcTypeLookup(models.Model):
    """
    Seed: positive | negative | flat
    """
    code        = models.SlugField(max_length=20, unique=True)
    label       = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    sort_order  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_character_arc_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Charakter-Arc-Typ"
        verbose_name_plural = "Charakter-Arc-Typen"

    def __str__(self):
        return f"{self.code} — {self.label}"


class EmotionLookup(models.Model):
    """
    Lookup: Emotionszustände für OutlineNode.emotion_start / emotion_end.
    Strukturierte Liste ermöglicht Spannungskurven-Visualisierung im
    Drama-Dashboard (ADR-154) und konsistente LLM-Prompts.

    Seed-Werte (Basis-Palette, erweiterbar):
        hope      | Hoffnung
        fear      | Angst
        grief     | Trauer
        anger     | Wut
        joy       | Freude
        shame     | Scham
        relief    | Erleichterung
        despair   | Verzweiflung
        tension   | Anspannung
        numbness  | Taubheit / Schock
    """
    code       = models.SlugField(max_length=30, unique=True)
    label      = models.CharField(max_length=80)
    valence    = models.SmallIntegerField(
        default=0,
        help_text="Positiv (+1) oder negativ (-1) — für automatisches Delta-Tracking"
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_emotion_lookup"
        ordering = ["sort_order"]
        verbose_name = "Emotion"
        verbose_name_plural = "Emotionen"

    def __str__(self):
        return f"{self.code} — {self.label}"


class SentenceLengthLookup(models.Model):
    """
    Seed: short | medium | long | mixed
    """
    code        = models.SlugField(max_length=20, unique=True)
    label       = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    sort_order  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_sentence_length_lookup"
        ordering = ["sort_order"]
        verbose_name = "Satzlänge"

    def __str__(self):
        return f"{self.code} — {self.label}"


class VocabularyLevelLookup(models.Model):
    """
    Seed: simple | standard | elevated | literary
    """
    code            = models.SlugField(max_length=20, unique=True)
    label           = models.CharField(max_length=50)
    description     = models.TextField(blank=True)
    authoringfw_key = models.CharField(max_length=20, blank=True)
    sort_order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_vocabulary_level_lookup"
        ordering = ["sort_order"]
        verbose_name = "Vokabular-Niveau"

    def __str__(self):
        return f"{self.code} — {self.label}"


class ImageryDensityLookup(models.Model):
    """
    Seed: sparse | moderate | rich
    """
    code        = models.SlugField(max_length=20, unique=True)
    label       = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    sort_order  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_imagery_density_lookup"
        ordering = ["sort_order"]
        verbose_name = "Bild-Dichte"

    def __str__(self):
        return f"{self.code} — {self.label}"


class IronyLevelLookup(models.Model):
    """
    Seed: none | light | heavy
    """
    code        = models.SlugField(max_length=20, unique=True)
    label       = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    sort_order  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_irony_level_lookup"
        ordering = ["sort_order"]
        verbose_name = "Ironie-Grad"

    def __str__(self):
        return f"{self.code} — {self.label}"
```

### 2. OutlineNode-Erweiterung (in `apps/projects/models.py`)

```python
from django.core.validators import MinValueValidator, MaxValueValidator

# --- DRAMATURGISCHE FELDER (ADR-151) ---
outcome = models.ForeignKey(
    "core.SceneOutcomeLookup",
    null=True, blank=True, on_delete=models.SET_NULL,
    verbose_name="Szenen-Outcome",
)
pov_character_id = models.UUIDField(
    null=True, blank=True,
    verbose_name="POV-Charakter (WeltenHub UUID)",
)
pov_type = models.ForeignKey(
    "core.POVTypeLookup",
    null=True, blank=True, on_delete=models.SET_NULL,
)
emotion_start = models.ForeignKey(
    "core.EmotionLookup",
    null=True, blank=True, on_delete=models.SET_NULL,
    related_name="scenes_starting_here",
    verbose_name="Emotion Szenenanfang",
)
emotion_end = models.ForeignKey(
    "core.EmotionLookup",
    null=True, blank=True, on_delete=models.SET_NULL,
    related_name="scenes_ending_here",
    verbose_name="Emotion Szenenende",
)
tension_numeric = models.SmallIntegerField(
    null=True, blank=True,
    validators=[MinValueValidator(1), MaxValueValidator(10)],
    help_text="Spannungsniveau 1 (minimal) bis 10 (Maximum)",
)
timeline_position = models.CharField(
    max_length=100, blank=True, default="",
    help_text="Narrativer Zeitpunkt in der Story-Chronologie — kein DateTimeField, "
              "da fiktive Zeitangaben ('Tag 3, 14:00') kein DB-Datum sind. "
              "Korrespondiert mit MasterTimeline/TimelineEntry (ADR-156).",
)
sequel_note = models.TextField(
    blank=True, default="",
    verbose_name="Sequel-Notiz",
    help_text="Offene Fäden / Konsequenzen, die in einer Folge-Szene aufgelöst werden müssen.",
)
```

**Hinweis:** `MinValueValidator`/`MaxValueValidator` greifen auf Model-Ebene
(full_clean) und im Django Admin. Für API-Endpunkte muss der Service zusätzlich
prüfen:
```python
if not (1 <= tension_numeric <= 10):
    raise ValueError("tension_numeric muss zwischen 1 und 10 liegen")
```

### 3. NarrativeVoice (neue Datei: `apps/projects/models_narrative.py`)

Alle Stil-Dimensionen konsequent als FKs auf Lookups aus `apps/core`:

```python
import uuid
from django.db import models
from core.models_lookups_drama import (
    POVTypeLookup, TempusLookup, NarrativeDistanceLookup,
    SentenceLengthLookup, VocabularyLevelLookup,
    ImageryDensityLookup, IronyLevelLookup,
)


class NarrativeVoice(models.Model):
    """
    Erzählperspektive eines Buchprojekts. 1:1 zu BookProject.
    Kompatibel mit authoringfw.StyleProfile.
    Alle Dimensionen als DB-Lookups — Admin-verwaltbar, erweiterbar.
    """
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="narrative_voice",
    )
    pov_type           = models.ForeignKey(POVTypeLookup, null=True, blank=True, on_delete=models.SET_NULL)
    tense              = models.ForeignKey(TempusLookup, null=True, blank=True, on_delete=models.SET_NULL)
    narrative_distance = models.ForeignKey(NarrativeDistanceLookup, null=True, blank=True, on_delete=models.SET_NULL)
    sentence_length    = models.ForeignKey(SentenceLengthLookup, null=True, blank=True, on_delete=models.SET_NULL)
    vocabulary_level   = models.ForeignKey(VocabularyLevelLookup, null=True, blank=True, on_delete=models.SET_NULL)
    imagery_density    = models.ForeignKey(ImageryDensityLookup, null=True, blank=True, on_delete=models.SET_NULL)
    irony_level        = models.ForeignKey(IronyLevelLookup, null=True, blank=True, on_delete=models.SET_NULL)
    notes              = models.TextField(blank=True, default="")

    class Meta:
        db_table = "wh_narrative_voice"
        verbose_name = "Erzählstimme"
        verbose_name_plural = "Erzählstimmen"

    def __str__(self):
        return f"NarrativeVoice: {self.project}"
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
    name                  = models.CharField(max_length=200)
    position_percent      = models.SmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
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

    def __str__(self):
        return f"{self.name} ({self.position_percent}%)"
```

### 5. Migration und Seeding

Migration `core/0001_lookups_drama` + `projects/0004_dramaturgic_fields`:
- `core/0001`: alle Lookup-Tabellen
- `projects/0004`: neue Felder auf `OutlineNode`, `wh_narrative_voice`, `wh_project_turning_points`

Management Command `seed_drama_lookups` (in `apps/core`):
```python
SCENE_OUTCOMES = [
    ("yes",     "Ja",                +2),
    ("no",      "Nein",              -2),
    ("yes_but", "Ja, aber...",       +1),
    ("no_and",  "Nein, und dazu..",  -3),
]
POV_TYPES      = ["first", "third_limited", "third_omniscient", "second"]
TEMPUS         = ["past", "present"]
DISTANCES      = ["close", "medium", "distant"]
ARC_TYPES      = ["positive", "negative", "flat"]
EMOTIONS = [
    ("hope", "Hoffnung", +1), ("fear", "Angst", -1), ("grief", "Trauer", -1),
    ("anger", "Wut", -1), ("joy", "Freude", +1), ("shame", "Scham", -1),
    ("relief", "Erleichterung", +1), ("despair", "Verzweiflung", -1),
    ("tension", "Anspannung", -1), ("numbness", "Taubheit / Schock", -1),
]
SENTENCE_LENGTHS   = ["short", "medium", "long", "mixed"]
VOCABULARY_LEVELS  = ["simple", "standard", "elevated", "literary"]
IMAGERY_DENSITIES  = ["sparse", "moderate", "rich"]
IRONY_LEVELS       = ["none", "light", "heavy"]
```

---

## Begründung

- **`apps/core` für Lookups** löst die zirkuläre Abhängigkeit `worlds ↔ projects`
  und ist der Standard-Pattern für plattformweite Stammdaten.
- **`EmotionLookup` statt `CharField`:** Typsicherheit, `valence`-Feld ermöglicht
  automatisches Emotions-Delta-Tracking im Drama-Dashboard (ADR-154) ohne
  String-Vergleiche.
- **`tension_numeric` mit Validator im Model:** Constraint greift im Admin,
  in der Shell und in Tests — nicht nur in der View. Zusätzliche Service-Prüfung
  für API-Endpunkte.
- **`sequel_note` als TextField:** Klarere Semantik als `sequel_needed: bool` —
  ein leerer String bedeutet "kein Sequel nötig", Text beschreibt was konkret
  aufgelöst werden muss.
- **Alle NarrativeVoice-Dimensionen als FKs:** Konsistentes Modell,
  Admin-verwaltbar, Mapping auf `authoringfw.StyleProfile` via `authoringfw_key`.
- **`__str__` auf allen Lookups:** Pflicht für Django Admin und Shell-Lesbarkeit.

---

## Abgelehnte Alternativen

**Outcome als CharField mit choices:** Nicht erweiterbar, kein `tension_delta`,
keine Admin-Verwaltung ohne Code-Änderung.

**`emotion_start/end` als CharField:** Kein automatisches Delta-Tracking,
kein konsistentes Vokabular für LLM-Prompts, Tippfehler möglich.

**NarrativeVoice als JSONField auf BookProject:** Keine Typsicherheit,
kein Mapping auf authoringfw.StyleProfile, keine Admin-Inline-Verwaltung.

**Lookups in `apps/projects`:** Erzeugt zirkuläre App-Abhängigkeit sobald
`worlds` (ProjectCharacterLink) auf `CharacterArcTypeLookup` zeigt.

---

## Konsequenzen

- Neue App `apps/core` mit `models_lookups_drama.py` (10 Lookup-Modelle)
- Migration `core/0001_lookups_drama` + `projects/0004_dramaturgic_fields`
- `seed_drama_lookups` Management Command mit 9 Lookup-Serien + Emotions
- Drama-Dashboard (ADR-154) profitiert direkt von `EmotionLookup.valence`
- LLM-Prompts erhalten `NarrativeVoice`-Kontext mit allen 7 Lookup-Dimensionen
- Admin-Inlines für alle neuen Modelle erforderlich

---

**Referenzen:** ADR-150, `docs/adr/input/p1a_outlinenode_dramaturgic.md`,  
`docs/adr/input/p1c_narrative_voice.md`, `docs/adr/input/schritt_02_makrostruktur.md`
