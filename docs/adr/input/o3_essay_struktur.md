# O3 — Essay/Sachbuch: Argumentationsstruktur

> `BookProject.content_type = "essay"` existiert — aber keinerlei
> essay-spezifische Struktur. Ein Essay ist kein Roman mit kürzeren Kapiteln.
> Er hat eine eigene Logik: These → Argument → Evidenz → Gegenargument → Synthese.

---

## O3.1 — Grundstruktur eines Essays (Literaturwissenschaftlich)

```
ESSAY vs. ROMAN:
    Roman:  Emotionale Wahrheit durch Figuren und Ereignisse
    Essay:  Intellektuelle Wahrheit durch Argumentation und Evidenz

ESSAY-STRUKTUR (klassisch):
    1. Hook / Exposition     → Leser in die Frage hineinziehen
    2. These                 → Die zentrale Behauptung
    3. Argument-Körper       → Beweise, Beispiele, Gegenargumente
    4. Synthese / Einsicht   → Was ist jetzt klarer als am Anfang?
    5. Coda                  → Resonanz, offene Frage, Ausblick

ARGUMENT-TYPEN (Toulmin-Modell):
    Claim        → Die Behauptung
    Ground       → Die Evidenz/Belege
    Warrant      → Die Brücke (warum belegt Ground die Claim?)
    Backing      → Unterstützung des Warrant
    Qualifier    → Einschränkung der Claim
    Rebuttal     → Gegenargument + Widerlegung
```

---

## O3.2 — Models (neue Datei: `apps/projects/models_essay.py`)

```python
"""
Essay-Struktur — ArgumentNode, EssayOutline, EssayThesis.

Für content_type in ('essay', 'nonfiction').
Toulmin-Argumentationsmodell als DB-Struktur.

Aktivierung: Wenn BookProject.content_type in ['essay', 'nonfiction']
             → EssayOutline.get_or_create(project=...)
"""
import uuid
from django.db import models


class EssayStructureTypeLookup(models.Model):
    """
    Lookup: Essay-Strukturmodelle.

    Seed-Werte:
        klassisch     | Klassischer Essay      | These-Argument-Synthese
        fünf_absatz   | Fünf-Absatz-Essay      | Standard akademisch
        montaigne     | Montaigne-Essay        | Mäandrierend, persönlich
        argumentativ  | Argumentativer Essay   | Strenger Toulmin-Aufbau
        narrativ      | Narrativer Essay       | Story-getrieben, persönlich
        vergleichend  | Vergleichender Essay   | A vs. B
    """
    code = models.SlugField(max_length=30, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_essay_structure_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Essay-Strukturtyp"
        verbose_name_plural = "Essay-Strukturtypen"

    def __str__(self):
        return self.label


class EssayOutline(models.Model):
    """
    Essay-Outline — strukturiertes Gegenstück zu OutlineVersion für Romane.

    1:1 zu BookProject (für content_type essay/nonfiction).
    Enthält:
        - Zentrale These
        - Übergeordnete Frage
        - Strukturmodell
        - Verbindung zum Argument-Netz
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="essay_outline",
    )
    structure_type = models.ForeignKey(
        EssayStructureTypeLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="essay_outlines",
    )

    # Kern-Elemente
    central_question = models.TextField(
        verbose_name="Zentrale Frage",
        help_text="Die Frage, die der Essay beantworten will. "
                  "Offener als die These — komplexer, facettenreicher.",
    )
    thesis = models.TextField(
        verbose_name="These",
        help_text="Die zentrale Behauptung des Essays. "
                  "Überprüfbar, spezifisch, vertretbar — nicht trivial.",
    )
    antithesis = models.TextField(
        blank=True, default="",
        verbose_name="Gegenthese",
        help_text="Die stärkste Gegenposition — muss im Essay ernst genommen werden.",
    )
    synthesis = models.TextField(
        blank=True, default="",
        verbose_name="Synthese",
        help_text="Was ergibt sich aus These + Gegenthese? "
                  "Tiefere Einsicht, die am Ende des Essays steht.",
    )

    # Für Sachbücher / längere Essays
    target_reader_knowledge = models.TextField(
        blank=True, default="",
        verbose_name="Vorwissen des Lesers",
        help_text="Was weiß der Leser bereits? Definiert Erklärungs-Tiefe.",
    )
    key_concepts = models.JSONField(
        default=list,
        verbose_name="Schlüsselbegriffe",
        help_text="Begriffe, die im Essay definiert und verwendet werden.",
    )
    sources_style = models.CharField(
        max_length=20,
        choices=[
            ("none",        "Keine Quellenangaben"),
            ("inline",      "Inline-Zitation"),
            ("footnotes",   "Fußnoten"),
            ("bibliography","Bibliographie"),
        ],
        default="none",
        verbose_name="Quellenformat",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_essay_outlines"
        verbose_name = "Essay-Outline"
        verbose_name_plural = "Essay-Outlines"

    def __str__(self):
        return f"Essay — {self.project.title}"


class ArgumentNodeTypeLookup(models.Model):
    """
    Lookup: Argument-Knoten-Typen (Toulmin-Modell + Essay-Struktur).

    Seed-Werte:
        hook         | Hook/Einstieg      | Leser hineinholen
        thesis       | These              | Zentrale Behauptung
        claim        | Argument/Claim     | Teilbehauptung
        ground       | Evidenz/Ground     | Beleg für Claim
        warrant      | Brücke/Warrant     | Verbindung Evidenz→Claim
        rebuttal     | Gegenargument      | Stärkste Gegenposition
        refutation   | Widerlegung        | Antwort auf Gegenargument
        example      | Beispiel           | Konkrete Illustration
        synthesis    | Synthese           | Zusammenführung
        coda         | Coda/Ausklang      | Resonanz, Ausblick
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    toulmin_role = models.CharField(
        max_length=30, blank=True,
        help_text="Entsprechende Rolle im Toulmin-Modell",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_argument_node_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Argument-Typ"
        verbose_name_plural = "Argument-Typen"

    def __str__(self):
        return self.label


class ArgumentNode(models.Model):
    """
    Ein Knoten im Argumentations-Netz des Essays.

    Entspricht einem OutlineNode für Romane — aber mit
    argumentativer statt dramaturgischer Logik.

    Hierarchie:
        EssayOutline
            └── ArgumentNode (thesis)
                    └── ArgumentNode (claim)
                            ├── ArgumentNode (ground)
                            ├── ArgumentNode (rebuttal)
                            └── ArgumentNode (refutation)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    essay_outline = models.ForeignKey(
        EssayOutline,
        on_delete=models.CASCADE,
        related_name="argument_nodes",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="children",
        verbose_name="Übergeordneter Knoten",
    )
    node_type = models.ForeignKey(
        ArgumentNodeTypeLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="argument_nodes",
    )

    # Inhalt
    claim = models.TextField(
        verbose_name="Behauptung / Inhalt",
        help_text="Die konkrete Aussage dieses Knotens.",
    )
    supporting_evidence = models.TextField(
        blank=True, default="",
        verbose_name="Belege / Evidenz",
        help_text="Fakten, Zitate, Studien, Beispiele",
    )
    source_notes = models.TextField(
        blank=True, default="",
        verbose_name="Quellen-Notizen",
    )

    # Stärke
    argument_strength = models.PositiveSmallIntegerField(
        default=5,
        help_text="Wie stark ist dieses Argument? (1=schwach, 10=zwingend)",
    )
    is_counterargument = models.BooleanField(
        default=False,
        verbose_name="Ist Gegenargument",
    )
    is_refuted = models.BooleanField(
        default=False,
        verbose_name="Ist widerlegt",
        help_text="Wurde dieses Gegenargument im Essay widerlegt?",
    )

    # Position
    order = models.PositiveIntegerField(default=0)
    target_words = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Ziel-Wörter",
    )
    content = models.TextField(blank=True, default="")
    word_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_argument_nodes"
        ordering = ["essay_outline", "order"]
        verbose_name = "Argument-Knoten"
        verbose_name_plural = "Argument-Knoten"

    def __str__(self):
        node_type_label = self.node_type.label if self.node_type else "?"
        return f"{node_type_label}: {self.claim[:60]}"

    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)

    @property
    def depth(self) -> int:
        """Tiefe im Argument-Baum (0 = Root)."""
        if not self.parent_id:
            return 0
        return 1 + self.parent.depth
```

---

## O3.3 — Migration: `0008_essay_structure.py`

```python
"""Migration 0008: EssayOutline, ArgumentNode, Lookups."""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0007_tension_architecture")]

    operations = [
        migrations.CreateModel(
            name="EssayStructureTypeLookup",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=30, unique=True)),
                ("label", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_essay_structure_type_lookup"},
        ),
        migrations.CreateModel(
            name="ArgumentNodeTypeLookup",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=80)),
                ("description", models.TextField(blank=True)),
                ("toulmin_role", models.CharField(max_length=30, blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_argument_node_type_lookup"},
        ),
        migrations.CreateModel(
            name="EssayOutline",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("project", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="essay_outline", to="projects.bookproject")),
                ("structure_type", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="essay_outlines", to="projects.essaystructuretypelookup")),
                ("central_question", models.TextField()),
                ("thesis", models.TextField()),
                ("antithesis", models.TextField(blank=True, default="")),
                ("synthesis", models.TextField(blank=True, default="")),
                ("target_reader_knowledge", models.TextField(blank=True, default="")),
                ("key_concepts", models.JSONField(default=list)),
                ("sources_style", models.CharField(default="none", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_essay_outlines"},
        ),
        migrations.CreateModel(
            name="ArgumentNode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("essay_outline", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="argument_nodes", to="projects.essayoutline")),
                ("parent", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="children", to="projects.argumentnode")),
                ("node_type", models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="argument_nodes", to="projects.argumentnodetypelookup")),
                ("claim", models.TextField()),
                ("supporting_evidence", models.TextField(blank=True, default="")),
                ("source_notes", models.TextField(blank=True, default="")),
                ("argument_strength", models.PositiveSmallIntegerField(default=5)),
                ("is_counterargument", models.BooleanField(default=False)),
                ("is_refuted", models.BooleanField(default=False)),
                ("order", models.PositiveIntegerField(default=0)),
                ("target_words", models.PositiveIntegerField(blank=True, null=True)),
                ("content", models.TextField(blank=True, default="")),
                ("word_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_argument_nodes"},
        ),
    ]
```

---

## O3.4 — Seed: Essay-Lookups

```python
ESSAY_STRUCTURE_TYPES = [
    dict(code="klassisch",    label="Klassischer Essay",      sort_order=1),
    dict(code="argumentativ", label="Argumentativer Essay",   sort_order=2),
    dict(code="narrativ",     label="Narrativer Essay",       sort_order=3),
    dict(code="vergleichend", label="Vergleichender Essay",   sort_order=4),
    dict(code="fuenf_absatz", label="Fünf-Absatz-Essay",      sort_order=5),
    dict(code="montaigne",    label="Montaigne-Essay",        sort_order=6),
]

ARGUMENT_NODE_TYPES = [
    dict(code="hook",       label="Hook/Einstieg",    toulmin_role="",        sort_order=1),
    dict(code="thesis",     label="These",            toulmin_role="claim",   sort_order=2),
    dict(code="claim",      label="Argument/Claim",   toulmin_role="claim",   sort_order=3),
    dict(code="ground",     label="Evidenz/Ground",   toulmin_role="ground",  sort_order=4),
    dict(code="warrant",    label="Brücke/Warrant",   toulmin_role="warrant", sort_order=5),
    dict(code="rebuttal",   label="Gegenargument",    toulmin_role="rebuttal",sort_order=6),
    dict(code="refutation", label="Widerlegung",      toulmin_role="backing", sort_order=7),
    dict(code="example",    label="Beispiel",         toulmin_role="ground",  sort_order=8),
    dict(code="synthesis",  label="Synthese",         toulmin_role="",        sort_order=9),
    dict(code="coda",       label="Coda/Ausklang",    toulmin_role="",        sort_order=10),
]
```

---

## O3.5 — Service: `EssayArgumentService`

```python
# apps/projects/services/essay_service.py
"""
EssayArgumentService — generiert Argumentationsstruktur via LLM.
action_code: essay_outline_generate
"""
import json
from aifw.service import sync_completion
from projects.models import (
    BookProject, EssayOutline, ArgumentNode, ArgumentNodeTypeLookup
)

ESSAY_SYSTEM = """
Du bist ein erfahrener Essay-Dramaturg. Du planst Argumentationsstrukturen.
Toulmin-Modell: Claim → Ground → Warrant → Rebuttal → Refutation.
Antworte nur als JSON.
"""

ESSAY_USER = """
Erstelle die Argumentationsstruktur für diesen Essay:

TITEL: {title}
GENRE/THEMA: {genre}
STRUKTURTYP: {structure_type}
THESE: {thesis}
GEGENTHESE: {antithesis}
ZIELWÖRTER: {word_count}

Erstelle 5-8 ArgumentNodes in logischer Reihenfolge:
[
  {{
    "node_type": "hook|thesis|claim|ground|warrant|rebuttal|refutation|example|synthesis|coda",
    "claim": "Die konkrete Aussage",
    "supporting_evidence": "Belege/Evidenz",
    "argument_strength": 1-10,
    "is_counterargument": false,
    "target_words": 300,
    "order": 1
  }}
]

Regel: Mindestens 1 rebuttal + 1 refutation. Synthesis am Ende.
"""


def generate_essay_outline(project: BookProject) -> EssayOutline:
    essay_outline = EssayOutline.objects.get(project=project)

    result = sync_completion(
        action_code="essay_outline_generate",
        messages=[
            {"role": "system", "content": ESSAY_SYSTEM},
            {"role": "user", "content": ESSAY_USER.format(
                title=project.title,
                genre=project.genre or "",
                structure_type=essay_outline.structure_type.label if essay_outline.structure_type else "klassisch",
                thesis=essay_outline.thesis,
                antithesis=essay_outline.antithesis,
                word_count=project.target_word_count or 3000,
            )},
        ],
    )

    if not result.success:
        raise RuntimeError(result.error)

    nodes_data = json.loads(result.content)
    type_cache = {t.code: t for t in ArgumentNodeTypeLookup.objects.all()}

    # Alte Nodes löschen, neue anlegen
    ArgumentNode.objects.filter(essay_outline=essay_outline).delete()

    for item in nodes_data:
        ArgumentNode.objects.create(
            essay_outline=essay_outline,
            node_type=type_cache.get(item.get("node_type")),
            claim=item.get("claim", ""),
            supporting_evidence=item.get("supporting_evidence", ""),
            argument_strength=item.get("argument_strength", 5),
            is_counterargument=item.get("is_counterargument", False),
            target_words=item.get("target_words"),
            order=item.get("order", 0),
        )

    return essay_outline
```

---

## O3.6 — Deployment

```bash
python manage.py migrate projects 0008_essay_structure
python manage.py seed_drama_lookups

# AIActionType anlegen:
#   essay_outline_generate

# Verify
python manage.py shell -c "
from projects.models import EssayStructureTypeLookup, ArgumentNodeTypeLookup
print('EssayStructureTypes:', EssayStructureTypeLookup.objects.count())
print('ArgumentNodeTypes:', ArgumentNodeTypeLookup.objects.count())
"
```

---

*writing-hub · Optimierung O3 · Essay/Sachbuch Argumentationsstruktur*
*Neue Tabellen: wh_essay_outlines, wh_argument_nodes + 2 Lookups*
*Toulmin-Modell: Claim → Ground → Warrant → Rebuttal → Refutation*
