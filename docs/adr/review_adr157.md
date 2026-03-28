# Review: ADR-157 — Antagonist-System, B-Story/Subplot-Tracking, DramaturgicHealthScore

**Reviewer:** Prof. Autor & Verleger  
**Datum:** 2026-03-28  
**Urteil:** ⚠️ **Revision erforderlich** — 7 Blocking Issues, 6 Minor Issues, 4 dramaturgische Anmerkungen

---

## Gesamtbewertung

Das ADR adressiert drei reale Lücken mit präziser verlegerischer Begründung.
Die Kernentscheidungen — `narrative_role` auf `ProjectCharacterLink`, `SubplotArc`
als eigenes Model, Health-Score als Service statt Model — sind architektonisch richtig
und konsequent mit dem bestehenden ADR-Stack (150–156).

**Stärken:** Antagonisten-Logik als Pflichtkonzept, Gewichtungsmodell 3/2/1,
Trennung Makrostruktur (SubplotArc) vs. Mesostruktur (OutlineSequence).

**Das ADR kann so nicht deployed werden.** Vier der sieben Blocking Issues
würden entweder Migrations-Fehler, LLM-Fehlinjektion oder stille Datenfehler
für nicht-Roman-Formate produzieren.

---

## BLOCKING ISSUES (müssen vor Merge behoben sein)

---

### B1 — `SubplotArc.thematic_mirror` fehlt `blank=True, default=""`

**Zeilen 201–205:**
```python
thematic_mirror = models.TextField(
    verbose_name="Thematischer Spiegel",
    help_text="...",
)
```

**Problem:** Kein `blank=True`. Alle anderen `TextField`-Felder im gesamten
writing-hub-Stack haben `blank=True, default=""` — das ist Plattform-Standard
(ADR-083). Ohne `blank=True` bricht jedes `ModelForm`, das dieses Feld nicht
explizit befüllt, mit `ValidationError`. Betrifft auch `SubplotArc`-Erstellung
via API und Admin.

**Fix:**
```python
thematic_mirror = models.TextField(
    blank=True, default="",
    verbose_name="Thematischer Spiegel",
    help_text="...",
)
```

---

### B2 — `SubplotArc` fehlt `updated_at`

Alle Models im Stack: `created_at` + `updated_at = models.DateTimeField(auto_now=True)`.
`SubplotArc` hat nur `created_at`. Betrifft Snapshot-Service, Admin-Ordering, API-ETags.

**Fix:** `updated_at = models.DateTimeField(auto_now=True)` ergänzen.

---

### B3 — Kein `content_type`-Guard im Health-Score

**Zeilen 274–422:** `compute_dramaturgic_health()` hat keine Abfrage
gegen `project.content_type` oder `ContentTypeProfile.has_dramatic_arc`.

**Konsequenz:** Ein Essay-Projekt (content_type="essay") bekommt:
- `"Kein Protagonist"` → FAIL (weight=3)
- `"Kein Antagonist"` → FAIL (weight=2)
- Score: ~20% — für ein vollständig ausgefülltes Essay-Projekt

Das macht den Health-Score für Essays und Sachbücher nicht nur nutzlos,
sondern aktiv irreführend. Mit `ContentTypeProfile` aus O5 existiert
bereits der richtige Ankerpunkt.

**Fix:**
```python
def compute_dramaturgic_health(project) -> DramaturgicHealthResult:
    # Format-Guard
    profile = getattr(
        getattr(project, "content_type_lookup", None), "profile", None
    )
    if profile and not profile.has_dramatic_arc:
        return _compute_essay_health(project)  # separater Pfad
    # ... bestehende Roman-Logik
```

Alternativ: `if project.content_type in ("essay", "nonfiction"): return early`
als kurzfristiger Fix bis `ContentTypeProfile` deployed ist.

---

### B4 — `Want ≠ Need`-Check: Logikfehler

**Zeilen 341–345:**
```python
passed=protagonist.want.strip() != protagonist.need.strip()
       if protagonist.want and protagonist.need else False,
```

**Problem:** Wenn `want` oder `need` noch leer ist (legitimerweise am Anfang),
gibt dieser Check `False` zurück. Damit schlägt ein Projekt mit leerem `want`
**zweimal** fehl — einmal beim "Want leer"-Check und einmal beim "Want ≠ Need"-Check.
Der Score wird doppelt bestraft für denselben Zustand.

Dramaturgisch ist der Check außerdem falsch formuliert: Er soll fehlschlagen wenn
`want == need`. Er soll neutral sein (oder gar nicht ausgeführt werden) wenn
eines der Felder leer ist — das fehlende Feld ist bereits ein anderer Check.

**Fix:**
```python
if protagonist.want and protagonist.need:
    want_neq_need = protagonist.want.strip() != protagonist.need.strip()
else:
    want_neq_need = True  # nicht prüfbar — anderen Check überlassen

checks.append(HealthCheck(
    label="Want ≠ Need",
    passed=want_neq_need,
    message="Want == Need — kein dramaturgischer Arc möglich.",
    weight=3,
))
```

---

### B5 — `carries_b_story` auf `ProjectCharacterLink` ist redundant zu `SubplotArc`

**Zeile 142–147** vs. **Zeilen 191–198:**

`ProjectCharacterLink.carries_b_story = True` und
`SubplotArc.carried_by_character_id` tracken dasselbe Konzept doppelt.

**Konsequenz:** Stille Inkonsistenz ist möglich:
- `carries_b_story=True` gesetzt, aber kein `SubplotArc` angelegt
- `SubplotArc` mit `carried_by_character_id=X` angelegt, aber `carries_b_story=False` bei X

Der Health-Check (Zeile 394) fragt `subplot_arcs.filter(story_label="b_story").exists()` —
ignoriert also `carries_b_story` komplett. Das macht `carries_b_story` wertlos.

**Entscheidung erforderlich:** Eines von beiden. Empfehlung:
`carries_b_story` auf `ProjectCharacterLink` entfernen. Die Information
ist vollständig in `SubplotArc.carried_by_character_id` + dem matching
`ProjectCharacterLink.narrative_role = "love_interest"/"mentor"` enthalten.
Eine Property `@property carries_b_story` auf `ProjectCharacterLink`
kann dies ableiten, ohne zu persistieren.

---

### B6 — `SubplotArc` hat keine OutlineNode-Verknüpfung

`begins_at_percent=37` und `ends_at_percent=95` sind gespeicherte Integer —
aber es gibt keine FK auf den `OutlineNode`, der den tatsächlichen B-Story-Beginn
markiert. Vergleich: `ForeshadowingEntry` hat `setup_node` und `payoff_node` FKs.

**Problem für LLM-Generierung:** Der Prompt-Layer (Teil D) kann sagen
"B-Story ist aktiv" — aber nicht "B-Story beginnt in Kapitel 7". Die Information
liegt zwar als Integer vor, ist aber nicht mit dem tatsächlichen Outline korreliert.
Bei einem Roman mit 24 Kapiteln ist "37%" ungefähr Kapitel 9 — aber ob Kapitel 9
oder 10 der erste B-Story-Moment ist, kann der Hub nicht entscheiden.

**Fix (minimal):**
```python
begins_at_node = models.ForeignKey(
    "projects.OutlineNode",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="subplot_begins",
)
ends_at_node = models.ForeignKey(
    "projects.OutlineNode",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="subplot_ends",
)
```
Die Prozent-Felder bleiben als Planungswerte — die FKs sind die operative Verknüpfung.

---

### B7 — `SubplotArc.begins_at_percent` erlaubt negative Werte

`SmallIntegerField` lässt `-1` durch. Plattform-Standard für
0–100-Prozent-Felder ist `PositiveSmallIntegerField` + Validators.

**Fix:**
```python
from django.core.validators import MinValueValidator, MaxValueValidator

begins_at_percent = models.PositiveSmallIntegerField(
    default=37,
    validators=[MinValueValidator(0), MaxValueValidator(100)],
)
ends_at_percent = models.PositiveSmallIntegerField(
    default=95,
    validators=[MinValueValidator(0), MaxValueValidator(100)],
)
```

Zusätzlich fehlt eine `clean()`-Methode, die `begins_at_percent < ends_at_percent`
erzwingt.

---

## MINOR ISSUES (sollten behoben werden, kein Deployment-Blocker)

---

### M1 — Kein Protagonist-Anzahl-Guard

`protagonist = project.projectcharacterlink_set.filter(narrative_role="protagonist").first()`
— gibt lautlos den ersten zurück, wenn zwei existieren. Ein Projekt mit zwei
Protagonisten (was vorkommen kann: Dual-POV-Roman) würde nur einen prüfen.

**Empfehlung:** Check ergänzen:
```python
protagonist_count = project.projectcharacterlink_set.filter(
    narrative_role="protagonist"
).count()
checks.append(HealthCheck(
    label="Genau ein Protagonist",
    passed=protagonist_count <= 2,  # max 2 für Dual-POV
    message=f"{protagonist_count} Protagonisten — ggf. narrative_role prüfen.",
    weight=1,
))
```

---

### M2 — Mehrere Antagonisten: Health-Check prüft nur ersten

Analog zu M1. Ein Krimi mit mehreren Verdächtigen, ein Fantasy-Roman mit
zwei Antagonisten — `.first()` evaluiert lautlos nur einen.

---

### M3 — `shadow`-Rolle vs. `antagonist`-Rolle: Überschneidung undokumentiert

`NARRATIVE_ROLES` enthält sowohl `antagonist` als auch `shadow`.
In der Literatur (Jung/Vogler) ist der Antagonist häufig AUCH der Schatten
des Protagonisten — das trifft auf viele der besten Romane zu
(Ahab/Moby Dick, Hannibal Lecter, Javert).

Das ADR erklärt nicht, wie eine Figur modelliert wird, die beide
Funktionen erfüllt. Empfehlung: In der Begründung einen Satz ergänzen,
z.B. "Für Figuren die Antagonist UND Schatten sind: `narrative_role='antagonist'`
setzen, `mirror_to_protagonist` befüllen — das ist die Schatten-Funktion."

---

### M4 — `information_advantage` für `antagonist_type='inner_self'` ergibt keinen Sinn

Wenn der Antagonist das innere Selbst ist (z.B. Sucht, Trauma, Persönlichkeitsspaltung),
hat er keinen `information_advantage` über den Protagonisten im klassischen Sinne.
Das Feld würde leer bleiben oder falsch befüllt werden.

**Empfehlung:** Im `help_text` klarstellen: "Nur relevant für externe Antagonisten
(`person`, `system`, `nature`)."

---

### M5 — `DramaturgicHealthResult` hat keine `top_issues`-Property

Ein Autor mit einem Score von 45% sieht eine Liste von 12–15 Checks.
Er braucht eine priorisierte Ansicht: "Das sind deine 3 wichtigsten Baustellen."

**Ergänzung:**
```python
@property
def top_issues(self) -> list[HealthCheck]:
    """Die 3 dringendsten fehlgeschlagenen Checks (nach Gewicht sortiert)."""
    return sorted(
        [c for c in self.checks if not c.passed],
        key=lambda c: -c.weight
    )[:3]
```

---

### M6 — `intersection_notes` als TextField verliert dramaturgischen Wert

Die Kreuzungspunkte zwischen B-Story und A-Story sind laut Framework
"typisch die emotionalen Hochpunkte" — sie sind strukturell relevant,
nicht nur notizartig. Als unstrukturierter Text können sie weder vom
Health-Score noch vom LLM-Prompt-Layer ausgewertet werden.

Mittelfristige Empfehlung: `JSONField` mit Liste von
`{"percent": 50, "description": "...", "node_id": "..."}` —
oder M2M zu `OutlineNode` (analog zu `MotifAppearance`).

---

## DRAMATURGISCHE ANMERKUNGEN

---

### D1 — 37%-Regel für B-Story ist Blake-Snyder-spezifisch, nicht universal

Der Default `begins_at_percent=37` und die Formulierung "typisch 37%" im `help_text`
sind korrekt für das **Save-the-Cat**-Framework. Im Drei-Akte-Modell (Aristoteles/McKee)
kann die B-Story erheblich früher beginnen — im literarischen Roman oft ab Seite 1.

**Empfehlung:** `help_text` anpassen:
"Empfehlung für Drei-Akte/Save-the-Cat: 37%. Im literarischen Roman und bei
Dual-POV-Strukturen oft früher."

---

### D2 — C-Story ohne Guidance ist eine Falle

`c_story` als Choice ist formal korrekt — sie existiert in langen Romanen
(Kriminalromane mit drei Handlungssträngen, epische Fantasy). Aber ohne
jede Guidance im ADR wird sie von Autoren in Kurzgeschichten und einfachen
Romanen verwendet, wo sie nicht hingehört.

**Empfehlung:** `c_story` mit einer `clean()`-Warnung versehen oder den
`help_text` erweitern: "C-Story nur für Romane > 80.000 Wörter mit etablierter
B-Story sinnvoll."

---

### D3 — Score 80% als "verlegerisch präsentierbar" — falsches Framing für frühe Phasen

Der Kommentar `"solid" # Verlegerisch präsentierbar` setzt den
Verlagseindruck mit der Planungsvollständigkeit gleich. Ein Autor,
der gerade die Struktur aufbaut, liest "20% — nur Grundstruktur"
als Urteil über die Qualität seines Werks.

**Empfehlung:** `level`-Labels anpassen:

```python
@property
def level(self) -> str:
    if self.score >= 80:
        return "solid"       # Struktur vollständig — bereit zum Schreiben
    if self.score >= 50:
        return "developing"  # Kernstruktur vorhanden — weiter ausbauen
    return "skeleton"        # Grundriss — MVN noch unvollständig
```

Und im Template kommunizieren: "Dieser Score misst Vollständigkeit der
Planung, nicht Qualität des Textes."

---

### D4 — LLM-Kontext-Layer für B-Story ist zu dünn

**Zeilen 444–446:**
```
B-STORY (falls aktiv in dieser Szene):
    {{ subplot.title }}: {{ subplot.thematic_mirror }}
```

Das reicht für das LLM nicht. Es fehlen:
- Wer trägt die B-Story? (Figurenname + Rolle)
- Ist die aktuelle Szene eine B-Story-Szene oder eine A-Story-Szene, die an die B-Story grenzt?
- Wo in der B-Story-Entwicklung stehen wir? (Beginn / Mitte / Eskalation / Auflösung)

**Erweiterungsvorschlag Layer 6:**
```
B-STORY (falls aktiv):
  Subplot: {{ subplot.title }}
  Träger: {{ subplot.carried_by_name }} ({{ subplot.get_story_label_display }})
  Thematischer Spiegel: {{ subplot.thematic_mirror }}
  B-Story-Phase: {{ b_story_phase }}  ← berechnet aus begins_at_percent / aktuelle Position
  Verbindung zum Need: {% if subplot.embodies_need %}Verkörpert das Need des Protagonisten{% endif %}
```

---

## Zusammenfassung der erforderlichen Änderungen

### Blocking — muss vor Merge behoben sein:

| ID | Was | Wo |
|----|-----|----|
| B1 | `thematic_mirror` braucht `blank=True, default=""` | `SubplotArc` |
| B2 | `updated_at` fehlt auf `SubplotArc` | `SubplotArc` |
| B3 | Content-type-Guard für Essay/Sachbuch im Health-Score | `health_service.py` |
| B4 | `Want ≠ Need`-Check: Logikfehler bei leeren Feldern | `health_service.py` |
| B5 | `carries_b_story` vs. `SubplotArc` — Redundanz auflösen | `ProjectCharacterLink` |
| B6 | `SubplotArc` braucht `begins_at_node` / `ends_at_node` FKs | `SubplotArc` |
| B7 | `begins_at_percent` / `ends_at_percent`: Validators + `clean()` | `SubplotArc` |

### Minor — sollten vor Merge behoben werden:

| ID | Was |
|----|-----|
| M1 | Protagonist-Anzahl-Guard im Health-Check |
| M2 | Antagonisten-Anzahl-Guard im Health-Check |
| M3 | `shadow` vs. `antagonist` Überschneidung dokumentieren |
| M4 | `information_advantage` bei `inner_self`-Antagonist |
| M5 | `top_issues`-Property auf `DramaturgicHealthResult` |
| M6 | `intersection_notes` strukturieren (JSONField oder M2M) |

### Dramaturgisch — für nächste Iteration:

| ID | Was |
|----|-----|
| D1 | 37%-Regel: Framing als Guideline, nicht Regel |
| D2 | C-Story: Guidance/Warnung ergänzen |
| D3 | Score-Labels: Vollständigkeit ≠ Qualität kommunizieren |
| D4 | LLM Layer 6: B-Story-Kontext erweitern |

---

## Entscheidungsempfehlung

**Nicht mergen in aktuellem Zustand.**

B3 (Essay-Guard) und B5 (carries_b_story-Redundanz) sind konzeptionelle
Fehler, keine Typos. B4 (Want≠Need-Logik) produziert falsche Score-Werte
für legitime Arbeitsstände.

Die Kernarchitektur des ADR ist solide. Mit den Korrekturen zu B1–B7
und mindestens M4 + M5 ist es deploybar.

Vorschlag: **ADR-157 Rev. 1** mit diesen Änderungen — dann Acceptance.
