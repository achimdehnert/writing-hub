# Schritt 1 — Grundontologie: Was ist ein Roman?

> **Für das LLM:** Bevor du eine einzige Zeile generierst, musst du verstehen, was ein Roman *systemisch* ist. Er ist kein langer Text — er ist ein Gefüge aus Ebenen, die sich gegenseitig bedingen und kontrollieren.

---

## 1.1 Die vier Systemebenen

Ein Roman existiert gleichzeitig auf vier Ebenen. Alle vier müssen im Hub als eigene Module existieren und miteinander kommunizieren:

```
┌─────────────────────────────────────────────────────────────┐
│  EBENE 4 — SUBSTRAT                                         │
│  Welt, Figuren, Regeln, Chronologie                         │
│  → Die unveränderliche Datenbank. Alles referenziert sie.   │
├─────────────────────────────────────────────────────────────┤
│  EBENE 1 — MAKROSTRUKTUR                                    │
│  Gesamtbogen, Akte, Wendepunkte, Arc                        │
│  → Der architektonische Plan. Legt alle Proportionen fest.  │
├─────────────────────────────────────────────────────────────┤
│  EBENE 2 — MESOSTRUKTUR                                     │
│  Kapitel, Szenen, Sequenzen                                 │
│  → Die Zimmer im Gebäude. Jede Einheit mit eigener Logik.   │
├─────────────────────────────────────────────────────────────┤
│  EBENE 3 — MIKROSTRUKTUR                                    │
│  Absätze, Dialoge, Sätze, Wortwahl                          │
│  → Die Oberfläche, die der Leser berührt.                   │
└─────────────────────────────────────────────────────────────┘
```

### Warum diese Trennung so wichtig ist

**Fehler, den LLMs typischerweise machen:** Sie generieren auf Mikroebene (Sätze schreiben), ohne die Makroebene (wo stehen wir im Akt?) oder das Substrat (was weiß diese Figur an diesem Punkt?) zu konsultieren.

Das Ergebnis: Texte, die gut klingen, aber dramaturgisch leer sind.

**Regel für den Hub:** Jede Generierungsanfrage muss mit dem Kontext aller vier Ebenen gefüttert werden.

---

## 1.2 Die Abhängigkeitshierarchie

Die Ebenen sind nicht gleichwertig. Sie haben eine klare Eltern-Kind-Beziehung:

```
SUBSTRAT
   └── definiert die Spielregeln für →
        MAKROSTRUKTUR
           └── legt den Rahmen für →
                MESOSTRUKTUR
                   └── bestimmt den Inhalt von →
                        MIKROSTRUKTUR
```

**Was das bedeutet:** Wenn du auf Mikroebene (ein Dialog) eine Entscheidung triffst, die der Makroebene widerspricht (der Protagonist kennt das Geheimnis noch nicht, aber du lässt ihn so reden, als ob er es wüsste) — dann ist der Roman beschädigt.

**LLM-Prüffrage vor jeder Generierung:**
> *"Verletzt dieser Output eine übergeordnete Ebene?"*

---

## 1.3 Was ein Roman NICHT ist

| Irrtum | Realität |
|--------|----------|
| Ein Roman ist ein langer Text | Ein Roman ist ein Systemgefüge |
| Kapitel sind beliebige Textabschnitte | Kapitel sind dramaturgische Einheiten mit eigener Logik |
| Figuren sind Beschreibungen | Figuren sind Funktionen + psychologische Systeme |
| Dialog ist, was Figuren sagen | Dialog ist das Sichtbarwerden von Subtext |
| Die Geschichte ist die Handlung | Die Geschichte ist die innere Transformation der Figur |

---

## 1.4 Die zwei Geschichten in jedem Roman

Jeder gut konstruierte Roman erzählt **immer zwei Geschichten gleichzeitig**:

```
ÄUSSERE GESCHICHTE (Plot)          INNERE GESCHICHTE (Arc)
─────────────────────────          ──────────────────────────
Was passiert?                      Was verändert sich in der Figur?
Ereignisse, Handlungen             Überzeugungen, Werte, Selbstbild
Sichtbar, dramatisch               Subtil, psychologisch
Treibt den Leser vorwärts          Gibt dem Roman Bedeutung
```

**Beispiel:**
- Äußere Geschichte: *Ein Detektiv sucht einen Mörder.*
- Innere Geschichte: *Ein Mann lernt, anderen Menschen wieder zu vertrauen.*

**LLM-Pflicht:** Beim Setup muss der Hub beide Geschichten explizit definieren und parallel verwalten.

---

## 1.5 Die drei Grundkonflikte

Ohne Konflikt gibt es keine Geschichte. Es gibt genau drei Quellen von Konflikt:

```
1. MENSCH gegen MENSCH (oder Institution)
   → Antagonist, Rivale, System, Gesellschaft
   → Sichtbarster Konflikt, treibt die äußere Geschichte

2. MENSCH gegen NATUR (oder Umwelt)
   → Katastrophe, Isolation, Überleben
   → Oft äußerer Rahmen

3. MENSCH gegen SICH SELBST
   → Innere Widersprüche, Trauma, falscher Glaube
   → Treibt die innere Geschichte, entscheidet den Charakter-Arc
```

**Die große Faustregel:** Der interessanteste Konflikt ist immer Typ 3, der sich durch Typ 1 ausdrückt.

---

## 1.6 Das Minimum Viable Novel (MVN)

Was braucht ein Roman **minimal**, damit er funktioniert?

```yaml
minimum_viable_novel:
  eine_figur_mit:
    - einem_wollen: string      # äußeres Ziel (konkret, erreichbar)
    - einem_brauchen: string    # innere Wahrheit (unbewusst)
    - einem_fehler: string      # psychologischer Riss
  ein_hindernis: string         # das verhindert das Wollen
  eine_entscheidung: string     # die den Fehler adressiert
  eine_konsequenz: string       # die zeigt, ob die Figur gewachsen ist
```

Alles andere — Nebenfiguren, Subplots, Weltenbau, Prosa — ist Elaboration dieses Kerns.

---

## 1.7 Arbeitsschritt für den LLM-Hub: Roman-Initialisierung

Wenn ein Nutzer einen Roman beginnen will, muss der Hub diese Fragen in dieser Reihenfolge klären:

### Phase A — Klärung der zwei Geschichten (2–3 Minuten)

```
PROMPT-TEMPLATE: Roman-Initialisierung Phase A

Du hilfst beim Aufbau eines Romans. Bevor wir irgendetwas schreiben,
klären wir die Grundstruktur.

Beantworte folgende Fragen präzise und knapp:

1. WER ist die Hauptfigur? (Name, Alter, Beruf, ein Satz Charakterisierung)
2. WAS will sie im Verlauf der Geschichte erreichen? (äußeres Ziel, konkret)
3. WAS braucht sie wirklich, ohne es zu wissen? (innere Wahrheit)
4. WAS hindert sie von außen? (Antagonist/Hindernis)
5. WAS hindert sie von innen? (ihr Fehler, ihre Wunde)
6. Wie ENDET die innere Reise? (Wachstum / Tragödie / Status quo)

Antworte im Format:
{
  "figur": "...",
  "aeusseres_ziel": "...",
  "innere_wahrheit": "...",
  "aeusseres_hindernis": "...",
  "inneres_hindernis": "...",
  "arc_ende": "positiv | negativ | flach"
}
```

### Phase B — Klärung des Genres und der Struktur

```
PROMPT-TEMPLATE: Roman-Initialisierung Phase B

Basierend auf den Antworten aus Phase A:

GENRE-ANALYSE:
Welches Genre passt am besten zu dieser Geschichte?
[ ] Thriller / Krimi
[ ] Literarischer Roman
[ ] Fantasy / Science-Fiction
[ ] Romance / Drama
[ ] Historischer Roman
[ ] Hybridform: ___

STRUKTUR-WAHL:
Welches Strukturmodell passt zu diesem Genre und dieser Geschichte?
[ ] Drei-Akte (empfohlen für Thriller, Romance, Mainstream)
[ ] Hero's Journey (empfohlen für Fantasy, Abenteuer)
[ ] Fünf-Akte (empfohlen für Tragödien, literarische Romane)
[ ] Vier-Akte (empfohlen für serielle Erzählungen)

TONALITÄT:
Beschreibe den Ton in 3 Adjektiven: ___
```

### Phase C — Validierung der Grundstruktur

```
PROMPT-TEMPLATE: Validierungs-Check

Überprüfe die Roman-Grundstruktur auf Konsistenz:

EINGABE: {roman_config_aus_phase_a_und_b}

PRÜFE:
1. Ist äußeres Ziel ≠ innere Wahrheit? (Falls gleich: kein Arc möglich)
2. Ist das innere Hindernis psychologisch glaubwürdig?
3. Passt das gewählte Strukturmodell zum Genre?
4. Ist das Arc-Ende konsistent mit dem Konflikttyp?

AUSGABE:
{
  "validierung": "ok | warnung | fehler",
  "probleme": ["..."],
  "empfehlungen": ["..."]
}
```

---

## 1.8 Zusammenfassung: Was das Hub-System in Schritt 1 anlegt

Nach Schritt 1 muss das Hub-System folgende Objekte persistent gespeichert haben:

```json
{
  "novel_core": {
    "id": "uuid",
    "titel": "",
    "genre": "",
    "struktur_modell": "",
    "ton": "",
    "aeussere_geschichte": "",
    "innere_geschichte": "",
    "hauptkonflikt_typ": "mensch_mensch | mensch_natur | mensch_selbst",
    "arc_richtung": "positiv | negativ | flach",
    "initialisiert_am": "datetime",
    "status": "setup"
  }
}
```

**Nächster Schritt:** Mit diesem Kern im Kontext wird die Makrostruktur ausgearbeitet. → Schritt 2

---

*Roman-Hub Anleitung | Schritt 1 von 8 | Version 1.0*
-e 

---


# Schritt 2 — Die Makrostruktur: Der dramaturgische Bogen

> **Für das LLM:** Die Makrostruktur ist der Bauplan des Hauses. Ohne ihn baust du Zimmer, die nirgendwo hinführen. Alles in Schritt 3–8 wird in diesem Rahmen positioniert.

---

## 2.1 Was die Makrostruktur leistet

Die Makrostruktur legt drei Dinge fest:

```
1. PROPORTION  → Wie viel Platz bekommt welcher Teil der Geschichte?
2. POSITION    → An welcher Stelle im Text passieren die Wendepunkte?
3. FUNKTION    → Was muss in jedem Abschnitt erreicht werden?
```

**Kritische LLM-Regel:** Die Makrostruktur wird einmal festgelegt und dann NICHT mehr verändert. Sie ist der Vertrag zwischen Autor und Leser.

---

## 2.2 Modell A — Das Drei-Akte-Modell

Das universellste und am häufigsten verwendete Modell. Basis für 80% aller erfolgreichen Romane und Filme.

### Die Proportionen

```
WORTANZAHL-BEISPIEL bei 90.000 Wörtern:
├── Akt I  (25%) → ca. 22.500 Wörter
├── Akt II (50%) → ca. 45.000 Wörter
└── Akt III(25%) → ca. 22.500 Wörter
```

### Die Wendepunkte und ihre Positionen

```
POSITION  NAME                     FUNKTION
────────  ───────────────────────  ──────────────────────────────────────
  1%      Opening Image            Erste Szene: zeigt den Status Quo
 10%      Inciting Incident        Das Ereignis, das alles verändert
 12%      Debate                   Figur zögert, den Ruf anzunehmen
 25%      Break into Act II        Figur betritt die neue Welt (kein Zurück)
 37%      B-Story begins           Nebenstrang / Liebesinteresse beginnt
 50%      Midpoint                 Scheinsieg oder Scheinniederlage
 62%      Bad Guys Close In        Alles wird schlimmer
 75%      All is Lost              Tiefpunkt: das Schlimmste passiert
 78%      Dark Night of the Soul   Figur gibt (fast) auf
 87%      Break into Act III       Neue Erkenntnis, letzter Entschluss
 98%      Climax                   Finale Konfrontation
100%      Resolution               Neue Normalwelt, veränderte Figur
```

### Die drei Akte im Detail

**AKT I — Setup (0–25%)**

```yaml
akt_1:
  funktion: "Zeige die Welt VOR der Veränderung"
  kernaufgaben:
    - normalwelt_etablieren: "Was ist der Alltag der Figur?"
    - figur_etablieren: "Wer ist sie? Was ist ihr Mangel?"
    - stakes_etablieren: "Was hat sie zu verlieren?"
    - inciting_incident: "Was wirft sie aus der Bahn?"
    - threshold: "Wann beschließt sie (oder wird gezwungen), zu handeln?"
  
  fehler_zu_vermeiden:
    - "Zu langer Setup ohne Spannung"
    - "Inciting Incident zu spät (nach 15%)"
    - "Figur passiv statt reaktiv"
  
  endet_mit: "Figur betritt eine neue, unbekannte Situation ohne Rückkehrmöglichkeit"
```

**AKT II — Konfrontation (25–75%)**

```yaml
akt_2:
  funktion: "Zeige den Kampf — äußerlich UND innerlich"
  kernaufgaben:
    - hindernisse_eskalieren: "Jedes Hindernis muss größer sein als das letzte"
    - midpoint_setzen: "Scheinbarer Erfolg → erhöht die Einsätze"
    - b_story_entwickeln: "Nebenstrang, der das Thema spiegelt"
    - innerer_conflict_intensivieren: "Der Fehler der Figur kommt immer mehr zum Vorschein"
    - all_is_lost: "Alles, was die Figur hatte, ist weg"
  
  struktur_innerhalb:
    erste_haelfte: "Figur lernt die neue Welt kennen, scheinbare Fortschritte"
    midpoint: "Wendepunkt — die Geschichte dreht sich"
    zweite_haelfte: "Figur verliert Kontrolle, Antagonist dominiert"
  
  endet_mit: "Dark Night of the Soul — Figur am Boden"
```

**AKT III — Auflösung (75–100%)**

```yaml
akt_3:
  funktion: "Zeige die Transformation — Figur wendet das Gelernte an"
  kernaufgaben:
    - neue_erkenntnis: "Figur versteht, was sie wirklich brauchte"
    - letzter_entschluss: "Aktive Entscheidung, nicht passive Rettung"
    - climax: "Finale Konfrontation — Figur muss ihren Fehler überwinden"
    - resolution: "Neue Normalwelt — aber verändert"
  
  fehler_zu_vermeiden:
    - "Figur wird gerettet, statt selbst zu handeln (Deus ex Machina)"
    - "Zu kurze Auflösung nach langem Climax"
    - "Neue Probleme einführen"
  
  endet_mit: "Closing Image — spiegelt Opening Image, zeigt die Veränderung"
```

---

## 2.3 Modell B — Die Hero's Journey (Campbell / Vogler)

12 Stationen. Geeignet für Fantasy, Mythos, Abenteuer. Tiefere archetypische Struktur.

```
STATION    POSITION  NAME                        INHALT
─────────  ────────  ──────────────────────────  ─────────────────────────────
    1         0–5%   Gewöhnliche Welt            Status quo des Helden
    2        5–10%   Der Ruf zum Abenteuer       Das Inciting Incident
    3       10–12%   Weigerung des Rufes         Held zögert, hat Angst
    4       12–15%   Begegnung mit dem Mentor    Mentor gibt Werkzeug/Rat
    5       15–25%   Überschreiten der Schwelle  Held betritt neue Welt
    6       25–45%   Tests, Verbündete, Feinde   Held lernt neue Regeln
    7       45–50%   Vordringen zur tiefsten     Vorbereitung auf große Prüfung
                     Höhle
    8       50–60%   Die entscheidende Prüfung   Held "stirbt" symbolisch
    9       60–70%   Belohnung                   Held gewinnt etwas
   10       70–80%   Der Rückweg                 Konsequenzen, Verfolgung
   11       80–95%   Die Auferstehung            Held wird transformiert
   12      95–100%   Rückkehr mit dem Elixier    Held bringt Weisheit heim
```

---

## 2.4 Modell C — Das Fünf-Akte-Modell (Shakespeare)

Für Tragödien und literarische Romane. Macht den Fall präziser.

```
AKT I   (0–20%)   Exposition     Einführung Welt und Figuren
AKT II  (20–40%)  Steigerung     Konflikt entwickelt sich
AKT III (40–60%)  Höhepunkt      Peripetie — der entscheidende Wendepunkt
AKT IV  (60–80%)  Retardation    Scheinbares Verzögern, Katastrophe naht
AKT V   (80–100%) Katastrophe    Tragischer Ausgang, Auflösung
```

---

## 2.5 Modell-Vergleichsmatrix

```
MODELL           | GENRE-FIT              | KOMPLEXITÄT | CHARAKTER-ARC
─────────────────┼────────────────────────┼─────────────┼───────────────
Drei-Akte        | Thriller, Romance,     | ★★☆☆☆       | Positiv/Negativ
                 | Mainstream             |             |
─────────────────┼────────────────────────┼─────────────┼───────────────
Hero's Journey   | Fantasy, Abenteuer,   | ★★★★☆       | Positiv
                 | Sci-Fi                 |             |
─────────────────┼────────────────────────┼─────────────┼───────────────
Fünf-Akte        | Literarisch, Tragödie  | ★★★☆☆       | Negativ/Komplex
─────────────────┼────────────────────────┼─────────────┼───────────────
Vier-Akte        | Seriell, TV-Romane     | ★★★☆☆       | Positiv/Flach
─────────────────┼────────────────────────┼─────────────┼───────────────
Kishotenketsu    | Literarisch, Japanisch | ★★★★★       | Transformation
```

---

## 2.6 Der Charakter-Arc: Drei Typen

Der Charakter-Arc ist die innere Reise parallel zur äußeren Handlung:

### Positiver Arc (häufigster Typ)
```
ANFANG: Figur glaubt an eine FALSCHE WAHRHEIT
        → "Ich brauche niemanden"
MITTE:  Die Geschichte stellt diese Überzeugung in Frage
ENDE:   Figur akzeptiert die WAHRE WAHRHEIT
        → "Stärke kommt durch Verbindung mit anderen"
```

### Negativer Arc (Tragödie)
```
ANFANG: Figur könnte die Wahrheit annehmen
MITTE:  Die Geschichte bietet ihr die Chance
ENDE:   Figur VERWEIGERT die Wahrheit und wird zerstört
```

### Flacher Arc (Weltveränderung)
```
ANFANG: Figur hat bereits die Wahrheit
MITTE:  Figur konfrontiert eine Welt, die sie nicht teilt
ENDE:   Figur verändert die Welt (statt sich zu verändern)
        → Superman, James Bond, Sherlock Holmes
```

---

## 2.7 Prompt-Templates für Makrostruktur-Planung

### Template M-1: Akt-Struktur generieren

```
SYSTEM:
Du bist ein erfahrener Dramaturg. Du planst die Makrostruktur eines Romans.
Antworte ausschließlich als valides JSON.

USER:
Erstelle die vollständige Akt-Struktur für diesen Roman:

ROMAN-KERN:
- Äußere Geschichte: {aeussere_geschichte}
- Innere Geschichte: {innere_geschichte}
- Genre: {genre}
- Strukturmodell: {struktur_modell}
- Zielwortanzahl: {wortanzahl}

Erstelle für jeden Wendepunkt:
- name: Bezeichnung des Wendepunkts
- position_prozent: Position im Roman (0–100)
- position_wort: Entsprechende Wortzahl
- was_passiert: Kurze Beschreibung des Ereignisses (2–3 Sätze)
- figur_zustand_innen: Innerer Zustand der Figur
- figur_zustand_aussen: Äußere Situation der Figur
- funktion: Dramaturgische Funktion dieses Wendepunkts

FORMAT:
{
  "struktur_modell": "...",
  "wendepunkte": [
    {
      "name": "...",
      "position_prozent": 0,
      "position_wort": 0,
      "was_passiert": "...",
      "figur_zustand_innen": "...",
      "figur_zustand_aussen": "...",
      "funktion": "..."
    }
  ]
}
```

### Template M-2: Akt-Inhalts-Planung

```
SYSTEM:
Du planst den Inhalt eines einzelnen Aktes. Antworte als JSON.

USER:
Plane AKT {akt_nummer} für den Roman "{titel}".

KONTEXT:
- Strukturmodell: {modell}
- Vorangehende Wendepunkte: {vorherige_wendepunkte}
- Figur-Zustand zu Beginn: {figur_zustand_anfang}
- Figur-Zustand am Ende: {figur_zustand_ende}
- Thema: {thema}
- Ton: {ton}

AUFGABE:
Definiere für diesen Akt:
1. kernaufgaben: Liste von 3–5 dramaturgischen Aufgaben
2. kapitel_anzahl: Empfohlene Kapitelanzahl
3. hauptereignisse: Liste der 3–4 wichtigsten Ereignisse
4. innere_entwicklung: Wie verändert sich die Figur innerlich?
5. subplots: Welche Nebenhandlungen sind aktiv?
6. spannungs_ziel: Spannungsintensität am Ende (1–10)

FORMAT: JSON
```

### Template M-3: Charakter-Arc validieren

```
SYSTEM:
Du prüfst, ob ein Charakter-Arc dramaturgisch funktioniert.

USER:
Validiere diesen Charakter-Arc:

FIGUR: {figur_name}
FALSCHE_ÜBERZEUGUNG: {falsche_wahrheit}
WAHRE_ERKENNTNIS: {wahre_wahrheit}
ARC_TYP: {positiv | negativ | flach}

WENDEPUNKTE:
- Akt I Ende: {figur_zustand_akt1}
- Midpoint: {figur_zustand_midpoint}
- Dark Night: {figur_zustand_dark_night}
- Climax: {figur_zustand_climax}
- Ende: {figur_zustand_ende}

PRÜFE:
1. Ist die Entwicklung organisch und glaubwürdig?
2. Gibt es einen klaren Moment der Erkenntnis?
3. Entscheidet die Figur AKTIV (kein Deus ex Machina)?
4. Entspricht das Ende dem gewählten Arc-Typ?

AUSGABE:
{
  "arc_funktioniert": true/false,
  "probleme": ["..."],
  "empfehlungen": ["..."],
  "staerksten_momente": ["..."]
}
```

---

## 2.8 Arbeitsschritte für den Hub: Makrostruktur aufbauen

**Schritt 2.1 — Strukturmodell wählen** (basiert auf Schritt 1 Output)
→ Nutze Template M-Auswahl-Matrix oben

**Schritt 2.2 — Wendepunkte generieren**
→ Nutze Template M-1 mit Roman-Kern aus Schritt 1

**Schritt 2.3 — Akt-Inhalte planen**
→ Nutze Template M-2 für jeden Akt einzeln

**Schritt 2.4 — Charakter-Arc validieren**
→ Nutze Template M-3

**Schritt 2.5 — Konsistenz-Check**

```
PRÜFFRAGEN:
✓ Sind alle Wendepunkte an den richtigen Positionen?
✓ Eskaliert jeder Akt die Einsätze gegenüber dem vorherigen?
✓ Ist der Climax der logische Höhepunkt aller Konflikte?
✓ Löst das Ende ALLE wesentlichen Fragen auf?
✓ Spiegelt das Ending Image das Opening Image?
```

---

## 2.9 Output: Makrostruktur-Objekt (persistieren)

```json
{
  "makrostruktur": {
    "modell": "drei_akte | heros_journey | fuenf_akte",
    "gesamt_wortanzahl": 0,
    "arc_typ": "positiv | negativ | flach",
    "falsche_wahrheit": "",
    "wahre_wahrheit": "",
    "wendepunkte": [
      {
        "name": "",
        "position_prozent": 0,
        "position_wort": 0,
        "was_passiert": "",
        "figur_innen": "",
        "figur_aussen": "",
        "funktion": ""
      }
    ],
    "akte": [
      {
        "nummer": 1,
        "von_prozent": 0,
        "bis_prozent": 25,
        "kernaufgaben": [],
        "hauptereignisse": [],
        "spannungsziel": 4
      }
    ]
  }
}
```

**Nächster Schritt:** Mit dieser Makrostruktur als Rahmen wird das Substrat aufgebaut — Welt und Figuren. → Schritt 3

---

*Roman-Hub Anleitung | Schritt 2 von 8 | Version 1.0*
-e 

---


# Schritt 3 — Das Substrat: Welt & Figuren

> **Für das LLM:** Das Substrat ist die Datenbank des Romans. Jede Szene, jeder Dialog, jede Entscheidung muss gegen das Substrat geprüft werden. Konsistenz ist hier nicht optional — sie ist die Grundbedingung für Glaubwürdigkeit.

---

## 3.1 Was das Substrat enthält

```
SUBSTRAT
├── WORLD BIBLE          → Wo und wann spielt die Geschichte?
│   ├── Setting          → Ort, Zeit, Atmosphäre
│   ├── Regeln           → Was gilt in dieser Welt?
│   └── Geographie       → Wo sind die wichtigsten Orte?
│
└── FIGUREN-SYSTEM       → Wer bevölkert die Geschichte?
    ├── Protagonist       → Die Hauptfigur mit Arc
    ├── Antagonist        → Die Gegenkraft
    ├── Supporting Cast   → Figuren mit dramaturgischer Funktion
    └── Figurenbeziehungen → Wer kennt wen, wer weiß was?
```

---

## 3.2 Die World Bible

Die World Bible definiert alles, was UNABHÄNGIG von den Figuren gilt.

### 3.2.1 Das Setting

```yaml
setting:
  name: string                    # "Berlin, Winter 1989"
  ort: string                     # Primärer Schauplatz
  zeit: string                    # Historisch, gegenwärtig, fiktiv
  atmosphaere: string             # "kalt, paranoid, untergründig"
  
  schauplaetze:                   # Wichtigste Orte mit Funktion
    - name: string
      beschreibung: string        # Wie sieht es aus, wie riecht es?
      atmosphaere: string
      assoziiert_mit: string      # Welcher Figur / welchem Thema?
      szenen_hier: []             # Wird später befüllt
```

**LLM-Regel:** Jeder Schauplatz muss eine emotionale Qualität haben. Ein Ort ist nie neutral — er drückt immer das Innenleben der Figur oder das Thema aus.

### 3.2.2 Weltregeln

```yaml
welt_regeln:
  physikalisch: []          # Was gilt physisch? (irrelevant in Realismus)
  sozial:                   # Soziale Normen und Hierarchien
    - "Frauen über 40 sind in dieser Firma unsichtbar"
    - "Loyalität zur Familie ist über Gesetz"
  informationsstand:        # Wer weiß was (KRITISCH für Spannung)
    - figur: string
      weiss: []
      weiss_nicht: []
  technologie: string       # Relevant für Setting
  macht_strukturen: []      # Wer hat Macht? Über wen?
```

**Warum Informationsstand?** Spannung entsteht aus Informations-Asymmetrie. Der Hub muss für jede Szene wissen, was jede Figur zu diesem Zeitpunkt weiß — sonst schreibt das LLM Widersprüche.

### 3.2.3 Ton und Atmosphäre

```yaml
ton:
  grundstimmung: string        # "bedrohlich, klaustrophobisch"
  genre_ton: string            # "Noir", "magischer Realismus"
  humor_level: string          # "keiner | leicht | durchgehend"
  gewalt_level: string         # "angedeutet | direkt | grafisch"
  erotik_level: string         # "keine | angedeutet | explizit"
  
  stil_verbote: []             # Was passt NICHT zu diesem Roman?
  stil_gebote: []              # Was MUSS immer präsent sein?
```

---

## 3.3 Das Figurensystem

### 3.3.1 Der Protagonist — Das vollständige Figur-Objekt

```yaml
protagonist:
  # ÄUSSERES
  name: string
  alter: int
  beruf: string
  aussehen: string             # Knapp, 2–3 prägende Merkmale
  stimme: string               # Wie klingt sie/er? Wie spricht sie/er?
  
  # DAS WOLLEN vs. DAS BRAUCHEN (kritischste Unterscheidung)
  want: string                 # Äußeres, bewusstes Ziel
                               # → "Den Mörder finden"
  need: string                 # Innere, unbewusste Wahrheit
                               # → "Lernen, Kontrolle loszulassen"
  
  # DER FEHLER (flaw) — treibt die Geschichte
  flaw: string                 # Der psychologische Riss
                               # → "Unfähigkeit, anderen zu vertrauen"
  
  # DER GEIST (ghost) — Ursprung des Fehlers
  ghost: string                # Das Trauma aus der Vergangenheit
                               # → "Als Kind von Vater verraten"
  
  # DER ARC
  arc_typ: positiv | negativ | flach
  falsche_wahrheit_anfang: string   # Was glaubt sie am Anfang?
  wahre_erkenntnis_ende: string     # Was versteht sie am Ende?
  
  # DIE STIMME (für Mikrostruktur)
  sprech_stil: string          # Kurze Sätze? Metaphern? Ironie?
  denk_muster: string          # Wie verarbeitet sie Dinge?
  weltanschauung: string       # Ihre Linse auf die Welt
  
  # INFORMATIONSSTAND
  weiss_am_anfang: []
  lernt_wann: []               # {info: string, wann: string}
```

### 3.3.2 Das Want/Need-Prinzip — vertieft

Dies ist der häufigste LLM-Fehler: Want und Need gleichzusetzen.

```
BEISPIELE:
┌─────────────────────────────────────────────────────────┐
│ FIGUR          │ WANT (bewusst)     │ NEED (unbewusst)   │
├─────────────────────────────────────────────────────────┤
│ Detektiv       │ Den Fall lösen     │ Vergeben können    │
│ Politikerin    │ Die Wahl gewinnen  │ Authentisch sein   │
│ Vater          │ Familie schützen   │ Loslassen lernen   │
│ Künstlerin     │ Ruhm erlangen      │ Sich selbst lieben │
└─────────────────────────────────────────────────────────┘
```

**LLM-Regel:** Die Figur tut alles, um ihr `want` zu erreichen. Die Geschichte zwingt sie dabei, sich mit ihrem `need` auseinanderzusetzen. Am Climax muss sie eine Entscheidung treffen, die want und need in Konflikt bringt.

### 3.3.3 Der Antagonist

```yaml
antagonist:
  name: string
  typ: person | system | natur | inneres_selbst | kombination
  
  motivation: string           # Was will der Antagonist? (Er hat RECHT in seiner Welt)
  weltanschauung: string       # Warum glaubt er, das Richtige zu tun?
  
  spiegel_zu_protagonist: string  # Was zeigt er, was der Protagonist sein KÖNNTE?
  gemeinsamkeit: string           # Was teilen sie? (macht den Konflikt tiefer)
  
  machtbasis: string           # Woher kommt seine Kraft/Bedrohung?
  schwaeche: string            # Was könnte ihn stoppen?
  
  informationsvorsprung: string  # Was weiß er, was der Protagonist nicht weiß?
```

**Kritisches Prinzip:** Der Antagonist denkt nicht, er sei böse. Er hat eine Logik, die in seiner Welt Sinn ergibt. Einfache Bösewichte sind das Zeichen eines schwachen Romans.

### 3.3.4 Archetypen der Nebenfiguren

```yaml
supporting_cast:
  - name: string
    archetyp: mentor | ally | trickster | love_interest | herald | threshold_guardian | shapeshifter | shadow
    funktion: string             # Was tut diese Figur für den Protagonisten-Arc?
    beziehung: string            # Wie kennen sie sich?
    
    # Ihre eigene kleine Geschichte
    eigenes_want: string
    konflikt_mit_protagonist: string   # Kein Nebenstrang ohne Reibung
    
    # Informationsstand
    weiss: []
    weiss_nicht: []
```

**Archetyp-Funktionen:**

| Archetyp | Funktion | Beispiele |
|----------|----------|-----------|
| Mentor | Gibt Werkzeug/Weisheit | Dumbledore, Yoda, der alte Detective |
| Ally | Spiegel und Unterstützung | Freund, Partner |
| Trickster | Humor, Dekonstruktion | Comic Relief, Jokerfigur |
| Love Interest | Verkörpert das Need | Bringt Nähe, die der Protagonist fürchtet |
| Herald | Bringt den Ruf | Der Bote des Inciting Incident |
| Threshold Guardian | Testet die Entschlossenheit | Türsteher der neuen Welt |
| Shapeshifter | Zweifelt Loyalität an | Doppelgänger, Maulwurf |
| Shadow | Spiegelt den Protagonisten | Was wäre er, wenn er anders gewählt hätte |

---

## 3.4 Figurenbeziehungen

```yaml
beziehungs_matrix:
  - figur_a: string
    figur_b: string
    beziehungstyp: string         # "Mentor-Schüler", "Rivalen", "heimliche Geliebte"
    machtverhaeltnis: string      # Wer hat mehr Macht?
    vertrauen: 1-10
    gemeinsames_geheimnis: string  # Falls vorhanden
    konflikt_potential: string
    entwicklung_ueber_roman: string  # Wie verändert sich die Beziehung?
```

---

## 3.5 Prompt-Templates für das Substrat

### Template S-1: Protagonist vollständig entwickeln

```
SYSTEM:
Du entwickelst einen Romanprotagonisten. Antworte ausschließlich als JSON.
Achte darauf, dass want ≠ need, und dass ghost den flaw psychologisch erklärt.

USER:
Entwickle den Protagonisten für diesen Roman:

ROMAN-KERN: {roman_kern_aus_schritt_1}
MAKROSTRUKTUR: {arc_typ, falsche_wahrheit, wahre_erkenntnis}
GENRE: {genre}
TON: {ton}

Erstelle ein vollständiges Figur-Objekt. Beachte:
1. Der ghost muss den flaw kausal erklären
2. Das want muss aktiv verfolgbar sein (konkretes Ziel)
3. Das need muss das Gegenteil oder die Ergänzung des flaws sein
4. Die Stimme muss zum Genre und Ton passen

FORMAT: Vollständiges protagonist-YAML-Objekt
```

### Template S-2: Antagonist entwickeln

```
SYSTEM:
Du entwickelst den Antagonisten. Er glaubt, das Richtige zu tun.
Antworte als JSON.

USER:
Entwickle den Antagonisten passend zu diesem Protagonisten:

PROTAGONIST: {protagonist_objekt}
GENRE: {genre}
THEMA: {thema}

ANFORDERUNGEN:
1. Motivation muss aus eigener Perspektive logisch sein
2. Der Antagonist muss den Protagonisten SPIEGELN
3. Sie müssen eine tiefe Gemeinsamkeit teilen
4. Seine Machtbasis muss zur äußeren Geschichte passen

FORMAT: Vollständiges antagonist-Objekt
```

### Template S-3: World Bible generieren

```
SYSTEM:
Du erstellst die World Bible für einen Roman. Sie ist die unveränderliche
Faktenbasis — alle späteren Szenen müssen konsistent mit ihr sein.

USER:
Erstelle die World Bible für diesen Roman:

SETTING: {setting_beschreibung}
GENRE: {genre}
THEMA: {thema}
TON: {ton}
PROTAGONIST: {protagonist_name_und_welt}

ERSTELLE:
1. Drei bis fünf Hauptschauplätze mit emotionaler Qualität
2. Fünf bis sieben Weltregeln (soziale Normen, Machtstrukturen)
3. Informationsstand aller Hauptfiguren zu Beginn
4. Tonalität mit konkreten Stil-Geboten und Verboten

FORMAT: world_bible-JSON-Objekt
```

### Template S-4: Nebenfiguren besetzen

```
SYSTEM:
Du besetzt Nebenfiguren nach dramaturgischer Funktion.
Jede Figur muss eine klare Funktion für den Protagonisten-Arc haben.
Antworte als JSON.

USER:
Erstelle das Supporting Cast für diesen Roman:

PROTAGONIST: {protagonist_objekt}
ANTAGONIST: {antagonist_objekt}
THEMA: {thema}
STRUKTUR_MODELL: {modell}

REGELN:
- Keine Figur ohne dramaturgische Funktion
- Jede Figur hat ein eigenes kleines Want
- Mindestens eine Figur verkörpert das Need des Protagonisten
- Keine zwei Figuren mit identischer Funktion

BENÖTIGTE ARCHETYPEN: Mentor, Ally, [genrespezifisch ergänzen]

FORMAT: supporting_cast-Array mit vollständigen Figur-Objekten
```

---

## 3.6 Konsistenz-Check: Das Substrat validieren

```
PROMPT-TEMPLATE: Substrat-Validierung

Validiere das Substrat-Paket auf interne Konsistenz:

SUBSTRAT: {vollstaendiges_substrat_objekt}

PRÜFE:
1. WANT/NEED: Sind diese klar verschieden?
2. GHOST/FLAW: Erklärt der Ghost den Flaw kausal?
3. ANTAGONIST-SPIEGEL: Spiegelt er den Protagonisten wirklich?
4. FIGUREN-FUNKTIONEN: Hat jede Figur eine einzigartige Funktion?
5. WELTREGELN: Sind sie konsistent untereinander?
6. INFORMATIONSSTAND: Gibt es Widersprüche?
7. TON: Ist die Weltbeschreibung tonalitätskonsistent?

AUSGABE:
{
  "substrat_valid": true/false,
  "kritische_fehler": ["..."],
  "warnungen": ["..."],
  "empfehlungen": ["..."]
}
```

---

## 3.7 Output: Substrat-Objekt (persistieren)

```json
{
  "substrat": {
    "world_bible": {
      "setting": {},
      "schauplaetze": [],
      "welt_regeln": {},
      "ton": {}
    },
    "figuren": {
      "protagonist": {},
      "antagonist": {},
      "supporting_cast": []
    },
    "beziehungs_matrix": [],
    "informations_stand_start": {}
  }
}
```

**Nächster Schritt:** Mit Substrat und Makrostruktur als Basis werden jetzt Kapitel und Szenen geplant. → Schritt 4

---

*Roman-Hub Anleitung | Schritt 3 von 8 | Version 1.0*
-e 

---


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
-e 

---


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
-e 

---


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
-e 

---


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
-e 

---


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
