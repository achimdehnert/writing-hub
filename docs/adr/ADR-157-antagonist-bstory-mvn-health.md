# ADR-157: Antagonist-System, B-Story/Subplot-Tracking und DramaturgicHealthScore

**Status:** Accepted  
**Datum:** 2026-03-28 (Rev.1: 2026-03-28)  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-151, ADR-152  
**Rev.1-Änderungen:** B1–B7 (alle Blocking Issues), M4, M5, D3, D4

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

### Lücke 2 — B-Story/Subplot fehlt als Strukturelement

Das Drei-Akte-Modell (ADR-150) definiert bei 37% explizit: "B-Story begins".
Die B-Story ist der **thematische Spiegel der inneren Geschichte** —
typischerweise die Figur, die das Need des Protagonisten verkörpert.

### Lücke 3 — Minimum Viable Novel (MVN) ist nicht messbar

Alle Felder sind `blank=True`. Ein Autor kann ein Projekt anlegen,
0 Felder befüllen, und der Hub zeigt kein Feedback.

---

## Entscheidung

### Teil A: Antagonisten-Felder auf ProjectCharacterLink

```python
# apps/worlds/models.py — Erweiterung ProjectCharacterLink

NARRATIVE_ROLES = [
    ("protagonist",        "Protagonist — Hauptfigur mit Arc"),
    ("antagonist",         "Antagonist — Gegenkraft mit eigener Logik"),
    ("deuteragonist",      "Deuteragonist — zweite Hauptfigur (B-Story)"),
    ("mentor",             "Mentor — gibt Werkzeug/Weisheit"),
    ("ally",               "Verbündeter — Spiegel und Unterstützung"),
    ("love_interest",      "Liebesinteresse — verkörpert das Need"),
    ("trickster",          "Trickster — Humor und Dekonstruktion"),
    ("herald",             "Herold — bringt den Ruf"),
    ("shapeshifter",       "Gestaltenwandler — zweifelt Loyalität an"),
    ("shadow",             "Schatten — was wäre der Protagonist wenn..."),
    ("threshold_guardian", "Schwellenwächter — testet Entschlossenheit"),
    ("supporting",         "Nebenfigur — dramaturgische Funktion"),
]

ANTAGONIST_TYPES = [
    ("person",     "Person / Gruppe"),
    ("system",     "System / Institution / Gesellschaft"),
    ("nature",     "Natur / Umwelt / Schicksal"),
    ("inner_self", "Inneres Selbst — die eigene dunkle Seite"),
    ("combination","Kombination mehrerer Typen"),
]

narrative_role = models.CharField(
    max_length=30,
    choices=NARRATIVE_ROLES,
    default="supporting",
    verbose_name="Narrative Rolle",
)
antagonist_type = models.CharField(
    max_length=20, choices=ANTAGONIST_TYPES,
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
    help_text="Was zeigt diese Figur, was der Protagonist sein KÖNNTE?",
)
shared_trait_with_protagonist = models.TextField(
    blank=True, default="",
    verbose_name="Gemeinsamkeit mit Protagonisten",
    help_text="Was teilen sie? Eine tiefe Gemeinsamkeit macht den Konflikt interessant.",
)
information_advantage = models.TextField(
    blank=True, default="",
    verbose_name="Informationsvorsprung",
    help_text="Was weiß diese Figur, was der Protagonist (noch) nicht weiß? "
              "Nur relevant für externe Antagonisten (person, system, nature). "
              "Bei inner_self leer lassen.",
)
# Rev.1 B5: carries_b_story entfernt — Information vollständig in
# SubplotArc.carried_by_character_id + narrative_role abgebildet.
# @property carries_b_story ableiten statt persistieren (s.u.)
```

**`carries_b_story` als Property (nicht persistiert, B5-Fix):**
```python
@property
def carries_b_story(self) -> bool:
    """
    Ableitung aus SubplotArc — keine persistierte Redundanz.
    Eine Figur trägt die B-Story wenn:
    1. Ein SubplotArc mit story_label='b_story' auf ihre UUID zeigt, ODER
    2. ihre narrative_role ist love_interest oder mentor (typische B-Story-Träger)
    """
    from projects.models import SubplotArc
    return SubplotArc.objects.filter(
        project=self.project,
        story_label="b_story",
        carried_by_character_id=self.weltenhub_character_id,
    ).exists()
```

### Teil B: SubplotArc (in `apps/projects/models_narrative.py`)

```python
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class SubplotArc(models.Model):
    """
    Dramaturgischer Nebenstrang (B-Story, C-Story).

    Die B-Story ist NICHT optional — sie ist das thematische Herz
    des Romans. Sie beginnt typischerweise bei ~37% (Save-the-Cat /
    Drei-Akte-Modell). Im literarischen Roman und bei Dual-POV-Strukturen
    kann sie erheblich früher beginnen — der Default 37% ist eine
    Guideline, keine Regel.

    C-Story: Nur für Romane > 80.000 Wörter mit etablierter B-Story sinnvoll.
    In Kurzgeschichten und einfachen Romanen nicht verwenden.

    story_label:
        a_story → Haupthandlung
        b_story → Thematischer Spiegel (Liebesinteresse/Mentor-Typ)
        c_story → Weiterer Subplot (nur bei Bedarf, s.o.)
    """
    STORY_LABELS = [
        ("a_story", "A-Story — Haupthandlung"),
        ("b_story", "B-Story — Thematischer Spiegel"),
        ("c_story", "C-Story — Weiterer Subplot (nur > 80k Wörter)"),
    ]

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="subplot_arcs",
    )
    story_label = models.CharField(max_length=10, choices=STORY_LABELS, default="b_story")
    title       = models.CharField(max_length=200, verbose_name="Subplot-Bezeichnung")

    carried_by_character_id = models.UUIDField(
        null=True, blank=True,
        verbose_name="Träger-Figur (WeltenHub UUID)",
    )
    carried_by_name = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Träger-Figur (Cache)",
    )

    # Rev.1 B1-Fix: blank=True, default="" ergänzt
    thematic_mirror = models.TextField(
        blank=True, default="",
        verbose_name="Thematischer Spiegel",
        help_text="Wie spiegelt dieser Subplot das Thema der A-Story?",
    )
    embodies_need = models.BooleanField(
        default=True,
        verbose_name="Verkörpert das Need",
        help_text="Dieser Subplot verkörpert das Need des Protagonisten.",
    )

    # Rev.1 B7-Fix: PositiveSmallIntegerField + Validators + clean()
    begins_at_percent = models.PositiveSmallIntegerField(
        default=37,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Beginn (%)",
        help_text="Empfehlung Drei-Akte/Save-the-Cat: 37%. "
                  "Im literarischen Roman und Dual-POV oft früher.",
    )
    ends_at_percent = models.PositiveSmallIntegerField(
        default=95,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Ende (%)",
    )

    # Rev.1 B6-Fix: OutlineNode-FKs für operative Kapitel-Verknüpfung
    begins_at_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subplot_begins",
        verbose_name="Beginnt in Kapitel/Szene",
        help_text="Operative Verknüpfung — überschreibt begins_at_percent für LLM.",
    )
    ends_at_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subplot_ends",
        verbose_name="Endet in Kapitel/Szene",
    )

    # Rev.1 M6: intersection_notes als strukturiertes JSONField
    intersection_nodes = models.ManyToManyField(
        "projects.OutlineNode",
        blank=True,
        related_name="subplot_intersections",
        help_text="Kapitel/Szenen, in denen dieser Subplot die A-Story kreuzt "
                  "(typisch: emotionale Hochpunkte).",
    )
    intersection_notes = models.TextField(
        blank=True, default="",
        verbose_name="Kreuzungspunkte — Anmerkungen",
        help_text="Freitext-Ergänzung zu den Kreuzungspunkten.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    # Rev.1 B2-Fix: updated_at ergänzt
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "wh_subplot_arcs"
        ordering        = ["project", "story_label"]
        verbose_name    = "Subplot-Arc"
        verbose_name_plural = "Subplot-Arcs"

    def __str__(self):
        return f"{self.get_story_label_display()}: {self.title}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Rev.1 B7-Fix: begins < ends erzwingen
        if self.begins_at_percent >= self.ends_at_percent:
            raise ValidationError(
                "begins_at_percent muss kleiner als ends_at_percent sein."
            )

    def b_story_phase(self, current_percent: int) -> str:
        """
        Berechnet die aktuelle Phase der B-Story für LLM-Kontext (D4-Fix).
        Gibt 'vor_beginn' | 'beginn' | 'entwicklung' | 'eskalation' | 'aufloesung' zurück.
        """
        if current_percent < self.begins_at_percent:
            return "vor_beginn"
        span = self.ends_at_percent - self.begins_at_percent
        if span <= 0:
            return "entwicklung"
        pos = (current_percent - self.begins_at_percent) / span
        if pos < 0.2:
            return "beginn"
        if pos < 0.5:
            return "entwicklung"
        if pos < 0.8:
            return "eskalation"
        return "aufloesung"
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
    weight: int = 1


@dataclass
class DramaturgicHealthResult:
    score: int
    checks: list[HealthCheck] = field(default_factory=list)
    mvn_complete: bool = False

    @property
    def level(self) -> str:
        # Rev.1 D3-Fix: Labels kommunizieren Vollständigkeit, nicht Qualitätsurteil
        if self.score >= 80:
            return "solid"       # Struktur vollständig — bereit zum Schreiben
        if self.score >= 50:
            return "developing"  # Kernstruktur vorhanden — weiter ausbauen
        return "skeleton"        # Grundriss — MVN noch unvollständig

    @property
    def top_issues(self) -> list[HealthCheck]:
        # Rev.1 M5-Fix: Die 3 dringendsten fehlgeschlagenen Checks
        return sorted(
            [c for c in self.checks if not c.passed],
            key=lambda c: -c.weight
        )[:3]


def compute_dramaturgic_health(project) -> DramaturgicHealthResult:
    """
    Berechnet den DramaturgicHealthScore eines BookProject.

    WICHTIG: Dieser Score misst die VOLLSTÄNDIGKEIT DER PLANUNG,
    nicht die Qualität des Textes. score=20% bedeutet "Planung
    noch am Anfang" — kein Urteil über das Schreibtalent.

    Rev.1 B3-Fix: content_type-Guard für Essay/Sachbuch.
    """
    checks: list[HealthCheck] = []

    # Rev.1 B3-Fix: Format-Guard — Essay/Sachbuch brauchen keinen Protagonisten
    content_type = getattr(project, "content_type", "roman")
    NON_DRAMATIC_TYPES = ("essay", "nonfiction", "sachbuch")
    if content_type in NON_DRAMATIC_TYPES:
        return _compute_nondramatic_health(project, content_type)

    # --- MVN-PFLICHTFELDER (Gewicht 3 — Blocker) ---

    checks.append(HealthCheck(
        label="Äußere Geschichte definiert",
        passed=bool(getattr(project, "outer_story", "").strip()),
        message="outer_story ist leer — Was passiert im Roman?",
        weight=3,
    ))
    checks.append(HealthCheck(
        label="Innere Geschichte definiert",
        passed=bool(getattr(project, "inner_story", "").strip()),
        message="inner_story ist leer — Was verändert sich in der Figur?",
        weight=3,
    ))
    checks.append(HealthCheck(
        label="Arc-Richtung gesetzt",
        passed=bool(getattr(project, "arc_direction", "")),
        message="arc_direction fehlt — positiv / negativ / flach?",
        weight=3,
    ))

    # --- PROTAGONIST (Gewicht 3) ---
    protagonists = list(
        project.projectcharacterlink_set.filter(narrative_role="protagonist")
    )

    # Rev.1 M1-Fix: Anzahl-Guard
    checks.append(HealthCheck(
        label="Protagonist definiert",
        passed=len(protagonists) >= 1,
        message="Kein Protagonist — narrative_role=protagonist nicht gesetzt.",
        weight=3,
    ))
    checks.append(HealthCheck(
        label="Protagonist-Anzahl plausibel",
        passed=len(protagonists) <= 2,
        message=f"{len(protagonists)} Protagonisten definiert — für Dual-POV max. 2.",
        weight=1,
    ))

    protagonist = protagonists[0] if protagonists else None
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

        # Rev.1 B4-Fix: Want≠Need nur prüfen wenn beide befüllt
        if protagonist.want.strip() and protagonist.need.strip():
            checks.append(HealthCheck(
                label="Want ≠ Need",
                passed=protagonist.want.strip() != protagonist.need.strip(),
                message="Want == Need — kein dramaturgischer Arc möglich.",
                weight=3,
            ))
        # Wenn eines leer ist: bereits durch obige Checks abgedeckt — kein Doppel-Penalty

    # --- ANTAGONIST (Gewicht 2) ---
    antagonists = list(
        project.projectcharacterlink_set.filter(narrative_role="antagonist")
    )

    # Rev.1 M2-Fix: Anzahl-Guard
    checks.append(HealthCheck(
        label="Antagonist definiert",
        passed=len(antagonists) >= 1,
        message="Kein Antagonist — ohne Gegenkraft kein Konflikt.",
        weight=2,
    ))

    antagonist = antagonists[0] if antagonists else None
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
        # Rev.1 M4-Fix: information_advantage nur für externe Antagonisten prüfen
        if antagonist.antagonist_type not in ("inner_self", ""):
            checks.append(HealthCheck(
                label="Informationsvorsprung",
                passed=bool(antagonist.information_advantage.strip()),
                message="information_advantage leer — Informations-Asymmetrie erzeugt Spannung.",
                weight=1,
            ))

    # --- MAKROSTRUKTUR (Gewicht 2) ---
    checks.append(HealthCheck(
        label="Wendepunkte definiert",
        passed=project.turning_points.exists(),
        message="Keine ProjectTurningPoints — Makrostruktur fehlt.",
        weight=2,
    ))

    # --- THEMA (Gewicht 2) ---
    has_theme = bool(getattr(project, "theme", None))
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
    checks.append(HealthCheck(
        label="Erzählstimme definiert",
        passed=bool(getattr(project, "narrative_voice", None)),
        message="NarrativeVoice fehlt.",
        weight=1,
    ))

    # Score
    total_weight = sum(c.weight for c in checks)
    earned_weight = sum(c.weight for c in checks if c.passed)
    score = int((earned_weight / total_weight) * 100) if total_weight else 0
    mvn_complete = all(c.passed for c in checks if c.weight == 3)

    return DramaturgicHealthResult(score=score, checks=checks, mvn_complete=mvn_complete)


def _compute_nondramatic_health(project, content_type: str) -> DramaturgicHealthResult:
    """
    Rev.1 B3-Fix: Separater Health-Pfad für Essays und Sachbücher.
    Prüft nur Format-spezifisch relevante Felder.
    """
    checks = []
    checks.append(HealthCheck(
        label="Äußere Geschichte / Kernthese",
        passed=bool(getattr(project, "outer_story", "").strip()),
        message="outer_story / Kernthese leer.",
        weight=3,
    ))
    checks.append(HealthCheck(
        label="Erzählstimme / Stil definiert",
        passed=bool(getattr(project, "narrative_voice", None)),
        message="NarrativeVoice fehlt.",
        weight=2,
    ))
    checks.append(HealthCheck(
        label="Outline vorhanden",
        passed=project.outline_versions.filter(is_active=True).exists(),
        message="Keine aktive Outline.",
        weight=2,
    ))
    total = sum(c.weight for c in checks)
    earned = sum(c.weight for c in checks if c.passed)
    score = int((earned / total) * 100) if total else 0
    return DramaturgicHealthResult(score=score, checks=checks, mvn_complete=True)
```

### Teil D: LLM-Kontext — Layer 6 erweitert (D4-Fix)

```
[USER — Layer 6 erweitert]

PROTAGONIST:
  Want: {{ protagonist.want }}
  Need: {{ protagonist.need }}
  Flaw: {{ protagonist.flaw }}
  False Belief: {{ protagonist.false_belief }}

ANTAGONIST:
  Typ: {{ antagonist.get_antagonist_type_display }}
  Logik (seine Perspektive): {{ antagonist.antagonist_logic }}
  Spiegel zum Protagonisten: {{ antagonist.mirror_to_protagonist }}
  Gemeinsamkeit: {{ antagonist.shared_trait_with_protagonist }}
  {% if antagonist.antagonist_type != "inner_self" %}
  Informationsvorsprung: {{ antagonist.information_advantage }}
  {% endif %}

{% if active_subplot %}
B-STORY (aktiv in dieser Szene):
  Subplot: {{ active_subplot.title }}
  Träger: {{ active_subplot.carried_by_name }}
  Phase: {{ active_subplot.b_story_phase(current_percent) }}
  Thematischer Spiegel: {{ active_subplot.thematic_mirror }}
  {% if active_subplot.embodies_need %}
  → Verkörpert das Need des Protagonisten
  {% endif %}
{% endif %}
```

**Hinweis zum Score-Level im Template (D3-Fix):**
```html
<!-- drama_health.html — Framing kommunizieren -->
<p class="text-muted fs-sm">
  Dieser Score misst die <strong>Vollständigkeit der Planung</strong>,
  nicht die Qualität deines Textes.
</p>
```

---

## Begründung

- **`narrative_role` als CharField** (fixe Taxonomie nach Campbell/Vogler):
  Analog zu `arc_direction` in ADR-150 — keine Admin-Verwaltung nötig.
- **`carries_b_story` als Property** (B5-Fix): Verhindert stille
  Inkonsistenz zwischen `carries_b_story=True` und fehlendem `SubplotArc`.
  SSoT ist der `SubplotArc`, nicht das Boolean-Flag.
- **`begins_at_node`/`ends_at_node` FKs** (B6-Fix): `37%` als Integer
  ist für LLM-Generierung nicht operativ. Die FK-Felder verknüpfen den
  Subplot direkt mit dem tatsächlichen Kapitel-Objekt.
- **Content-type-Guard** (B3-Fix): Ein Essay mit Score 20% wäre aktiv
  irreführend. Nicht-dramaturgische Formate brauchen eigene Checks.
- **B4-Fix Want≠Need**: Nur prüfen wenn beide Felder befüllt — sonst
  doppeltes Penalty für denselben Zustand.
- **`shadow` vs. `antagonist`** (M3): Für Figuren, die beide Funktionen
  erfüllen (Ahab/Moby Dick, Javert): `narrative_role="antagonist"` setzen,
  `mirror_to_protagonist` befüllen — das ist die Schatten-Funktion.
  `shadow` als Rolle ist für Figuren reserviert, die den Protagonisten
  spiegeln OHNE Antagonisten-Funktion.
- **`top_issues`-Property** (M5-Fix): Autor mit 45% Score sieht sofort
  seine 3 wichtigsten Baustellen — keine 15-Item-Liste durchforsten.

---

## Abgelehnte Alternativen

**Separates AntagonistProfile-Modell:** Redundant — eine Figur kann in
verschiedenen Projekten verschiedene Rollen spielen.

**`carries_b_story` persistieren:** Erzeugt stille Inkonsistenz.
Property ist die saubere Lösung.

**MVN-Pflichtfelder erzwingen (NOT NULL):** Würde bestehende Projekte brechen.
Soft-Enforcement über Health-Score ist der richtige Ansatz.

**DramaturgicHealthScore als berechnetes DB-Feld:** Denormalisiert.
Service-on-demand ist effizienter.

---

## Konsequenzen

- Migration `worlds/0004_narrative_role_antagonist`
- Migration `projects/0011_subplot_arc` (inkl. `begins_at_node`, `ends_at_node`,
  `intersection_nodes` M2M, `updated_at`)
- `compute_dramaturgic_health()` + `_compute_nondramatic_health()` in
  `apps/projects/services/health_service.py`
- URL `projects/<pk>/health/` + View + Template (mit Score-Framing-Hinweis)
- Layer 6 im Prompt-Service: Antagonist + B-Story-Phase ergänzen
- `SubplotArc.b_story_phase()` im Prompt-Context-Builder nutzen
- Admin: `narrative_role` als prominentes Feld in `ProjectCharacterLinkInline`

---

**Referenzen:** ADR-150, ADR-151, ADR-152, ADR-154, ADR-158,  
`docs/adr/input/roman_hub_komplett.md` (Schritt 1.6, 3.3.3),  
`docs/adr/review_adr157.md` (Rev.1-Grundlage),  
`docs/adr/input/optimierungen/KONSEQUENZANALYSE_ADR158.md`
