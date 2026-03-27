# ADR-154: Drama-Dashboard und Content-Type-spezifische UIs

**Status:** Accepted  
**Datum:** 2026-03-27  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-151 (Dramaturgische Felder), ADR-153 (HTMX/CSS)

---

## Kontext

Nach Implementierung der dramaturgischen Felder (ADR-151) entstehen Daten,
die eine dedizierte Visualisierung benötigen:

- `OutlineNode.tension_numeric` → Spannungskurve über alle Kapitel
- `OutlineNode.emotion_start/end` → Emotions-Delta pro Szene
- `ProjectTurningPoint` → Markierungen auf der Spannungskurve
- `OutlineNode.outcome` → Farbkodierung nach YES/NO/YES-BUT/NO-AND

Zusätzlich hat der writing-hub verschiedene Content-Typen
(`BookProject.content_type`: Roman, Essay, Serie, Kurzgeschichte), die
strukturell unterschiedliche UIs benötigen. Die aktuelle Lösung verwendet
ein einheitliches Template — es enthält Elemente, die für Essays irrelevant
sind, und fehlt Elemente, die für Serien nötig wären.

Schließlich fehlen `ProjectTheme` und `ProjectMotif` als Modelle vollständig
(Gap 4 aus der Gap-Analyse) — das thematische Fundament eines Romans ist
strukturell von `BookProject` trennbar und verdient ein eigenes UI.

---

## Entscheidung

### Teil A: Drama-Dashboard

Neue View `project_drama_dashboard` in `apps/projects/views_html.py`:

```
URL:      /projekte/<pk>/drama/
Template: templates/projects/drama_dashboard.html
Access:   Login required, Projekt-Owner
```

**Dashboard-Layout:**

```
┌─────────────────────────────────────────────────────┐
│  SPANNUNGSKURVE (Chart.js Line Chart)               │
│  X: Kapitel 1–N | Y: tension_numeric 1–10           │
│  Punkt-Farbe: Outcome (grün=yes, rot=no,            │
│               gelb=yes_but, dunkelrot=no_and)        │
│  Vertikale Marker: ProjectTurningPoint-Positionen   │
├─────────────────────────────────────────────────────┤
│  EMOTIONS-DELTA-ÜBERSICHT                           │
│  Pro Kapitel: emotion_start → emotion_end           │
│  Positiv-Delta = grün, Negativ-Delta = rot          │
├─────────────────────────────────────────────────────┤
│  WENDEPUNKTE-LISTE                                  │
│  ProjectTurningPoint mit Position + Funktion        │
│  Inline-Edit via HTMX                               │
├─────────────────────────────────────────────────────┤
│  THEMA & MOTIVE (Tab, Prio 2)                       │
│  ProjectTheme.core_question + thematic_answer       │
│  ProjectMotif-Liste mit MotifAppearance-Tracking    │
└─────────────────────────────────────────────────────┘
```

**Chart.js via CDN** (nur im Drama-Dashboard-Template, nicht global):
```html
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
{% endblock %}
```

**Service:** `DramaDashboardService` in `apps/projects/services/drama_service.py`:

```python
class DramaDashboardService:
    def __init__(self, project: BookProject):
        self.project = project

    def get_tension_chart_data(self) -> dict:
        """
        Gibt Chart.js-kompatibles JSON zurück.
        Kein ORM direkt — nur Service-Layer (SL-001).
        """
        nodes = OutlineNode.objects.filter(
            outline__project=self.project
        ).select_related("outcome").order_by("sort_order")
        return {
            "labels": [n.title for n in nodes],
            "datasets": [{
                "data": [n.tension_numeric or 0 for n in nodes],
                "pointBackgroundColor": [
                    self._outcome_color(n.outcome) for n in nodes
                ],
            }],
        }

    def get_turning_points(self) -> list:
        return list(self.project.turning_points.order_by("position_percent"))

    @staticmethod
    def _outcome_color(outcome) -> str:
        COLOR_MAP = {
            "yes":     "#22c55e",
            "no":      "#ef4444",
            "yes_but": "#f59e0b",
            "no_and":  "#7f1d1d",
        }
        return COLOR_MAP.get(outcome.code if outcome else "", "#94a3b8")
```

**HTMX Lazy-Load** verhindert langsame Projektseite bei vielen Kapiteln:
```html
<div hx-get="/projekte/{{ project.pk }}/drama/data/"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="spinner">Lade Daten...</div>
</div>
```

### Teil B: Content-Type-spezifische UIs

`BookProject.content_type` bestimmt, welche Tabs im Projekt-Detail erscheinen:

```python
CONTENT_TYPE_TAB_MAP = {
    "roman":          ["outline", "kapitel", "drama", "welten", "lektorat"],
    "essay":          ["essay_outline", "kapitel", "lektorat"],
    "serie":          ["serie_uebersicht", "baende", "shared_chars", "drama"],
    "kurzgeschichte": ["outline", "kapitel", "lektorat"],
}
```

Template-Logik in `project_detail.html`:
```html
{% if "drama" in content_type_tabs %}
  <a href="{% url 'projects:drama_dashboard' project.pk %}">Drama</a>
{% endif %}
{% if "essay_outline" in content_type_tabs %}
  <a href="{% url 'projects:essay_outline' project.pk %}">Essay-Struktur</a>
{% endif %}
```

**Essay-Outline-UI** (`/projekte/<pk>/essay/`):

Argumentationsbaum: These / Antithese / Synthese mit `ArgumentNode`-Hierarchie.

```python
class ArgumentNode(models.Model):
    """
    Knoten im Argumentationsbaum eines Essays.
    Unterscheidet sich strukturell vom Roman-OutlineNode:
    kein Spannungs-Tracking, stattdessen Claim/Evidence/Counter-System.
    """
    project      = models.ForeignKey(BookProject, on_delete=models.CASCADE,
                                     related_name="argument_nodes")
    parent       = models.ForeignKey("self", null=True, blank=True,
                                     on_delete=models.CASCADE, related_name="children")
    node_type    = models.CharField(max_length=20,
                                    choices=[("claim","These"),("evidence","Beleg"),
                                             ("counter","Gegenargument"),("synthesis","Synthese")])
    content      = models.TextField()
    sort_order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_argument_nodes"
        ordering = ["sort_order"]
```

KI-Generierung via HTMX:
```html
<form hx-post="{% url 'projects:essay_generate' project.pk %}"
      hx-target="#argument-tree"
      hx-swap="innerHTML">
  <button type="submit">Argumentationsbaum generieren</button>
</form>
```

**Serien-UI** (`/projekte/<pk>/serie/`):
- Band-Übersicht mit Arc-Fortschritt pro Band
- `SharedCharacter`/`SharedWorld`-Konsistenz-Check via LLM
- Arc-Tracking: In welchem Band wird welcher Charakter-Arc aufgelöst?

### Teil C: ProjectTheme & ProjectMotif (Prio 2, neue Datei: `apps/projects/models_theme.py`)

```python
class ProjectTheme(models.Model):
    """
    Thematisches Fundament. 1:1 zu BookProject.
    Das Thema wird NIEMALS im Roman ausgesprochen —
    nur durch Figuren-Entscheidungen und Motive verkörpert.
    """
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(BookProject, on_delete=models.CASCADE,
                                   related_name="theme")
    core_question       = models.TextField()
    thematic_answer     = models.TextField(blank=True, default="")
    these_character_id  = models.UUIDField(null=True, blank=True)   # WeltenHub-Ref
    antithese_character_id = models.UUIDField(null=True, blank=True)
    synthesis_note      = models.TextField(blank=True, default="")

    class Meta:
        db_table = "wh_project_themes"


class ProjectMotif(models.Model):
    """
    Wiederkehrendes Motiv. N:1 zu BookProject.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project     = models.ForeignKey(BookProject, on_delete=models.CASCADE,
                                    related_name="motifs")
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    arc_start   = models.TextField(blank=True, default="")
    arc_end     = models.TextField(blank=True, default="")

    class Meta:
        db_table = "wh_project_motifs"


class MotifAppearance(models.Model):
    """
    Erscheinen eines Motivs in einer Szene.
    """
    motif        = models.ForeignKey(ProjectMotif, on_delete=models.CASCADE,
                                     related_name="appearances")
    outline_node = models.ForeignKey("projects.OutlineNode", on_delete=models.CASCADE)
    function     = models.CharField(max_length=20,
                                    choices=[("setup","Setup"),("echo","Echo"),
                                             ("inversion","Inversion"),("payoff","Payoff")])
    note         = models.TextField(blank=True, default="")

    class Meta:
        db_table = "wh_motif_appearances"
```

---

## Begründung

- **Drama-Dashboard** macht die dramaturgischen Felder (ADR-151) sichtbar und
  nutzbar — ohne Visualisierung sind `tension_numeric` und `outcome` wertlose
  Datenbankfelder. Das Dashboard ist der primäre Nutzen von ADR-151.
- **Chart.js via CDN** ist adäquat für eine interne Autoren-App.
  D3.js wäre Overkill; Canvas-native zu komplex. Chart.js liefert
  interaktive Kurven mit <5 Zeilen JavaScript.
- **Content-Type-UIs sind strukturell verschieden:** Ein Essay-Argumentationsbaum
  und ein Roman-Outline-Baum haben unterschiedliche Semantik, unterschiedliche
  Felder, unterschiedliche Generierungslogik. Erzwungene Vereinheitlichung
  ergibt schlechtere UX für beide.
- **HTMX für Lazy-Load der Chart-Daten** verhindert, dass das Projekt-Detail
  bei 50+ Kapiteln langsam wird. Chart-Daten werden erst nach Page-Load geladen.
- **ProjectTheme als eigenes Modell:** Thema ist ein vollständiges Konzept
  mit eigener Logik (These/Antithese-Figuren, Frage/Antwort-Struktur) —
  kein TextField auf BookProject.

---

## Abgelehnte Alternativen

**Spannungskurve als statisches PNG (Matplotlib):** Server-side Rendering
ist langsam und nicht interaktiv. Chart.js ist die bessere Wahl.

**Ein einheitliches Template für alle Content-Typen:** Ergibt ein
kompromissbelastetes UI, das für keinen Content-Typ optimal ist.

**Echtzeitkurve via WebSocket:** Overkill für dieses Szenario.
HTMX Polling oder SSE reicht für LLM-Generation-Updates.

**ArgumentNode als spezialisierter OutlineNode (mit type-Feld):**
Die unterschiedliche Semantik (claim/evidence vs. scene/chapter) rechtfertigt
ein eigenes Modell. Polymorphismus über einen type-Discriminator ist
fehleranfälliger und erschwert Queries.

---

## Konsequenzen

- Neue URLs: `projects/<pk>/drama/`, `projects/<pk>/drama/data/`, `projects/<pk>/essay/`
- `DramaDashboardService` in `apps/projects/services/drama_service.py`
- Template `templates/projects/drama_dashboard.html` + `essay_outline.html`
- `ArgumentNode` in `apps/projects/models.py` oder eigene Datei
- `ProjectTheme`, `ProjectMotif`, `MotifAppearance` in `apps/projects/models_theme.py`
- `Chart.js` CDN-Einbindung nur im Drama-Dashboard-Template (`{% block extra_js %}`)
- **Reihenfolge:** ADR-151 → ADR-153 → ADR-154 (harte Abhängigkeit)

---

**Referenzen:** ADR-151, ADR-153,  
`docs/adr/input/fe3_drama_dashboard.md`,  
`docs/adr/input/fe4_fe5_essay_series_frontend.md`,  
`docs/adr/input/p1d_theme_motif.md`,  
`docs/adr/input/schritt_07_thema_motiv.md`
