# ADR-156: Zeitstruktur, Foreshadowing und OutlineSequence

**Status:** Accepted  
**Datum:** 2026-03-27  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-151

---

## Kontext

Drei zusammenhängende Prio-2-Lücken aus der Gap-Analyse (ADR-150):

### Gap 6 — MasterTimeline fehlt

Das LLM kennt keine Story-Chronologie. Resultat: Figuren wissen Dinge, die
sie noch nicht wissen können (Info-Leak), und Zeitangaben widersprechen sich.
`CharacterKnowledgeState` (ADR-152) adressiert das auf Figuren-Ebene —
aber ohne übergeordnete `MasterTimeline` fehlt der Anker: wann passiert was
relativ zueinander?

### Gap 7 — ForeshadowingEntry fehlt

Das LLM vergisst eingeführte Chekhov's Guns. Wenn in Kapitel 3 eine Narbe
erwähnt wird, die in Kapitel 18 erklärt werden soll, gibt es keine DB-Referenz.
Das LLM generiert Kapitel 18 ohne diese Verpflichtung zu kennen.

### Gap 8 — OutlineSequence fehlt (Mesostruktur-Zwischenebene)

Die Hierarchie `Outline → OutlineNode` fehlt eine Zwischenebene: Sequenzen.
Eine Sequenz ist eine Gruppe von 3–5 Szenen mit einer eigenen Logik
(Ziel → Versuch → Ergebnis). Ohne sie behandelt das LLM jede Szene isoliert
statt als Teil eines größeren Mesostruktur-Blocks.

### Abgrenzung: MasterTimeline vs. CharacterKnowledgeState

| Konzept | Modell | Frage |
|---------|--------|-------|
| **Wann passiert X?** | `MasterTimeline` / `TimelineEntry` | Chronologie |
| **Weiß Figur X davon?** | `CharacterKnowledgeState` (ADR-152) | Wissensstand |

Beide sind nötig — sie antworten auf unterschiedliche Fragen. Die Timeline
ist die objektive Chronologie; `CharacterKnowledgeState` ist die subjektive
Perspektive jeder Figur auf diese Chronologie.

---

## Entscheidung

### Teil A: MasterTimeline & TimelineEntry (in `apps/projects/models_timeline.py`)

```python
import uuid
from django.db import models


class NarrativeModelLookup(models.Model):
    """
    Lookup: Erzähl-Zeitmodelle.

    Seed-Werte:
        linear        | Linear              | A→B→C→D, Erzählzeit = Story-Zeit
        in_medias_res | In medias res       | Beginnt in der Mitte, dann Analepsen
        non_linear    | Nicht-linear        | Kapitel-Reihenfolge ≠ Story-Chronologie
        parallel      | Parallel            | Mehrere Zeitstränge gleichzeitig
    """
    code        = models.SlugField(max_length=20, unique=True)
    label       = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    sort_order  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table        = "wh_narrative_model_lookup"
        ordering        = ["sort_order"]
        verbose_name    = "Erzähl-Zeitmodell"
        verbose_name_plural = "Erzähl-Zeitmodelle"

    def __str__(self):
        return f"{self.code} — {self.label}"


class MasterTimeline(models.Model):
    """
    Story-Chronologie eines Buchprojekts. 1:1 zu BookProject.

    Trennt Story Time (was wirklich passiert, wann) von Discourse Time
    (wie der Roman es erzählt). Dieses Modell hält die Story Time.

    Notiz: story_start_date und story_time_span sind CharFields, nicht
    DateFields — fiktive Zeitangaben ("Tag 3 nach der Ankunft") passen
    nicht in ein echtes Datenbankdatum.
    """
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="master_timeline",
    )
    narrative_model = models.ForeignKey(
        NarrativeModelLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="timelines",
        verbose_name="Erzähl-Zeitmodell",
    )
    story_time_span = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Story-Zeitraum",
        help_text="z.B. '3 Wochen', 'Sommer 1989', '200 Jahre Zukunft'",
    )
    story_start_date = models.CharField(
        max_length=100, blank=True, default="",
        verbose_name="Story-Startpunkt",
        help_text="Narrativer Startpunkt (kein DateField — kann fiktiv sein). "
                  "z.B. 'Montag, 3. März' oder 'Tag 1 nach der Landung'",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "wh_master_timelines"
        verbose_name    = "Master-Chronologie"
        verbose_name_plural = "Master-Chronologien"

    def __str__(self):
        return f"Timeline — {self.project.title}"


class TimelineEntry(models.Model):
    """
    Ein Ereignis auf der Story-Chronologie.

    entry_type:
        pre_story  → Vorgeschichte (Ghost, Traumata, Vorgeschichte der Figuren)
        story      → Handlung des Romans (verknüpft mit OutlineNode)
        post_story → Implied Future nach dem Ende (optional, für Epiloge)

    characters_involved speichert WeltenHub-UUIDs als Liste:
        ["uuid1", "uuid2"]
    """
    ENTRY_TYPES = [
        ("pre_story",  "Pre-Story (Vorgeschichte)"),
        ("story",      "Story (Handlung)"),
        ("post_story", "Post-Story (Implied Future)"),
    ]

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timeline = models.ForeignKey(
        MasterTimeline, on_delete=models.CASCADE, related_name="entries",
    )
    node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="timeline_entries",
        verbose_name="Verknüpfte Szene/Kapitel",
        help_text="Nur bei entry_type=story relevant.",
    )
    entry_type          = models.CharField(max_length=20, choices=ENTRY_TYPES, default="story")
    story_date          = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Narrativer Zeitpunkt z.B. 'Tag 3, 14:00' oder 'Drei Jahre früher'",
    )
    event_description   = models.TextField(verbose_name="Ereignis-Beschreibung")
    characters_involved = models.JSONField(
        default=list,
        help_text="WeltenHub-UUIDs der beteiligten Figuren",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table        = "wh_timeline_entries"
        ordering        = ["timeline", "order"]
        verbose_name    = "Chronologie-Eintrag"
        verbose_name_plural = "Chronologie-Einträge"

    def __str__(self):
        return f"{self.get_entry_type_display()} | {self.story_date or '—'}: {self.event_description[:60]}"
```

### Teil B: ForeshadowingEntry (in `apps/projects/models_timeline.py`)

```python
class ForeshadowingTypeLookup(models.Model):
    """
    Lookup: Typen von Foreshadowing.

    Seed-Werte:
        objekt     | Objekt        | Physisches Objekt (Waffe, Brief, Narbe)
        dialog     | Dialog        | Gesprochenes Wort mit Doppelbedeutung
        bild       | Bild/Symbol   | Visuelles Motiv mit späterer Bedeutung
        name       | Name          | Name der Figur oder des Ortes enthält Hinweis
        verhalten  | Verhalten     | Charakterverhalten, das spätere Entscheidung vorausdeutet
        atmosphaere | Atmosphäre   | Stimmung/Setting signalisiert kommendes Ereignis
    """
    code        = models.SlugField(max_length=20, unique=True)
    label       = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    sort_order  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table        = "wh_foreshadowing_type_lookup"
        ordering        = ["sort_order"]
        verbose_name    = "Foreshadowing-Typ"
        verbose_name_plural = "Foreshadowing-Typen"

    def __str__(self):
        return f"{self.code} — {self.label}"


class ForeshadowingEntry(models.Model):
    """
    Eine Chekhov's Gun: Setup-Payoff-Paar.

    Kritische LLM-Funktion: Beim Generieren von Szenen nahe `resolved_in`
    MUSS das LLM alle offenen ForeshadowingEntries (status=open) kennen.
    Ohne dies vergisst das LLM, was es in Kapitel 3 versprochen hat.

    Status-Übergänge:
        open   → planted (Setup eingebaut, noch nicht aufgelöst)
        planted → resolved (Payoff eingebaut)
        planted → abandoned (bewusst aufgegeben mit Begründung)
    """
    STATUS = [
        ("open",      "Geplant (noch nicht eingebaut)"),
        ("planted",   "Eingebaut (wartet auf Auflösung)"),
        ("resolved",  "Aufgelöst"),
        ("abandoned", "Aufgegeben"),
    ]

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject", on_delete=models.CASCADE,
        related_name="foreshadowing_entries",
    )
    foreshadow_type = models.ForeignKey(
        ForeshadowingTypeLookup,
        on_delete=models.SET_NULL, null=True, blank=True,
    )

    label          = models.CharField(
        max_length=200,
        verbose_name="Bezeichner",
        help_text="Kurzer Name: 'Die Narbe an seiner Hand', 'Der Brief in der Schublade'",
    )
    setup_description   = models.TextField(
        verbose_name="Setup",
        help_text="Was wird eingeführt? Wie? In welchem Kontext?",
    )
    payoff_description  = models.TextField(
        blank=True, default="",
        verbose_name="Payoff",
        help_text="Wie wird es aufgelöst? Was bedeutet es dann?",
    )
    thematic_meaning    = models.TextField(
        blank=True, default="",
        verbose_name="Thematische Bedeutung",
        help_text="Warum ist dieses Foreshadowing thematisch relevant?",
    )

    introduced_in = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="foreshadowing_setups",
        verbose_name="Eingeführt in",
    )
    resolved_in = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="foreshadowing_payoffs",
        verbose_name="Aufgelöst in",
    )

    status            = models.CharField(max_length=20, choices=STATUS, default="open")
    abandonment_reason = models.TextField(
        blank=True, default="",
        verbose_name="Grund für Aufgabe",
        help_text="Nur bei status=abandoned relevant.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "wh_foreshadowing_entries"
        ordering        = ["project", "status", "label"]
        verbose_name    = "Foreshadowing-Eintrag"
        verbose_name_plural = "Foreshadowing-Einträge"

    def __str__(self):
        return f"{self.label} [{self.get_status_display()}]"
```

### Teil C: PlannedFlashback (in `apps/projects/models_timeline.py`)

```python
class PlannedFlashback(models.Model):
    """
    Geplante Rückblende: Wo, wie und warum wird ein Flashback eingesetzt?

    Unterschied zu TimelineEntry:
        TimelineEntry = Was passiert chronologisch (Story Time)
        PlannedFlashback = Wie wird ein vergangenes Ereignis erzählt (Discourse Time)

    technique:
        hard_cut    → Abrupter Wechsel ohne Überleitung
        trigger     → Sinneseindruck löst Erinnerung aus
        chapter_break → Ganzes Kapitel als Rückblende (Titel mit Zeitangabe)
    """
    TECHNIQUES = [
        ("hard_cut",      "Hard Cut (abrupter Wechsel)"),
        ("trigger",       "Trigger (Sinneseindruck)"),
        ("chapter_break", "Kapitelwechsel (ganzes Kapitel als Rückblende)"),
    ]

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject", on_delete=models.CASCADE,
        related_name="planned_flashbacks",
    )
    trigger_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="flashback_triggers",
        verbose_name="Ausgelöst in Szene",
        help_text="Die Gegenwarts-Szene, aus der heraus der Flashback startet.",
    )

    content_summary  = models.TextField(verbose_name="Inhalt der Rückblende")
    dramatic_purpose = models.TextField(
        verbose_name="Dramaturgischer Zweck",
        help_text="Warum jetzt? Was trägt dieser Flashback zur Szene/Arc bei?",
    )
    technique       = models.CharField(max_length=20, choices=TECHNIQUES, default="trigger")
    return_technique = models.TextField(
        blank=True, default="",
        verbose_name="Rückkehr-Technik",
        help_text="Wie kehrt man zur Gegenwart zurück? "
                  "z.B. 'Ähnliches Objekt in Gegenwart', 'Direkte Zeitmarkierung'",
    )

    class Meta:
        db_table        = "wh_planned_flashbacks"
        verbose_name    = "Geplante Rückblende"
        verbose_name_plural = "Geplante Rückblenden"

    def __str__(self):
        return f"Flashback ({self.get_technique_display()}) in {self.trigger_node}"
```

### Teil D: OutlineSequence (in `apps/projects/models_outline.py`)

```python
class OutlineSequence(models.Model):
    """
    Mesostruktur-Zwischenebene zwischen Akt und Kapitel.

    Eine Sequenz = Gruppe von 3–5 Szenen mit eigener Logik:
        Ziel → Versuche → Ergebnis (positiv/negativ)

    Hierarchie:
        OutlineVersion → OutlineSequence → OutlineNode

    OutlineNode erhält ein optionales FK auf OutlineSequence.
    Damit können Szenen einer Sequenz zugeordnet werden, ohne
    die bestehende OutlineNode-Hierarchie zu brechen.

    Warum: Das LLM generiert bessere Szenen, wenn es weiß,
    dass es Teil einer Sequenz ist und welches Sequenz-Ziel
    am Ende stehen soll.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    outline_version = models.ForeignKey(
        "projects.OutlineVersion",
        on_delete=models.CASCADE,
        related_name="sequences",
    )
    act = models.CharField(
        max_length=20, blank=True, default="",
        verbose_name="Akt-Zugehörigkeit",
        help_text="z.B. 'act_1', 'act_2a', 'act_3'",
    )
    title       = models.CharField(max_length=200)
    goal        = models.TextField(
        verbose_name="Sequenz-Ziel",
        help_text="Was versucht die Figur in dieser Sequenz zu erreichen?",
    )
    start_state = models.TextField(
        blank=True, default="",
        verbose_name="Ausgangslage",
        help_text="Wie ist der Zustand der Figur zu Beginn der Sequenz?",
    )
    end_state = models.TextField(
        blank=True, default="",
        verbose_name="Endzustand",
        help_text="Wie ist der Zustand am Ende? Positiv (Ziel erreicht) oder "
                  "negativ (Ziel verfehlt, Komplikation)?",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table        = "wh_outline_sequences"
        ordering        = ["outline_version", "sort_order"]
        verbose_name    = "Sequenz"
        verbose_name_plural = "Sequenzen"

    def __str__(self):
        return f"Seq {self.sort_order}: {self.title}"
```

**Verknüpfung mit OutlineNode:** Ein neues optionales FK-Feld auf `OutlineNode`:

```python
# Auf OutlineNode (Migration nötig):
sequence = models.ForeignKey(
    "projects.OutlineSequence",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="nodes",
    verbose_name="Sequenz-Zugehörigkeit",
)
```

### LLM-Integration

**ForeshadowingEntry im Layer 8 (ADR-150):**
```python
def get_open_foreshadowing_context(project, current_node) -> str:
    """
    Gibt alle offenen Foreshadowing-Einträge zurück, die vor der aktuellen
    Szene eingeführt wurden und noch nicht aufgelöst sind.
    """
    entries = ForeshadowingEntry.objects.filter(
        project=project,
        status="planted",
        introduced_in__sort_order__lt=current_node.sort_order,
    ).select_related("foreshadow_type")

    if not entries:
        return ""

    lines = ["OFFENE CHEKHOV'S GUNS (müssen irgendwann aufgelöst werden):"]
    for e in entries:
        lines.append(f"  - [{e.foreshadow_type.label if e.foreshadow_type else '?'}] "
                     f"{e.label}: {e.setup_description[:100]}")
    return "\n".join(lines)
```

**OutlineSequence im Layer 5 (ADR-150):**
```
[SZENE IN SEQUENZ: {{ node.sequence.title }}]
Sequenz-Ziel: {{ node.sequence.goal }}
Ausgangslage: {{ node.sequence.start_state }}
Angestrebtes Sequenz-Ende: {{ node.sequence.end_state }}
→ Diese Szene muss auf das Sequenz-Ziel hinarbeiten oder es aktiv behindern.
```

---

## Begründung

- **`MasterTimeline.story_start_date` als CharField:** Fiktive Zeitangaben
  ("Tag 3 nach der Ankunft", "Sommer 1942") passen nicht in `DateField`.
  Freier Text ist hier korrekt — eine DB-Datums-Validierung würde
  Fiktions-Zeitangaben ablehnen.
- **`ForeshadowingEntry.status` mit 4 Zuständen:** `abandoned` ist kritisch —
  ohne es gibt es keine saubere Trennung zwischen "nicht aufgelöst" und
  "bewusst nicht aufgelöst". Beides würde im Layer-8-Kontext auftauchen.
- **`PlannedFlashback` als eigenes Modell** (nicht Teil von `TimelineEntry`):
  `TimelineEntry` = Story Time. `PlannedFlashback` = Discourse Time (wie
  erzählt man es). Zwei verschiedene Konzepte, auch wenn sie dasselbe
  vergangene Ereignis referenzieren können.
- **`OutlineSequence` mit optionalem FK** statt Pflicht-Verknüpfung:
  Bestehende Projekte können OutlineNodes weiter ohne Sequenz nutzen.
  Keine Breaking Migration.
- **`NarrativeModelLookup` in `apps/projects`** (nicht `apps/core`):
  Enge Kopplung an `MasterTimeline` — kein App-übergreifender Bedarf.
  Ausnahme von der Core-App-Regel (ADR-151): nur wenn cross-app nötig.

---

## Abgelehnte Alternativen

**`MasterTimeline` als JSONField auf `BookProject`:** Kein gezielter
Abfragefilter (z.B. "alle Pre-Story-Ereignisse"), keine Admin-Verwaltung,
kein FK auf OutlineNode.

**`ForeshadowingEntry` als `MotifAppearance`-Erweiterung:** Foreshadowing
und Motiv sind verwandte, aber verschiedene Konzepte. Foreshadowing ist
ein technisches Setup-Payoff-Paar; Motiv ist thematisch. Beide brauchen
eigene Modelle.

**`OutlineSequence` als Pflicht-FK auf `OutlineNode`:** Würde bestehende
OutlineNodes ohne Sequenz brechen. Optionales FK ist der richtige Kompromiss.

**Flashback-Planung als Kommentar auf `OutlineNode`:** Kein strukturierter
Zugriff, kein LLM-Layer, keine Technik-Unterscheidung.

---

## Konsequenzen

- Migration `projects/0009_master_timeline` (neue Tabellen: `wh_master_timelines`,
  `wh_timeline_entries`, `wh_foreshadowing_type_lookup`, `wh_foreshadowing_entries`,
  `wh_planned_flashbacks`)
- Migration `projects/0010_outline_sequence` (neue Tabelle: `wh_outline_sequences`,
  optionales FK `OutlineNode.sequence`)
- Seed: `NarrativeModelLookup` (4 Typen), `ForeshadowingTypeLookup` (6 Typen)
- Layer 8 (ADR-150): `get_open_foreshadowing_context()` in Service-Layer
- Layer 5 (ADR-150): Sequenz-Kontext in OutlineNode-Generierung
- Admin: `ForeshadowingEntry` als Projekt-Inline mit Status-Filter
- Admin: `TimelineEntry` als Inline in `MasterTimeline`

---

**Deployment-Reihenfolge (aus o4_o6_timeline_profile_uebersicht.md):**
```bash
python manage.py migrate projects 0009_master_timeline
python manage.py migrate projects 0010_outline_sequence
python manage.py seed_drama_lookups  # NarrativeModelLookup + ForeshadowingTypeLookup
```

---

**Referenzen:** ADR-150, ADR-151, ADR-152,  
`docs/adr/input/o4_o6_timeline_profile_uebersicht.md`,  
`docs/adr/input/schritt_08_zeitstruktur.md`,  
`docs/adr/input/o1_roman_spannungsarchitektur.md`
