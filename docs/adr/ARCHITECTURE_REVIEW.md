# ARCHITECTURE_REVIEW — writing-hub

**Datum:** 2026-03-28 (aktualisiert: 2026-03-28 nach ADR-158 Accepted, ADR-161 Renummerierung)  
**Reviewer:** Prof. Autor & Verleger / Systemarchitekt  
**Basis:** ADR-150–161, Repo-Analyse achimdehnert/writing-hub (main)  
**Typ:** Zustandsdokument — keine bindende Entscheidung  

---

## 1. Systemzustand: Was der Hub heute kann

### 1.1 Stärken

```
DRAMATURGISCHE KERN-MODELLIERUNG (nach Prio-1 ADRs):
  ✅ OutlineNode: outcome, emotion_start/end, tension_numeric, pov
  ✅ ProjectCharacterLink: want, need, flaw, ghost, arc_type
  ✅ NarrativeVoice: POV, Tempus, Distanz, Stil-Direktiven
  ✅ ProjectTheme: Themen-Frage + Antwort, Motiv-System
  ✅ ForeshadowingEntry: Setup/Payoff-Paare (Chekhov's Gun)
  ✅ ProjectTurningPoint: Wendepunkte mit outlinefw-Sync
  ✅ MasterTimeline + CharacterKnowledgeState (Zeitkonsistenz)

LLM-INFRASTRUKTUR:
  ✅ iil-aifw: DB-getriebenes LLM-Routing, sync/async, Fallback
  ✅ iil-promptfw: Jinja2 5-Layer Prompt-Stack
  ✅ iil-authoringfw: StyleProfile, CharacterProfile, WorldContext
  ✅ iil-outlinefw: 5 Frameworks, BeatDefinitions, OutlineGenerator
  ✅ iil-weltenfw: WeltenHub SSoT für Welten/Charaktere/Orte

QUALITÄTSSYSTEM:
  ✅ ChapterQualityScore + QualityDimension + GateDecisionType
  ✅ LektoratSession + LektoratIssue (6 Issue-Typen)
  ✅ StyleChecker (regelbasiert, Regex-Antipattern)
  ✅ ADR-157 Rev.1: DramaturgicHealthScore (alle 7 Blocking Issues behoben, deploybar)
  ✅ ADR-158: Dialogue Subtext, Opening/Closing Image, GenrePromise, QualityDimension

PRODUKTIONS-FEATURES:
  ✅ ChapterWriter (Vanilla-JS, KI-Generierung + Polling)
  ✅ ManuscriptSnapshot (FIFO, max. 10 pro Projekt)
  ✅ Export (DOCX, PDF, Markdown)
  ✅ PublishingProfile (ISBN, BISAC, Keywords, Cover)
  ✅ Celery + Redis (Async Tasks)
```

### 1.2 Bereits geplante Erweiterungen (ADRs in Pipeline)

```
ADR-159 (Proposed):
  → ComparableTitle + PitchDocument + PitchGeneratorService

ADR-160 (Proposed):
  → ResearchNote + GenreConventionProfile + BetaReaderSession

ADR-161 (Proposed, ex ADR-158-produktions-infrastruktur):
  → TextAnalysisSnapshot + BudgetService + BatchWriteJob

O1–O6 (spezifiziert, noch nicht als ADR):
  → SeriesArc + SeriesCharacterContinuity (ADR-155 ✅)
  → EssayOutline + ArgumentNode
  → OutlineSequence (ADR-156 ✅)
  → ContentTypeProfile
```

---

## 2. Identifizierte Lücken

### 2.1 Ebene A — Verlegerisch kritisch

| # | Lücke | Fehlende Objekte | Warum kritisch |
|---|-------|------------------|----------------|
| A1 | **Kein Pitch-Format** | ComparableTitle, PitchDocument | Manuskript nicht einsendefertig |
| A2 | **Genre-Konventionen nicht prüfbar** | GenreConventionProfile | Falsches Genre-Label nicht erkennbar |
| A3 | **Antagonist ohne System** | ADR-157 (in Revision) | >80% Ablehnungen bei Erstromanen |

### 2.2 Ebene B — Technisch/Qualitativ

| # | Lücke | Fehlende Objekte | Symptom |
|---|-------|------------------|---------|
| B1 | **Dead Scenes nicht erkannt** | TextAnalysisSnapshot | emotion_start == emotion_end unbemerkt |
| B2 | **Voice Drift bei KI-Kapiteln** | TextAnalysisSnapshot | Stil-Abweichung über 50k Wörter |
| B3 | **Character Screen Time** | TextAnalysisSnapshot | Antagonist in 3 von 20 Kapiteln |
| B4 | **Pacing-Anti-Pattern** | PacingAnalysis | Längste Kapitel vor Climax |
| B5 | **Kein Wortanzahl-Budget** | BudgetService | Akt I überschreitet 60% des Budgets |
| B6 | **Batch-Generierung fehlt** | BatchWriteJob | 20× Button klicken für 20 Kapitel |

### 2.3 Ebene C — Wissens-Infrastruktur

| # | Lücke | Fehlende Objekte | Symptom |
|---|-------|------------------|---------|
| C1 | **Keine Recherche-Notes** | ResearchNote | Fakten im Notizbuch, nicht im Hub |
| C2 | **Kein Beta-Reader-Feedback** | BetaReaderSession | Testleser-Feedback nicht strukturiert |
| C3 | **Inline-Styles über 30 Templates** | CSS Custom Properties | Theme-Änderung = 500 Grep-Ersetzungen |
| C4 | **Kein HTMX** | HTMX-Integration | Filter = Full-Page-Reload |

---

## 3. Geplante ADRs

### ADR-158 — Dialogue Subtext, Opening/Closing Image, GenrePromise ✅ Accepted

**Scope:** DialogueScene + TurningPointTypeLookup (konsolidiert) + GenrePromise + QualityDimension  
**Neue Tabellen:**
```
wh_dialogue_scenes
wh_turning_point_type_lookup  (core-App, K1-konsolidiert)
wh_genre_promise_lookup       (core-App)
wh_project_genre_promises
```

---

### ADR-159 — Publikationsvorbereitung

**Scope:** ComparableTitle + PitchDocument + PitchGeneratorService  
**Priorität:** Hoch — schließt den Weg zum Verlag  
**Neue Tabellen:**
```
wh_comparable_titles
wh_pitch_documents
```
**Kern-Entscheidung:** Pitch-Typen (logline / expose_de / synopsis / query)
als DB-Objekte mit Versionierung; LLM-Generierung via aifw.

---

### ADR-160 — Wissens-Infrastruktur

**Scope:** ResearchNote + GenreConventionProfile + BetaReaderSession  
**Priorität:** Mittel  
**Neue Tabellen:**
```
wh_research_notes
wh_genre_convention_profiles
wh_beta_reader_sessions
wh_beta_reader_feedbacks
```
**Kern-Entscheidung:** ResearchNote M2M zu OutlineNode (Fakten bei
Kapitel-Generierung injizierbar); GenreConventionProfile Admin-verwaltbar
(keine Code-Änderung für neue Genres).
**K2-Fix:** `reader_promise` auf `GenreConventionProfile` gestrichen —
dieses Konzept gehört in `GenrePromiseLookup` (ADR-158).

---

### ADR-161 — Produktions-Infrastruktur (ex ADR-158-produktions-infrastruktur)

**Scope:** TextAnalysisSnapshot + BudgetService + PacingAnalysis + BatchWriteJob  
**Priorität:** Hoch — direkt nach ADR-157 Rev.1  
**Neue Tabellen:**
```
wh_text_analysis_snapshots
wh_batch_write_jobs
```
**Kern-Entscheidung:** Textanalyse als gecachter Snapshot (nicht live berechnet),
Batch-Generierung mit max_chapters=10 Sicherheitslimit.
**Renummerierung:** War ADR-158-produktions-infrastruktur.md — umbenannt wegen
Nummerierungskonflikt mit ADR-158 (Accepted, Dialogue Subtext).

---

## 4. Frontend-Roadmap

| Schritt | Was | Aufwand | Status |
|---------|-----|---------|--------|
| FE1 | CSS Custom Properties (`:root`) | 2h | offen |
| FE2 | HTMX Filter + Auto-Save + Inline-Edit | 4h | offen |
| FE3 | Drama-Dashboard (Chart.js Spannungskurve) | 3h | offen |
| FE4 | Essay Argument-Tree UI | 2h | offen |
| FE5 | Series Arc Dashboard | 2h | offen |

---

## 5. Gesamt-Tabellen-Inventar (nach allen Optimierungen)

### Prio-1 (ADR-150–156, deployed/geplant)

```
wh_scene_outcome_lookup
wh_pov_type_lookup
wh_tension_level_lookup
wh_character_arc_type_lookup
wh_tempus_lookup
wh_narrative_distance_lookup
wh_vocabulary_level_lookup
wh_narrative_voices
wh_project_themes
wh_motif_type_lookup
wh_project_motifs
wh_motif_appearances
wh_foreshadowing_type_lookup
wh_foreshadowing_entries
wh_turning_point_type_lookup
wh_project_turning_points
wh_content_type_profiles
wh_narrative_model_lookup
wh_master_timelines
wh_timeline_entries
wh_character_knowledge_states
```

### ADR-157 (in Revision)

```
wh_subplot_arcs
```

### O2–O3 (spezifiziert, ADR pending)

```
wh_series_arc_type_lookup
wh_series_arcs
wh_series_volume_roles
wh_series_character_continuities
wh_essay_structure_type_lookup
wh_argument_node_type_lookup
wh_essay_outlines
wh_argument_nodes
```

### ADR-158 (Accepted)

```
wh_dialogue_scenes
wh_turning_point_type_lookup
wh_genre_promise_lookup
wh_project_genre_promises
```

### ADR-159

```
wh_comparable_titles
wh_pitch_documents
```

### ADR-160

```
wh_research_notes
wh_genre_convention_profiles
wh_beta_reader_sessions
wh_beta_reader_feedbacks
```

### ADR-161 (ex ADR-158)

```
wh_text_analysis_snapshots
wh_batch_write_jobs
```

**Gesamt: 46 neue Tabellen** (ADR-158 Accepted: +4) (alle `wh_`-prefixed, alle idempotent seedbar)

---

## 6. Sprint-Empfehlung

```
SPRINT 1 — "Dramaturgie sauber" (1–2 Wochen)
  ADR-157 Rev.1 ✅ (alle 7 Blocking Issues behoben)
  ADR-158 ✅ (Accepted: Dialogue Subtext, GenrePromise, Image Mirror)
  FE1 CSS Custom Properties
  OPT1 Dead Scene Detection (regelbasiert, aus ADR-161)

SPRINT 2 — "Schreiben effizienter" (2–3 Wochen)
  ADR-161 (TextAnalysis + Budget + Batch)
  FE2 HTMX Filter + Auto-Save
  FE3 Drama-Dashboard

SPRINT 3 — "Zum Verlag" (3–4 Wochen)
  ADR-159 (Comps + Pitch + Exposé)
  ADR-160 Recherche-Notes
  OPT3 Genre-Konventionen (Seed-Arbeit im Admin)

SPRINT 4 — "Serien & Essays" (4–6 Wochen)
  O2 Series Arc ADR
  O3 Essay-Struktur ADR
  FE4 + FE5
  ADR-160 Beta-Reader
```

---

## 7. Die 5 kritischsten offenen Punkte

Nach verlegerischer Priorität:

**1. ADR-157 Rev.1 deployen** ✅ behoben  
Alle 7 Blocking Issues (B1–B7) + M4/M5 + D3/D4 in Rev.1 adressiert.

**2. Kein Pitch-Format (ADR-159)**  
Der Hub führt den Autor bis zum fertigen Manuskript — dann endet er.
Das Transmissions-Format zum Verlag fehlt.

**3. Genre-Label nicht validierbar (ADR-160)**  
Ein "Thriller" ohne die Thriller-Konventionen zu erfüllen ist
kein vermarktbarer Thriller. Das Hub kann das aktuell nicht erkennen.

**4. Dead Scene Detection fehlt (ADR-161)**  
KI-generierte Kapitel produzieren Dead Scenes stillos.
Die Detection ist trivial (reine DB-Abfrage) — der Aufwand
steht in keinem Verhältnis zum Nutzen.

**5. Inline-Style-Debt (FE1)**  
30+ Templates mit 500+ Inline-Styles sind ein Wartungs-Risiko.
FE1 kostet 2h und eliminiert das Problem strukturell.

---

*writing-hub · ARCHITECTURE_REVIEW.md*  
*Kein ADR — Zustandsdokument, nicht bindend*  
*Nachfolge-ADRs: 159, 160, 161 (ADR-158 Accepted)*
