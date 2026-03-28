# Prio-1 · Schritt C — `NarrativeVoice` Model

> **Ziel:** Neues Model `NarrativeVoice` (1:1 zu `BookProject`) speichert
> die Erzählperspektive als DB-Objekt — vollständig kompatibel mit
> `authoringfw.StyleProfile` (tone, pov, tense, vocabulary_level, sentence_rhythm).
> Prompt-Injection via `iil-promptfw`.

---

## C.1 — Neue Lookup-Tabellen

In `apps/projects/models_lookups_drama.py` ergänzen:

```python
class TempusLookup(models.Model):
    """
    Lookup: Erzähl-Tempus.
    Kompatibel mit authoringfw.StyleProfile.tense.

    Seed-Werte:
        past    | Präteritum  | Standard im deutschsprachigen Roman
        present | Präsens     | Erhöhte Unmittelbarkeit, für Thriller/Jugend
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    authoringfw_key = models.CharField(max_length=20, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_tempus_lookup"
        ordering = ["sort_order"]
        verbose_name = "Tempus"
        verbose_name_plural = "Tempora"

    def __str__(self):
        return self.label


class NarrativeDistanceLookup(models.Model):
    """
    Lookup: Narrative Distanz (Nähe zur Figur).

    Seed-Werte:
        close   | Nah     | Fast im Kopf der Figur, jede Wahrnehmung gefärbt
        medium  | Mittel  | Beobachten mit leichtem Abstand
        distant | Weit    | Kamera-Perspektive, nur Äußeres sichtbar
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_narrative_distance_lookup"
        ordering = ["sort_order"]
        verbose_name = "Narrative Distanz"
        verbose_name_plural = "Narrative Distanzen"

    def __str__(self):
        return self.label


class VocabularyLevelLookup(models.Model):
    """
    Lookup: Wortschatz-Niveau.
    Kompatibel mit authoringfw.StyleProfile.vocabulary_level.

    Seed-Werte:
        simple     | Einfach      | Kurze Sätze, alltäglicher Wortschatz
        educated   | Gebildet     | Differenzierter Wortschatz, variierende Satzlänge
        literary   | Literarisch  | Reiche Sprache, Metaphern, komplexe Strukturen
        colloquial | Umgangsspr.  | Dialekt, Slang, gesprochene Sprache
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    authoringfw_key = models.CharField(max_length=30, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_vocabulary_level_lookup"
        ordering = ["sort_order"]
        verbose_name = "Wortschatz-Niveau"
        verbose_name_plural = "Wortschatz-Niveaus"

    def __str__(self):
        return self.label
```

---

## C.2 — `NarrativeVoice` Model (neue Datei: `apps/projects/models_narrative.py`)

```python
"""
NarrativeVoice — Erzählstimme eines BookProject.

1:1 zu BookProject. Vollständig kompatibel mit authoringfw.StyleProfile.
Kann als Prompt-Kontext via iil-promptfw injiziert werden.
"""
import uuid
from django.db import models


class NarrativeVoice(models.Model):
    """
    Erzählstimme eines Buchprojekts.

    Dieses Objekt ist die Quelle der Wahrheit für alle stilistischen
    Entscheidungen auf Projekt-Ebene. Es wird bei der Szenen-Generierung
    in den Prompt injiziert.

    Kompatibilität:
        authoringfw.StyleProfile.pov          → pov_type (FK)
        authoringfw.StyleProfile.tense        → tempus (FK)
        authoringfw.StyleProfile.vocabulary_level → vocabulary_level (FK)
        authoringfw.StyleProfile.tone         → tone (TextField)
        authoringfw.StyleProfile.sentence_rhythm → sentence_rhythm (FK → SentenceRhythmLookup)
        authoringfw.StyleProfile.author_signature → project.writing_style
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="narrative_voice",
        verbose_name="Projekt",
    )

    # ── Perspektive ──────────────────────────────────────────────────────────
    pov_type = models.ForeignKey(
        "projects.POVTypeLookup",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="narrative_voices",
        verbose_name="POV-Typ",
        help_text="Erzählperspektive für das gesamte Projekt "
                  "(kann per Kapitel in OutlineNode überschrieben werden)",
    )
    tempus = models.ForeignKey(
        "projects.TempusLookup",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="narrative_voices",
        verbose_name="Tempus",
    )
    distance = models.ForeignKey(
        "projects.NarrativeDistanceLookup",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="narrative_voices",
        verbose_name="Narrative Distanz",
    )

    # ── Stil ──────────────────────────────────────────────────────────────────
    vocabulary_level = models.ForeignKey(
        "projects.VocabularyLevelLookup",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="narrative_voices",
        verbose_name="Wortschatz-Niveau",
    )
    tone = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Grundton",
        help_text="z.B. 'düster, ironisch' | 'warmherzig, humorvoll' "
                  "→ authoringfw.StyleProfile.tone",
    )
    irony_level = models.CharField(
        max_length=20, blank=True, default="none",
        choices=[
            ("none",   "Keine Ironie"),
            ("mild",   "Leichte Ironie"),
            ("heavy",  "Starke Ironie"),
        ],
        verbose_name="Ironie-Level",
    )
    imagery_density = models.CharField(
        max_length=20, blank=True, default="functional",
        choices=[
            ("sparse",      "Sparsam"),
            ("functional",  "Funktional"),
            ("rich",        "Reich"),
            ("poetic",      "Poetisch"),
        ],
        verbose_name="Bild-Dichte",
    )
    sentence_length_profile = models.CharField(
        max_length=20, blank=True, default="varied",
        choices=[
            ("short",   "Kurz (Tempo, Thriller)"),
            ("varied",  "Variiert (empfohlen)"),
            ("long",    "Lang (Literarisch)"),
        ],
        verbose_name="Satzlänge-Profil",
    )

    # ── Stil-Direktiven ───────────────────────────────────────────────────────
    style_mandates = models.JSONField(
        default=list,
        verbose_name="Stil-Gebote",
        help_text="Was MUSS in jedem generierten Text präsent sein? "
                  "Liste von Strings. Wird in LLM-Prompt injiziert.",
    )
    style_prohibitions = models.JSONField(
        default=list,
        verbose_name="Stil-Verbote",
        help_text="Was darf NIEMALS vorkommen? "
                  "Ergänzt WritingStyle.taboo_list auf Projekt-Ebene.",
    )

    # ── authoringfw-Prompt-Block (gecacht) ────────────────────────────────────
    authoringfw_prompt_block = models.TextField(
        blank=True, default="",
        verbose_name="authoringfw Prompt-Block (gecacht)",
        help_text="Wird von to_style_profile() generiert und gecacht. "
                  "Wird bei Speichern automatisch aktualisiert.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_narrative_voices"
        verbose_name = "Narrative Voice"
        verbose_name_plural = "Narrative Voices"

    def __str__(self):
        return f"NarrativeVoice — {self.project.title}"

    def to_style_profile(self):
        """
        Konvertiert NarrativeVoice → authoringfw.StyleProfile.
        Für direkte Injection in LLM-Prompts.

        Returns:
            authoringfw.StyleProfile
        """
        from authoringfw import StyleProfile

        return StyleProfile(
            tone=self.tone or "",
            pov=self.pov_type.authoringfw_key if self.pov_type else "",
            tense=self.tempus.authoringfw_key if self.tempus else "",
            vocabulary_level=self.vocabulary_level.authoringfw_key if self.vocabulary_level else "",
            sentence_rhythm=self.sentence_length_profile,
        )

    def to_prompt_constraints(self) -> str:
        """
        Gibt einen fertigen Prompt-Constraint-String zurück.
        Direkt verwendbar als {voice_constraints} in promptfw-Templates.
        """
        profile = self.to_style_profile()
        base = profile.to_constraints()

        extras = []
        if self.style_mandates:
            extras.append("IMMER: " + "; ".join(self.style_mandates))
        if self.style_prohibitions:
            extras.append("NIE: " + "; ".join(self.style_prohibitions))

        return base + ("\n" + "\n".join(extras) if extras else "")

    def save(self, *args, **kwargs):
        # Prompt-Block bei jedem Speichern aktualisieren
        try:
            self.authoringfw_prompt_block = self.to_prompt_constraints()
        except Exception:
            pass  # Graceful degradation falls authoringfw nicht verfügbar
        super().save(*args, **kwargs)
```

---

## C.3 — Migration: `apps/projects/migrations/0005_narrative_voice.py`

```python
"""
Migration 0005: NarrativeVoice + Tempus/Distance/Vocabulary Lookups.

Neue Tabellen:
    wh_tempus_lookup
    wh_narrative_distance_lookup
    wh_vocabulary_level_lookup
    wh_narrative_voices
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0004_dramaturgic_fields"),
    ]

    operations = [
        # ── Lookups ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name="TempusLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=50)),
                ("description", models.TextField(blank=True)),
                ("authoringfw_key", models.CharField(max_length=20, blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_tempus_lookup", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="NarrativeDistanceLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=50)),
                ("description", models.TextField(blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_narrative_distance_lookup", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="VocabularyLevelLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=20, unique=True)),
                ("label", models.CharField(max_length=80)),
                ("authoringfw_key", models.CharField(max_length=30, blank=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"db_table": "wh_vocabulary_level_lookup", "ordering": ["sort_order"]},
        ),
        # ── NarrativeVoice ───────────────────────────────────────────────────
        migrations.CreateModel(
            name="NarrativeVoice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("project", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="narrative_voice",
                    to="projects.bookproject",
                    verbose_name="Projekt",
                )),
                ("pov_type", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="narrative_voices",
                    to="projects.povtypelookup",
                )),
                ("tempus", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="narrative_voices",
                    to="projects.tempuslookup",
                )),
                ("distance", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="narrative_voices",
                    to="projects.narrativedistancelookup",
                )),
                ("vocabulary_level", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="narrative_voices",
                    to="projects.vocabularylevellookup",
                )),
                ("tone", models.CharField(blank=True, default="", max_length=200)),
                ("irony_level", models.CharField(blank=True, default="none", max_length=20)),
                ("imagery_density", models.CharField(blank=True, default="functional", max_length=20)),
                ("sentence_length_profile", models.CharField(blank=True, default="varied", max_length=20)),
                ("style_mandates", models.JSONField(default=list)),
                ("style_prohibitions", models.JSONField(default=list)),
                ("authoringfw_prompt_block", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_narrative_voices"},
        ),
    ]
```

---

## C.4 — Seed: `seed_drama_lookups.py` ergänzen

```python
from projects.models import TempusLookup, NarrativeDistanceLookup, VocabularyLevelLookup

TEMPORA = [
    dict(code="past",    label="Präteritum", authoringfw_key="past",    sort_order=1,
         description="Standard im deutschsprachigen Roman."),
    dict(code="present", label="Präsens",    authoringfw_key="present", sort_order=2,
         description="Erhöhte Unmittelbarkeit."),
]

NARRATIVE_DISTANCES = [
    dict(code="close",   label="Nah",    sort_order=1,
         description="Fast im Kopf der Figur, jede Wahrnehmung gefärbt."),
    dict(code="medium",  label="Mittel", sort_order=2,
         description="Beobachten mit leichtem Abstand."),
    dict(code="distant", label="Weit",   sort_order=3,
         description="Kamera-Perspektive, nur Äußeres sichtbar."),
]

VOCABULARY_LEVELS = [
    dict(code="simple",     label="Einfach",       authoringfw_key="simple",     sort_order=1),
    dict(code="educated",   label="Gebildet",      authoringfw_key="educated",   sort_order=2),
    dict(code="literary",   label="Literarisch",   authoringfw_key="literary",   sort_order=3),
    dict(code="colloquial", label="Umgangsspr.",   authoringfw_key="colloquial", sort_order=4),
]

# In handle():
self._seed(TempusLookup, TEMPORA, "TempusLookup")
self._seed(NarrativeDistanceLookup, NARRATIVE_DISTANCES, "NarrativeDistanceLookup")
self._seed(VocabularyLevelLookup, VOCABULARY_LEVELS, "VocabularyLevelLookup")
```

---

## C.5 — promptfw Template-Integration

Erstelle `PROMPT_TEMPLATES_DIR/scene_write.j2`:

```jinja2
{# scene_write.j2 — Szenen-Schreib-Template #}
ERZÄHLSTIMME:
{{ voice_constraints }}

SZENE:
- POV: {{ pov_name }}
- Ort: {{ location }}
- Emotion Start: {{ emotion_start }}
- Emotion Ende: {{ emotion_end }}
- Ziel der Figur: {{ scene_goal }}
- Konflikt: {{ scene_conflict }}
- Outcome: {{ outcome_label }}

THEMA: {{ theme_question }}

Schreibe ca. {{ word_count }} Wörter. Zeigen, nicht erklären. Kein Info-Dump.
```

Verwendung:

```python
from promptfw import PromptStack

stack = PromptStack()
messages = stack.render_to_messages(
    "scene_write",
    voice_constraints=project.narrative_voice.to_prompt_constraints(),
    pov_name=pov_character_name,
    emotion_start=node.emotion_start,
    emotion_end=node.emotion_end,
    scene_goal=node.description,
    scene_conflict="...",
    outcome_label=node.outcome.label if node.outcome else "",
    theme_question=project.theme.core_question if hasattr(project, "theme") else "",
    word_count=node.target_words or 1500,
    location=node.story_timeline_position,
)
```

---

## C.6 — Admin

```python
from .models import NarrativeVoice

class NarrativeVoiceInline(admin.StackedInline):
    model = NarrativeVoice
    extra = 0
    fieldsets = [
        ("Perspektive", {"fields": ["pov_type", "tempus", "distance"]}),
        ("Stil",        {"fields": ["vocabulary_level", "tone", "irony_level",
                                    "imagery_density", "sentence_length_profile"]}),
        ("Direktiven",  {"fields": ["style_mandates", "style_prohibitions"]}),
        ("Gecacht",     {"fields": ["authoringfw_prompt_block"],
                         "classes": ["collapse"]}),
    ]

# Dem BookProjectAdmin hinzufügen:
# inlines = [..., NarrativeVoiceInline]
```

---

## C.7 — Deployment

```bash
python manage.py migrate projects 0005_narrative_voice
python manage.py seed_drama_lookups

# Verify
python manage.py shell -c "
from projects.models import NarrativeVoice, TempusLookup
print('Tempora:', TempusLookup.objects.count())
# Test to_style_profile
from projects.models import BookProject
p = BookProject.objects.first()
if p:
    nv, _ = NarrativeVoice.objects.get_or_create(project=p)
    print('StyleProfile:', nv.to_style_profile())
"
```

---

*writing-hub · Prio-1 Schritt C von 4 · NarrativeVoice Model*
*Packages: iil-authoringfw 0.8.0 · iil-promptfw*
