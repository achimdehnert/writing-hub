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
