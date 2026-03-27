# ADR-155: Serien-Dramaturgie — SeriesArc, VolumeRole, CharacterContinuity

**Status:** Accepted  
**Datum:** 2026-03-27  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-152

---

## Kontext

`BookSeries` und `SeriesVolume` existieren bereits in `apps/series/models.py`,
aber nur mit minimalen Feldern:

```
BookSeries:  title, description, genre
SeriesVolume: series, project, volume_number
```

Für die LLM-gestützte Serien-Generierung fehlt das dramaturgische Fundament.
Das konkrete Problem: Wenn ein Autor Band 3 schreibt, weiß das LLM nicht:

- Welchen Teil des Serien-Arcs trägt Band 3?
- Was hat Figur X am Ende von Band 2 erlebt/gelernt?
- Welches Versprechen aus Band 2 muss in Band 3 eingelöst werden?
- Was ist der übergreifende Antagonist / Konflikt der gesamten Serie?

**Ohne diese Daten generiert das LLM inkonsistenten, arc-blinden Text.**

### Abgrenzung: Serien-Arc vs. Band-Arc

| Dimension | Band-Arc (ADR-152) | Serien-Arc (ADR-155) |
|-----------|-------------------|---------------------|
| Scope | Ein Buch | Alle Bände zusammen |
| want/need | Figur im Kontext dieses Bandes | Figur über alle Bände |
| false/true_belief | Überzeugung zu Beginn/Ende des Bandes | Überzeugung zu Beginn/Ende der Serie |
| Modell | `ProjectCharacterLink` | `SeriesArc` |
| Auflösung | Am Ende des Bandes | Am Ende des letzten Bandes |

Band-Arc und Serien-Arc sind **komplementär** — nicht redundant. Ein Band kann
einen positiven Mini-Arc haben, der Teil eines negativen Serien-Arcs ist.

### App-Struktur

Alle neuen Modelle kommen in `apps/series/models_arc.py`. Die Lookup-Tabelle
`SeriesArcTypeLookup` kommt in `apps/core/models_lookups_drama.py` (ADR-151) —
konsistent mit der Core-App-Strategie für alle Lookups.

---

## Entscheidung

### 1. SeriesArcTypeLookup (in `apps/core/models_lookups_drama.py`)

```python
class SeriesArcTypeLookup(models.Model):
    """
    Lookup: Serien-Arc-Typen.

    Seed-Werte:
        single_arc     | Durchgehender Arc  | Eine Figur, ein Arc über alle Bände
        anthology      | Anthologie         | Jeder Band eigenständig, lose verbunden
        escalating_arc | Eskalierender Arc  | Jeder Band erhöht die Einsätze
        dual_arc       | Doppel-Arc         | Haupt-Arc + Band-eigener Arc parallel
    """
    code       = models.SlugField(max_length=30, unique=True)
    label      = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table        = "wh_series_arc_type_lookup"
        ordering        = ["sort_order"]
        verbose_name    = "Serien-Arc-Typ"
        verbose_name_plural = "Serien-Arc-Typen"

    def __str__(self):
        return self.label
```

### 2. SeriesArc (in `apps/series/models_arc.py`)

```python
import uuid
from django.db import models
from core.models_lookups_drama import SeriesArcTypeLookup


class SeriesArc(models.Model):
    """
    Übergreifender dramaturgischer Arc einer Buchserie. 1:1 zu BookSeries.

    Speichert den SERIEN-WEITEN want/need/false_belief/true_belief —
    tiefer als die Band-spezifischen Felder auf ProjectCharacterLink.
    """
    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    # Serien-weite Dramaturgie (analog zu ADR-152, aber übergreifend)
    series_want = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Want",
        help_text="Was verfolgt die Hauptfigur über ALLE Bände hinweg?",
    )
    series_need = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Need",
        help_text="Was braucht sie wirklich — wird erst im letzten Band klar.",
    )
    series_false_belief = models.TextField(
        blank=True, default="",
        verbose_name="Überzeugung Serien-Beginn",
    )
    series_true_belief = models.TextField(
        blank=True, default="",
        verbose_name="Erkenntnis Serien-Ende",
    )
    overarching_conflict = models.TextField(
        blank=True, default="",
        verbose_name="Übergreifender Konflikt",
        help_text="Antagonist / Hindernis, das über alle Bände aktiv ist.",
    )
    series_theme_question = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Themen-Frage",
        help_text="Die Frage, die die gesamte Serie stellt — tiefer als Einzel-Band-Themen.",
    )
    total_volumes_planned = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="Geplante Bände",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "wh_series_arcs"
        verbose_name    = "Serien-Arc"
        verbose_name_plural = "Serien-Arcs"

    def __str__(self):
        return f"Arc — {self.series.title}"
```

### 3. SeriesVolumeRole (in `apps/series/models_arc.py`)

```python
class SeriesVolumeRole(models.Model):
    """
    Dramaturgische Rolle eines Bandes im Serien-Bogen. 1:1 zu SeriesVolume.

    Erweitert SeriesVolume um:
        - Arc-Position (welchen Teil des Serien-Arcs trägt dieser Band?)
        - Serien-Versprechen (was verspricht dieser Band für den nächsten?)
        - Cliffhanger-Typ
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

    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volume = models.OneToOneField(
        "series.SeriesVolume",
        on_delete=models.CASCADE,
        related_name="role",
    )
    arc_position = models.CharField(
        max_length=20, choices=VOLUME_ARC_POSITION, default="escalation",
        verbose_name="Arc-Position im Serien-Bogen",
    )
    series_arc_contribution = models.TextField(
        blank=True, default="",
        verbose_name="Beitrag zum Serien-Arc",
        help_text="Welchen Teil des Serien-Arcs trägt dieser Band?",
    )
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
    cliffhanger_type = models.CharField(
        max_length=20, choices=CLIFFHANGER_TYPES, default="none",
    )
    cliffhanger_description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "wh_series_volume_roles"
        verbose_name    = "Serien-Band-Rolle"
        verbose_name_plural = "Serien-Band-Rollen"

    def __str__(self):
        return f"{self.volume} — {self.get_arc_position_display()}"
```

### 4. SeriesCharacterContinuity (in `apps/series/models_arc.py`)

```python
class SeriesCharacterContinuity(models.Model):
    """
    Figur-Zustand am Ende eines Bandes — der Übergabe-Vertrag zwischen Bänden.

    Ohne dieses Modell: LLM beginnt Band 3 ohne zu wissen, was in Band 2
    passiert ist → Figur-Widersprüche, Wissens-Fehler, Arc-Brüche.

    Schema für knowledge_gained / unresolved_threads:
        Liste von Strings — direkt als Prompt-Context injizierbar.

    Schema für relationships_changed:
        {"<character_uuid>": "<neue Beziehungsbeschreibung>"}
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series       = models.ForeignKey(
        "series.BookSeries", on_delete=models.CASCADE,
        related_name="character_continuities",
    )
    volume       = models.ForeignKey(
        "series.SeriesVolume", on_delete=models.CASCADE,
        related_name="character_continuities",
        verbose_name="Am Ende von Band",
    )
    character_id   = models.UUIDField(verbose_name="Figur (WeltenHub UUID)")
    character_name = models.CharField(
        max_length=200,
        verbose_name="Figurenname (Cache)",
        help_text="Gecacht — vermeidet API-Call bei jeder Anzeige",
    )

    physical_state        = models.TextField(blank=True, default="",
                                             verbose_name="Physischer Zustand")
    emotional_state       = models.TextField(blank=True, default="",
                                             verbose_name="Emotionaler Zustand")
    arc_progress          = models.TextField(blank=True, default="",
                                             verbose_name="Arc-Fortschritt")
    knowledge_gained      = models.JSONField(default=list,
                                             verbose_name="Neu erworbenes Wissen")
    relationships_changed = models.JSONField(default=dict,
                                             verbose_name="Veränderte Beziehungen")
    unresolved_threads    = models.JSONField(default=list,
                                             verbose_name="Offene Fäden")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "wh_series_character_continuities"
        unique_together = [("series", "volume", "character_id")]
        ordering        = ["series", "volume__volume_number", "character_name"]
        verbose_name    = "Figur-Kontinuität"
        verbose_name_plural = "Figur-Kontinuitäten"

    def __str__(self):
        return f"{self.character_name} — Ende Band {self.volume.volume_number}"

    def to_next_volume_context(self) -> str:
        """
        Gibt Zustand als LLM-Prompt-Block für Band N+1 zurück.
        """
        lines = [
            f"FIGUR: {self.character_name}",
            f"PHYSISCH: {self.physical_state}",
            f"EMOTIONAL: {self.emotional_state}",
            f"ARC-STAND: {self.arc_progress}",
        ]
        if self.knowledge_gained:
            lines.append(f"WEISSPUNKTE: {'; '.join(self.knowledge_gained)}")
        if self.unresolved_threads:
            lines.append(f"OFFENE FÄDEN: {'; '.join(self.unresolved_threads)}")
        return "\n".join(lines)
```

### 5. SeriesContinuityService (in `apps/series/services/continuity_service.py`)

```python
def build_continuity_context(series: BookSeries, for_volume_number: int) -> str:
    """
    Erstellt Prompt-Kontext für Band N aus den Kontinuitäts-Daten von Band N-1.
    Direkt in Layer-4-Kontext (ADR-150) injizierbar.
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

    lines = [f"=== KONTINUITÄT AUS BAND {for_volume_number - 1} ==="]
    for c in continuities:
        lines.append(c.to_next_volume_context())
        lines.append("")

    try:
        role = prev_volume.role
        if role.promise_to_reader:
            lines.append(f"VERSPRECHEN AN LESER: {role.promise_to_reader}")
        if role.cliffhanger_description:
            lines.append(f"CLIFFHANGER: {role.cliffhanger_description}")
    except Exception:
        pass

    return "\n".join(lines)
```

### 6. LLM-Kontext für Serien-Generierung

Ergänzung zu ADR-150 Layer 4 bei Serien-Projekten:

```
[USER — zusätzliche Layer für Serie]
  Layer 4a — SeriesArc
              (series_want, series_need, series_false_belief,
               overarching_conflict, series_theme_question)
  Layer 4b — SeriesVolumeRole dieses Bandes
              (arc_position, series_arc_contribution,
               promise_fulfilled_from)
  Layer 4c — Kontinuität aus Vorgänger-Band
              (SeriesCharacterContinuity.to_next_volume_context())
```

---

## Begründung

- **`SeriesArc` als eigenes Modell** (nicht Erweiterung von `BookSeries`):
  Trennung zwischen Metadaten (Titel, Genre) und Dramaturgie — konsistent
  mit dem Prinzip aus ADR-151/152 (Lookup-getriebene Dramaturgie-Felder).
- **`SeriesVolumeRole` 1:1 zu `SeriesVolume`:** Nicht alle Bände einer Serie
  haben eine definierte Rolle (Prio 2) — optionale Erweiterung, keine
  Breaking Change an `SeriesVolume`.
- **`SeriesCharacterContinuity` mit `unique_together`:** Pro Figur/Band/Serie
  genau ein Snapshot — keine inkonsistenten Doppeleinträge.
- **`character_name` gecacht:** Vermeidet WeltenHub-API-Call bei jeder
  Listenansicht — performance-kritisch bei vielen Figuren.
- **`to_next_volume_context()`-Methode direkt auf Model:** Service-Layer
  bleibt schlank; die String-Formatierung gehört zur Modell-Verantwortlichkeit.
- **`SeriesArcTypeLookup` in `apps/core`:** Konsistent mit ADR-151 — alle
  Lookups sind app-übergreifend in `core` um zirkuläre Abhängigkeiten
  `series → projects` zu vermeiden.

---

## Abgelehnte Alternativen

**Serien-Dramaturgie-Felder direkt auf `BookSeries`:** Verletzt das
Trennung-Prinzip — `BookSeries` sind Metadaten, Dramaturgie ist ein
separates Konzept.

**`SeriesCharacterContinuity` als JSONField auf `SeriesVolume`:** Kein
Admin-Inline, kein gezielter Abfragefilter nach Figur, keine UUID-Referenz
typsicher abbildbar.

**`character_name` nicht cachen:** Jede Listenansicht würde einen
WeltenHub-API-Call auslösen — Performance-Problem bei vielen Figuren.

**`SeriesArcTypeLookup` in `apps/series`:** Würde den FK `series → series`
erzeugen (unkritisch, aber inkonsistent mit der Core-App-Strategie).

---

## Konsequenzen

- Migration `series/0003_series_arc` (neue Tabellen: `wh_series_arcs`,
  `wh_series_volume_roles`, `wh_series_character_continuities`)
- `SeriesArcTypeLookup` in `apps/core` ergänzen + Seed-Daten
- `SeriesContinuityService` in `apps/series/services/`
- Admin: `SeriesArc` als Inline in `BookSeriesAdmin`, `SeriesVolumeRole` als
  Inline in `SeriesVolumeAdmin`
- AIActionType `series_continuity_extract` anlegen für LLM-Snapshot-Generierung
- Serien-UI in ADR-154 (Tab `serie_uebersicht`) kann implementiert werden
  sobald diese Migration läuft

---

**Referenzen:** ADR-082, ADR-150, ADR-151, ADR-152, ADR-154,  
`docs/adr/input/o2_serie_dramaturgie.md`
