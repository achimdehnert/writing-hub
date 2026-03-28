# ADR-INDEX — writing-hub

**Letzte Aktualisierung:** 2026-03-28  
**Basis:** ADR-150–161  
**Legende:**
- Status: `Accepted` ✅ | `Proposed` 📋 | `Deprecated` ⛔
- Impl: `none` ⬜ | `partial` 🔶 | `implemented` ✅ | `verified` ✅✅

---

## Übersicht

| ADR | Titel | Status | Impl | Migrations | Abhängig von |
|-----|-------|--------|------|------------|--------------|
| [150](#adr-150) | Romanstruktur 4-Ebenen-Datenmodell | ✅ Accepted | ⬜ none | `projects/0001` (Basis) | — |
| [151](#adr-151) | Dramaturgische Felder OutlineNode + Lookups | ✅ Accepted | ⬜ none | `projects/0008`, `core/initial` | 150 |
| [152](#adr-152) | Charakter-Arc-Dramaturgie | ✅ Accepted | ⬜ none | `worlds/0003` | 150, 151 |
| [153](#adr-153) | Frontend CSS Design Tokens + HTMX | ✅ Accepted | ⬜ none | — (Frontend) | — |
| [154](#adr-154) | Drama-Dashboard + Content-Type-UIs | ✅ Accepted | ⬜ none | `projects/0009` | 151, 152 |
| [155](#adr-155) | Serien-Dramaturgie | ✅ Accepted | ⬜ none | `series/0001` | 150, 152 |
| [156](#adr-156) | Zeitstruktur, Foreshadowing, Sequenz | ✅ Accepted | ⬜ none | `projects/0010+` | 150, 151 |
| [157](#adr-157) | Antagonist-System, B-Story/Subplot, MVN-Health **Rev.1** | ✅ Accepted | ⬜ none | `worlds/0004`, `projects/0014` | 150, 151, 152 |
| [158](#adr-158) | Dialogue Subtext, Opening/Closing Image, GenrePromise | ✅ Accepted | ⬜ none | `core/0001`, `projects/0014` | 150, 151, 157 |
| [159](#adr-159) | Publikationsvorbereitung — Comps, Pitch, Exposé | 📋 Proposed | ⬜ none | `projects/0015` | 083, 150, 157-Rev1, 158 |
| [160](#adr-160) | Wissens-Infrastruktur — Recherche, Genre, Beta-Reader | 📋 Proposed | ⬜ none | `projects/0016` | 083, 150, 157-Rev1, 158, 159 |
| [161](#adr-161) | Produktions-Infrastruktur — TextAnalysis, Budget, Batch | 📋 Proposed | ⬜ none | `projects/0017`, `authoring/0003` | 150, 151, 153, 157-Rev1 |

---

## Sprint-Reihenfolge

```
SPRINT 1 — "Dramaturgie sauber" (jetzt bereit)
  ├── ADR-157 Rev.1  →  worlds/0004 + projects/0014_narrative_role_subplot_arc
  ├── ADR-158        →  core/0001_lookups_drama + projects/0014_dialogue_genre
  └── FE1: CSS Custom Properties (ADR-153)

SPRINT 2 — "Schreiben effizienter"
  ├── ADR-161  →  projects/0017 + authoring/0003
  └── FE2: HTMX Filter + Auto-Save

SPRINT 3 — "Zum Verlag"
  ├── ADR-159  →  projects/0015
  ├── ADR-160  →  projects/0016
  └── FE3: Drama-Dashboard (Chart.js)

SPRINT 4 — "Serien & Essays"
  ├── ADR-155 Impl  →  series/ (bereits Accepted, noch nicht implementiert)
  ├── ADR-156 Impl  →  projects/ (bereits Accepted)
  └── FE4/FE5
```

---

## Detailansicht

### ADR-150

**Titel:** Romanstruktur 4-Ebenen-Datenmodell  
**Datei:** `ADR-150-romanstruktur-4-ebenen-datenmodell.md`  
**Kern-Entscheidung:** Vier-Ebenen-Modell (Substrat → Makro → Meso → Mikro). `BookProject` als zentrales Objekt. LLM-Kontext-Hierarchie Layer 1–5.  
**Neue Tabellen:** `wh_book_projects` (Erweiterung)  
**Offene Impl-Fragen:** `outer_story`, `inner_story`, `arc_direction`, `theme`-FK auf `BookProject` — in vorhandener Migration?

---

### ADR-151

**Titel:** Dramaturgische Felder OutlineNode + Lookups  
**Datei:** `ADR-151-dramaturgische-felder-outlinenode-lookups.md`  
**Kern-Entscheidung:** `SceneOutcomeLookup`, `POVTypeLookup`, `EmotionLookup` in `apps/core`. `ProjectTurningPoint`. `NarrativeVoice`. `timeline_position` als `CharField` (Rev.1-Fix).  
**Neue Tabellen:**
```
wh_scene_outcome_lookup
wh_pov_type_lookup
wh_emotion_lookup
wh_narrative_voice
wh_project_turning_points
```
**Migrations:** `projects/0008_outlinenode_extended_fields` existiert bereits (position_start, position_end etc.)  
**Offene Impl-Fragen:** Sind `emotion_start`/`emotion_end` bereits auf `OutlineNode`? → Prüfen ob `0008` diese Felder enthält.

---

### ADR-152

**Titel:** Charakter-Arc-Dramaturgie  
**Datei:** `ADR-152-charakter-arc-dramaturgie.md`  
**Kern-Entscheidung:** `ProjectCharacterLink` erweitert um `want`, `need`, `flaw`, `ghost`, `false_belief`, `true_belief`, `arc_type`, `voice_description`. `CharacterKnowledgeState` (synchronisiert mit ADR-156: `as_of_node`, `suspects`).  
**Neue Tabellen:** `wh_character_knowledge_states`  
**Migrations:** `worlds/0002_projektlinks` → Felder in folge-Migration

---

### ADR-153

**Titel:** Frontend CSS Design Tokens + HTMX  
**Datei:** `ADR-153-frontend-css-design-tokens-htmx.md`  
**Kern-Entscheidung:** CSS Custom Properties in `:root`. HTMX CDN mit SRI. CSRF via `hx-headers`. SSE für LLM-Status.  
**Keine DB-Migration.** Nur Template/Static-Änderungen.  
**SRI-Hash-TODO:** `htmx-ext-sse` Hash muss vor Deploy ermittelt werden.

---

### ADR-154

**Titel:** Drama-Dashboard + Content-Type-UIs  
**Datei:** `ADR-154-drama-dashboard-content-type-uis.md`  
**Kern-Entscheidung:** `DramaDashboardService` (Spannungskurve, Emotionsverlauf). `ArgumentNode` für Essays. `ProjectTheme`, `ProjectMotif`, `MotifAppearance`. ORM-Fix: `outline_version__project` (nicht `outline__project`).  
**Neue Tabellen:**
```
wh_argument_nodes
wh_project_themes
wh_project_motifs
wh_motif_appearances
```

---

### ADR-155

**Titel:** Serien-Dramaturgie  
**Datei:** `ADR-155-serien-dramaturgie.md`  
**Kern-Entscheidung:** `SeriesArc`, `SeriesVolumeRole`, `SeriesCharacterContinuity`. LLM-Layer 8 (Serien-Kontext).  
**Neue Tabellen:**
```
wh_series_arc_type_lookup
wh_series_arcs
wh_series_volume_roles
wh_series_character_continuities
```

---

### ADR-156

**Titel:** Zeitstruktur, Foreshadowing, Sequenz  
**Datei:** `ADR-156-zeitstruktur-foreshadowing-sequenz.md`  
**Kern-Entscheidung:** `MasterTimeline`, `ForeshadowingEntry`, `PlannedFlashback`, `OutlineSequence`. `timeline_position` als `CharField` (fiktive Zeit).  
**Neue Tabellen:**
```
wh_master_timelines
wh_foreshadowing_entries
wh_planned_flashbacks
wh_outline_sequences
```

---

### ADR-157

**Titel:** Antagonist-System, B-Story/Subplot-Tracking, DramaturgicHealthScore  
**Datei:** `ADR-157-antagonist-bstory-mvn-health-rev1.md` ← **Rev.1 ist die gültige Version**  
**Alte Datei:** `ADR-157-antagonist-bstory-mvn-health.md` → **löschen**  
**Kern-Entscheidung:** `narrative_role`/`antagonist_*` auf `ProjectCharacterLink`. `SubplotArc` (inkl. `begins_at_node`/`ends_at_node`). `compute_dramaturgic_health()` mit content-type-Guard.  
**Neue Tabellen:**
```
wh_subplot_arcs
wh_subplot_arcs_intersection_nodes  (M2M)
```
**Felder auf bestehenden Modellen:**
```
ProjectCharacterLink: +narrative_role, +antagonist_type, +antagonist_logic,
                      +mirror_to_protagonist, +shared_trait_with_protagonist,
                      +information_advantage
```
**Migrations:**
```
worlds/0004_narrative_role_antagonist
projects/0014_subplot_arc
```
**`core`-App:** Vorhanden (`apps/core/`) — kein neues App-Setup nötig  
**`n.act`:** Bestätigt — `OutlineNode.act = CharField(max_length=100)` (`models.py:259`)  
**Sprint:** 1 — jetzt bereit ✅

---

### ADR-158

**Titel:** Dialogue Subtext, Opening/Closing Image, GenrePromise, QualityDimension  
**Datei:** `ADR-158-dialogue-subtext-genre-promise-quality.md`  
**Kern-Entscheidung:** `DialogueScene`. `TurningPointTypeLookup` (konsolidiert: `default_position_percent` + `default_position_normalized`, `app_label="core"`). `GenrePromiseLookup` + `ProjectGenrePromise`. QualityDimension-Erweiterung (Layer 10).  
**Neue Tabellen:**
```
wh_dialogue_scenes
wh_turning_point_type_lookup   (core, app_label="core")
wh_genre_promise_lookup        (core, app_label="core")
wh_project_genre_promises
```
**Migrations:**
```
core/0001_lookups_drama
projects/0015_dialogue_genre_promise   (nach ADR-157 Migration 0014)
```
**Sprint:** 1 — jetzt bereit ✅

---

### ADR-159

**Titel:** Publikationsvorbereitung — Comps, Pitch, Exposé  
**Datei:** `ADR-159-publikationsvorbereitung.md`  
**Status:** Proposed — wartet auf ADR-157+158 deployed  
**Neue Tabellen:** `wh_comparable_titles`, `wh_pitch_documents`  
**Migration:** `projects/0015_comparable_titles_pitch` (nach ADR-157+158)  
**Sprint:** 3

---

### ADR-160

**Titel:** Wissens-Infrastruktur — Recherche, Genre-Konventionen, Beta-Reader  
**Datei:** `ADR-160-wissens-infrastruktur.md`  
**Status:** Proposed  
**Neue Tabellen:**
```
wh_research_notes
wh_research_notes_relevant_nodes  (M2M)
wh_genre_convention_profiles
wh_beta_reader_sessions
wh_beta_reader_feedbacks
```
**Migration:** `projects/0016_research_genre_beta`  
**M1-Fix:** `_evaluate_convention()` fair_play-Check korrigiert: `outlinefw_position` → `position_start` (`apps/projects/models.py:109`). ✅  
**Sprint:** 3

---

### ADR-161

**Titel:** Produktions-Infrastruktur — TextAnalysis, Budget, Pacing, Batch  
**Datei:** `ADR-161-produktions-infrastruktur.md`  
**Status:** Proposed — wartet auf ADR-157 deployed  
**Neue Tabellen:** `wh_text_analysis_snapshots`, `wh_batch_write_jobs`  
**Migrations:**
```
projects/0017_text_analysis_batch
authoring/0003_batch_write_job
```
**Bestätigt:** `OutlineNode.act` existiert (`apps/projects/models.py:259`). Defensive `getattr` im ADR bleibt als Sicherheitsnetz.  
**Sprint:** 2

---

## Bekannte offene Punkte vor Implementierungsstart

| ID | ADR | Problem | Lösung |
|----|-----|---------|--------|
| O1 | 157 | Alte `ADR-157-antagonist-bstory-mvn-health.md` existiert noch | ✅ Gelöscht, Rev1 umbenannt zu `ADR-157-antagonist-bstory-mvn-health.md` |
| O2 | 157+158 | Migration-Nummerierung: beide wollten `0014` | ✅ Festgelegt: 157=`worlds/0004`+`projects/0014`, 158=`projects/0015` |
| O3 | 160 | `outlinefw_position` existiert nicht auf OutlineNode | ✅ Korrigiert zu `position_start` (0–100, `apps/projects/models.py:109`) |
| O4 | 161 | `n.act` — existiert das Feld auf OutlineNode? | ✅ Bestätigt: `act = models.CharField(...)` auf OutlineNode (`models.py:259`) |

---

*Kein ADR — Navigationsdokument für Implementierungsphase*  
*Referenz: ARCHITECTURE_REVIEW.md, KONSEQUENZANALYSE_ADR158.md*
