# Schritt 8 — Zeitstruktur & Chronologie

> **Für das LLM:** Zeit ist kein neutrales Gefäß, in dem Ereignisse stattfinden. Zeit ist ein dramaturgisches Werkzeug. Wie du mit Zeit umgehst, entscheidet über Spannung, Rhythm us, Überraschung und die emotionale Wirkung des Romans.

---

## 8.1 Zwei Zeitachsen: Story Time vs. Discourse Time

```
STORY TIME (Fabula):
Die chronologische Zeit, in der die Ereignisse stattfinden.
"Was wirklich passiert ist, in welcher Reihenfolge."
→ Objekt: Alle Ereignisse auf einem Zeitstrahl

DISCOURSE TIME (Sjuzet):
Die Zeit, wie sie der Roman erzählt.
"In welcher Reihenfolge und mit welcher Gewichtung wird erzählt."
→ Objekt: Kapitel-Reihenfolge + Gewichtung
```

### Die drei Grundrelationen

```
STORY TIME = DISCOURSE TIME
→ Lineares Erzählen
→ Klar, direkt, zugänglich
→ Standard für Thriller, Abenteuer

STORY TIME ≠ DISCOURSE TIME (Verzerrung)
→ Nicht-lineares Erzählen
→ Flashbacks, Ellipsen, Analepsen
→ Standard für literarische Romane, Noir, Trauma-Geschichten

STORY TIME >> DISCOURSE TIME (Komprimierung)
→ Zeitraffer-Passagen
→ "Drei Jahre vergingen."
→ Für unwichtige Übergangszeiten
```

---

## 8.2 Zeitliche Erzähltechniken

### 8.2.1 Analepse (Flashback)

```yaml
analepse:
  definition: "Rückblende auf Ereignisse, die vor dem Erzählbeginn liegen"
  
  wann_verwenden:
    - "Um den Ghost der Figur zu zeigen"
    - "Um ein Mystery aufzuklären (Auflösung)"
    - "Um Foreshadowing einzulösen"
    - "Um Kontrast zur Gegenwart zu schaffen"
  
  techniken:
    hard_cut:
      beschreibung: "Abrupter Wechsel ohne Überleitung"
      signal: "Damals. / Zehn Jahre früher."
      effekt: "Unmittelbarkeit, Schock"
    
    trigger:
      beschreibung: "Sinneseindruck löst Erinnerung aus"
      signal: "Der Geruch erinnerte sie an..."
      effekt: "Psychologisch glaubwürdig, organisch"
    
    chapter_break:
      beschreibung: "Ganzes Kapitel als Rückblende"
      signal: "Kapitel-Titel mit Zeitangabe: 'Berlin, 1989'"
      effekt: "Für längere Rückblenden"
  
  rueckkehr:
    beschreibung: "Wie kehrt man zur Gegenwart zurück?"
    techniken:
      - "Ähnliches Bild/Objekt in Gegenwart"
      - "Direkte Zeitmarkierung: 'Jetzt.'"
      - "Reaktion der Figur auf die Erinnerung"
  
  fehler_vermeiden:
    - "Flashback als Info-Dump (trockene Fakten)"
    - "Flashback ohne dramaturgischen Zweck"
    - "Zu langer Flashback (Leser verliert Gegenwart)"
```

### 8.2.2 Prolepse (Flashforward / Vorausdeutung)

```yaml
prolepse:
  definition: "Vorgriff auf Ereignisse, die noch nicht passiert sind"
  
  typen:
    explizite_prolepse:
      beispiel: "Er würde diesen Tag nie vergessen."
      effekt: "Erwartung + Ironie (wenn der Tag harmlos erscheint)"
    
    foreshadowing:
      beispiel: "Ein Detail, das Bedeutung bekommt"
      effekt: "Unbewusste Spannung, Kohärenz beim Wiederlesen"
    
    in_medias_res_opening:
      beschreibung: "Roman beginnt am Höhepunkt, springt dann zurück"
      effekt: "Sofortige Spannung, strukturelle Ironie"
      beispiel: "Openings wie: 'Drei Stunden später würde ich tot sein. Aber zuerst...'"
```

### 8.2.3 Ellipse (Zeitraffung / Auslassung)

```yaml
ellipse:
  definition: "Zeitabschnitte, die ausgelassen werden"
  
  wann_verwenden:
    - "Ereignisse ohne dramatischen Wert"
    - "Zeitsprünge zwischen Akt-Übergängen"
    - "Reise-/Wartezeiten"
  
  techniken:
    satz_ellipse:
      beispiel: "Drei Tage später."
      einsatz: "Kurze Sprünge"
    
    absatz_ellipse:
      beispiel: "Sie wartete. Manchmal fragten Leute, ob es ihr gut ginge."
      einsatz: "Zusammenfassung einer Periode"
    
    kapitel_ellipse:
      beispiel: "Kapitel endet → Neues Kapitel beginnt Wochen später"
      signal: "Erster Satz des neuen Kapitels gibt Zeit an"
  
  fehler_vermeiden:
    - "Wichtige Ereignisse in der Ellipse (Leser fühlt sich betrogen)"
    - "Zu lange Ellipsen ohne Orientierung"
```

### 8.2.4 Dehnung (Szene > Story Time)

```yaml
dehnung:
  definition: "Szene dauert im Lesen länger als in der Story"
  
  techniken:
    inner_monolog:
      beschreibung: "Gedanken dehnen eine kurze Handlungszeit"
      beispiel: "Sekunde des Falls → Seiten der Erinnerungen"
    
    zeitlupe_action:
      beschreibung: "Präzise Beschreibung jeder Bewegung"
      effekt: "Maximale Spannung im entscheidenden Moment"
    
    sensorische_verdichtung:
      beschreibung: "Alle Sinne einer kurzen Situation"
      effekt: "Atmosphärische Tiefe"
  
  wann_verwenden:
    - "Climax"
    - "All is Lost"
    - "Emotionale Höhepunkte"
    - "Wenn jede Sekunde zählt"
```

---

## 8.3 Erzähl-Zeitmodelle

### 8.3.1 Lineares Modell (Standard)

```
STORY TIME:    A → B → C → D → E
DISCOURSE TIME: A → B → C → D → E
```

Geeignet für: Thriller, Genre-Roman, Abenteuer

### 8.3.2 In-Media-Res-Modell

```
STORY TIME:    A → B → C → D → E
DISCOURSE TIME: D → A → B → C → D (Fortsetzung) → E
               ↑
           Roman beginnt hier (Mitte des Konflikts)
           dann zurück zum Anfang
```

Geeignet für: Thriller, literarischer Roman

### 8.3.3 Verschachteltes Zeitmodell (Nicht-linear)

```
STORY TIME:    A(1990) → B(1995) → C(2010) → D(2023)
DISCOURSE TIME: C(2010) → A(1990) → D(2023) → B(1995)
```

Geeignet für: Literarischer Roman, Psychologischer Thriller, Trauma-Narrative

### 8.3.4 Paralleles Zeitmodell

```
STORY TIME:    Figur A (Gegenwart) parallel zu Figur B (Gegenwart)
DISCOURSE TIME: Abwechselnde Kapitel A/B
```

Geeignet für: Multi-POV-Romane, Thriller mit mehreren Strängen

---

## 8.4 Die Roman-Chronologie — Das Master-Dokument

Jeder Roman braucht eine interne Chronologie — die "Geschichte hinter der Geschichte":

```yaml
master_chronologie:
  
  # PRE-STORY (vor Kapitel 1)
  pre_story:
    - datum: string
      ereignis: string
      beteiligte: []
      einfluss_auf_roman: string  # Warum ist das relevant?
  
  # STORY (Kapitel 1 bis Ende)
  story_timeline:
    - story_datum: string         # "Tag 1, 08:00"
      kapitel: int
      szene: string
      ereignis: string
      beteiligte: []
      informationsstand_danach:
        - figur: string
          weiss_jetzt: []
  
  # POST-STORY (nach letztem Kapitel)
  post_story:
    - datum: string
      ereignis: string
      funktion: "Resolution | Implied Future"
```

---

## 8.5 Zeitkonsistenz — Was der Hub prüfen muss

### 8.5.1 Figuren-Informationsstand-Tracking

Der häufigste Zeitfehler in LLM-generierten Texten: Eine Figur weiß etwas, das sie zu diesem Zeitpunkt nicht wissen kann.

```yaml
informations_tracker:
  - figur: string
    weiss_ab_kapitel:
      - kapitel: int
        info: string
        quelle: string          # Woher hat sie diese Information?
```

**LLM-Pflicht:** Vor jeder Szenen-Generierung muss der Hub prüfen:
> Was weiß diese Figur zu diesem Zeitpunkt — und was weiß sie NICHT?

### 8.5.2 Objekt- und Orts-Tracking

```yaml
objekt_tracker:
  - objekt: string              # "Der Brief"
    zuletzt_gesehen:
      - kapitel: int
        ort: string
        bei_figur: string
    aktueller_ort: string
```

### 8.5.3 Zeitkonsistenz-Check

```
VOR JEDER SZENE:
✓ Passt die Tageszeit zur Story-Chronologie?
✓ Hat die Figur genug Zeit für den Weg von Ort A nach Ort B?
✓ Ist das Wissen der Figur korrekt für diesen Zeitpunkt?
✓ Sind Objekte dort, wo sie sein sollten?
```

---

## 8.6 Zeitliche Spannungswerkzeuge

### 8.6.1 Die Klammer-Struktur

```
KAPITEL BEGINNT: Zeitmarke A
→ Ereignisse
KAPITEL ENDET: Zeitmarke B

NÄCHSTES KAPITEL: "Drei Stunden früher" / "Gleichzeitig"
→ Erzeugt Rückblende oder Parallelerzählung
→ Starkes Spannungswerkzeug
```

### 8.6.2 Das Gleichzeitigkeits-Prinzip

Bei mehreren POVs:

```yaml
gleichzeitigkeit:
  kapitel_a:
    pov: "Figur A"
    story_zeit: "Tag 5, 14:00–15:30"
    ereignis: "..."
  
  kapitel_b:
    pov: "Figur B"
    story_zeit: "Tag 5, 14:00–15:30"  # Gleiche Zeit!
    ereignis: "..."
    
  effekt: "Leser weiß mehr als jede einzelne Figur"
  spannungstyp: "Dramatic Irony"
```

### 8.6.3 Die Zeitkompression im Climax

```
STANDARD-KAPITEL:   1 Erzähl-Seite = ca. 1 Story-Stunde
CLIMAX:             1 Erzähl-Seite = ca. 1 Story-Minute
```

Diese Verdichtung erzeugt Intensität ohne Action zu beschleunigen.

---

## 8.7 Prompt-Templates für Zeitstruktur

### Template ZT-1: Master-Chronologie aufbauen

```
SYSTEM:
Du erstellst die interne Chronologie eines Romans.
Diese Chronologie ist das Master-Dokument für alle zeitlichen Fragen.
Antworte als JSON.

USER:
Erstelle die Master-Chronologie für diesen Roman:

MAKROSTRUKTUR: {wendepunkte}
SUBSTRAT: {figuren_und_ihre_geheimnisse}
GENRE: {genre}
ZEITRAUM: {story_time_gesamt}

AUFGABE:
1. Pre-Story: Wichtige Ereignisse VOR dem Roman (min. 3)
2. Story-Timeline: Alle Kapitel mit Datum/Zeit und Informationsstand-Updates
3. Informations-Tracker für alle Hauptfiguren

PRÜFE:
- Gibt es zeitliche Widersprüche?
- Ist die Zeit zwischen Ort-Wechseln realistisch?
- Werden alle Informationen korrekt timed (Figur weiß A erst nach Kapitel X)?

FORMAT: master_chronologie-Objekt
```

### Template ZT-2: Rückblenden-Architektur planen

```
SYSTEM:
Du planst die Rückblenden-Architektur eines Romans.
Jede Rückblende muss einen klaren dramaturgischen Zweck haben.

USER:
Plane die Rückblenden für diesen Roman:

PROTAGONIST_GHOST: {was_ist_das_trauma_aus_der_vergangenheit}
MAKROSTRUKTUR: {wendepunkte}
PRE_STORY: {wichtige_vergangene_ereignisse}

AUFGABE:
Plane 3–5 Rückblenden:
1. Wann (in welchem Kapitel / an welchem Arc-Punkt)?
2. Welche Pre-Story-Ereignisse werden gezeigt?
3. Warum hier? (Dramaturgischer Zweck)
4. Wie wird die Rückblende eingeleitet? (Technik)
5. Wie kehren wir zur Gegenwart zurück?

PRINZIP:
- Frühe Rückblenden: zeigen den Ghost, eher fragmentarisch
- Mittlere Rückblenden: vertiefen das Verständnis
- Späte Rückblenden: enthüllen die volle Wahrheit

FORMAT: rueckblenden_plan-Array
```

### Template ZT-3: Zeitkonsistenz einer Szene prüfen

```
SYSTEM:
Du prüfst die zeitliche Konsistenz einer Szene gegen die Master-Chronologie.

USER:
Prüfe diese Szene auf Zeitkonsistenz:

SZENE: {szenen_objekt}
MASTER_CHRONOLOGIE: {relevanter_ausschnitt}
INFORMATIONS_TRACKER: {figuren_wissensstand_aktuell}

PRÜFE:
1. Story-Zeit: Stimmt die Zeitangabe der Szene?
2. Ort-Konsistenz: Kann die Figur hier sein (ausgehend von letztem Auftreten)?
3. Informationsstand: Weiß die Figur nur, was sie wissen kann?
4. Objekte: Sind alle erwähnten Objekte dort, wo sie sein sollten?

AUSGABE:
{
  "zeitlich_konsistent": true/false,
  "fehler": ["..."],
  "korrekturen": ["..."]
}
```

### Template ZT-4: Zeitliche Spannungsverdichtung (Climax)

```
SYSTEM:
Du planst die zeitliche Verdichtung für den Climax-Abschnitt.

USER:
Plane die Zeitstruktur für den Climax:

CLIMAX_INHALT: {was_passiert_im_climax}
BETEILIGTE_FIGUREN: {figuren_und_ihre_ziele_im_climax}
STORY_ZEITRAUM: {wie_lange_dauert_der_climax_in_story_time}

AUFGABE:
1. Teile den Climax in Segmente auf
2. Plane für jedes Segment: Story-Zeit vs. Discourse-Zeit
3. Identifiziere den Moment maximaler Verdichtung (Zeitlupe)
4. Plane Gleichzeitigkeits-Momente (falls mehrere POVs)

FORMAT: climax_zeitplan-Objekt
```

---

## 8.8 Zeitliche Anti-Patterns

```
ANTI-PATTERN 1: Die Wissens-Zeitreise
Figur weiß in Kapitel 3, was sie erst in Kapitel 8 erfahren wird.
→ LÖSUNG: Informations-Tracker konsequent führen

ANTI-PATTERN 2: Die unmögliche Reise
Figur ist in Kapitel 10 in Berlin und in Kapitel 11 in Tokyo —
ohne dass Zeit vergangen ist.
→ LÖSUNG: Zeitmarken explizit setzen, Reisezeiten einplanen

ANTI-PATTERN 3: Die ewige Gegenwart
Jede Szene wird gleich ausführlich erzählt, egal wie wichtig.
→ LÖSUNG: Ellipsen für unwichtige Zeiten, Dehnung für Climax

ANTI-PATTERN 4: Der vergessene Zeitstrang
Subplot verschwindet für 15 Kapitel ohne Erklärung.
→ LÖSUNG: Jeder Zeitstrang braucht regelmäßige Erwähnung

ANTI-PATTERN 5: Die anachronistische Figuren-Reaktion
Figur reagiert auf etwas, das sie noch nicht wissen kann.
→ LÖSUNG: Vor jeder Szene Informationsstand prüfen
```

---

## 8.9 Output: Zeitstruktur-Objekte

```json
{
  "zeitstruktur": {
    "erzaehl_modell": "linear | in_medias_res | nicht_linear | parallel",
    "story_zeitraum": "",
    "pre_story": [],
    "master_chronologie": [],
    "informations_tracker": {},
    "objekt_tracker": {},
    "rueckblenden": [],
    "ellipsen": [],
    "gleichzeitigkeits_momente": []
  }
}
```

---

## 8.10 Das vollständige Roman-Substrat nach Schritt 8

Nach Abschluss aller acht Schritte verfügt der Hub über:

```
✓ Schritt 1: roman_core        → Grundstruktur, Genre, Arc-Richtung
✓ Schritt 2: makrostruktur     → Akte, Wendepunkte, Proportionen
✓ Schritt 3: substrat          → World Bible, Figuren, Beziehungen
✓ Schritt 4: mesostruktur      → Kapitel, Szenen, Outcomes
✓ Schritt 5: narrative_voice   → Stimme, POV, Stil-Marker
✓ Schritt 6: spannungs_architektur → Typen, Kurve, Foreshadowing
✓ Schritt 7: thema_und_motiv   → Frage, Antwort, Motiv-System
✓ Schritt 8: zeitstruktur      → Chronologie, Tracker, Techniken
```

**Dieser Gesamtkomplex ist das Roman-Bible** — das unveränderliche Referenzdokument für alle Generierungsaufgaben.

**Nächster Schritt:** Mit diesem vollständigen Roman-Bible kann das Hub-System anfangen, den Roman tatsächlich zu schreiben — Szene für Szene, Kapitel für Kapitel, immer mit Zugriff auf alle Ebenen. → Schritt 9 (Qualitäts-Checkpoints & Schreib-Workflows)

---

*Roman-Hub Anleitung | Schritt 8 von 8 | Version 1.0*
