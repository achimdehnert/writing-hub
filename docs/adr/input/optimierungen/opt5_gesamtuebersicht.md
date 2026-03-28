# OPT5 — Gesamtübersicht: Alle Optimierungen im writing-hub

> Vollständige Roadmap aller identifizierten Optimierungen.
> Prio-1 (A–D) + ADR-157 bereits spezifiziert.
> O1–O6 + FE1–FE5 + OPT1–OPT4 sind die Erweiterungsebenen.

---

## Systemübersicht: Was optimiert was

```
DRAMATURGISCHE EBENE          TECHNISCHE EBENE           VERLEGERISCHE EBENE
──────────────────────        ────────────────────       ────────────────────
Prio-1 A: OutlineNode         FE1: CSS Tokens            OPT2: Comps
Prio-1 B: Char Arc            FE2: HTMX                  OPT2: Exposé
Prio-1 C: NarrativeVoice      FE3: Drama-Dashboard       OPT2: Query Letter
Prio-1 D: Thema/Motiv         FE4: Essay Tree UI         OPT3: Genre-Konventionen
ADR-157:  Antagonist          FE5: Series Arc UI         OPT3: Beta-Reader
ADR-157:  B-Story             OPT1: Dead Scenes          OPT4: Budget-Management
ADR-157:  MVN Health-Score    OPT1: Voice Drift
O1: Foreshadowing             OPT1: Screen Time
O2: Series Arc                OPT4: Pacing-Analyse
O3: Essay-Struktur            OPT4: Batch-Generierung
O4: MasterTimeline
O5: ContentTypeProfile
O6: alle Tabellen

                              OPT3: Recherche-Notes
```

---

## Prioritäts-Matrix

```
IMPACT × AUFWAND:

                    AUFWAND NIEDRIG     AUFWAND MITTEL      AUFWAND HOCH
                    ─────────────────   ────────────────    ──────────────────
IMPACT HOCH         FE1 CSS Tokens      ADR-157             O3 Essay
                    ADR-157 B3/B4 Fix   OPT2 Comps+Pitch    O2 Series Arc
                    OPT2 Logline        FE2 HTMX Filter      OPT3 Beta-Reader
                                        FE3 Drama-Dashboard

IMPACT MITTEL       OPT1 Dead Scenes    OPT1 Voice Drift     O4 Timeline
                    OPT4 Budget         FE4 Essay UI          OPT4 Batch-Job
                    O1 Foreshadowing    FE5 Series UI

IMPACT NIEDRIG      OPT3 Recherche      OPT3 Genre-Conv.
                    (Langzeit-Nutzen)    (Admin-Aufwand)
```

---

## Vollständige Tabellen-Übersicht (alle Optimierungen)

### Bereits spezifiziert (Prio-1 + O1–O6)

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
wh_series_arc_type_lookup
wh_series_arcs
wh_series_volume_roles
wh_series_character_continuities
wh_essay_structure_type_lookup
wh_argument_node_type_lookup
wh_essay_outlines
wh_argument_nodes
wh_narrative_model_lookup
wh_master_timelines
wh_timeline_entries
wh_character_knowledge_states
wh_content_type_profiles
```

### ADR-157

```
wh_subplot_arcs                 ← neu
(+ narrative_role auf ProjectCharacterLink)
```

### OPT1–OPT4

```
wh_text_analysis_snapshots      ← OPT1
wh_comparable_titles            ← OPT2
wh_pitch_documents              ← OPT2
wh_research_notes               ← OPT3
wh_genre_convention_profiles    ← OPT3
wh_beta_reader_sessions         ← OPT3
wh_beta_reader_feedbacks        ← OPT3
wh_batch_write_jobs             ← OPT4
```

**Gesamt: 42 neue Tabellen**

---

## Was der writing-hub dann kann — als Verleger formuliert

### Für den Autor:

```
SETUP (Stunden 1–3):
    → Roman-Kern definieren (Schritt 1)
    → Makrostruktur wählen + Wendepunkte (Schritt 2 + O1)
    → Protagonist: want/need/flaw/ghost (Prio-1 B)
    → Antagonist: Logik, Spiegel, Informationsvorsprung (ADR-157)
    → B-Story: Träger, Position, thematischer Spiegel (ADR-157)
    → Health-Score: MVN vollständig? (ADR-157)

ENTWICKLUNG (Tage/Wochen):
    → Outline generieren (outlinefw)
    → Kapitel schreiben / KI-generieren (ChapterWriter)
    → Dead Scenes erkennen (OPT1)
    → Pacing prüfen (OPT4)
    → Recherche-Notizen verknüpfen (OPT3)
    → Budget überwachen (OPT4)

ABSCHLUSS:
    → Lektorat (bestehend)
    → Beta-Leser (OPT3)
    → Voice Drift prüfen (OPT1)
    → Drama-Dashboard: Spannungskurve final (FE3)
```

### Für die Verlagsanfrage:

```
PITCH-PAKET:
    → Logline 1 Satz (OPT2)
    → Comparable Titles 2–3 Stück (OPT2)
    → Deutsches Exposé (OPT2)
    → Query Letter EN (OPT2)
    → Genre-Konventions-Check: passt das Label? (OPT3)
    → PublishingProfile: BISAC, Keywords, ISBN (bestehend)
```

---

## Die 5 kritischsten Lücken nach verlegerischer Priorität

Als jemand, der Manuskripte ablehnt und annimmt:

### Lücke 1 — Antagonist ohne Logik (ADR-157, jetzt in Revision)
80% der abgelehnten Erstromane haben einen Antagonisten, der
einfach böse ist. Der Hub kann das jetzt messen — aber ADR-157 muss
erst korrekt deployed sein.

### Lücke 2 — Kein Exposé / kein Pitch (OPT2)
Ein Autor, der seinen Roman im Hub fertig hat, kann ihn trotzdem
nicht an Verlage schicken — es fehlt das Transmissions-Format.
Das Exposé ist die Brücke zwischen Hub und Markt.

### Lücke 3 — Genre-Konventionen nicht prüfbar (OPT3)
Ein "Thriller" ohne Bedrohung in den ersten 15% ist kein Thriller.
Das Hub kann das Genre-Label nicht validieren — der Autor kann
unwissentlich das falsche Label wählen.

### Lücke 4 — Keine Textrhythmus-Analyse (OPT1)
KI-generierte Kapitel tendieren zur Gleichförmigkeit.
Dead Scenes, Voice Drift und Monotonie-Pacing sind
die wichtigsten Qualitätsprobleme bei KI-Manuskripten.

### Lücke 5 — Keine Recherche (OPT3)
Für jeden Roman mit historischem oder technischem Inhalt
(Thriller, Sci-Fi, historischer Roman) fehlt der Ort für
Fakten. LLM-generierte Kapitel ohne Fakten-Injection produzieren
plausibel klingende, aber falsche Details.

---

## Empfohlene Sprint-Planung

```
SPRINT 1 (1–2 Wochen):
    ADR-157 Rev.1 (7 Blocking Issues beheben)
    FE1 CSS Tokens
    OPT1 Dead Scene Detection (regelbasiert, kein LLM)

SPRINT 2 (2–3 Wochen):
    FE2 HTMX Filter + Auto-Save
    FE3 Drama-Dashboard
    OPT2 ComparableTitle + Logline-Generierung

SPRINT 3 (3–4 Wochen):
    OPT2 Exposé + Query Letter
    OPT4 Budget-Service + Pacing
    OPT3 Recherche-Notes

SPRINT 4 (4–6 Wochen):
    O2 Series Arc (nach Series-Hub Launch)
    O3 Essay-Struktur (nach Essay-Content-Type-Adoption)
    OPT3 Beta-Reader + Genre-Konventionen
    FE4 Essay Tree UI
    FE5 Series Arc UI
```

---

*writing-hub · OPT5 · Gesamtübersicht*
*42 neue Tabellen · 4 neue Sprint-Zyklen · Verlegerisches Ziel: Manuskript → Pitch-Paket*
