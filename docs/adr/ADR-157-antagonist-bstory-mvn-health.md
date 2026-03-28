# ADR-157: Antagonist-System, B-Story/Subplot-Tracking und DramaturgicHealthScore

**Status:** Accepted  
**Datum:** 2026-03-28  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-151, ADR-152

---

## Kontext

Eine verlegerische Analyse der bestehenden ADRs (150–156) zeigt drei
systematische Lücken, die in über 80% der abgelehnten Erstromane
als Hauptursache identifiziert werden:

### Lücke 1 — Antagonist fehlt als dramaturgisches System

`ProjectCharacterLink` hat `want/need/flaw/ghost` für Figuren — aber kein
einziges Feld unterscheidet Protagonist von Antagonist dramaturgisch.
Das Romanstruktur-Framework (Schritt 3.3.3) definiert:

> *"Der Antagonist denkt nicht, er sei böse. Er hat eine Logik, die
> in seiner Welt Sinn ergibt."*

Fehlende Konzepte:
- **Antagonisten-Logik** — seine Motivation aus eigener Perspektive
- **Spiegel-Beziehung** — was zeigt der Antagonist, was der Protagonist sein KÖNNTE?
- **Informationsvorsprung** — was weiß er, was der Protagonist nicht weiß?
- **Antagonisten-Typ** — Person / System / Natur / inneres Selbst

### Lücke 2 — B-Story/Subplot fehlt als Strukturelement

Das Drei-Akte-Modell (ADR-150) definiert bei 37% explizit: "B-Story begins".
Die B-Story ist kein optionaler Nebenstrang — sie ist der **thematische
Spiegel der inneren Geschichte**. Typischerweise: die Liebesbeziehung, die
das Need der Hauptfigur verkörpert.

Im writing-hub gibt es kein Modell, das unterscheidet:
- Welche Figur trägt welchen Subplot?
- Wo beginnt / endet der Subplot?
- In welcher Beziehung steht er zur A-Story-Thematik?

### Lücke 3 — Minimum Viable Novel (MVN) ist nicht messbar

Das Framework definiert das MVN (Schritt 1.6):
```yaml
minimum_viable_novel:
  eine_figur_mit:
    - einem_wollen   # äußeres Ziel
    - einem_brauchen # innere Wahrheit
    - einem_fehler   # psychologischer Riss
  ein_hindernis      # verhindert das Wollen
  eine_entscheidung  # adressiert den Fehler
  eine_konsequenz    # zeigt ob die Figur gewachsen ist
```

Alle Felder in allen ADRs sind `blank=True`. Ein Autor kann ein
Projekt anlegen, 0 Felder befüllen, und der Hub zeigt kein Feedback.
**Ein Roman ohne MVN ist kein Roman** — aber das System zwingt den
Autor nicht, das zu erkennen.

---

## Entscheidung

### Teil A: Antagonisten-Felder auf ProjectCharacterLink

Statt ein separates Modell für Antagonisten zu schaffen, wird
`ProjectCharacterLink` um eine `narrative_role` und antagonisten-spezifische
Felder erweitert. Eine Figur ist immer eine Figur — ihre Rolle im Projekt
ist kontextuell.

```python
# apps/worlds/models.py — Erweiterung ProjectCharacterLink

# --- NARRATIVE ROLLE (ADR-157) ---

NARRATIVE_ROLES = [
    ("protagonist",   "Protagonist — Hauptfigur mit Arc"),
    ("antagonist",    "Antagonist — Gegenkraft mit eigener Logik"),
    ("deuteragonist", "Deuteragonist — zweite Hauptfigur (B-Story)"),
    ("mentor",        "Mentor — gibt Werkzeug/Weisheit"),
    ("ally",          "Verbündeter — Spiegel und Unterstützung"),
    ("love_interest", "Liebesinteresse — verkörpert das Need"),
    ("trickster",     "Trickster — Humor und Dekonstruktion"),
    ("herald",        "Herold — bringt den Ruf"),
    ("shapeshifter",  "Gestaltenwandler — zweifelt Loyalität an"),
    ("shadow",        "Schatten — was wäre der Protagonist wenn..."),
    ("threshold_guardian", "Schwellenwächter — testet Entschlossenheit"),
    ("supporting",    "Nebenfigur — dramaturgische Funktion"),
]

ANTAGONIST_TYPES = [
    ("person",       "Person / Gruppe"),
    ("system",       "System / Institution / Gesellschaft"),
    ("nature",       "Natur / Umwelt / Schicksal"),
    ("inner_self",   "Inneres Selbst — die eigene dunkle Seite"),
    ("combination",  "Kombination mehrerer Typen"),
]

narrative_role = models.CharField(
    max_length=30,
    choices=NARRATIVE_ROLES,
    default="supporting",
    verbose_name="Narrative Rolle",
    help_text="Dramaturgische Funktion dieser Figur in diesem Projekt.",
)

# Antagonisten-spezifische Felder (nur relevant wenn narrative_role=antagonist)
antagonist_type = models.CharField(
    max_length=20,
    choices=ANTAGONIST_TYPES,
    blank=True, default="",
    verbose_name="Antagonisten-Typ",
)
antagonist_logic = models.TextField(
    blank=True, default="",
    verbose_name="Antagonisten-Logik",
    help_text="Warum glaubt der Antagonist, das Richtige zu tun? "
              "Aus SEINER Perspektive muss seine Motivation vollständig logisch sein.",
)
mirror_to_protagonist = models.TextField(
    blank=True, default="",
    verbose_name="Spiegel zum Protagonisten",
    help_text="Was zeigt diese Figur, was der Protagonist sein KÖNNTE, "
              "wenn er eine andere Wahl träfe?",
)
shared_trait_with_protagonist = models.TextField(
    blank=True, default="",
    verbose_name="Gemeinsamkeit mit Protagonisten",
    help_text="Was teilen sie? Eine tiefe Gemeinsamkeit macht den Konflikt "
              "unauflöslich interessant.",
)
information_advantage = models.TextField(
    blank=True, default="",
    verbose_name="Informationsvorsprung",
    help_text="Was weiß diese Figur, was der Protagonist (noch) nicht weiß? "
              "Informations-Asymmetrie erzeugt Spannung.",
)

# B-Story / Subplot-Träger
carries_b_story = models.BooleanField(
    default=False,
    verbose_name="Träger der B-Story",
    help_text="Diese Figur trägt den thematischen Gegenstrang "
              "(typischerweise das Liebesinteresse oder der Mentor).",
)
```

**Begründung narrative_role als CharField (nicht Lookup):** Die Archetypen
nach Campbell/Vogler sind eine fixierte Taxonomie des Romanstruktur-Frameworks
— analog zu `arc_direction` in ADR-150. Kein Admin-verwaltbarer Erweiterungsbedarf.

### Teil B: SubplotArc (in `apps/projects/models_narrative.py`)

```python
class SubplotArc(models.Model):
    """
    Ein dramaturgischer Nebenstrang (B-Story, C-Story).

    Die B-Story ist NICHT optional — sie ist das thematische Herz
    des Romans. Sie beginnt bei ~37% (Drei-Akte-Modell), wenn die
    A-Story-Welt etabliert ist, und endet parallel zum Climax.

    Beziehung zur A-Story:
        - Spiegelt das Thema (zeigt das Need aus anderer Perspektive)
        - Verkörpert das Need des Protagonisten (Liebesinteresse, Mentor)
        - Läuft parallel, kreuzt die A-Story an definierten Punkten

    story_label:
        a_story  → Haupthandlung (Protagonist vs. Antagonist)
        b_story  → Thematischer Spiegel (typisch: Liebesinteresse/Mentor)
        c_story  → Humorelement / Subplot 3 (selten, für längere Romane)
    """
    STORY_LABELS = [
        ("a_story", "A-Story — Haupthandlung"),
        ("b_story", "B-Story — Thematischer Spiegel"),
        ("c_story", "C-Story — Weiterer Subplot"),
    ]

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="subplot_arcs",
    )
    story_label = models.CharField(max_length=10, choices=STORY_LABELS, default="b_story")
    title       = models.CharField(max_length=200, verbose_name="Subplot-Bezeichnung")

    # Träger-Figur (typisch: Liebesinteresse, Mentor)
    carried_by_character_id = models.UUIDField(
        null=True, blank=True,
        verbose_name="Träger-Figur (WeltenHub UUID)",
    )
    carried_by_name = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Träger-Figur (Cache)",
    )

    # Thematische Funktion
    thematic_mirror = models.TextField(
        verbose_name="Thematischer Spiegel",
        help_text="Wie spiegelt dieser Subplot das Thema der A-Story? "
                  "Was zeigt er, das die A-Story nicht direkt zeigen kann?",
    )
    embodies_need = models.BooleanField(
        default=True,
        verbose_name="Verkörpert das Need",
        help_text="Wenn True: dieser Subplot verkörpert das Need des Protagonisten "
                  "— die innere Wahrheit, die er noch nicht erkannt hat.",
    )

    # Strukturelle Position
    begins_at_percent = models.SmallIntegerField(
        default=37,
        verbose_name="Beginn (%)",
        help_text="Position im Roman (0–100). B-Story: typisch 37%.",
    )
    ends_at_percent = models.SmallIntegerField(
        default=95,
        verbose_name="Ende (%)",
    )

    # Kreuzungspunkte mit A-Story
    intersection_notes = models.TextField(
        blank=True, default="",
        verbose_name="Kreuzungspunkte mit A-Story",
        help_text="An welchen Punkten kreuzt dieser Subplot die A-Story? "
                  "Diese Momente sind typisch die emotionalen Hochpunkte.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "wh_subplot_arcs"
        ordering        = ["project", "story_label"]
        verbose_name    = "Subplot-Arc"
        verbose_name_plural = "Subplot-Arcs"

    def __str__(self):
        return f"{self.get_story_label_display()}: {self.title}"
```

### Teil C: DramaturgicHealthScore (in `apps/projects/services/health_service.py`)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HealthCheck:
    label: str
    passed: bool
    message: str
    weight: int = 1       # Gewichtung für Gesamt-Score


@dataclass
class DramaturgicHealthResult:
    score: int            # 0–100
    checks: list[HealthCheck] = field(default_factory=list)
    mvn_complete: bool = False

    @property
    def level(self) -> str:
        if self.score >= 80:
            return "solid"      # Verlegerisch präsentierbar
        if self.score >= 50:
            return "developing" # Arbeitsentwurf
        return "skeleton"       # Nur Grundstruktur


def compute_dramaturgic_health(project) -> DramaturgicHealthResult:
    """
    Berechnet den DramaturgicHealthScore eines BookProject.

    Prüft das Minimum Viable Novel (MVN) und alle dramaturgischen
    Kernkonzepte aus dem Romanstruktur-Framework (Schritt 1.6).

    Gewichtung:
        MVN-Pflichtfelder:  3 Punkte je Check (Blocker)
        Dramaturgie-Felder: 2 Punkte je Check
        Vertiefungs-Felder: 1 Punkt je Check
    """
    checks: list[HealthCheck] = []

    # --- MVN-PFLICHTFELDER (Gewicht 3 — Blocker) ---

    checks.append(HealthCheck(
        label="Äußere Geschichte definiert",
        passed=bool(project.outer_story.strip()),
        message="outer_story ist leer — Was passiert im Roman?",
        weight=3,
    ))
    checks.append(HealthCheck(
        label="Innere Geschichte definiert",
        passed=bool(project.inner_story.strip()),
        message="inner_story ist leer — Was verändert sich in der Figur?",
        weight=3,
    ))
    checks.append(HealthCheck(
        label="Arc-Richtung gesetzt",
        passed=bool(project.arc_direction),
        message="arc_direction fehlt — positiv / negativ / flach?",
        weight=3,
    ))

    # --- PROTAGONIST (Gewicht 3) ---
    protagonist = project.projectcharacterlink_set.filter(
        narrative_role="protagonist"
    ).first()

    checks.append(HealthCheck(
        label="Protagonist definiert",
        passed=protagonist is not None,
        message="Kein Protagonist — narrative_role=protagonist nicht gesetzt.",
        weight=3,
    ))
    if protagonist:
        checks.append(HealthCheck(
            label="Protagonist: Want",
            passed=bool(protagonist.want.strip()),
            message="Protagonist.want leer — äußeres Ziel fehlt.",
            weight=3,
        ))
        checks.append(HealthCheck(
            label="Protagonist: Need",
            passed=bool(protagonist.need.strip()),
            message="Protagonist.need leer — innere Wahrheit fehlt.",
            weight=3,
        ))
        checks.append(HealthCheck(
            label="Protagonist: Flaw",
            passed=bool(protagonist.flaw.strip()),
            message="Protagonist.flaw leer — ohne Fehler kein Arc.",
            weight=3,
        ))
        checks.append(HealthCheck(
            label="Want ≠ Need",
            passed=protagonist.want.strip() != protagonist.need.strip()
                   if protagonist.want and protagonist.need else False,
            message="Want == Need — kein dramaturgischer Arc möglich.",
            weight=3,
        ))

    # --- ANTAGONIST (Gewicht 2) ---
    antagonist = project.projectcharacterlink_set.filter(
        narrative_role="antagonist"
    ).first()

    checks.append(HealthCheck(
        label="Antagonist definiert",
        passed=antagonist is not None,
        message="Kein Antagonist — ohne Gegenkraft kein Konflikt.",
        weight=2,
    ))
    if antagonist:
        checks.append(HealthCheck(
            label="Antagonisten-Logik",
            passed=bool(antagonist.antagonist_logic.strip()),
            message="antagonist_logic leer — warum glaubt er, das Richtige zu tun?",
            weight=2,
        ))
        checks.append(HealthCheck(
            label="Spiegel-Beziehung",
            passed=bool(antagonist.mirror_to_protagonist.strip()),
            message="mirror_to_protagonist leer — ohne Spiegel ist der Antagonist flach.",
            weight=2,
        ))

    # --- MAKROSTRUKTUR (Gewicht 2) ---
    checks.append(HealthCheck(
        label="Wendepunkte definiert",
        passed=project.turning_points.exists(),
        message="Keine ProjectTurningPoints — Makrostruktur fehlt.",
        weight=2,
    ))

    # --- THEMA (Gewicht 2) ---
    has_theme = hasattr(project, "theme") and bool(
        getattr(project, "theme", None)
    )
    checks.append(HealthCheck(
        label="Thema definiert",
        passed=has_theme,
        message="ProjectTheme fehlt — ohne Thema fehlt dem Roman Bedeutung.",
        weight=2,
    ))

    # --- B-STORY (Gewicht 1) ---
    checks.append(HealthCheck(
        label="B-Story definiert",
        passed=project.subplot_arcs.filter(story_label="b_story").exists(),
        message="Keine B-Story — thematischer Spiegel fehlt.",
        weight=1,
    ))

    # --- ERZÄHLSTIMME (Gewicht 1) ---
    has_voice = hasattr(project, "narrative_voice") and bool(
        getattr(project, "narrative_voice", None)
    )
    checks.append(HealthCheck(
        label="Erzählstimme definiert",
        passed=has_voice,
        message="NarrativeVoice fehlt.",
        weight=1,
    ))

    # Score berechnen
    total_weight = sum(c.weight for c in checks)
    earned_weight = sum(c.weight for c in checks if c.passed)
    score = int((earned_weight / total_weight) * 100) if total_weight else 0

    # MVN vollständig wenn alle Gewicht-3-Checks bestanden
    mvn_complete = all(c.passed for c in checks if c.weight == 3)

    return DramaturgicHealthResult(
        score=score,
        checks=checks,
        mvn_complete=mvn_complete,
    )
```

### Teil D: LLM-Kontext-Erweiterung (ADR-150 Layer 6)

Der bestehende Layer 6 (Figuren) wird um Antagonisten-Kontext erweitert:

```
[USER — Layer 6 erweitert]
  PROTAGONIST:
    Want: {{ protagonist.want }}
    Need: {{ protagonist.need }}
    Flaw: {{ protagonist.flaw }}
    False Belief: {{ protagonist.false_belief }}

  ANTAGONIST:
    Typ: {{ antagonist.antagonist_type }}
    Logik: {{ antagonist.antagonist_logic }}
    Spiegel: {{ antagonist.mirror_to_protagonist }}
    Gemeinsamkeit: {{ antagonist.shared_trait_with_protagonist }}
    Informationsvorsprung: {{ antagonist.information_advantage }}

  B-STORY (falls aktiv in dieser Szene):
    {{ subplot.title }}: {{ subplot.thematic_mirror }}
```

### Teil E: Admin-Integration und URL

```
URL Health-Check: /projekte/<pk>/health/
View: project_dramaturgic_health (LoginRequired, Owner)
Template: templates/projects/dramaturgic_health.html

DramaturgicHealthResult-Felder im Template:
  - score (0–100, mit Farb-Codierung: rot < 50, gelb < 80, grün ≥ 80)
  - level (skeleton / developing / solid)
  - mvn_complete (Ja/Nein — Pflicht-Gate)
  - checks (Liste mit label, passed, message)
```

---

## Begründung

- **`narrative_role` auf `ProjectCharacterLink`** statt separatem Antagonisten-Modell:
  Eine Figur ist immer eine Figur. Die Rolle ist projekt-spezifisch — konsistent
  mit dem Prinzip, das die Dramaturgie lokal hält (ADR-152). Eine Figur kann
  in Projekt A Protagonist und in Projekt B Antagonist sein.
- **`antagonist_logic` als Pflichtkonzept:** Verlegerisch ist ein Antagonist
  ohne eigene Logik der häufigste Grund für "flache Geschichte"-Ablehnungen.
  Das Framework formuliert es absolut: "Er hat RECHT in seiner Welt."
- **`SubplotArc` als eigenes Modell** (nicht via `OutlineSequence`):
  Sequenzen (ADR-156) sind Mesostruktur-Einheiten. Ein Subplot-Arc ist
  Makrostruktur — er hat eine eigene thematische Funktion, eine eigene
  Figur als Träger, und strukturelle Position (37%–95%).
- **`DramaturgicHealthScore`** als Service (nicht Model): Der Score wird
  berechnet, nicht persistiert — er ändert sich mit jedem Feld-Update.
  Eine eigene Tabelle wäre denormalisiert und wartungsintensiv.
- **Gewichtung 3/2/1:** MVN-Felder (Gewicht 3) sind Blocker — ohne sie ist
  kein Roman möglich. Dramaturgie-Felder (Gewicht 2) sind kritisch. Vertiefung
  (Gewicht 1) ist professionell aber optional.

---

## Abgelehnte Alternativen

**Separates AntagonistProfile-Modell:** Redundant zu `ProjectCharacterLink`.
Eine Figur kann beide Rollen in verschiedenen Projekten spielen.

**DramaturgicHealthScore als berechnetes DB-Feld:** Würde bei jedem
Feld-Update eine komplexe Berechnung erzwingen. Service-on-demand ist
effizienter.

**`carries_b_story` als B-Story-Modell reicht:** Zu unstrukturiert.
`SubplotArc` gibt dem B-Story-Konzept seine thematische Funktion und
strukturelle Position — das ist für LLM-Prompts nötig.

**MVN-Pflichtfelder erzwingen (NOT NULL):** Würde bestehende Projekte
brechen. Soft-Enforcement über Health-Score ist der richtige Ansatz —
der Autor sieht, was fehlt, wird aber nicht blockiert.

---

## Konsequenzen

- Migration `worlds/0004_narrative_role_antagonist` — neue Felder auf
  `ProjectCharacterLink`
- Migration `projects/0011_subplot_arc` — neue Tabelle `wh_subplot_arcs`
- `compute_dramaturgic_health()` in `apps/projects/services/health_service.py`
- URL `projects/<pk>/health/` + View + Template
- Admin: `narrative_role` als prominentes Feld in `ProjectCharacterLinkInline`
- LLM-Prompts: Layer 6 mit Antagonisten-Block erweitern (ADR-150)
- Seed: `narrative_role`-Choices sind Code-seitig definiert — kein Seed nötig

---

**Referenzen:** ADR-150, ADR-151, ADR-152, ADR-154,  
`docs/adr/input/roman_hub_komplett.md` (Schritt 1.6, 3.3.3),  
`docs/adr/input/schritt_02_makrostruktur.md` (B-Story bei 37%)
