# Schritt 6 — Spannungsarchitektur: Wie Spannung entsteht und gesteuert wird

> **Für das LLM:** Spannung ist kein Zufallsprodukt und kein Synonym für Action. Sie ist eine präzise steuerbare Wirkung, die aus der Kontrolle von Information und Erwartung entsteht. Du kannst Spannung planen, messen und gezielt einsetzen.

---

## 6.1 Was Spannung wirklich ist

```
DEFINITION:
Spannung = Die Erwartung eines Lesers, dass etwas Bedeutsames passieren wird,
           kombiniert mit der Unsicherheit, was genau passieren wird.

FORMEL:
Spannung = Einsatz × Unsicherheit × Zeitdruck
```

**Was bedeutet das:**
- **Einsatz** (Stakes): Was verliert die Figur, wenn sie scheitert?
- **Unsicherheit**: Wir wissen nicht, wie es ausgeht
- **Zeitdruck**: Es muss jetzt entschieden werden

Wenn einer dieser Faktoren null ist, gibt es keine Spannung.

---

## 6.2 Die drei Spannungstypen

### Typ 1: Mystery (Informationsdefizit beim Leser)

```
PRINZIP:
Der Leser weiß weniger als die Figur.
Der Leser will wissen, was passiert ist / was los ist.

FRAGE-STRUKTUR:
"Wer hat X getan?"
"Was bedeutet dieses Zeichen?"
"Was verbirgt diese Person?"

INSTRUMENTE:
- Andeutungen ohne Auflösung
- Unzuverlässiger Erzähler
- Fragmentierte Information
- Zeitliche Nichtlinearität

GEEIGNET FÜR: Krimi, Thriller, Noir
VORSICHT: Mystery ohne Payoff frustriert den Leser
```

### Typ 2: Suspense (Informationsvorsprung des Lesers)

```
PRINZIP:
Der Leser weiß mehr als die Figur.
Der Leser will schreien: "Vorsicht! Schau hin!"

HITCHCOCK-PRINZIP:
Zwei Menschen sitzen an einem Tisch und reden über Fußball.
Plötzlich explodiert eine Bombe.
→ ÜBERRASCHUNG: 15 Sekunden Schock

Zwei Menschen sitzen an einem Tisch. Wir sehen: Unter dem Tisch liegt eine Bombe.
Sie sehen es nicht. Sie reden über Fußball.
→ SUSPENSE: 15 Minuten Spannung

INSTRUMENTE:
- Leser über Gefahr informieren, Figur nicht
- Ironische Gespräche (Figur redet normal, Leser leidet)
- Scenic irony
- Revealed villain / revealed plan

GEEIGNET FÜR: Thriller, Horror, Drama
```

### Typ 3: Dramatic Irony (Wissensvorsprung über Konsequenzen)

```
PRINZIP:
Der Leser versteht die tiefere Bedeutung einer Situation,
die den Figuren verborgen bleibt.

BEISPIEL:
Figur feiert, weil sie das Ziel erreicht hat.
Leser weiß: Das Ziel war eine Falle.

INSTRUMENTE:
- Vorausdeutungen (Foreshadowing)
- Symbolik, die der Leser versteht
- Informationen aus anderen POV-Kapiteln

GEEIGNET FÜR: Tragödie, literarischer Roman, alle Genres
```

---

## 6.3 Die Spannungskurve: Makro-Ebene

### 6.3.1 Das Gesetz der eskalierenden Einsätze

Jeder Akt muss die Einsätze gegenüber dem vorherigen erhöhen:

```
AKT I:   "Figur könnte ihr Ziel verlieren"
AKT II:  "Figur könnte alles verlieren"
AKT III: "Figur könnte sich selbst verlieren"
```

**Die Einsatz-Leiter:**
```
GLOBAL STAKES    → Welt, Gesellschaft, viele Leben
PERSÖNLICHE STAKES → Das, was die Figur liebt
PROFESSIONELLE STAKES → Karriere, Reputation
PHYSISCHE STAKES → Körper, Leben
PSYCHOLOGISCHE STAKES → Identität, Werte, Seele
```

Die stärkste Spannung entsteht, wenn die äußeren Stakes (physisch) die inneren Stakes (psychologisch) spiegeln.

### 6.3.2 Das Rhythmus-Gesetz

Spannung braucht Pausen:

```
SPANNUNG OHNE PAUSE:    Leser erschöpft → Abstumpfung
PAUSE OHNE SPANNUNG:    Leser gelangweilt → Abbruch
SPANNUNG + PAUSE:       Leser erholt → bereit für nächste Welle

OPTIMALER RHYTHMUS:
[Spannung hoch] → [kurze Atempause] → [Spannung noch höher] → ...
```

```yaml
spannungs_rhythmus:
  zyklus_laenge: "2–4 Kapitel"
  peak_dauer: "1–2 Kapitel"
  valley_dauer: "0.5–1 Kapitel"
  valley_funktion: "Charakter-Moment | Humor | Atmosphäre | Beziehung"
```

### 6.3.3 Das vollständige Spannungsbogen-Objekt

```yaml
spannungs_bogen:
  gesamt_verlauf:
    - position_prozent: 0
      intensitaet: 2
      name: "Normalwelt"
      typ: "setup"
    
    - position_prozent: 10
      intensitaet: 4
      name: "Inciting Incident"
      typ: "peak"
    
    - position_prozent: 15
      intensitaet: 2
      name: "Debate"
      typ: "valley"
      valley_funktion: "Figur-Charakter"
    
    - position_prozent: 25
      intensitaet: 5
      name: "End of Act I"
      typ: "peak"
    
    - position_prozent: 37
      intensitaet: 3
      name: "B-Story begins"
      typ: "valley"
      valley_funktion: "Beziehung"
    
    - position_prozent: 50
      intensitaet: 7
      name: "Midpoint"
      typ: "peak"
    
    - position_prozent: 62
      intensitaet: 6
      name: "Escalation"
      typ: "rising"
    
    - position_prozent: 75
      intensitaet: 8
      name: "All is Lost"
      typ: "peak"
    
    - position_prozent: 78
      intensitaet: 3
      name: "Dark Night"
      typ: "valley"
      valley_funktion: "Psychologisch, introspektiv"
    
    - position_prozent: 87
      intensitaet: 7
      name: "Break into Act III"
      typ: "rising"
    
    - position_prozent: 98
      intensitaet: 10
      name: "Climax"
      typ: "peak"
    
    - position_prozent: 100
      intensitaet: 3
      name: "Resolution"
      typ: "valley"
      valley_funktion: "Abschluss, neue Normalwelt"
```

---

## 6.4 Die Spannungskurve: Meso-Ebene (Kapitel)

Jedes Kapitel hat seine eigene Mini-Spannungskurve:

```yaml
kapitel_spannung:
  anfang: int       # 1–10, wo startet dieses Kapitel?
  verlauf: string   # "steigend | fallend | plateau | berg"
  peak: int         # Maximale Spannung im Kapitel
  peak_position: string  # "anfang | mitte | ende"
  ende: int         # Wo endet das Kapitel?
  
  # EMPFOHLENE MUSTER:
  muster_1: "Niedrig start → steigend → hoch ende"     # Cliffhanger
  muster_2: "Mittel start → peak mitte → tief ende"    # Aftermath
  muster_3: "Hoch start (in medias res) → plateau"     # Action-Kapitel
```

**Empfehlung:** Kapitel-Anfangs-Spannung sollte leicht höher liegen als das Ende des vorherigen Kapitels.

---

## 6.5 Spannung auf Szenen-Ebene: Die fünf Werkzeuge

### Werkzeug 1: Der Ticking Clock

```
PRINZIP: Zeitdruck erhöht Spannung sofort
EINSATZ: "Er hat 20 Minuten bis der Zug abfährt."
VARIANTEN:
- Expliziter Countdown ("Noch drei Tage bis zur Verhandlung")
- Impliziter Zeitdruck ("Wenn er das herausfindet, bevor ich...")
- Eskalierender Zeitdruck (Deadline wird näher)
```

### Werkzeug 2: Das Unvollständige Gespräch

```
PRINZIP: Unterbrochener Dialog/Gedanke = Offene Frage
EINSATZ: Figur beginnt, etwas Wichtiges zu sagen — wird unterbrochen
EFFEKT: Leser muss weiterlesen, um die Antwort zu finden
```

### Werkzeug 3: Das Falsche Sicherheitsgefühl

```
PRINZIP: Figur (und Leser) glauben kurz, die Gefahr ist vorbei
         → Dann ist es schlimmer als zuvor
HITCHCOCK: "Das Schlimmste ist nicht, wenn die Bombe explodiert —
            das Schlimmste ist, wenn sie es nicht tut"
EINSATZ: Scheinsieg → Neue, größere Bedrohung
```

### Werkzeug 4: Das Withheld Information Device

```
PRINZIP: Leser weiß, dass die Figur etwas weiß, was wir nicht wissen
EINSATZ: "Sie sah den Brief. Danach war nichts mehr wie vorher."
         → Wir wissen nicht, was im Brief steht — aber wir müssen es wissen
```

### Werkzeug 5: Die moralische Falle

```
PRINZIP: Figur muss zwischen zwei gleich schlechten Optionen wählen
EINSATZ: "Rettet sie den einen und opfert den anderen — oder verliert sie beide?"
EFFEKT: Stärkste Form von Spannung, weil sie innere und äußere Ebene verbindet
```

---

## 6.6 Foreshadowing und Payoff

Spannung über langen Zeitraum entsteht durch Versprechen (Foreshadowing) und Einlösung (Payoff):

```yaml
foreshadowing_system:
  - id: "fw_001"
    typ: objekt | dialog | bild | name | ereignis
    eingeführt_in_kapitel: int
    eingeführt_wie: string      # Wie unauffällig wird es gezeigt?
    bedeutung: string           # Was bedeutet es wirklich?
    aufgeloest_in_kapitel: int
    payoff: string              # Wie wird es aufgelöst?
    
    # BEISPIEL:
    # typ: "objekt"
    # eingeführt_wie: "Beiläufige Erwähnung einer Narbe"
    # bedeutung: "Zeuge eines alten Verbrechens"
    # payoff: "Narbe identifiziert ihn als Täter im Climax"
```

**Chekhov's Gun:**
> "Wenn im ersten Akt eine Waffe an der Wand hängt, muss sie im dritten Akt abgefeuert werden."

Und umgekehrt: Wenn im dritten Akt eine Waffe abgefeuert wird, muss sie im ersten Akt an der Wand gehangen haben.

---

## 6.7 Prompt-Templates für Spannungsarchitektur

### Template SP-1: Spannungsbogen analysieren

```
SYSTEM:
Du analysierst und optimierst den Spannungsbogen eines Romans.
Antworte als JSON.

USER:
Analysiere diesen Spannungsbogen:

KAPITEL_LISTE: {liste_aller_kapitel_mit_spannung_anfang_ende}
MAKROSTRUKTUR: {wendepunkte}

PRÜFE:
1. Gibt es Spannungsplateaus, die zu lang sind (> 3 Kapitel ohne Veränderung)?
2. Gibt es Sprünge ohne Vorbereitung?
3. Ist der Climax wirklich das Maximum (sollte 10/10 sein)?
4. Gibt es Valley-Momente nach jedem Peak?
5. Stimmt die Kurve mit der Makrostruktur überein?

AUSGABE:
{
  "spannungs_kurve": [{kapitel: int, intensitaet: int}],
  "probleme": ["..."],
  "empfehlungen": ["..."]
}
```

### Template SP-2: Foreshadowing-Netz planen

```
SYSTEM:
Du planst das Foreshadowing-Netz eines Romans.
Jedes Element muss einen Payoff haben. Kein Payoff ohne Setup.

USER:
Plane das Foreshadowing für diesen Roman:

MAKROSTRUKTUR: {wendepunkte}
SUBSTRAT: {figuren_und_thema}
CLIMAX: {was_passiert_im_climax}

AUFGABE:
1. Identifiziere 5–8 Elemente, die im Climax oder der Resolution
   eine Rolle spielen werden
2. Plane für jedes Element ein frühes, unauffälliges Auftreten
3. Stelle sicher, dass kein Element "aus dem Nichts" kommt

FORMAT: foreshadowing_system-Array
```

### Template SP-3: Stakes-Eskalations-Plan

```
SYSTEM:
Du planst die Eskalation der Einsätze über den Roman.

USER:
Plane die Stakes-Eskalation für:

PROTAGONIST: {protagonist_objekt}
MAKROSTRUKTUR: {drei_akte}

AUFGABE:
Definiere für jeden Akt:
1. Was hat die Figur zu verlieren? (konkret)
2. Auf welcher Stakes-Ebene spielen wir? (global/persönlich/physisch/psychologisch)
3. Wie hoch sind die Stakes auf einer Skala 1–10?
4. Wie wird diese Erhöhung dramaturgisch sichtbar gemacht?

PRINZIP: Akt III muss psychologische Stakes enthalten
         (Identität der Figur steht auf dem Spiel)

FORMAT: stakes_plan-Objekt
```

### Template SP-4: Kapitel-Spannung kalibrieren

```
SYSTEM:
Du kalibrierst die Spannungsverteilung innerhalb eines Kapitels.

USER:
Kalibriere die Spannungsverteilung für Kapitel {nummer}:

KAPITEL-OBJEKT: {kapitel}
SZENEN-PLAN: {szenen}
VORHERIGES_KAPITEL_ENDE_SPANNUNG: {int}
NÄCHSTES_KAPITEL_ANFANG_SPANNUNG: {int}

AUFGABE:
1. Prüfe, ob die Szenen-Reihenfolge eine sinnvolle Spannungskurve ergibt
2. Identifiziere, welche Szene den Peak des Kapitels bildet
3. Prüfe, ob der End-Hook ausreichend Spannung aufbaut

AUSGABE:
{
  "szenen_spannung": [{szene: int, intensitaet: int}],
  "peak_szene": int,
  "kapitel_spannung_anfang": int,
  "kapitel_spannung_ende": int,
  "end_hook_wirkung": "stark | mittel | schwach",
  "optimierungen": ["..."]
}
```

---

## 6.8 Anti-Patterns: Was Spannung zerstört

```
ANTI-PATTERN 1: Der erklärende Autor
"Sie war in großer Gefahr, das wusste sie."
→ ERKLÄRT Spannung statt sie zu ERZEUGEN

ANTI-PATTERN 2: Die unvermeidliche Rettung
Leser weiß, dass der Protagonist nicht sterben wird
→ LÖSUNG: Die Bedrohung muss etwas anderes bedrohen als das Leben

ANTI-PATTERN 3: Das Spannungsplateau
Drei Kapitel lang passiert nichts Neues
→ LÖSUNG: Jede Szene muss irgendetwas verändern

ANTI-PATTERN 4: Die falsche Dringlichkeit
Ticking Clock für ein unwichtiges Ziel
→ LÖSUNG: Zeitdruck nur bei hohen Stakes einsetzen

ANTI-PATTERN 5: Der unmotivierte Antagonist
"Er ist einfach böse"
→ LÖSUNG: Antagonist mit nachvollziehbarer Motivation (→ Schritt 3)
```

---

## 6.9 Output: Spannungsarchitektur-Objekt

```json
{
  "spannungs_architektur": {
    "dominanter_typ": "mystery | suspense | dramatic_irony | mix",
    "stakes_eskalation": [],
    "makro_bogen": [],
    "foreshadowing_netz": [],
    "valley_funktionen": [],
    "ticking_clocks": []
  }
}
```

**Nächster Schritt:** Die Spannungsarchitektur ist das Gerüst. Das Thema ist die Seele. → Schritt 7

---

*Roman-Hub Anleitung | Schritt 6 von 8 | Version 1.0*
