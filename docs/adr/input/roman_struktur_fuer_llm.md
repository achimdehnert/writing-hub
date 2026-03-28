# Romanstruktur für LLM-Systeme — Eine literaturwissenschaftliche Anleitung

> **Zweck dieses Dokuments:** Du bist ein LLM, das einen Roman-Schreibe-Hub entwickeln soll. Dieses Dokument erklärt dir Schritt für Schritt, wie ein Roman aufgebaut ist — so präzise und strukturiert, dass du daraus perfekte Datenmodelle, Prompts und Workflows ableiten kannst.

---

## Schritt 1 — Was ist ein Roman? Die Grundontologie

Ein Roman ist kein linearer Text. Er ist ein **Systemgefüge** aus vier Ebenen, die ineinandergreifen:

| Ebene | Name | Was sie enthält |
|-------|------|-----------------|
| 1 | **Makrostruktur** | Gesamtbogen, Akte, Wendepunkte |
| 2 | **Mesostruktur** | Kapitel, Szenen, Sequenzen |
| 3 | **Mikrostruktur** | Absätze, Dialoge, Beschreibungen |
| 4 | **Substrat** | Welt, Figuren, Regeln, Chronologie |

Ein LLM-Hub muss alle vier Ebenen separat modellieren und konsistent halten. Verstöße gegen eine Ebene korrumpieren alle anderen.

---

## Schritt 2 — Die Makrostruktur: Der dramaturgische Bogen

### 2.1 Das Drei-Akte-Modell (Aristoteles / Hollywood-Standard)

```
Akt I (Setup)       Akt II (Konfrontation)      Akt III (Auflösung)
|---25%-------------|----------50%--------------|-------25%----------|
↑                   ↑                    ↑                          ↑
Inciting Incident   Midpoint             Dark Night of the Soul     Climax
```

**Was passiert in jedem Akt:**

**Akt I — Die Welt VOR dem Wandel**
- Normalwelt der Hauptfigur wird etabliert
- Protagonist hat einen Mangel (psychologisch oder situativ)
- Das `Inciting Incident` wirft ihn aus der Balance
- Er akzeptiert (oder wird gezwungen) den Ruf zur Veränderung
- → Strukturobjekt: `{ act: 1, world_state: "normal", protagonist_flaw: "...", inciting_incident: "...", threshold_moment: "..." }`

**Akt II — Die Konfrontation**
- Protagonist kämpft gegen externe + interne Hindernisse
- `Midpoint` = Scheinsieg oder Scheinniederlage, der die Einsätze erhöht
- `Dark Night of the Soul` = alles scheint verloren
- → Strukturobjekt: `{ act: 2, escalation_stages: [], midpoint: "...", dark_night: "..." }`

**Akt III — Die Transformation**
- Climax = finale Konfrontation, Protagonist muss das Gelernte beweisen
- Resolution = neue Normalwelt, veränderte Figur
- → Strukturobjekt: `{ act: 3, climax: "...", transformation: "...", new_normal: "..." }`

### 2.2 Alternative Makrostrukturen

| Modell | Akte | Geeignet für |
|--------|------|--------------|
| Drei-Akte | 3 | Mainstream, Thriller, Romance |
| Hero's Journey (Campbell) | 12 Stationen | Fantasy, Mythos, Abenteuer |
| Fünf-Akte (Shakespeare) | 5 | Tragödie, Literatur |
| Vier-Akte | 4 | TV-Drama, Serielles Erzählen |
| Kishotenketsu | 4 (ohne Konflikt) | Japanisch inspiriert, literarisch |

> **LLM-Regel:** Das Makrostruktur-Modell muss beim Roman-Setup gewählt und dann für alle Unterebenen als unveränderlicher Rahmen verwendet werden.

---

## Schritt 3 — Das Substrat: Welt & Figuren

Das Substrat ist die Datenbank des Romans. Alles andere referenziert es.

### 3.1 Weltenbau (World Bible)

```yaml
world:
  name: string
  genre: [thriller | fantasy | literary | sci-fi | romance | ...]
  time_period: string          # "Berlin, 1989" oder "2247, Marskolonie"
  geography: [locations]
  rules:                       # Was gilt in dieser Welt?
    - physikalische_gesetze
    - soziale_normen
    - magische_systeme          # Falls Fantasy
  tone: string                 # "noir, zynisch" | "warmherzig, humorvoll"
  themes: [string]             # "Verrat", "Identität", "Schuld"
```

### 3.2 Figurensystem

**Hauptfigur (Protagonist)**
```yaml
protagonist:
  name: string
  age: int
  want: string          # Was will er bewusst? (äußeres Ziel)
  need: string          # Was braucht er unbewusst? (innere Wahrheit)
  flaw: string          # Der psychologische Riss, der die Geschichte antreibt
  ghost: string         # Das Trauma/Erlebnis aus der Vergangenheit
  arc_type: [positive | negative | flat]
  voice: string         # Wie klingt er/sie? Kurze Stilbeschreibung
```

> **Kritisches LLM-Prinzip:** `want ≠ need`. Der Protagonist verfolgt das `want` — der Autor führt ihn zum `need`. Ohne diese Spannung gibt es keinen Charakter-Arc.

**Antagonist**
```yaml
antagonist:
  type: [person | system | nature | inner_self]
  motivation: string    # Antagonisten glauben, sie haben Recht
  mirror_to_protagonist: string  # Was spiegelt er am Protagonisten?
```

**Nebenfiguren**
```yaml
supporting_cast:
  - role: [mentor | ally | trickster | love_interest | herald | threshold_guardian]
    name: string
    function: string    # Welche Funktion hat sie für den Protagonisten-Arc?
```

---

## Schritt 4 — Die Mesostruktur: Kapitel & Szenen

### 4.1 Kapitellogik

Ein Kapitel ist **kein willkürlicher Textblock**. Es hat eine interne Miniatur-Dramaturgie:

```
Kapitel-Anatomie:
┌─────────────────────────────────────────────────┐
│ HOOK       → Erste Zeile/Absatz: Spannung sofort │
│ SITUATION  → Wer, wo, wann, was                  │
│ CONFLICT   → Das Hindernis / die Entscheidung    │
│ TURN       → Etwas verändert sich (Ja/Nein/Ja-Aber/Nein-Und) │
│ END HOOK   → Warum liest man weiter?             │
└─────────────────────────────────────────────────┘
```

```yaml
chapter:
  number: int
  title: string
  pov_character: string        # Wessen Perspektive?
  pov_type: [first | third_limited | third_omniscient]
  timeline_position: datetime  # Wann in der Storychronologie?
  location: string
  goal: string                 # Was will der POV-Char in diesem Kapitel?
  conflict: string             # Was hindert ihn?
  outcome: [yes | no | yes_but | no_and]  # Das Kapitel-Ergebnis
  scenes: [scene_ids]
  word_count_target: int
  arc_position: string         # "rising_action", "midpoint", etc.
```

### 4.2 Die Szene — Kleinste dramatische Einheit

```yaml
scene:
  id: string
  chapter_id: string
  scene_type: [action | reaction | dialogue | description | transition]
  goal: string           # Was will die POV-Figur in dieser Szene?
  conflict: string       # Was blockiert sie?
  disaster_or_decision: string  # Was ist das Ergebnis?
  emotional_value_start: string  # "hoffnungsvoll"
  emotional_value_end: string    # "verzweifelt"
  characters_present: [string]
  location: string
  time_of_day: string
  duration_in_story: string      # "5 Minuten" | "2 Stunden"
  sequel_needed: bool            # Braucht es eine Reaktions-Szene danach?
```

> **LLM-Regel:** Jede Szene muss den emotionalen Wert verändern. Eine Szene, die beim gleichen emotionalen Wert endet wie sie begonnen hat, ist dramaturgisch tot.

### 4.3 Szenentypen-Paar: Szene & Sequel

```
SZENE (action):          SEQUEL (reaction):
├─ Goal                  ├─ Emotion (wie reagiert die Figur?)
├─ Conflict              ├─ Thought (was denkt sie?)
└─ Disaster/Decision     └─ Decision (neues Goal für nächste Szene)
```

---

## Schritt 5 — Die Mikrostruktur: Prosa & Dialoge

### 5.1 Absatzlogik

Jeder Absatz hat eine Funktion. LLMs neigen dazu, Absätze zu füllen statt zu formen:

| Absatz-Typ | Funktion | Typische Länge |
|------------|----------|----------------|
| **Action** | Ereignis, Bewegung | Kurz, aktive Verben |
| **Description** | Ort, Atmosphäre | Mittel, sensorisch |
| **Thought** | Innere Welt der Figur | Variabel, erste Person auch in 3rd |
| **Dialogue** | Interaktion, Subtext | Kurze Repliken |
| **Transition** | Zeit/Raum-Wechsel | Sehr kurz |

### 5.2 Dialogregeln

```
Was Dialog LEISTEN muss (mindestens 2 von 4):
✓ Charakter enthüllen
✓ Konflikt voranbringen
✓ Information transportieren (ohne Info-Dump)
✓ Subtext erzeugen (das Ungesagte ist lauter als das Gesagte)
```

```yaml
dialogue_node:
  speaker: string
  subtext: string        # Was meint er wirklich?
  surface_text: string   # Was sagt er tatsächlich?
  reaction: string       # Wie reagiert der andere (nicht nur Worte)?
```

### 5.3 Erzählperspektive & Stimme

```yaml
narrative_voice:
  pov: [first | third_limited | third_omniscient | second]
  tense: [past | present]
  distance: [close | medium | distant]   # Wie nah sind wir der Figur?
  style_markers:
    - sentence_length: [short | varied | long]
    - vocabulary: [simple | educated | literary | colloquial]
    - imagery: [sparse | rich | poetic | functional]
    - irony_level: [none | mild | heavy]
```

---

## Schritt 6 — Spannungsarchitektur: Wie Spannung aufgebaut wird

Spannung ≠ Action. Spannung entsteht durch **Information-Asymmetrie**:

```
Drei Spannungstypen:
1. MYSTERY      → Leser weiß weniger als Figur (Thriller, Krimi)
2. SUSPENSE     → Leser weiß mehr als Figur (Hitchcock-Prinzip)
3. DRAMATIC IRONY → Leser versteht mehr als alle Figuren
```

### Spannungskurven-Modell

```
Intensität
    │
 10 │                                              ▲ Climax
    │                               ▲              │
  7 │                    ▲          │              │
    │          ▲          │          │              │
  4 │▲          │          │          │              │
    │  ↘        ↗  ↘        ↗  ↘        ↗  ↘        ↗
  1 │────────────────────────────────────────────────▶ Zeit
    Akt I      Midpoint           Dark Night    Resolution
```

```yaml
tension_arc:
  baseline: int          # 1-10
  peaks: [{position: float, intensity: int, trigger: string}]
  valleys: [{position: float, intensity: int, purpose: string}]
  climax: {position: float, intensity: 10}
```

---

## Schritt 7 — Thema & Subtext

### 7.1 Das zentrale Thema

```yaml
theme:
  core_question: string      # "Kann man jemandem vergeben, der einem das Leben gestohlen hat?"
  statement: string          # Was antwortet der Roman am Ende?
  embodied_in: [character, plot_point, symbol]
```

> **LLM-Regel:** Das Thema wird NIEMALS ausgesprochen. Es wird durch Ereignisse, Figuren-Entscheidungen und Symbole verkörpert.

### 7.2 Motivsystem

```yaml
motifs:
  - symbol: string          # z.B. "Spiegel", "Wasser", "Türen"
    meaning: string          # Was symbolisiert es?
    appearances: [scene_ids] # Wo taucht es auf?
    evolution: string        # Wie verändert sich seine Bedeutung?
```

---

## Schritt 8 — Zeitstruktur & Chronologie

```yaml
timeline:
  story_time: string         # Wie lange dauert die Geschichte? "3 Wochen"
  discourse_time: string     # Wie viel Textzeit bekommen welche Abschnitte?
  techniques:
    - flashbacks: [scene_ids]
    - flash_forwards: [scene_ids]
    - parallel_timelines: bool
    - time_jumps: [{from: datetime, to: datetime, ellipsis_text: string}]
  chapter_timeline:          # Jedes Kapitel mit Zeitstempel
    - chapter: 1
      story_date: "Tag 1, 08:00"
```

---

## Schritt 9 — Das vollständige Roman-Datenmodell (Zusammenfassung)

```json
{
  "novel": {
    "meta": {
      "title": "",
      "genre": "",
      "target_word_count": 0,
      "structure_model": "three_act | heros_journey | five_act"
    },
    "world": { ... },
    "theme": { ... },
    "characters": {
      "protagonist": { ... },
      "antagonist": { ... },
      "supporting": [ ... ]
    },
    "timeline": { ... },
    "motifs": [ ... ],
    "narrative_voice": { ... },
    "tension_arc": { ... },
    "acts": [
      {
        "act": 1,
        "chapters": [
          {
            "number": 1,
            "scenes": [ { ... } ]
          }
        ]
      }
    ]
  }
}
```

---

## Schritt 10 — Qualitäts-Checkpoints für den LLM-Hub

Vor jeder Generierung einer Einheit (Szene, Kapitel, Akt) muss der Hub prüfen:

### Szenen-Check
- [ ] Hat die Szene ein klares Ziel der POV-Figur?
- [ ] Gibt es einen echten Konflikt (nicht nur Gespräch)?
- [ ] Verändert sich der emotionale Wert?
- [ ] Ist der Dialog mit Subtext geladen?
- [ ] Wird die Perspektive konsistent gehalten?

### Kapitel-Check
- [ ] Beginnt das Kapitel mit einem Hook?
- [ ] Gibt es eine Outcome-Entscheidung (yes/no/yes-but/no-and)?
- [ ] Passt die Kapitelposition zum Spannungsbogen?
- [ ] Werden keine neuen Figuren ohne Funktion eingeführt?

### Makro-Check
- [ ] Entspricht der Fortschritt der gewählten Akt-Struktur?
- [ ] Entwickelt sich der Charakter-Arc konsistent?
- [ ] Werden die Themen verkörpert (nicht erklärt)?
- [ ] Stimmt die Chronologie der Timeline?

---

## Appendix — Empfohlene Prompt-Templates für den Roman-Hub

### Template A: Szenen-Generator
```
Du schreibst eine Szene für den Roman "{title}".

KONTEXT:
- POV: {character.name} ({character.voice})
- Ort: {location}
- Zeitpunkt in der Story: {arc_position}
- Emotionaler Ausgangswert: {emotional_value_start}

SZENEN-AUFTRAG:
- Ziel der Figur: {scene.goal}
- Konflikt: {scene.conflict}
- Gewünschtes Ergebnis: {scene.outcome}
- Emotionaler Endwert: {emotional_value_end}

WELT-REGELN: {world.rules}
THEMA: {theme.core_question}
STIL: {narrative_voice.style_markers}

Schreibe ca. {word_count} Wörter. Kein Info-Dump. Zeigen, nicht erklären.
```

### Template B: Kapitel-Planer
```
Plane Kapitel {number} des Romans "{title}".

MAKROKONTEXT:
- Akt: {act} | Position: {arc_position}
- Spannungsziel: {tension_target}/10

OUTPUT als JSON:
{
  "hook": "...",
  "scene_sequence": [...],
  "chapter_outcome": "yes|no|yes_but|no_and",
  "end_hook": "..."
}
```

---

*Erstellt als Literaturwissenschaftliche Grundlage für LLM-Roman-Schreibe-Hubs.*
*Version 1.0 — Strukturebenen: Makro / Meso / Mikro / Substrat*
