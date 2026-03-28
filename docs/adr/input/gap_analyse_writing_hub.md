# Gap-Analyse: writing-hub vs. Romanstruktur-Framework (8 Schritte)

> Stand: writing-hub @ achimdehnert/writing-hub (main)
> Analysiert: apps/projects, apps/authoring, apps/authors, apps/worlds

---

## Übersicht: Was bereits vorhanden ist ✅

| Schritt | Konzept | Implementierung |
|---------|---------|-----------------|
| S1 | Grundontologie / BookProject | `BookProject` (UUID PK, genre, content_type, target_word_count) ✅ |
| S2 | Makrostruktur / Frameworks | `OutlineFramework` + `OutlineFrameworkBeat` (position_start/end) ✅ |
| S2 | Akt-Nodes | `OutlineNode.act`, `beat_phase` ✅ |
| S3 | Welt-Referenzen | `ProjectWorldLink`, `ProjectCharacterLink` via WeltenHub SSoT ✅ |
| S3 | Figur-Beziehung zu Arc | `ProjectCharacterLink.project_arc` ✅ (basic) |
| S4 | Szenen-Hierarchie | `OutlineNode.beat_type` (chapter/scene/beat/act/part) ✅ |
| S4 | Emotionaler Bogen | `OutlineNode.emotional_arc` (CharField) ⚠️ (unstrukturiert) |
| S5 | Prosa-Typen | `WritingStyleSample.SITUATIONS` (action/dialogue/description/emotion/inner...) ✅ |
| S5 | Style Lab | `WritingStyle.do_list/dont_list/taboo_list/signature_moves` ✅ |
| S5 | Autoren-Stimme | `AuthorStyleDNA` ✅ |
| S6 | Quality Scoring | `ChapterQualityScore`, `QualityDimension` (inkl. pacing) ✅ |
| S6 | Lektorat / Issues | `LektoratSession`, `LektoratIssue` (inkl. timeline-Typ) ✅ |
| alle | LLM-Kontext | `AuthoringSession.context_window` ✅ |
| alle | Workflow-Phasen | `ProjectPhaseExecution` mit Gate-System ✅ |

---

## Gap-Analyse: Was fehlt ❌

### Gap 1 — Schritt 1: Grundontologie fehlen auf `BookProject`

```python
# FEHLT auf BookProject:
inner_story = models.TextField(blank=True)      # Die innere Geschichte
outer_story = models.TextField(blank=True)       # Die äußere Geschichte
arc_direction = models.CharField(               # positiv | negativ | flach
    max_length=10,
    choices=[("positive","Positiv"),("negative","Negativ"),("flat","Flach")],
    blank=True
)
main_conflict_type = models.CharField(          # mensch_mensch | mensch_natur | mensch_selbst
    max_length=20, blank=True
)
```

### Gap 2 — Schritt 2: Wendepunkte fehlen

`OutlineFrameworkBeat` hat `position_start/end` und `name` — aber kein semantisches Modell für Wendepunkte mit Figur-Zustand:

```python
# FEHLT: StructureTurningPoint (pro Projekt, nicht pro Framework)
class ProjectTurningPoint(models.Model):
    project = FK(BookProject)
    name = CharField()               # "Inciting Incident", "Midpoint" etc.
    position_percent = SmallInt()    # 0-100
    position_word = IntField()
    what_happens = TextField()
    character_state_inner = TextField()
    character_state_outer = TextField()
    dramatic_function = TextField()
```

### Gap 3 — Schritt 3: Figuren-Dramaturgie fehlt

Charaktere leben in WeltenHub (SSoT richtig!) — aber `want/need/flaw/ghost` sind dramaturgische Konzepte, die *lokal* gebraucht werden:

```python
# FEHLT: Erweiterung von ProjectCharacterLink
want = TextField(blank=True)         # Äußeres, bewusstes Ziel
need = TextField(blank=True)         # Innere, unbewusste Wahrheit
flaw = TextField(blank=True)         # Psychologischer Riss
ghost = TextField(blank=True)        # Trauma-Ursprung des Fehlers
false_belief = TextField(blank=True) # Falsche Überzeugung Anfang
true_belief = TextField(blank=True)  # Wahre Erkenntnis Ende
arc_type = CharField(...)            # positiv | negativ | flach
voice_description = TextField()      # Wie klingt diese Figur?

# FEHLT: InformationTracker
class CharacterKnowledgeState(models.Model):
    project = FK(BookProject)
    character_id = UUIDField()       # WeltenHub-Referenz
    chapter_ref = FK(OutlineNode)
    knows = JSONField()              # Was weiß die Figur ab hier?
    does_not_know = JSONField()
```

### Gap 4 — Schritt 4: OutlineNode braucht mehr Dramaturgie

```python
# FEHLT auf OutlineNode:
outcome = CharField(
    max_length=10,
    choices=[("yes","Ja"),("no","Nein"),("yes_but","Ja, aber"),("no_and","Nein, und")],
    blank=True
)
pov_character_id = UUIDField(null=True, blank=True)  # WeltenHub-Referenz
pov_type = CharField(choices=[...], blank=True)       # first | third_limited | omniscient
emotion_start = CharField(max_length=100, blank=True) # "hoffnungsvoll"
emotion_end = CharField(max_length=100, blank=True)   # "verzweifelt"
sequel_needed = BooleanField(default=False)
tension_level = SmallIntegerField(null=True, blank=True)  # 1-10
timeline_position = DateTimeField(null=True, blank=True)  # Story-Zeitpunkt

# FEHLT: Sequenz-Ebene zwischen Akt und Kapitel
class OutlineSequence(models.Model):
    outline_version = FK(OutlineVersion)
    act = CharField(max_length=20)
    title = CharField(max_length=200)
    goal = TextField()
    start_state = TextField()
    end_state = TextField()
    order = PositiveIntegerField()
    # Nodes verlinken per sequence FK
```

### Gap 5 — Schritt 5: Erzählstimme pro Projekt fehlt

```python
# FEHLT: NarrativeVoice (1:1 zu BookProject)
class NarrativeVoice(models.Model):
    project = OneToOneField(BookProject)
    pov_type = CharField(choices=[...])    # first | third_limited | omniscient
    tense = CharField(choices=[...])       # past | present
    distance = CharField(choices=[...])    # close | medium | distant
    sentence_length = CharField(choices=[...])
    vocabulary_level = CharField(choices=[...])
    imagery_density = CharField(choices=[...])
    irony_level = CharField(choices=[...])
```

`WritingStyleSample.SITUATIONS` deckt die Prosa-Typen gut ab ✅ — aber kein strukturiertes `DialogueNode`-Modell.

### Gap 6 — Schritt 6: Spannungsarchitektur fehlt

```python
# FEHLT: TensionArc pro Projekt
class ProjectTensionArc(models.Model):
    project = FK(BookProject)
    dominant_tension_type = CharField(
        choices=[("mystery","Mystery"),("suspense","Suspense"),("dramatic_irony","Dramatic Irony")]
    )

# FEHLT: ForeshadowingEntry
class ForeshadowingEntry(models.Model):
    project = FK(BookProject)
    label = CharField(max_length=200)   # "Die Narbe an seiner Hand"
    foreshadow_type = CharField(...)    # objekt | dialog | bild | name
    introduced_in = FK(OutlineNode, related_name="foreshadowing_setups")
    resolved_in = FK(OutlineNode, related_name="foreshadowing_payoffs")
    meaning = TextField()
    payoff = TextField()
```

### Gap 7 — Schritt 7: Thema & Motiv fehlen vollständig

```python
# FEHLT: ProjectTheme (1:1)
class ProjectTheme(models.Model):
    project = OneToOneField(BookProject)
    core_question = TextField()         # "Kann man vergeben?"
    thematic_answer = TextField()       # Was der Roman am Ende antwortet
    thesis_character_id = UUIDField()   # WeltenHub-Ref: verkörpert die These
    antithesis_character_id = UUIDField()

# FEHLT: ProjectMotif
class ProjectMotif(models.Model):
    project = FK(BookProject)
    label = CharField(max_length=200)   # "Der Spiegel"
    motif_type = CharField(...)         # objekt | handlung | natur | farbe | dialog
    theme_connection = TextField()
    evolution = TextField()
    payoff = TextField()

# FEHLT: MotifAppearance
class MotifAppearance(models.Model):
    motif = FK(ProjectMotif)
    node = FK(OutlineNode)
    context = TextField()
    meaning_at_this_point = TextField()
    prominence = CharField(...)         # beiläufig | aufgeladen | symbolisch
```

### Gap 8 — Schritt 8: Zeitstruktur fehlt

```python
# FEHLT: MasterTimeline + TimelineEntry
class MasterTimeline(models.Model):
    project = OneToOneField(BookProject)
    narrative_model = CharField(
        choices=[("linear","Linear"),("in_medias_res","In medias res"),
                 ("non_linear","Nicht-linear"),("parallel","Parallel")]
    )
    story_time_span = CharField(max_length=200)  # "3 Wochen"

class TimelineEntry(models.Model):
    timeline = FK(MasterTimeline)
    entry_type = CharField(choices=[("pre_story","Pre-Story"),("story","Story"),("post_story","Post-Story")])
    story_date = CharField(max_length=100)        # "Tag 3, 14:00"
    node = FK(OutlineNode, null=True, blank=True)
    event_description = TextField()
    characters_involved = JSONField(default=list)  # WeltenHub UUIDs

# FEHLT: Flashback-Planung
class PlannedFlashback(models.Model):
    project = FK(BookProject)
    trigger_node = FK(OutlineNode, related_name="flashback_triggers")
    content_summary = TextField()
    dramatic_purpose = TextField()
    technique = CharField(...)  # hard_cut | trigger | chapter_break
    return_technique = TextField()
```

---

## Prioritäts-Empfehlung

### Priorität 1 — Sofort (maximaler dramaturgischer Impact)

| Gap | Migration | Aufwand |
|-----|-----------|---------|
| `OutlineNode` + outcome/emotion/tension | `0004_dramaturgic_fields` | ~30 min |
| `ProjectCharacterLink` + want/need/flaw/ghost | `0003_character_arc_fields` | ~20 min |
| `NarrativeVoice` | neues Model | ~30 min |
| `ProjectTheme` | neues Model | ~20 min |

### Priorität 2 — Mittelfristig

| Gap | Migration | Aufwand |
|-----|-----------|---------|
| `ProjectTurningPoint` | neues Model | ~45 min |
| `ForeshadowingEntry` | neues Model | ~30 min |
| `ProjectMotif` + `MotifAppearance` | neue Models | ~45 min |
| `OutlineSequence` | neues Model + Refactor | ~60 min |

### Priorität 3 — Langfristig

| Gap | Migration | Aufwand |
|-----|-----------|---------|
| `MasterTimeline` + `TimelineEntry` | neue Models | ~90 min |
| `CharacterKnowledgeState` | neues Model | ~60 min |
| `PlannedFlashback` | neues Model | ~30 min |

---

## Was der Hub bereits sehr gut macht

- **LLM-Routing**: `iil-aifw` + `AIActionType` ist perfekt für modulare Prompt-Templates
- **Prompt-Framework**: `iil-promptfw` mit 5-Layer Jinja2 ist ideal für die Template-Hierarchie aus Schritt 5/6
- **Quality Gate**: `ChapterQualityScore` + `QualityDimension` + `GateDecisionType` → direkt erweiterbar um dramaturgische Dimensionen (tension, emotional_arc_consistency, theme_resonance)
- **Style Lab**: `WritingStyle.do_list/dont_list/taboo_list` deckt Schritt 5 fast vollständig ab
- **WeltenHub SSoT**: richtige Entscheidung — lokale Dramaturgie-Felder auf den Link-Objekten ist die saubere Lösung

---

*Analysiert gegen: Romanstruktur-Framework Schritt 1–8 (roman_hub_komplett.md)*
*Repo: achimdehnert/writing-hub @ main*
