# ADR-150: Romanstruktur-Framework als 4-Ebenen-Datenmodell

**Status:** Accepted  
**Datum:** 2026-03-27  
**Kontext:** writing-hub @ achimdehnert/writing-hub

---

## Kontext

Ein Roman ist kein langer Text, sondern ein Systemgefüge aus vier Ebenen,
die sich gegenseitig bedingen und kontrollieren:

```
EBENE 4 — SUBSTRAT      Welt, Figuren, Regeln, Chronologie
EBENE 1 — MAKROSTRUKTUR Gesamtbogen, Akte, Wendepunkte, Arc
EBENE 2 — MESOSTRUKTUR  Kapitel, Szenen, Sequenzen
EBENE 3 — MIKROSTRUKTUR Absätze, Dialoge, Sätze, Wortwahl
```

LLMs machen typischerweise folgenden Fehler: Sie generieren auf Mikroebene
(Sätze schreiben), ohne die Makroebene (wo stehen wir im Akt?) oder das
Substrat (was weiß diese Figur an diesem Punkt?) zu konsultieren.
Das Ergebnis: Texte, die gut klingen, aber dramaturgisch leer sind.

Eine Gap-Analyse gegen das 8-Schritte-Romanstruktur-Framework zeigt:
Der writing-hub hat bereits eine solide Basis, aber 8 systematische
Lücken in Dramaturgie, Erzählstimme, Thema/Motiv und Zeitstruktur.

### Gap-Übersicht (aus gap_analyse_writing_hub.md)

| Gap | Bereich | Prio |
|-----|---------|------|
| 1 | OutlineNode fehlen dramaturgische Szenen-Felder (Outcome, POV, Tension) | P1 |
| 2 | NarrativeVoice (Erzählperspektive) fehlt als DB-Objekt | P1 |
| 3 | ProjectCharacterLink fehlen want/need/flaw/ghost/arc | P1 |
| 4 | ProjectTheme & ProjectMotif fehlen | P1 |
| 5 | BookProject fehlen inner_story/outer_story/arc_direction | P1 |
| 6 | MasterTimeline fehlt (wer weiß was wann) | P2 |
| 7 | ForeshadowingEntry fehlt (Setup/Payoff-Tracking) | P2 |
| 8 | OutlineSequence fehlt (Mesostruktur-Zwischenebene) | P2 |

---

## Entscheidung

Das Datenmodell des writing-hub wird entlang des 4-Ebenen-Modells
strukturiert und erweitert. Jede Generierungsanfrage an das LLM
muss Kontext aus allen vier Ebenen erhalten.

### Ebenen-Mapping auf Django-Modelle

| Ebene | Konzept | Django-Modell |
|-------|---------|---------------|
| SUBSTRAT | Welt, Figuren, Orte | WeltenHub SSoT via `iil-weltenfw` |
| SUBSTRAT (lokal) | Dramaturgie-Felder | `ProjectCharacterLink` (want/need/flaw/ghost) |
| MAKROSTRUKTUR | Gesamtbogen, Akte | `OutlineFramework`, `OutlineFrameworkBeat` |
| MAKROSTRUKTUR | Wendepunkte | `ProjectTurningPoint` (neu, ADR-151) |
| MAKROSTRUKTUR | Innere/Äußere Geschichte | `BookProject.inner_story/outer_story` (neu) |
| MESOSTRUKTUR | Kapitel, Szenen | `OutlineNode` mit dramaturgischen Feldern (ADR-151) |
| MESOSTRUKTUR | Sequenzen | `OutlineSequence` (neu, Prio 2) |
| MIKROSTRUKTUR | Erzählstimme | `NarrativeVoice` (neu, ADR-151) |
| MIKROSTRUKTUR | Stil-DNA | `WritingStyle` (vorhanden) |

### Erweiterungen auf BookProject (Prio 1)

Folgende Felder werden auf `BookProject` ergänzt:

```python
inner_story = models.TextField(blank=True, default="")
outer_story  = models.TextField(blank=True, default="")
arc_direction = models.CharField(
    max_length=10,
    choices=[("positive","Positiv"),("negative","Negativ"),("flat","Flach")],
    blank=True, default=""
)
main_conflict_type = models.CharField(
    max_length=20,
    choices=[("mensch_mensch","Mensch gegen Mensch"),
             ("mensch_natur","Mensch gegen Natur"),
             ("mensch_selbst","Mensch gegen sich selbst")],
    blank=True, default=""
)
```

### LLM-Kontext-Regel

Jeder LLM-Prompt muss die folgende Kontext-Hierarchie enthalten:

```
System-Prompt:
  [1] NarrativeVoice (POV, Tempus, Distanz, Stil)
  [2] WritingStyle DNA (DO/DONT/Taboo)
  [3] BookProject.inner_story + outer_story
User-Prompt:
  [4] Aktiver OutlineFramework-Beat (Position im Akt)
  [5] OutlineNode (Szenen-Outcome, Tension, Emotion)
  [6] Relevante Figuren (want/need/flaw aus ProjectCharacterLink)
  [7] MasterTimeline-Position (wer weiß was)
```

---

## Begründung

- Die 4-Ebenen-Trennung ist kein akademisches Konzept, sondern ein technischer
  Constraint: ohne sie generiert das LLM inkonsistenten Text.
- WeltenHub bleibt SSoT für Welt/Figuren-Stammdaten (ADR-082) —
  Dramaturgie-Felder sind *lokal*, weil sie projekt-spezifisch sind.
- DB-getriebene Lookup-Tabellen statt Enum-Hardcoding ermöglichen
  Admin-Verwaltung ohne Code-Änderungen.

---

## Abgelehnte Alternativen

**Flat structure (alles auf BookProject):** Zu unübersichtlich, keine
saubere Ebenen-Trennung, LLM-Kontext wird unhandhabbar groß.

**WeltenHub-Erweiterung für Dramaturgie:** Dramaturgie ist projekt-spezifisch
(dieselbe Figur kann in Projekt A Protagonistin sein, in B Antagonistin).
Diese Daten gehören in den writing-hub, nicht in den SSoT.

---

## Konsequenzen

- Migrations: `0004_bookproject_story_fields` (klein, nur 4 neue Felder)
- Alle folgenden ADRs (151–154) bauen auf dieser Entscheidung auf
- LLM-Services müssen auf alle 4 Ebenen zugreifen — Service-Refactoring nötig
- `iil-promptfw`-Templates erhalten 7-Layer-Kontext-Struktur

---

**Referenzen:** ADR-082 (WeltenHub SSoT), ADR-083 (writing-hub Extraktion),  
`docs/adr/input/roman_hub_komplett.md`, `docs/adr/input/gap_analyse_writing_hub.md`
