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
