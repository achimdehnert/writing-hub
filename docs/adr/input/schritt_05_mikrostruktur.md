# Schritt 5 — Die Mikrostruktur: Prosa, Dialog & Stimme

> **Für das LLM:** Die Mikrostruktur ist das, was der Leser tatsächlich berührt. Hier entscheidet sich, ob der Roman lebt oder klingt wie eine Zusammenfassung. Die Makro- und Mesostruktur schaffen den Rahmen — die Mikrostruktur gibt ihm Fleisch, Blut und Stimme.

---

## 5.1 Die drei Säulen der Mikrostruktur

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   PROSA-TYPEN    │  │  DIALOG-SYSTEM   │  │  ERZÄHLSTIMME    │
│                  │  │                  │  │                  │
│ Action           │  │ Obertext         │  │ POV-Typ          │
│ Description      │  │ Subtext          │  │ Tempus           │
│ Thought          │  │ Funktion         │  │ Distanz          │
│ Dialogue         │  │ Beat/Pause       │  │ Stil-Marker      │
│ Transition       │  │ Non-verbal       │  │ Figur-Stimme     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 5.2 Die fünf Prosa-Typen

### 5.2.1 Action-Prosa

```
KENNZEICHEN:
- Aktive Verben, kurze Sätze
- Zeitlich präzise (A passiert, dann B, dann C)
- Keine Reflexion — nur Ereignis

TYPISCHE SATZSTRUKTUR:
"Er griff nach dem Telefon. Klingelte nicht. Er wählte noch einmal."

VERBOTEN:
- Passivkonstruktionen ("Das Telefon wurde gegriffen")
- Adverbien statt präziser Verben ("Er ging schnell" → "Er hetzte")
- Lange Einschübe während der Handlung

WANN VERWENDEN:
- Verfolgungsjagden
- Physische Auseinandersetzungen
- Entscheidungen unter Druck
- Wenn Tempo wichtig ist
```

### 5.2.2 Description-Prosa

```
KENNZEICHEN:
- Atmosphärisch, sensorisch (alle fünf Sinne)
- Immer gefiltert durch die Figur (nicht objektiv)
- Kurz halten — Leser wollen Handlung

TYPISCHE SATZSTRUKTUR:
"Die Bar roch nach altem Bier und Männerschweiß. Genau das, was sie
gesucht hatte: einen Ort, an dem man unbemerkt verschwand."

VERBOTEN:
- Rein dekorative Beschreibungen ohne Funktion
- Listen von Adjektiven
- Touristisch-neutrale Beschreibungen ("Der Bahnhof war groß und hatte
  viele Gleise")

FAUSTREGEL:
Jede Beschreibung muss entweder (a) die Atmosphäre verdichten,
(b) das Innenleben der Figur spiegeln oder (c) dramaturgisch relevant sein.
```

### 5.2.3 Thought-Prosa (Innerer Monolog)

```
KENNZEICHEN:
- Zeigt das Innenleben der Figur
- Kann in 3rd Person trotzdem intim sein (Free Indirect Discourse)
- Enthüllt Widersprüche zwischen Denken und Handeln

FREE INDIRECT DISCOURSE:
Narration und Gedanke verschmelzen ohne Anführungszeichen:
"Er sagte, es sei alles gut. Natürlich war es das. Es war immer alles gut,
bis es das plötzlich nicht mehr war."

VERBOTEN:
- Zu erklärende Gedanken ("Sie dachte, dass sie Angst hatte")
- Längere Thought-Passagen mitten in Action
- Wiederholung von Informationen, die der Leser schon hat

WANN VERWENDEN:
- Nach Disaster-Momenten (Sequel)
- Bei schwierigen Entscheidungen
- Um falsche Überzeugungen sichtbar zu machen
```

### 5.2.4 Dialogue-Prosa

Wird in 5.3 ausführlich behandelt.

### 5.2.5 Transition-Prosa

```
KENNZEICHEN:
- So kurz wie möglich
- Orientiert Leser in Zeit und Raum
- Trägt emotionale Qualität

STATT:
"Drei Tage später fuhr er mit dem Auto zur Polizeiwache, wo er ankam
und den Beamten nach dem Stand der Ermittlungen fragte."

BESSER:
"Drei Tage. Dann die Polizeiwache.
'Gibt es Neuigkeiten?' "

TECHNIKEN:
- Weißraum / Sternchen als Szenentrenner
- Erste Zeile der neuen Szene als implizite Transition
- Zeitmarker am Szenenanfang ("Drei Tage später.", "Die nächste Woche.")
```

---

## 5.3 Das Dialog-System

### 5.3.1 Die vier Funktionen von Dialog

Jede Dialogsequenz muss **mindestens zwei** dieser Funktionen erfüllen:

```
FUNKTION 1: CHARAKTER ENTHÜLLEN
→ Wie eine Figur spricht, zeigt, wer sie ist
→ Wortwahl, Satzlänge, was sie NICHT sagt

FUNKTION 2: KONFLIKT VORANBRINGEN
→ Dialog ist nie friedlich — immer eine Form von Kampf
→ Jemand will etwas, jemand anderes widersetzt sich

FUNKTION 3: INFORMATION TRANSPORTIEREN
→ Nur das Nötigste, ohne Info-Dump
→ Information muss durch Konflikt verdient sein

FUNKTION 4: SUBTEXT ERZEUGEN
→ Das Ungesagte ist lauter als das Gesagte
→ Figuren lügen, verbergen, vermeiden
```

### 5.3.2 Das Obertext/Subtext-Modell

```
OBERTEXT:   Was die Figur sagt
SUBTEXT:    Was sie meint

BEISPIEL:

OBERTEXT: "Das Essen war gut heute."
SUBTEXT:  "Ich bin froh, dass du wieder da bist, aber ich werde
           es dir nicht sagen, weil du mich verletzt hast."

REGEL: Der Subtext macht den Dialog lebendig.
       Wenn Obertext = Subtext, ist der Dialog flach.
```

### 5.3.3 Die Dialog-Beat-Struktur

```yaml
dialog_sequenz:
  - sprecher: "A"
    obertext: "Was du gesagt hast, war falsch."
    subtext: "Ich bin verletzt und will eine Entschuldigung."
    non_verbal: "schlägt Tasse auf den Tisch"
    
  - sprecher: "B"
    obertext: "Ich habe nur die Wahrheit gesagt."
    subtext: "Ich entschuldige mich nicht. Du weißt, dass ich recht habe."
    non_verbal: "dreht sich weg"
    
  - beat: "Stille. Drei Sekunden."
    funktion: "Machtverschiebung sichtbar machen"
    
  - sprecher: "A"
    obertext: "Vergiss es."
    subtext: "Damit ist das Gespräch beendet. Ich gebe auf."
    non_verbal: "nimmt Jacke"
```

### 5.3.4 Dialog-Verbote

```
VERBOTEN:
✗ "As-you-know-Bob" (Info-Dump durch Dialog)
  "Wie du weißt, bin ich seit 15 Jahren Detektiv in dieser Stadt..."
  → Figuren sagen sich nicht, was sie beide wissen

✗ Gleichförmige Sprechweise aller Figuren
  → Jede Figur muss eine einzigartige Stimme haben

✗ Dialog-Ettikettitis
  "sagte er", "fragte sie", "antwortete er"
  → Abwechslung durch Non-verbal-Beats

✗ Höflichkeits-Dialog
  "Hallo. Wie geht's? Gut, danke. Und dir?"
  → Einstieg immer mitten in den Konflikt

✗ Zu langer Monolog
  → Figuren reden nicht länger als 3–4 Sätze ohne Reaktion
```

### 5.3.5 Figurenstimmen-Differenzierung

Jede Figur braucht ein stimmliches Fingerabdruck-System:

```yaml
figur_stimme:
  name: string
  satz_laenge: kurz | mittel | lang | variabel
  wortschatz: einfach | gebildet | technisch | slang | regional
  metaphern: keine | selten | häufig | spezifisch_für_bereich
  schweigen: kommuniziert_durch_schweigen: bool
  lieblingsphrasen: []          # 2–3 charakteristische Ausdrücke
  vermeidet: []                 # Was sagt sie NIE?
  wenn_aufgeregt: string        # Wie verändert sich ihr Sprechen?
  wenn_luegt: string            # Non-verbale Signale
  spricht_in_fragen: bool       # Macht Aussagen als Fragen?
```

---

## 5.4 Die Erzählstimme

### 5.4.1 POV-Typen im Vergleich

```
ERSTE PERSON (Ich-Erzähler)
─────────────────────────────
+ Maximale Intimität
+ Starke Figur-Stimme
+ Unreliable Narrator möglich
- Wissensgrenze: Erzähler kann nur das wissen, was er erlebt
- Keine anderen Perspektiven (außer Rahmenerzählung)
→ Geeignet: Psychologische Thriller, Charakterstudien

DRITTE PERSON LIMITIERT
─────────────────────────────
+ Intimität + leichte Distanz möglich
+ Mehrere POVs in verschiedenen Kapiteln
+ Lesbarste Form für Mainstream
- Perspektivbrüche sind tödlich
→ Geeignet: Fast alles. Empfehlung für LLM-Generierung.

DRITTE PERSON OMNISZIENT
─────────────────────────────
+ Gott-Perspektive, kommentiert alles
+ Mehrere Köpfe gleichzeitig möglich
- Leicht altmodisch
- Emotionale Distanz zum Leser
→ Geeignet: Epische Romane, bestimmte literarische Formen

ZWEITE PERSON (Du-Form)
─────────────────────────────
+ Extrem ungewöhnlich, intensiv
- Schwer durchzuhalten
→ Geeignet: Experimentell, bestimmte Kurzprosa
```

### 5.4.2 Das Tempus-System

```
PRÄTERITUM (Vergangenheit):
"Er öffnete die Tür. Sie war leer."
→ Standard im deutschsprachigen Roman
→ Natürliche Distanz, aber trotzdem spannend möglich

PRÄSENS (Gegenwart):
"Er öffnet die Tür. Sie ist leer."
→ Erhöhte Unmittelbarkeit
→ Kann auf Dauer anstrengend werden
→ Geeignet: Thriller, Jugendliteratur, Literarischer Roman
```

### 5.4.3 Die narrative Distanz

```
NAH (close):
Wir sind fast im Kopf der Figur. Jede Wahrnehmung gefärbt.
"Das Licht in diesem Raum war falsch. Schon immer falsch gewesen.
 Sie hasste diese Art von Licht."

MITTEL (medium):
Wir beobachten die Figur mit leichtem Abstand.
"Sie betrat den Raum und runzelte die Stirn. Das Licht störte sie."

WEIT (distant):
Kamera-Perspektive. Wir sehen nur das Äußere.
"Sie betrat den Raum."
```

---

## 5.5 Show, don't tell — konkret umgesetzt

Dies ist die meistgenannte Regel und am schlechtesten erklärte.

```
TELL:
"Sie war wütend."

SHOW (Action):
"Sie schob den Stuhl so hart zurück, dass er umkippte."

SHOW (Körper):
"Ihre Hände zitterten. Nicht vor Kälte."

SHOW (Dialog):
"Ich bin vollkommen ruhig." Ihre Stimme war ein Flüstern.
 Das war nie gut.

SHOW (Wahrnehmung):
"Das Klackern seiner Tastatur klang plötzlich zu laut."
```

**LLM-Regel:** Wenn du ein Adjektiv oder Adverb verwendest, das einen emotionalen Zustand beschreibt, frage dich: Wie würde diese Emotion sich im Körper, im Verhalten, in der Wahrnehmung zeigen?

---

## 5.6 Prompt-Templates für Mikrostruktur

### Template MI-1: Szene schreiben (Haupttemplate)

```
SYSTEM:
Du bist ein erfahrener Romanautor. Du schreibst eine Szene im Stil des Romans.
Halte dich exakt an die Szenen-Ausarbeitung. Zeige, beschreibe nicht.
Bewahre strikt die POV-Perspektive. Kein Perspektivbruch.

USER:
Schreibe diese Szene:

SZENEN-AUSARBEITUNG: {szenen_objekt_aus_schritt_4_template_3}

NARRATIVE VOICE: {narrative_voice_objekt}
  - POV: {pov_typ}
  - Tempus: {tempus}
  - Distanz: {distanz}
  - POV-Figur-Stimme: {figur_stimme_objekt}

SUBSTRAT-KONTEXT:
  - Was weiß die POV-Figur jetzt: {informationsstand}
  - Beziehungen zu anwesenden Figuren: {beziehungen}
  - Schauplatz-Atmosphäre: {schauplatz_beschreibung}

THEMA & MOTIV:
  - Aktive Motive in dieser Szene: {motiv_einsatz}
  - Themen-Resonanz: {thema_beruehrung}

SCHREIB-ANWEISUNGEN:
  - Zielwortanzahl: ca. {wortanzahl} Wörter
  - Erster Satz muss sofort Spannung erzeugen
  - Emotionaler Deltawert: {emotion_anfang} → {emotion_ende}
  - Kein Info-Dump in den ersten 100 Wörtern
  - Mindestens ein nicht-verbaler Beat im Dialog
```

### Template MI-2: Dialog verfassen

```
SYSTEM:
Du schreibst einen Dialog-Ausschnitt. Jede Aussage hat einen Subtext.
Figuren sagen nie direkt, was sie meinen.

USER:
Schreibe einen Dialog für diese Situation:

KONTEXT:
- Figur A: {name}, Ziel im Dialog: {goal_a}, Verbirgt: {subtext_a}
- Figur B: {name}, Ziel im Dialog: {goal_b}, Verbirgt: {subtext_b}
- Situation: {situation}
- Machtbalance am Anfang: {macht_anfang}
- Machtbalance am Ende: {macht_ende}

FIGURENSTIMMEN:
- {figur_a_stimme}
- {figur_b_stimme}

ANFORDERUNGEN:
- Länge: ca. {austausch_anzahl} Austausche
- Mindestens 2 non-verbale Beats
- Eine Aussage, die offensichtlich nicht stimmt
- Dialog endet mit Machtverschiebung
- Keine Dialog-Ettiketten außer "sagte" (nur wenn nötig)
```

### Template MI-3: Schauplatz-Beschreibung (durch Figur-Wahrnehmung)

```
SYSTEM:
Du beschreibst einen Schauplatz durch die Wahrnehmung einer Figur.
Die Beschreibung spiegelt den emotionalen Zustand der Figur.
Maximal 150 Wörter.

USER:
Beschreibe diesen Schauplatz:

ORT: {schauplatz_name_und_basisinfo}
POV-FIGUR: {figur_name}
EMOTIONALER ZUSTAND DER FIGUR: {aktueller_zustand}
FUNKTION DER BESCHREIBUNG: {atmosphaere | bedrohung | zuflucht | ...}
MOTIV-EINSATZ: {motiv falls aktiv}

ANFORDERUNGEN:
- Mindestens drei Sinneswahrnehmungen
- Keine neutrale Touristenbeschreibung
- Die Wahrnehmung zeigt, wie sich die Figur fühlt
- Ein Detail, das dramaturgisch relevant ist
```

### Template MI-4: Innerer Monolog / Free Indirect Discourse

```
SYSTEM:
Du schreibst einen inneren Monolog im Stil des Free Indirect Discourse.
Narration und Gedanke verschmelzen. Keine "Sie dachte, dass..."-Konstruktionen.

USER:
Schreibe den inneren Monolog für diese Situation:

FIGUR: {name}
SITUATION: {was ist gerade passiert?}
FALSCHE ÜBERZEUGUNG DER FIGUR: {was glaubt sie fälschlicherweise?}
WAHRE WAHRHEIT: {was ahnt sie vielleicht?}
ENTSCHEIDUNG, DIE SIE TREFFEN MUSS: {decision}

STIMME DER FIGUR: {stimme_objekt}
LÄNGE: ca. {wortanzahl} Wörter

ANFORDERUNGEN:
- Zeige den Widerspruch zwischen Denken und Wissen
- Kein direkter Abschluss — sie entscheidet sich noch nicht vollständig
- Die falsche Überzeugung muss spürbar sein, ohne benannt zu werden
```

---

## 5.7 Qualitäts-Checks für Mikrostruktur

```
NACH DEM SCHREIBEN EINER SZENE:

PROSA-CHECK:
✓ Variiert die Satzlänge? (Monotone Rhythmik = einschläfernd)
✓ Überwiegen aktive Verben gegenüber Substantivkonstruktionen?
✓ Gibt es "leere" Adverbien, die ein besseres Verb ersetzen sollten?
✓ Sind Beschreibungen durch die Figur gefiltert (nicht objektiv)?

DIALOG-CHECK:
✓ Hat jede Aussage einen Subtext?
✓ Klingen alle Figuren unterschiedlich?
✓ Gibt es mindestens einen non-verbalen Beat?
✓ Vermeidet der Dialog Info-Dumps?

PERSPEKTIV-CHECK:
✓ Bleibt die POV strikt bei einer Figur?
✓ Weiß die Figur nur, was sie wissen kann?
✓ Ist die emotionale Wahrnehmung konsistent mit dem Figur-Zustand?

SHOW-CHECK:
✓ Gibt es versteckte "tell"-Konstruktionen? (Adjektive für Emotionen)
✓ Werden Emotionen durch Verhalten/Körper gezeigt?
```

---

## 5.8 Output: Mikrostruktur-Objekte

```json
{
  "narrative_voice": {
    "pov": "third_limited",
    "tempus": "praeteritum",
    "distanz": "nah",
    "stil_marker": {
      "satz_laenge": "variabel",
      "wortschatz": "gebildet",
      "imagery": "funktional",
      "ironie": "mild"
    }
  },
  "figur_stimmen": {
    "figur_id": {
      "satz_laenge": "kurz",
      "wortschatz": "direkt",
      "lieblingsphrasen": [],
      "vermeidet": []
    }
  }
}
```

**Nächster Schritt:** Die fertige Mikrostruktur wird in die Spannungsarchitektur eingebettet — wie die einzelnen Szenen und Kapitel zusammen den Gesamtspannungsbogen erzeugen. → Schritt 6

---

*Roman-Hub Anleitung | Schritt 5 von 8 | Version 1.0*
