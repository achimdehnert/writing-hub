# Schritt 7 — Thema, Subtext & Motivsystem

> **Für das LLM:** Das Thema ist das, was ein Roman zu sagen hat. Aber es wird nie gesagt — es wird gezeigt. Dieser Schritt erklärt, wie Bedeutung durch Struktur, Symbole und Entscheidungen in den Roman eingewoben wird, ohne dass der Autor je den Zeigefinger hebt.

---

## 7.1 Was ein Thema ist (und was nicht)

```
THEMA IST NICHT:
✗ Ein Sujet ("Es geht um Krieg")
✗ Eine Moral ("Lügen ist falsch")
✗ Eine Aussage über ein Thema ("Dieser Roman handelt von Verrat")

THEMA IST:
✓ Eine Frage, die der Roman stellt
✓ Eine Antwort, die er durch das Ende gibt
✓ Eine Wahrheit, die durch Figuren-Entscheidungen verkörpert wird
```

### Das Thema als Frage + Antwort

```yaml
thema:
  frage: string
    # "Kann man ein gutes Leben führen, wenn man das Böse kennt?"
    # "Ist Loyalität stärker als Gerechtigkeit?"
    # "Werden wir von unserer Vergangenheit definiert oder von unseren Entscheidungen?"
  
  antwort_des_romans: string
    # Was behauptet der Roman am Ende durch seine Ereignisse?
    # Diese Antwort muss nie GESAGT werden — nur GEZEIGT.
  
  verkörpert_durch:
    - figur: string             # Welche Figur repräsentiert welche Position?
    - plot_punkt: string        # Welches Ereignis zeigt die Themen-Antwort?
    - symbol: string            # Welches Motiv trägt das Thema?
```

---

## 7.2 Thema und Charakter-Arc: Die Verbindung

Das Thema und der Charakter-Arc sind zwei Seiten derselben Münze:

```
CHARAKTER-ARC:
"Figur glaubt falsche Wahrheit → erkennt wahre Wahrheit"

THEMA:
"Roman fragt: Was ist die wahre Wahrheit?"

ZUSAMMEN:
Die falsche Überzeugung der Figur = Thesen-Ablehnung
Die Reise der Figur = Auseinandersetzung mit der Frage
Die Erkenntnis der Figur = Themen-Antwort des Romans
```

**Beispiel:**

| Element | Inhalt |
|---------|--------|
| Themen-Frage | "Macht Schweigen uns zu Komplizen?" |
| Falsche Überzeugung (Figur) | "Wenn ich nichts sage, bin ich nicht schuldig" |
| Arc-Reise | Figur wird mit den Konsequenzen ihres Schweigens konfrontiert |
| Wahre Erkenntnis | "Schweigen ist eine Entscheidung — und damit Schuld" |
| Themen-Antwort | "Ja, Schweigen macht uns zu Komplizen" |

---

## 7.3 Das Themen-Gerüst: Wie das Thema in die Struktur eingebaut wird

### 7.3.1 Die Thesen-Figur und die Anti-Thesen-Figur

```yaml
themen_figuren:
  these:
    figur: string               # Verkörpert die Antwort des Romans
    position: string            # "Schweigen macht schuldig"
    wie_verkörpert: string      # Durch welche Handlungen?
  
  antithese:
    figur: string               # Verkörpert die gegenteilige Position
    position: string            # "Schweigen ist Selbstschutz"
    wie_verkörpert: string
  
  synthese:
    figur: string               # Oft der Protagonist am Ende
    position: string            # Die Antwort, zu der der Roman kommt
```

### 7.3.2 Das Thema in den Plot-Punkten

Das Thema muss in den wichtigsten Momenten des Romans sichtbar sein:

```yaml
thema_in_plot:
  inciting_incident:
    event: string               # Das Ereignis
    thema_bezug: string         # Wie stellt es die Themen-Frage?
  
  midpoint:
    event: string
    thema_bezug: string         # Wie verschärft es die Frage?
  
  all_is_lost:
    event: string
    thema_bezug: string         # Was verliert die Figur, weil sie die falsche Wahrheit glaubt?
  
  climax:
    event: string
    thema_bezug: string         # Wie beantwortet die Entscheidung die Themen-Frage?
```

---

## 7.4 Das Motivsystem

### 7.4.1 Was ein Motiv ist

```
MOTIV:
Ein wiederkehrendes Element (Objekt, Bild, Wort, Handlung, Farbe),
das bei jeder Wiederkehr eine neue Bedeutungsschicht trägt
und das Thema sinnlich erfahrbar macht.

UNTERSCHIED ZU SYMBOL:
Symbol = Einmalig, trägt Bedeutung beim Auftreten
Motiv  = Wiederkehrend, entwickelt Bedeutung über Wiederholung
```

### 7.4.2 Motivtypen

```yaml
motiv_typen:
  
  objekt_motiv:
    beispiel: "Ein Spiegel"
    moegliche_bedeutung: "Selbsttäuschung | Identität | Doppelgänger"
  
  handlungs_motiv:
    beispiel: "Türen schließen"
    moegliche_bedeutung: "Ausschluss | Selbstschutz | verpasste Chancen"
  
  naturmotiv:
    beispiel: "Regen / Gewitter"
    moegliche_bedeutung: "Reinigung | Bedrohung | Wendepunkt"
  
  farb_motiv:
    beispiel: "Rot"
    moegliche_bedeutung: "Gefahr | Leidenschaft | Blut"
  
  dialog_motiv:
    beispiel: "Eine wiederkehrende Phrase"
    moegliche_bedeutung: "Verändert Bedeutung je nach Kontext"
```

### 7.4.3 Das Motiv-Entwicklungs-Prinzip

Ein Motiv muss sich entwickeln — sonst ist es nur eine Wiederholung:

```
ERSTE ERWÄHNUNG:
→ Neutral, beiläufig eingeführt
→ Leser registriert es nicht bewusst

ZWEITE ERWÄHNUNG:
→ Im anderen Kontext, leicht verändert
→ Leser beginnt, Verbindung herzustellen

DRITTE ERWÄHNUNG (Wendepunkt):
→ In einem dramatisch aufgeladenen Moment
→ Die Bedeutung wird klar / verändert sich grundlegend

VIERTE ERWÄHNUNG (Auflösung):
→ Im Climax oder Resolution
→ Trägt die volle symbolische Last
→ Krönt die Entwicklung
```

### 7.4.4 Vollständiges Motiv-Objekt

```yaml
motiv:
  id: string
  bezeichnung: string              # "Der Spiegel"
  typ: objekt | handlung | natur | farbe | dialog | musik | name
  thema_bezug: string              # Wie trägt es das Thema?
  
  auftritte:
    - kapitel_id: string
      szene_id: string
      kontext: string              # Wie wird es verwendet?
      bedeutung_an_diesem_punkt: string
      wie_einfuehren: string       # "beiläufig | aufgeladen | symbolisch"
  
  entwicklung: string              # Wie verändert sich die Bedeutung über den Roman?
  payoff: string                   # Was bedeutet es am Ende?
  verknuepft_mit_figur: string     # Optional: Figur, die mit diesem Motiv assoziiert ist
```

---

## 7.5 Subtext auf Ebene des gesamten Romans

### 7.5.1 Was Subtext auf Roman-Ebene bedeutet

Subtext auf Szenenebene = Was eine Figur wirklich meint (→ Schritt 5)
Subtext auf Roman-Ebene = Was der Roman wirklich sagt (über die Oberfläche hinaus)

```
OBERFLÄCHE DES ROMANS:     "Ein Detektiv löst einen Mordfall"
SUBTEXT DES ROMANS:        "Ein Mann findet sich selbst, indem er lernt,
                             anderen zu vertrauen"
TIEFERER SUBTEXT:          "Institutionen schützen nicht — Menschen schützen Menschen"
```

**LLM-Regel:** Der Hub sollte beim Setup klären, ob der Roman einen oder mehrere Subtext-Ebenen hat. Literarische Romane haben mehr Schichten als Genre-Romane.

### 7.5.2 Subtext durch strukturelle Ironie

```
STRUKTURELLE IRONIE:
Die Art, wie die Geschichte aufgebaut ist, sagt mehr als ihr Inhalt.

BEISPIEL:
Roman über "die Suche nach Freiheit" —
endet damit, dass die Figur freiwillig eine Verpflichtung eingeht.
→ Strukturelle Aussage: "Wahre Freiheit entsteht durch Bindung, nicht durch ihre Abwesenheit"
```

---

## 7.6 Thema durch Figurenentscheidungen zeigen

**Die wichtigste Technik:** Lass Figuren Entscheidungen treffen, die das Thema embodyen.

```
NICHT:
Figur erklärt ihr Weltbild in einem Monolog.

SONDERN:
Figur steht vor einer Wahl, bei der beide Optionen eine Antwort auf die Themen-Frage sind.
Ihre Entscheidung zeigt, wie sie die Frage beantwortet.
```

```yaml
themen_entscheidungen:
  - kapitel_id: string
    figur: string
    situation: string              # Die Entscheidungssituation
    option_a: string               # Entscheidung, die falsche Wahrheit bestätigt
    option_b: string               # Entscheidung, die wahre Wahrheit annimmt
    wahl: string                   # Was wählt die Figur? (verändert sich über den Roman)
    thema_aussage: string          # Was zeigt diese Entscheidung über das Thema?
```

**Progression der Themen-Entscheidungen:**
- Akt I: Figur wählt konsequent Option A (falsche Wahrheit)
- Akt II: Figur schwankt, trifft erste zögerliche Entscheidungen für B
- Climax: Figur muss die endgültige Entscheidung zwischen A und B treffen

---

## 7.7 Prompt-Templates für Thema & Motiv

### Template TH-1: Thema aus Roman-Kern ableiten

```
SYSTEM:
Du leitest das Thema eines Romans aus seinem Kern ab.
Das Thema soll nie explizit genannt werden müssen — es zeigt sich durch Ereignisse.
Antworte als JSON.

USER:
Leite das Thema für diesen Roman ab:

ROMAN-KERN: {roman_kern}
CHARAKTER-ARC: {arc_typ, falsche_wahrheit, wahre_erkenntnis}
GENRE: {genre}

AUFGABE:
1. Formuliere die Themen-FRAGE (offen, nicht moralisierend)
2. Formuliere die Themen-ANTWORT (die der Roman durch sein Ende gibt)
3. Identifiziere 2–3 Figuren, die verschiedene Positionen zu dieser Frage verkörpern
4. Benenne 3 Plot-Momente, in denen die Frage besonders scharf wird

PRÜFE:
- Ist die Frage wirklich offen (kein "offensichtlich ist X falsch")?
- Wird die Antwort erst durch den Climax klar?
- Ist das Thema universell genug für breite Leserschaft?

FORMAT: thema-Objekt als JSON
```

### Template TH-2: Motivsystem entwickeln

```
SYSTEM:
Du entwickelst das Motivsystem eines Romans.
Motive müssen sich entwickeln und einen dramaturgischen Payoff haben.
Antworte als JSON.

USER:
Entwickle das Motivsystem für diesen Roman:

THEMA: {thema_objekt}
SUBSTRAT: {welt_und_hauptfiguren}
GENRE: {genre}

AUFGABE:
Entwickle 4–6 Motive:
- 2 Hauptmotive (tragen das Thema direkt)
- 2–4 Nebenmotive (unterstützen, variieren, kontrastieren)

Für jedes Motiv:
1. Typ und Bezeichnung
2. Thema-Bezug
3. Vier Auftritte mit Bedeutungsentwicklung
4. Payoff am Ende

PRÜFE:
- Entwickeln sich alle Motive über den Roman?
- Gibt es Verbindungen zwischen den Motiven?
- Sind die ersten Einführungen unauffällig genug?

FORMAT: motiv_system-Array
```

### Template TH-3: Themen-Entscheidungen in Szenen verankern

```
SYSTEM:
Du verankerst das Thema in konkreten Figuren-Entscheidungen.
Das Thema wird nie erklärt — nur durch Handlungen gezeigt.

USER:
Verankere das Thema in diesen Schlüsselmomenten:

THEMA: {thema_objekt}
MAKROSTRUKTUR: {wendepunkte}
PROTAGONIST: {protagonist_arc}

FÜR JEDEN WENDEPUNKT:
Definiere eine Entscheidungssituation, in der der Protagonist zwischen
der falschen und der wahren Wahrheit wählen kann.

Akt I Ende: Figur wählt falsche Wahrheit (erwartbar)
Midpoint: Figur wählt ambivalent
Dark Night: Figur wählt falsche Wahrheit aus Verzweiflung
Climax: Figur wählt wahre Wahrheit (oder verweigert sie → Tragödie)

FORMAT: themen_entscheidungen-Array
```

### Template TH-4: Motiv in Szene einweben

```
SYSTEM:
Du webst ein Motiv in eine existierende Szene ein.
Das Motiv soll an dieser Stelle (Schritt in der Entwicklung) korrekt positioniert sein.
Nie aufdringlich, immer organisch.

USER:
Webe dieses Motiv in die Szene ein:

MOTIV: {motiv_objekt}
AKTUELLER AUFTRITS-SCHRITT: {1 | 2 | 3 | 4}
ERWARTETE BEDEUTUNG AN DIESEM PUNKT: {bedeutung}
SZENE: {szenen_objekt}

AUFGABE:
Schlage vor, wie das Motiv in diese Szene eingewoben werden kann:
1. An welchem Punkt der Szene erscheint es?
2. Wie wird es gezeigt? (Beschreibung, Dialog, Handlung?)
3. Wie unauffällig oder aufgeladen soll es sein?
4. Wie viele Wörter sollte der Motiv-Moment einnehmen?

FORMAT: Konkreter Textvorschlag + Erklärung
```

---

## 7.8 Anti-Patterns: Was Thema und Subtext zerstört

```
ANTI-PATTERN 1: Der Themen-Monolog
Figur hält einen langen Monolog über den Sinn des Lebens.
→ Leser merkt: Der Autor spricht. Immersion gebrochen.

ANTI-PATTERN 2: Zu viele Themen
Drei gleichwertige Themen = keines bekommt genug Raum.
→ LÖSUNG: Ein Hauptthema, max. zwei Subthemen

ANTI-PATTERN 3: Das unentwickelte Motiv
Symbol wird einmal eingeführt, einmal aufgelöst.
→ Kein echter Entwicklungsbogen, kein emotionaler Resonanzeffekt

ANTI-PATTERN 4: Die explizite Moral
Letzter Satz erklärt, was der Roman bedeutet.
→ "Und so lernte sie, dass Vertrauen das Wichtigste im Leben ist."
→ LÖSUNG: Letztes Bild zeigt es — Leser schließt selbst.

ANTI-PATTERN 5: Thema ohne Figur-Entscheidung
Das Thema hängt in der Luft, wird von niemandem embodyed.
→ LÖSUNG: Jede Thesen-Position braucht eine Figur, die sie lebt.
```

---

## 7.9 Output: Thema & Motiv-Objekte

```json
{
  "thema": {
    "frage": "",
    "antwort": "",
    "these_figur": "",
    "antithese_figur": "",
    "thema_in_plot": {},
    "themen_entscheidungen": []
  },
  "motiv_system": [
    {
      "id": "",
      "bezeichnung": "",
      "typ": "",
      "thema_bezug": "",
      "auftritte": [],
      "entwicklung": "",
      "payoff": ""
    }
  ]
}
```

**Nächster Schritt:** Zeitstruktur und Chronologie — wie der Roman mit Zeit umgeht. → Schritt 8

---

*Roman-Hub Anleitung | Schritt 7 von 8 | Version 1.0*
