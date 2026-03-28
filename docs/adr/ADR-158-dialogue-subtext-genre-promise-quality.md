# ADR-158: Dialogue Subtext, Opening/Closing Image, GenrePromise und QualityDimension-Erweiterung

**Status:** Accepted  
**Datum:** 2026-03-28  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-151, ADR-154, ADR-157

---

## Kontext

Vier weitere verlegerisch-dramaturgische Lücken, die nach einer Vollanalyse
der ADRs 150–157 identifiziert wurden:

### Lücke 1 — Dialogue Subtext: häufigster LLM-Fehler Nr. 1

Das Romanstruktur-Framework (Schritt 1.3) formuliert:

> *"Dialog ist das Sichtbarwerden von Subtext — nicht was Figuren sagen,
> sondern was sie NICHT sagen."*

LLMs generieren standardmäßig **On-Nose-Dialog** (Figuren sagen genau
was sie meinen). Ohne strukturierten Subtext-Kontext im Prompt ist das
unvermeidbar. Der writing-hub hat keine Struktur für:

- Was will jede Figur IN DIESER Konversation erreichen? (Dialog-Goal)
- Was darf sie NICHT direkt sagen? (Subtext-Constraint)
- Welche Informations-Asymmetrie besteht? (wer weiß was)
- Was ändert sich durch den Dialog? (Dialog-Outcome)

### Lücke 2 — Opening/Closing Image fehlt als semantischer Typ

Das Drei-Akte-Modell (ADR-150) betont explizit:

> *"Closing Image spiegelt Opening Image — zeigt die Transformation."*

`ProjectTurningPoint` (ADR-151) hat `position_percent` und `name` —
aber keine semantische Unterscheidung zwischen:
- Opening Image (1%) — zeigt Status Quo VOR der Veränderung
- Closing Image (100%) — zeigt neue Normalwelt, spiegelt Opening
- Dark Night of the Soul (78%) — emotionaler Tiefpunkt

Ohne diesen Typ kann das LLM nicht prüfen: *"Spiegelt das Ending das Opening?"*

### Lücke 3 — GenrePromise: verlegerische Pflicht

Professionelle Verlage lehnen Romane ab, wenn das **Genre-Versprechen**
nicht eingelöst wird — unabhängig von handwerklicher Qualität:

- Thriller: Alle Geheimnisse aufgelöst, Spannung bis letzte Seite
- Romance: HEA (Happily Ever After) oder HFN (Happy For Now) — PFLICHT
- Literary Fiction: Thematische Resonanz und Stil über Plot
- Fantasy: Weltenkonsistenz + Magie-System-Integrität

Kein ADR definiert, was das konkrete Genre-Versprechen ist, ob es eingelöst
wurde, und wie das LLM beim Schreiben daran erinnert werden soll.

### Lücke 4 — QualityDimension fehlen dramaturgische Dimensionen

Die Gap-Analyse identifiziert bereits: `ChapterQualityScore` und
`QualityDimension` existieren ✅ — aber die dramaturgischen Dimensionen
fehlen:
- `dramaturgic_tension` — Spannungsniveau konsistent mit Kurve?
- `emotional_arc_consistency` — Emotions-Delta stimmt mit Figuren-Arc?
- `theme_resonance` — Szene zahlt auf Thema ein?
- `subtext_quality` — Dialog-Qualität (on-nose vs. subtextreich)?

---

## Entscheidung

### Teil A: DialogueScene (in `apps/projects/models_narrative.py`)

```python
import uuid
from django.db import models


class DialogueScene(models.Model):
    """
    Subtext-Struktur einer Dialog-Szene.

    Eine DialogueScene ist KEINE Szene im OutlineNode-Sinne — sie ist
    die dramaturgische Analyse eines einzelnen Gesprächs.
    Pro OutlineNode kann es 0–N DialogueScenes geben.

    Kernprinzip: On-Nose-Dialog ist der häufigste LLM-Fehler.
    Dieses Modell gibt dem LLM die Subtext-Schicht explizit.

    Dialog-Outcome-Typen:
        status_quo     → Dialog ändert nichts (selten erlaubt)
        info_shift     → Informationsstand verändert sich
        power_shift    → Machtverhältnis kippt
        relationship   → Beziehung verändert sich
        revelation     → Enthüllung — etwas kommt ans Licht
        decision       → Entscheidung wird herbeigeführt
    """
    DIALOGUE_OUTCOMES = [
        ("status_quo",    "Status Quo — nichts ändert sich (Ausnahme!)"),
        ("info_shift",    "Info-Shift — Wissensstand verändert sich"),
        ("power_shift",   "Power-Shift — Machtverhältnis kippt"),
        ("relationship",  "Beziehungs-Shift — Nähe/Distanz verändert"),
        ("revelation",    "Enthüllung — etwas kommt ans Licht"),
        ("decision",      "Entscheidungs-Katalysator"),
    ]

    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.CASCADE,
        related_name="dialogue_scenes",
        verbose_name="Szene",
    )

    # Beteiligte Figuren
    speaker_a_character_id = models.UUIDField(
        null=True, blank=True,
        verbose_name="Figur A (WeltenHub UUID)",
    )
    speaker_a_name = models.CharField(max_length=200, blank=True, default="",
                                       verbose_name="Figur A (Cache)")
    speaker_b_character_id = models.UUIDField(
        null=True, blank=True,
        verbose_name="Figur B (WeltenHub UUID)",
    )
    speaker_b_name = models.CharField(max_length=200, blank=True, default="",
                                       verbose_name="Figur B (Cache)")

    # Dialog-Goals (was will jede Figur IN DIESEM Gespräch erreichen?)
    goal_a = models.TextField(
        blank=True, default="",
        verbose_name="Ziel Figur A im Dialog",
        help_text="Was will Figur A durch dieses Gespräch erreichen? "
                  "Konkret, aktiv, nicht 'Informationen austauschen'.",
    )
    goal_b = models.TextField(
        blank=True, default="",
        verbose_name="Ziel Figur B im Dialog",
    )

    # Subtext-Constraints (was darf NICHT direkt gesagt werden?)
    subtext_a = models.TextField(
        blank=True, default="",
        verbose_name="Subtext Figur A",
        help_text="Was meint Figur A wirklich, kann/darf es aber nicht direkt sagen? "
                  "Dieser Subtext muss ZWISCHEN den Zeilen lesbar sein.",
    )
    subtext_b = models.TextField(
        blank=True, default="",
        verbose_name="Subtext Figur B",
    )

    # Informations-Asymmetrie
    info_asymmetry = models.TextField(
        blank=True, default="",
        verbose_name="Informations-Asymmetrie",
        help_text="Was weiß eine Figur, was die andere nicht weiß? "
                  "Diese Asymmetrie erzeugt dramatische Ironie.",
    )

    # Outcome
    dialogue_outcome = models.CharField(
        max_length=20,
        choices=DIALOGUE_OUTCOMES,
        default="info_shift",
        verbose_name="Dialog-Outcome",
    )
    outcome_description = models.TextField(
        blank=True, default="",
        verbose_name="Outcome-Beschreibung",
        help_text="Was ändert sich konkret durch diesen Dialog?",
    )

    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table        = "wh_dialogue_scenes"
        ordering        = ["node", "sort_order"]
        verbose_name    = "Dialog-Subtext"
        verbose_name_plural = "Dialog-Subtexte"

    def __str__(self):
        return f"Dialog: {self.speaker_a_name} ↔ {self.speaker_b_name} [{self.get_dialogue_outcome_display()}]"

    def to_prompt_context(self) -> str:
        """
        Gibt Subtext-Struktur als LLM-Prompt-Block zurück.
        Verhindert On-Nose-Dialog.
        """
        lines = [
            f"[DIALOG: {self.speaker_a_name} ↔ {self.speaker_b_name}]",
            f"ZIEL {self.speaker_a_name}: {self.goal_a}",
            f"ZIEL {self.speaker_b_name}: {self.goal_b}",
        ]
        if self.subtext_a:
            lines.append(f"SUBTEXT {self.speaker_a_name}: {self.subtext_a} "
                         f"(darf NICHT direkt gesagt werden)")
        if self.subtext_b:
            lines.append(f"SUBTEXT {self.speaker_b_name}: {self.subtext_b} "
                         f"(darf NICHT direkt gesagt werden)")
        if self.info_asymmetry:
            lines.append(f"INFORMATIONS-ASYMMETRIE: {self.info_asymmetry}")
        lines.append(f"ERWARTETER OUTCOME: {self.get_dialogue_outcome_display()} — "
                     f"{self.outcome_description}")
        return "\n".join(lines)
```

### Teil B: TurningPointTypeLookup — Opening/Closing Image (in `apps/core/models_lookups_drama.py`)

```python
class TurningPointTypeLookup(models.Model):
    """
    Lookup: Semantische Typen von Wendepunkten.
    App: apps/core/models_lookups_drama.py (Core-App — app_label="core")

    KONSOLIDIERT aus zwei Specs (K1-Fix, KONSEQUENZANALYSE_ADR158):
        - ADR-158 nutzte SmallInt (0–100) für default_position
        - O1-Spec nutzte Decimal (0.0–1.0) für outlinefw-Kompatibilität
        - Lösung: beide Felder, gegenseitig ableitbar

    Seed-Werte (Drei-Akte-Modell + universelle Typen):
        opening_image    | Opening Image     |  1% | Status Quo VOR der Veränderung
        inciting_incident| Inciting Incident | 10% | Das auslösende Ereignis
        debate           | Debate            | 12% | Figur zögert
        break_into_2     | Break into Act II | 25% | Kein Zurück
        b_story_begins   | B-Story Start     | 37% | Thematischer Spiegel beginnt
        midpoint         | Midpoint          | 50% | Scheinsieg / Scheinniederlage
        bad_guys_close   | Bad Guys Close In | 62% | Alles wird schlimmer
        all_is_lost      | All Is Lost       | 75% | Tiefpunkt
        dark_night       | Dark Night        | 78% | Figur gibt (fast) auf
        break_into_3     | Break into Act III| 87% | Neue Erkenntnis
        climax           | Climax            | 98% | Finale Konfrontation
        closing_image    | Closing Image     |100% | Neue Normalwelt — spiegelt Opening
    """
    code               = models.SlugField(max_length=30, unique=True)
    label              = models.CharField(max_length=100)
    description        = models.TextField(blank=True, default="")

    # K1-Fix: SmallInt (0–100) — konsistent mit position_percent im gesamten Stack
    default_position_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text="Typische Position im Roman (0–100%)",
    )
    # K1-Fix: Decimal (0.0–1.0) — für outlinefw-Kompatibilität
    default_position_normalized = models.DecimalField(
        max_digits=4, decimal_places=3,
        null=True, blank=True,
        help_text="Normiert (0.0–1.0) — für outlinefw-Kompatibilität, ableitbar aus default_position_percent / 100",
    )
    # K1-Fix: outlinefw-Mapping aus O1-Spec
    outlinefw_beat_name = models.CharField(
        max_length=80, blank=True, default="",
        help_text="Mapping auf outlinefw BeatDefinition-Name (falls vorhanden)",
    )
    mirrors_type_code  = models.SlugField(
        max_length=30, blank=True, default="",
        help_text="Code des gespiegelten Typs (z.B. closing_image → opening_image)",
    )
    sort_order         = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table        = "wh_turning_point_type_lookup"
        app_label       = "core"   # Core-App besitzt die Tabelle — kein Migration-Crash
        ordering        = ["sort_order"]
        verbose_name    = "Wendepunkt-Typ"
        verbose_name_plural = "Wendepunkt-Typen"

    def __str__(self):
        return f"{self.code} — {self.label} ({self.default_position_percent}%)"
```

**`ProjectTurningPoint` erhält FK auf `TurningPointTypeLookup` (K4-Fix: app_label=core):**

```python
# Auf ProjectTurningPoint (ADR-151) — neue Felder:
# K4-Fix: FK zeigt auf core.TurningPointTypeLookup (nicht projects.)
turning_point_type = models.ForeignKey(
    "core.TurningPointTypeLookup",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    verbose_name="Wendepunkt-Typ",
    help_text="Semantischer Typ (Opening Image, Midpoint, Closing Image...)",
)
mirrors_node = models.ForeignKey(
    "projects.OutlineNode",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="mirrored_by_turning_points",
    verbose_name="Gespiegelte Szene",
    help_text="Nur für closing_image: die OutlineNode des Opening Image.",
)
```

**Validierungs-Regel für Opening/Closing-Spiegel:**

```python
def validate_image_mirror(project) -> tuple[bool, str]:
    """
    Prüft ob Closing Image das Opening Image spiegelt.
    Gibt (True, "") oder (False, Warnung) zurück.
    """
    opening = project.turning_points.filter(
        turning_point_type__code="opening_image"
    ).first()
    closing = project.turning_points.filter(
        turning_point_type__code="closing_image"
    ).first()

    if not opening:
        return False, "Opening Image fehlt — erste Szene nicht definiert."
    if not closing:
        return False, "Closing Image fehlt — letzte Szene nicht definiert."
    if not closing.mirrors_node and not closing.what_happens:
        return False, "Closing Image hat keinen Bezug zum Opening Image."
    return True, ""
```

### Teil C: GenrePromise (in `apps/projects/models_narrative.py`)

```python
class GenrePromiseLookup(models.Model):
    """
    Lookup: Was verspricht ein bestimmtes Genre dem Leser?

    Verlage lehnen Romane ab, wenn das Genre-Versprechen nicht eingelöst
    wird — unabhängig von handwerklicher Qualität.

    Seed-Werte:
        thriller     | Thriller    | Alle Rätsel aufgelöst, Spannung bis letzte Seite
        romance      | Romance     | HEA oder HFN — Happily Ever After / Happy For Now
        literary     | Literarisch | Thematische Tiefe + Stilqualität über Plot
        fantasy      | Fantasy     | Weltenkonsistenz + Magie-System-Integrität
        scifi        | Science-Fiction | Wissenschaftliche Logik + Worldbuilding
        mystery      | Krimi/Mystery | Täter identifiziert, alle Hinweise fair gelegt
        horror       | Horror      | Bedrohung realisiert sich oder bleibt unheimlich
        historical   | Historisch  | Historische Authentizität + Charaktertiefe
        ya           | Young Adult | Coming-of-Age-Transformation, zugänglicher Stil
    """
    code             = models.SlugField(max_length=30, unique=True)
    label            = models.CharField(max_length=100)
    core_promise     = models.TextField(
        verbose_name="Kern-Versprechen",
        help_text="Was erwartet der Leser UNBEDINGT? Verletzung = Ablehnung.",
    )
    reader_expectation = models.TextField(
        blank=True, default="",
        verbose_name="Leser-Erwartung",
        help_text="Was erhofft der Leser zusätzlich? Erfüllung = Begeisterung.",
    )
    llm_reminder     = models.TextField(
        blank=True, default="",
        verbose_name="LLM-Erinnerung",
        help_text="Prompt-Formulierung für LLM: 'Stelle sicher, dass...'",
    )
    sort_order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table        = "wh_genre_promise_lookup"
        ordering        = ["sort_order"]
        verbose_name    = "Genre-Versprechen"
        verbose_name_plural = "Genre-Versprechen"

    def __str__(self):
        return f"{self.code} — {self.label}"


class ProjectGenrePromise(models.Model):
    """
    Das Genre-Versprechen eines konkreten Projekts. 1:1 zu BookProject.

    Koppelt das abstrakte Genre-Versprechen (GenrePromiseLookup) mit der
    projekt-spezifischen Einlösung:
        - Wie wird das Versprechen in DIESEM Roman eingelöst?
        - Ist es bereits erfüllt (am Ende der Planungsphase)?
        - LLM-Erinnerung für Szenen-Generierung
    """
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="genre_promise",
    )
    genre_promise_type = models.ForeignKey(
        GenrePromiseLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Genre-Versprechen-Typ",
    )

    # Projekt-spezifische Einlösung
    how_fulfilled = models.TextField(
        blank=True, default="",
        verbose_name="Einlösung im Projekt",
        help_text="Wie löst DIESER Roman das Genre-Versprechen konkret ein?",
    )
    fulfillment_scene = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="genre_promise_fulfillments",
        verbose_name="Einlösungs-Szene",
        help_text="In welcher Szene wird das Versprechen eingelöst?",
    )
    is_fulfilled = models.BooleanField(
        default=False,
        verbose_name="Eingelöst",
        help_text="Wurde das Genre-Versprechen in der Planung berücksichtigt?",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "wh_project_genre_promises"
        verbose_name    = "Projekt-Genre-Versprechen"
        verbose_name_plural = "Projekt-Genre-Versprechen"

    def __str__(self):
        return f"GenrePromise — {self.project.title}"

    def to_prompt_context(self) -> str:
        """Gibt Genre-Versprechen als LLM-Erinnerung zurück."""
        if not self.genre_promise_type:
            return ""
        lines = [
            f"GENRE-VERSPRECHEN ({self.genre_promise_type.label}):",
            f"  Kern: {self.genre_promise_type.core_promise}",
        ]
        if self.how_fulfilled:
            lines.append(f"  Einlösung in diesem Roman: {self.how_fulfilled}")
        if self.genre_promise_type.llm_reminder:
            lines.append(f"  ERINNERUNG: {self.genre_promise_type.llm_reminder}")
        return "\n".join(lines)
```

### Teil D: QualityDimension-Erweiterung (Seed-Daten)

```python
# In seed_drama_lookups.py — Erweiterung der bestehenden QualityDimension-Seeds:

DRAMATIC_QUALITY_DIMENSIONS = [
    dict(
        code="dramaturgic_tension",
        label="Dramaturgische Spannung",
        description="Ist das Spannungsniveau dieser Szene konsistent mit der "
                    "Spannungskurve (tension_numeric)? Zu flach = Leser verliert Interesse. "
                    "Zu hoch ohne Eskalation = Wirkung verpufft.",
        weight=3,
    ),
    dict(
        code="emotional_arc_consistency",
        label="Emotions-Arc-Konsistenz",
        description="Stimmt das Emotions-Delta (emotion_start → emotion_end) mit "
                    "dem Figuren-Arc überein? Eine Figur darf nicht 'falsch' fühlen.",
        weight=3,
    ),
    dict(
        code="theme_resonance",
        label="Thematische Resonanz",
        description="Zahlt diese Szene auf das Thema (ProjectTheme.core_question) ein? "
                    "Jede Szene sollte das Thema berühren — direkt oder durch Kontrast.",
        weight=2,
    ),
    dict(
        code="subtext_quality",
        label="Subtext-Qualität",
        description="Sprechen Figuren im Dialog ON-NOSE (sagen direkt was sie meinen) "
                    "oder mit Subtext? On-Nose-Dialog ist das häufigste LLM-Schwächezeichen.",
        weight=2,
    ),
    dict(
        code="genre_promise_consistency",
        label="Genre-Versprechen-Konsistenz",
        description="Hält diese Szene das Genre-Versprechen? "
                    "Ein Thriller muss auch in ruhigen Szenen latente Bedrohung erzeugen.",
        weight=2,
    ),
]
```

### Teil E: LLM-Kontext-Erweiterung (ADR-150 Layer 5 + neuer Layer 10)

**Layer 5 erweitert** (aktiver OutlineNode):
```
Layer 5 — Aktiver OutlineNode
  ... (bestehende Felder)
  DIALOG-SUBTEXT (falls DialogueScene vorhanden):
    {{ dialogue.to_prompt_context() }}
```

**Neuer Layer 10** (Genre-Versprechen — immer im System-Prompt):
```
[SYSTEM — Layer 10]
  {{ project.genre_promise.to_prompt_context() }}
  → Jede generierte Szene muss dieses Versprechen einhalten.
```

---

## Begründung

- **`DialogueScene` als separates Modell** (nicht auf `OutlineNode`):
  Nicht jede Szene hat Dialog. Nicht jeder Dialog braucht Subtext-Struktur.
  Optional, aber wenn vorhanden, gibt es dem LLM präzise Constraint-Vorgaben.
- **`to_prompt_context()`-Methoden** direkt auf Models: Konsistent mit
  `SeriesCharacterContinuity` (ADR-155) und `CharacterKnowledgeState` (ADR-152).
  String-Formatierung für LLM-Prompts gehört zur Model-Verantwortlichkeit.
- **`TurningPointTypeLookup`** mit `mirrors_type_code`: Ermöglicht die
  Opening/Closing-Spiegel-Validierung ohne hardcoded String-Vergleiche.
  Der `mirrors_type_code` ist ein Lookup-zu-Lookup-Verweis (Slug, kein FK —
  zirkulärer FK würde den Seed-Prozess komplizieren).
- **`GenrePromiseLookup` in `apps/core`**: Wird app-übergreifend referenziert
  (`projects` + evtl. `series`). Konsistent mit Core-App-Strategie (ADR-151).
- **QualityDimension als Seed** (nicht neues Modell): `QualityDimension`
  existiert bereits. Die 5 neuen Dimensionen sind Daten, kein Schema-Change.
- **Layer 10 im System-Prompt**: Das Genre-Versprechen gilt für JEDEN
  generierten Satz — es ist kein szenen-spezifischer Kontext, sondern ein
  globaler Constraint wie die NarrativeVoice (Layer 1).

---

## Abgelehnte Alternativen

**Subtext als TextField auf `OutlineNode`:** Nicht typsicher, keine Figuren-
Zuordnung, kein Outcome-Tracking, kein `to_prompt_context()`.

**`TurningPointType` als CharField-choices:** Kein `default_position`,
kein `mirrors_type_code`, keine Admin-Verwaltung.

**`GenrePromise` als Felder auf `BookProject`:** `BookProject` wird schon
mit ADR-150 um 4 Felder erweitert. Ein eigenes Modell hält es schlank
und ermöglicht die LLM-Erinnerung als strukturierten Lookup-Wert.

**Neue QualityDimension-Modelle:** Die bestehende Tabelle `wh_quality_dimensions`
ist via Seed befüllt — neue Einträge sind idempotent addierbar ohne Migration.

---

## Konsequenzen

- Migration `projects/0012_dialogue_scene` (neue Tabelle `wh_dialogue_scenes`)
- Migration `core/0002_turning_point_type_lookup` (neue Tabelle
  `wh_turning_point_type_lookup`)
- Migration `projects/0013_turning_point_type_fk` (FK auf `ProjectTurningPoint`)
- Migration `core/0003_genre_promise_lookup` + `projects/0014_genre_promise`
  (Tabellen `wh_genre_promise_lookup`, `wh_project_genre_promises`)
- Seed: `TurningPointTypeLookup` (12 Typen), `GenrePromiseLookup` (9 Genres),
  5 neue `QualityDimension`-Einträge
- ADR-150 Layer 5 und Layer 10 im Prompt-Service implementieren
- `validate_image_mirror()` in `apps/projects/services/health_service.py`
  (ergänzt `compute_dramaturgic_health()` aus ADR-157)
- Admin: `DialogueScene` als Inline in `OutlineNodeAdmin`
- Admin: `ProjectGenrePromise` als Inline in `BookProjectAdmin`

---

**Deployment-Reihenfolge:**
```bash
python manage.py migrate core    0002_turning_point_type_lookup
python manage.py migrate core    0003_genre_promise_lookup
python manage.py migrate projects 0012_dialogue_scene
python manage.py migrate projects 0013_turning_point_type_fk
python manage.py migrate projects 0014_genre_promise
python manage.py seed_drama_lookups   # TurningPointType + GenrePromise + QualityDimensions
```

---

**Referenzen:** ADR-150, ADR-151, ADR-154, ADR-157,  
`docs/adr/input/roman_hub_komplett.md` (Schritt 1.3, 2.2, 3.3),  
`docs/adr/input/schritt_02_makrostruktur.md` (Opening/Closing Image)
