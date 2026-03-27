# ADR-150: Romanstruktur-Framework als 4-Ebenen-Datenmodell

**Status:** Accepted  
**Datum:** 2026-03-27 (rev. 2026-03-27)  
**Kontext:** writing-hub @ achimdehnert/writing-hub

---

## Kontext

Ein Roman ist kein langer Text, sondern ein Systemgefüge aus vier Ebenen,
die sich gegenseitig bedingen und kontrollieren. Die Ebenen sind
**hierarchisch abhängig** — jede übergeordnete Ebene setzt Constraints für
alle untergeordneten:

```
┌─────────────────────────────────────────────────┐
│  SUBSTRAT                                        │
│  Welt, Figuren, Regeln, Chronologie              │
│  → Die unveränderliche Datenbank.                │
│  → Setzt die Spielregeln für alle anderen Ebenen.│
├─────────────────────────────────────────────────┤
│  MAKROSTRUKTUR                                   │
│  Gesamtbogen, Akte, Wendepunkte, Arc             │
│  → Der architektonische Plan.                    │
├─────────────────────────────────────────────────┤
│  MESOSTRUKTUR                                    │
│  Kapitel, Szenen, Sequenzen                      │
│  → Die Zimmer im Gebäude.                        │
├─────────────────────────────────────────────────┤
│  MIKROSTRUKTUR                                   │
│  Absätze, Dialoge, Sätze, Wortwahl               │
│  → Die Oberfläche, die der Leser berührt.        │
└─────────────────────────────────────────────────┘
```

**Abhängigkeitshierarchie:**
```
SUBSTRAT → definiert Regeln für → MAKROSTRUKTUR
           → legt Rahmen für → MESOSTRUKTUR
              → bestimmt Inhalt von → MIKROSTRUKTUR
```

LLMs machen typischerweise folgenden Fehler: Sie generieren auf Mikroebene
(Sätze schreiben), ohne die Makroebene (wo stehen wir im Akt?) oder das
Substrat (was weiß diese Figur an diesem Punkt?) zu konsultieren.
Das Ergebnis: Texte, die gut klingen, aber dramaturgisch leer sind.

Eine Gap-Analyse gegen das 8-Schritte-Romanstruktur-Framework zeigt:
Der writing-hub hat bereits eine solide Basis, aber 8 systematische
Lücken in Dramaturgie, Erzählstimme, Thema/Motiv und Zeitstruktur.

### Gap-Übersicht (aus gap_analyse_writing_hub.md)

| Gap | Bereich | Prio | ADR |
|-----|---------|------|-----|
| 1 | OutlineNode: Outcome, POV, Tension fehlen | P1 | ADR-151 |
| 2 | NarrativeVoice fehlt als DB-Objekt | P1 | ADR-151 |
| 3 | ProjectCharacterLink: want/need/flaw/ghost fehlen | P1 | ADR-152 |
| 4 | ProjectTheme & ProjectMotif fehlen | P1 | ADR-154 |
| 5 | BookProject: inner_story/outer_story/arc_direction fehlen | P1 | ADR-150 |
| 6 | MasterTimeline fehlt (Zeitkonsistenz) | P2 | ADR-156 |
| 7 | ForeshadowingEntry fehlt (Setup/Payoff-Tracking) | P2 | ADR-156 |
| 8 | OutlineSequence fehlt (Mesostruktur-Zwischenebene) | P2 | ADR-156 |
| — | Serien-Dramaturgie: SeriesArc/Kontinuität fehlen | P2 | ADR-155 |

---

## Entscheidung

Das Datenmodell des writing-hub wird entlang des 4-Ebenen-Modells
strukturiert und erweitert. Jede Generierungsanfrage an das LLM
muss Kontext aus allen vier Ebenen erhalten.

### Ebenen-Mapping auf Django-Modelle

| Ebene | Konzept | Django-Modell | ADR |
|-------|---------|---------------|-----|
| SUBSTRAT | Welt, Figuren, Orte | WeltenHub SSoT via `iil-weltenfw` | ADR-082 |
| SUBSTRAT (lokal) | Figur-Dramaturgie | `ProjectCharacterLink` (want/need/flaw/ghost) | ADR-152 |
| SUBSTRAT (lokal) | Zeitkonsistenz | `CharacterKnowledgeState` | ADR-156 |
| MAKROSTRUKTUR | Grundontologie | `BookProject` (inner/outer story, arc) | ADR-150 |
| MAKROSTRUKTUR | Akt-Struktur | `OutlineFramework`, `OutlineFrameworkBeat` | bestehend |
| MAKROSTRUKTUR | Wendepunkte | `ProjectTurningPoint` | ADR-151 |
| MAKROSTRUKTUR | Thema & Motiv | `ProjectTheme`, `ProjectMotif` | ADR-154 |
| MAKROSTRUKTUR | Foreshadowing | `ForeshadowingEntry` | ADR-156 |
| MESOSTRUKTUR | Kapitel, Szenen | `OutlineNode` + dramaturgische Felder | ADR-151 |
| MESOSTRUKTUR | Sequenzen | `OutlineSequence` | ADR-156 |
| MIKROSTRUKTUR | Erzählstimme | `NarrativeVoice` | ADR-151 |
| MIKROSTRUKTUR | Stil-DNA | `WritingStyle` (vorhanden) | — |

### Erweiterungen auf BookProject (Gap 5, Prio 1)

```python
# apps/projects/models.py — neue Felder auf BookProject

# Zwei-Geschichten-Struktur (Schritt 1 des Romanstruktur-Frameworks)
inner_story = models.TextField(
    blank=True, default="",
    verbose_name="Innere Geschichte",
    help_text="Die psychologische Transformation der Hauptfigur. "
              "Antwortet auf: Was verändert sich innerlich?",
)
outer_story = models.TextField(
    blank=True, default="",
    verbose_name="Äußere Geschichte",
    help_text="Der Plot — Was passiert? Konkrete Ereignisse und Handlungen.",
)

# Arc-Richtung — als CharField (keine Lookup-Tabelle nötig: 3 Werte,
# semantisch fest definiert durch das Romanstruktur-Framework)
arc_direction = models.CharField(
    max_length=10,
    choices=[
        ("positive", "Positiver Arc — Figur wächst"),
        ("negative", "Negativer Arc — Figur scheitert/verweigert"),
        ("flat",     "Flacher Arc — Figur verändert die Welt"),
    ],
    blank=True, default="",
    verbose_name="Arc-Richtung",
)

# Konflikttyp (Schritt 1.5 — drei strukturelle Grundkonflikte)
main_conflict_type = models.CharField(
    max_length=20,
    choices=[
        ("mensch_mensch", "Mensch gegen Mensch / Institution"),
        ("mensch_natur",  "Mensch gegen Natur / Umwelt"),
        ("mensch_selbst", "Mensch gegen sich selbst"),
    ],
    blank=True, default="",
    verbose_name="Hauptkonflikt-Typ",
    help_text="Der interessanteste Konflikt ist immer Typ 3 (ausgedrückt durch Typ 1).",
)
```

**Begründung `arc_direction` als CharField:** Die drei Arc-Richtungen sind
konzeptionell unveränderliche Kategorien des Romanstruktur-Frameworks
(Robert McKee / John Truby) — keine Admin-verwaltbaren Lookup-Werte.
Lookup-Tabellen sind für inhaltlich erweiterbare Domänen (Emotionen,
POV-Typen) sinnvoll, nicht für strukturell fixierte 3er-Taxonomien.

### LLM-Kontext-Regel (9-Layer-Hierarchie)

Jeder LLM-Prompt muss die folgende Kontext-Hierarchie einhalten.
Layer 1–3 kommen in den **System-Prompt**, Layer 4–9 in den **User-Prompt**:

```
[SYSTEM]
  Layer 1 — NarrativeVoice (POV, Tempus, Distanz, Satzrhythmus)
  Layer 2 — WritingStyle DNA (DO/DONT/Taboo/Signature Moves)
  Layer 3 — BookProject Grundontologie
             (inner_story, outer_story, arc_direction, main_conflict_type)

[USER]
  Layer 4 — Aktiver OutlineFramework-Beat (Position im Akt, Funktion)
  Layer 5 — Aktiver OutlineNode
             (Outcome, Tension, Emotion-Start/End, POV-Figur, sequel_note)
  Layer 6 — Relevante Figuren
             (want/need/flaw/ghost/false_belief aus ProjectCharacterLink)
  Layer 7 — ProjectTheme + aktive MotifAppearances dieser Szene
  Layer 8 — ForeshadowingEntries mit status=open (was wurde eingeführt
             aber noch nicht aufgelöst?)
  Layer 9 — CharacterKnowledgeState der beteiligten Figuren
             (wer weiß was an diesem Punkt?)
```

**Pflicht-Layers:** 1, 2, 3, 4, 5 — immer.  
**Bedingte Layers:** 6 (wenn Figuren aktiv), 7 (wenn Motiv-Check), 8 (wenn Szene Setup/Payoff), 9 (wenn Dialog-Generierung).

---

## Begründung

- Die 4-Ebenen-Trennung ist kein akademisches Konzept, sondern ein technischer
  Constraint: ohne sie generiert das LLM dramaturgisch inkonsistenten Text.
- WeltenHub bleibt SSoT für Welt/Figuren-Stammdaten (ADR-082) —
  Dramaturgie-Felder sind *lokal*, weil sie projekt-spezifisch sind.
- `arc_direction` als CharField (nicht Lookup): semantisch fixiert durch
  das Framework, nicht admin-verwaltbar.
- 9-Layer-Kontext statt 7: `ProjectTheme` (Layer 7) und `ForeshadowingEntry`
  (Layer 8) wurden als Missing Links identifiziert — ohne sie fehlt dem LLM
  die thematische Dimension beim Schreiben einzelner Szenen.

---

## Abgelehnte Alternativen

**Flat structure (alles auf BookProject):** Zu unübersichtlich, keine
saubere Ebenen-Trennung, LLM-Kontext wird unhandhabbar groß.

**WeltenHub-Erweiterung für Dramaturgie:** Dramaturgie ist projekt-spezifisch
(dieselbe Figur kann in Projekt A Protagonistin sein, in B Antagonistin).
Diese Daten gehören in den writing-hub, nicht in den SSoT.

**`arc_direction` als FK auf Lookup:** Overkill — 3 fixierte Kategorien
aus einem Standardwerk, keine Erweiterbarkeit durch den Admin sinnvoll.

---

## Konsequenzen

- Migration `projects/0004_bookproject_story_fields` (4 neue Felder)
- Alle folgenden ADRs (151–156) bauen auf dieser Entscheidung auf
- LLM-Services müssen auf alle 4 Ebenen zugreifen — Service-Refactoring
- `iil-promptfw`-Templates erhalten 9-Layer-Kontext-Struktur
- Layer 8 (Foreshadowing) und Layer 9 (KnowledgeState) sind optional —
  Services die sie nicht benötigen überspringen sie (kein Breaking Change)

---

**Referenzen:** ADR-082 (WeltenHub SSoT), ADR-083 (writing-hub Extraktion),  
ADR-151, ADR-152, ADR-154, ADR-155, ADR-156,  
`docs/adr/input/roman_hub_komplett.md`, `docs/adr/input/gap_analyse_writing_hub.md`,  
`docs/adr/input/schritt_01_grundontologie.md`, `docs/adr/input/schritt_02_makrostruktur.md`
