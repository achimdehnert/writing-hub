# Schritt 4 — Die Mesostruktur: Kapitel & Szenen

> **Für das LLM:** Die Mesostruktur ist das Gerüst aus Kapiteln und Szenen. Sie übersetzt die abstrakte Makrostruktur in konkrete, schreibbare Einheiten. Jede Einheit hat ihre eigene interne Logik — sie ist kein Textblock, sondern eine dramaturgische Einheit.

---

## 4.1 Die Hierarchie der Mesostruktur

```
ROMAN
└── AKTE (Makrostruktur)
    └── SEQUENZEN (Gruppe thematisch verbundener Kapitel)
        └── KAPITEL (dramaturgische Einheit, 2.000–5.000 Wörter)
            └── SZENEN (kleinste dramatische Einheit, 500–2.000 Wörter)
                └── SEQUEL (Reaktions-Einheit nach dramatischer Szene)
```

---

## 4.2 Die Sequenz — oft vergessen, immer wichtig

Eine Sequenz ist eine Gruppe von Kapiteln, die zusammen eine Miniatur-Geschichte erzählen:

```yaml
sequenz:
  nummer: int
  akt: int                         # In welchem Akt?
  titel: string                    # "Die erste Begegnung"
  ziel_der_sequenz: string         # Was versucht der Protagonist hier?
  start_zustand: string            # Situation zu Beginn
  end_zustand: string              # Situation am Ende
  kapitel_ids: []
  beitraegt_zu_arc: string         # Wie trägt sie zur Figur-Entwicklung bei?
```

**Sequenzen** ermöglichen mittelfristige Planung ohne in Kapitel-Details zu versinken. Empfohlen: 4–8 Sequenzen pro Akt.

---

## 4.3 Das Kapitel — die dramaturgische Einheit

### 4.3.1 Die Kapitel-Anatomie (intern)

Jedes Kapitel ist selbst ein Mini-Drama:

```
┌──────────────────────────────────────────────────────┐
│  1. HOOK         Erste Zeile/Absatz: Spannung sofort  │
│                  → Frage, Bild, Handlung, Provokation │
├──────────────────────────────────────────────────────┤
│  2. SITUATION    Orientierung: Wer, wo, wann, warum?  │
│                  → So kurz wie möglich                │
├──────────────────────────────────────────────────────┤
│  3. ZIEL         Was will die POV-Figur hier?         │
│                  → Muss konkret und erreichbar sein   │
├──────────────────────────────────────────────────────┤
│  4. KONFLIKT     Was hindert sie?                     │
│                  → Extern + intern                    │
├──────────────────────────────────────────────────────┤
│  5. TURN         Etwas verändert sich unwiderruflich  │
│                  → Das Kapitel-Outcome                │
├──────────────────────────────────────────────────────┤
│  6. END HOOK     Warum muss man weiterlesen?          │
│                  → Frage, Enthüllung, Cliffhanger     │
└──────────────────────────────────────────────────────┘
```

### 4.3.2 Das Kapitel-Outcome-System

Dies ist das wichtigste Werkzeug für Spannung auf Kapitel-Ebene:

```
OUTCOME-TYP    BEDEUTUNG                    EFFEKT AUF LESER
─────────────  ──────────────────────────── ─────────────────────
YES            Figur erreicht ihr Ziel       Befriedigung, aber...
               → "Ja, aber..." folgt oft     ...neue Komplexität

NO             Figur scheitert               Frustration + Mitgefühl
               → Dinge werden schlimmer

YES, BUT       Teilsieg mit Preis            Ambivalenz, Spannung
               → Ziel erreicht, aber Kosten

NO, AND        Scheitern + Neue Komplikation Maximale Spannung
               → Worst case + Verstärkung
```

**LLM-Regel:** Verteile die Outcomes über den Roman. Zu viele "YES" = langweilig. Zu viele "NO" = zermürbend. Empfohlene Verteilung: ~20% YES, ~30% NO, ~30% YES_BUT, ~20% NO_AND.

### 4.3.3 Vollständiges Kapitel-Objekt

```yaml
kapitel:
  id: string                     # "k001"
  nummer: int
  titel: string                  # Optional, für interne Orientierung
  sequenz_id: string
  akt: int
  arc_position: string           # "setup | rising_action | midpoint | dark_night | climax | resolution"
  
  # PERSPEKTIVE
  pov_figur: string              # Wessen Kopf sind wir?
  pov_typ: first | third_limited | third_omniscient
  
  # DRAMATURGIK
  kapitel_ziel: string           # Was will die POV-Figur?
  kapitel_konflikt: string       # Was hindert sie?
  kapitel_outcome: yes | no | yes_but | no_and
  
  # ZEITSTRUKTUR
  timeline_position: string      # "Tag 3, 14:00"
  zeitraum: string               # "2 Stunden"
  
  # ORT
  haupt_schauplatz: string
  
  # HOOK & ENDING
  erster_satz: string            # (Entwurf)
  end_hook: string               # (Konzept)
  
  # TECHNISCHES
  ziel_wortanzahl: int
  szenen_ids: []
  
  # SPANNUNGSBOGEN
  spannung_anfang: int           # 1–10
  spannung_ende: int             # 1–10
  
  # THEMA & MOTIV
  thema_beruehrung: string       # Wie berührt dieses Kapitel das Thema?
  motiv_einsatz: []              # Welche Motive tauchen auf?
```

---

## 4.4 Die Szene — kleinste dramatische Einheit

### 4.4.1 Was eine Szene ist

Eine Szene ist eine kontinuierliche Handlungseinheit an einem Ort zu einer Zeit. Sie endet, wenn:
- Der Schauplatz wechselt
- Die Zeit springt
- Eine neue Figur die Dynamik grundlegend verändert

### 4.4.2 Das Goal-Conflict-Outcome-System der Szene

Jede Szene hat drei Pflichtbestandteile:

```
GOAL       Was will die POV-Figur in DIESER Szene?
           → Klein, konkret, sofort erreichbar
           → "Sie will, dass er ihr die Wahrheit sagt"

CONFLICT   Was verhindert die Zielerreichung?
           → Jemand oder etwas widersetzt sich
           → "Er lügt systematisch und ist gut darin"

OUTCOME    Was passiert wirklich?
           → Eines der vier Outcomes (YES/NO/YES_BUT/NO_AND)
           → "Sie glaubt ihm — aber wir (Leser) sehen, dass er lügt"
```

### 4.4.3 Der emotionale Deltawert — Pflicht für jede Szene

```
EMOTIONAL VALUE SHIFT:
Anfang → Ende

"hoffnungsvoll" → "verzweifelt"         (negativer Shift)
"misstrauisch"  → "überzeugend"         (positiver Shift)
"neutral"       → "erschüttert"         (dramatischer Shift)

VERBOTEN: "neutral" → "neutral"         (Dead Scene — kein Wert)
```

### 4.4.4 Vollständiges Szenen-Objekt

```yaml
szene:
  id: string                     # "s001_k001"
  kapitel_id: string
  position_in_kapitel: int       # 1, 2, 3...
  
  # TYP
  szenen_typ: action | reaction | dialogue | description | transition
  
  # DRAMATURGIK
  pov_figur: string
  goal: string
  conflict: string
  outcome: yes | no | yes_but | no_and
  disaster_oder_decision: string  # Was ist das konkrete Ergebnis?
  
  # EMOTIONALER DELTAWERT
  emotion_anfang: string
  emotion_ende: string
  
  # FIGUREN & ORT
  figuren_anwesend: []
  schauplatz: string
  tageszeit: string
  wetter_atmosphaere: string
  
  # ZEITSTRUKTUR
  story_dauer: string            # "15 Minuten"
  timeline_position: string
  
  # INFORMATION
  informationen_enthüllt: []     # Was erfährt der Leser?
  informationen_verborgen: []    # Was verbirgt die Szene (für Spannung)?
  
  # SEQUEL
  sequel_nötig: bool
  sequel_emotion: string         # Falls sequel: Welche Reaktion folgt?
  
  # THEMA & MOTIV
  motiv_einsatz: []
  
  # TECHNISCHES
  ziel_wortanzahl: int
  geschrieben: bool
```

---

## 4.5 Das Szenen-Sequel-Paar

Dies ist die dramaturgische Grundeinheit. LLMs schreiben oft endlose Aktionsketten ohne Raum für Reaktion.

```
SZENE (Aktion)          SEQUEL (Reaktion)
──────────────────      ──────────────────────
Goal                    Emotion
  ↓                       ↓
Conflict                Thought
  ↓                       ↓
Disaster/Decision       Decision (→ neues Goal)
```

**Wann braucht es ein Sequel?**
- Nach jedem dramatischen Tiefpunkt
- Wenn eine Figur eine wichtige Information erhält
- Wenn eine fundamentale Entscheidung getroffen wurde
- Nach dem Climax

**Wann kann man das Sequel überspringen?**
- Bei Neben-Szenen mit geringem emotionalen Gewicht
- Wenn das Tempo hoch bleiben soll (Action-Sequenzen)
- Wenn die nächste Szene das Sequel implizit enthält

---

## 4.6 Szenentypen im Detail

### Action-Szene
```yaml
action_szene:
  kennzeichen:
    - "Figur verfolgt aktiv ein Ziel"
    - "Aktive Verben dominieren"
    - "Keine langen Reflexionen"
    - "Endet mit Disaster oder Decision"
  tempo: schnell
  dialog: knapp oder keiner
  innenleben: minimal
```

### Reaction/Sequel-Szene
```yaml
reaction_szene:
  kennzeichen:
    - "Figur verarbeitet das Disaster der vorherigen Szene"
    - "Emotionen, Gedanken, Reflexion stehen im Vordergrund"
    - "Endet mit neuer Entscheidung (neuem Goal)"
  tempo: langsam
  dialog: optional (mit sich selbst / Vertrautem)
  innenleben: maximal
```

### Dialogue-Szene
```yaml
dialogue_szene:
  kennzeichen:
    - "Enthüllung durch Gespräch"
    - "Subtext wichtiger als Text"
    - "Jede Aussage hat eine Gegenaussage"
  tempo: mittel
  pflicht: "Jeder Dialog verändert die Machtbalance"
```

### Description-Szene
```yaml
description_szene:
  kennzeichen:
    - "Atmosphärische Verdichtung"
    - "Zeigt Welt durch Wahrnehmung der Figur"
    - "Nie rein dekorativ — immer funktional"
  warnung: "Nie länger als nötig — Leser wollen Handlung"
```

---

## 4.7 Prompt-Templates für Mesostruktur

### Template ME-1: Kapitel-Sequenzplan generieren

```
SYSTEM:
Du planst die Kapitelstruktur eines Romans. Antworte als JSON.
Halte dich exakt an die Makrostruktur.

USER:
Erstelle den Kapitel-Sequenzplan für AKT {akt_nummer}:

MAKROSTRUKTUR: {akt_objekt_mit_wendepunkten}
SUBSTRAT: {substrat_kurzfassung}
ZIEL_WORTANZAHL_AKT: {wortanzahl}

AUFGABE:
Erstelle 3–6 Sequenzen für diesen Akt.
Jede Sequenz hat 2–4 Kapitel.
Jedes Kapitel hat einen klaren Outcome-Typ.

PRÜFE:
- Sind alle Wendepunkte des Aktes in Kapitel verankert?
- Eskaliert die Spannung innerhalb des Aktes?
- Variieren die Outcome-Typen?

FORMAT:
{
  "sequenzen": [
    {
      "nummer": 1,
      "titel": "...",
      "ziel": "...",
      "kapitel": [
        {
          "nummer": 1,
          "arc_position": "...",
          "kapitel_ziel": "...",
          "kapitel_konflikt": "...",
          "outcome": "...",
          "ziel_wortanzahl": 0,
          "spannung_anfang": 0,
          "spannung_ende": 0
        }
      ]
    }
  ]
}
```

### Template ME-2: Szenenplan für ein Kapitel

```
SYSTEM:
Du planst die Szenenstruktur eines Kapitels. Antworte als JSON.
Jede Szene muss einen emotionalen Deltawert haben.

USER:
Erstelle den Szenenplan für Kapitel {kapitel_nummer}:

KAPITEL-OBJEKT: {kapitel_objekt}
SUBSTRAT: {relevante_figuren_und_schauplatz}
VORHERIGES_KAPITEL_ENDE: {letzter_zustand_figur}

AUFGABE:
Plane 2–5 Szenen für dieses Kapitel.
Stelle sicher:
1. Die erste Szene beginnt mit einem Hook
2. Mindestens eine Szene hat hohen emotionalen Deltawert
3. Die letzte Szene endet mit einem End-Hook
4. Der Kapitel-Outcome ist klar erkennbar

FORMAT:
{
  "kapitel_hook": "...",
  "szenen": [
    {
      "position": 1,
      "typ": "...",
      "goal": "...",
      "conflict": "...",
      "outcome": "...",
      "emotion_anfang": "...",
      "emotion_ende": "...",
      "figuren": [],
      "schauplatz": "...",
      "ziel_wortanzahl": 0,
      "sequel_nötig": false
    }
  ],
  "kapitel_end_hook": "..."
}
```

### Template ME-3: Einzelne Szene ausarbeiten

```
SYSTEM:
Du arbeitest eine Szene dramaturgisch vollständig aus, bevor sie geschrieben wird.
Antworte als JSON. Diese Ausarbeitung wird als Schreib-Brief verwendet.

USER:
Arbeite diese Szene aus:

SZENEN-PLAN: {szenen_objekt}
SUBSTRAT: {relevante_figuren_mit_wissen_und_motivation}
KAPITEL_KONTEXT: {kapitel_objekt}
ROMAN_THEMA: {thema}

ERSTELLE:
1. opening_moment: Erste Handlung / erstes Bild (nicht erster Satz, aber Bild)
2. szenen_dynamik: Wie entwickelt sich das Kräfteverhältnis?
3. subtext_ebene: Was wird NICHT gesagt aber gemeint?
4. emotional_journey: Schritt-für-Schritt emotionale Entwicklung
5. turning_point: Genauer Moment des Turns
6. closing_image: Letztes Bild vor dem Schnitt
7. schreib_anweisungen: 3–5 konkrete Hinweise für den Schreibprozess

FORMAT: JSON-Objekt mit diesen Feldern
```

---

## 4.8 Konsistenz-Checks für die Mesostruktur

```
VOR KAPITEL-GENERIERUNG:
✓ Liegt das Kapitel an der richtigen Arc-Position?
✓ Weiß die POV-Figur genau das, was sie zu diesem Punkt wissen kann?
✓ Passt der Kapitel-Outcome zur Spannungskurve des Aktes?
✓ Gibt es einen echten Hook in der ersten Szene?

VOR SZENEN-GENERIERUNG:
✓ Hat die Szene ein klares, konkretes Goal?
✓ Gibt es einen echten Conflict (nicht nur Talk)?
✓ Verändert sich der emotionale Wert?
✓ Ist der Schauplatz zur Atmosphäre des Themas stimmig?
✓ Wird die POV-Perspektive strikt eingehalten?
```

---

## 4.9 Output: Mesostruktur-Objekt

```json
{
  "mesostruktur": {
    "akt_1": {
      "sequenzen": [
        {
          "id": "seq_1_1",
          "kapitel": [
            {
              "id": "k001",
              "szenen": [
                { "id": "s001_k001" }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

**Nächster Schritt:** Mit dem Szenenplan als Grundlage wird die Mikrostruktur — die eigentliche Prosa — entwickelt. → Schritt 5

---

*Roman-Hub Anleitung | Schritt 4 von 8 | Version 1.0*
