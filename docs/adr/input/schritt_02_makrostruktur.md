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
