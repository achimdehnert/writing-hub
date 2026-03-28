# O4 — Alle Formate: `MasterTimeline` & `CharacterKnowledgeState`

> Zeitkonsistenz ist der häufigste LLM-Fehler bei langen Texten:
> Figuren wissen etwas, das sie noch nicht wissen können.
> Dieses Model ist die Datenbank-Grundlage für den Informations-Tracker.

---

## O4.1 — Models (in `apps/projects/models_timeline.py`)

```python
"""
MasterTimeline — Story-Chronologie und Figuren-Wissensstand.

Romanstruktur-Framework Schritt 8.
Gilt für: Roman, Serie (pro Band), Essay (Argumentations-Chronologie).
"""
import uuid
from django.db import models


class NarrativeModelLookup(models.Model):
    """
    Lookup: Erzähl-Zeitmodelle.

    Seed-Werte:
        linear        | Linear              | A→B→C→D
        in_medias_res | In medias res       | Mitte→Anfang→Ende
        non_linear    | Nicht-linear        | Freie Reihenfolge
        parallel      | Parallel            | Mehrere Zeitstränge gleichzeitig
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_narrative_model_lookup"
        ordering = ["sort_order"]
        verbose_name = "Erzähl-Zeitmodell"


class MasterTimeline(models.Model):
    """
    Chronologie eines Buchprojekts. 1:1 zu BookProject.

    Speichert:
        - Erzähl-Zeitmodell (linear/in_medias_res/...)
        - Gesamtzeitraum der Story
        - Referenz auf Pre-Story-Ereignisse
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="master_timeline",
    )
    narrative_model = models.ForeignKey(
        NarrativeModelLookup,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="timelines",
    )
    story_time_span = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Story-Zeitraum",
        help_text="z.B. '3 Wochen', 'Sommer 1989', '200 Jahre'",
    )
    story_start_date = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Narrativer Startpunkt (kein DateField — kann fiktiv sein)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_master_timelines"
        verbose_name = "Master-Chronologie"


class TimelineEntry(models.Model):
    """
    Ein Ereignis auf der Story-Chronologie.

    entry_type:
        pre_story  → Ereignisse vor Kapitel 1 (Ghost, Vorgeschichte)
        story      → Ereignisse im Roman (verknüpft mit OutlineNode)
        post_story → Implied Future nach dem Ende
    """
    ENTRY_TYPES = [
        ("pre_story",  "Pre-Story (Vorgeschichte)"),
        ("story",      "Story (Handlung)"),
        ("post_story", "Post-Story (Implied Future)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timeline = models.ForeignKey(
        MasterTimeline, on_delete=models.CASCADE, related_name="entries",
    )
    node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="timeline_entries",
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default="story")
    story_date = models.CharField(
        max_length=100, blank=True, default="",
        help_text="z.B. 'Tag 3, 14:00' oder 'Montag, 3. März'",
    )
    event_description = models.TextField()
    characters_involved = models.JSONField(
        default=list,
        help_text="WeltenHub-UUIDs der beteiligten Figuren",
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_timeline_entries"
        ordering = ["timeline", "order"]
        verbose_name = "Chronologie-Eintrag"


class CharacterKnowledgeState(models.Model):
    """
    Figur-Wissensstand zu einem bestimmten Zeitpunkt (OutlineNode).

    Kritischste Anti-Pattern-Prevention:
    → Figur weiß in Kapitel 5, was sie erst in Kapitel 12 erfährt.

    Wird nach jedem dramaturgisch relevanten Ereignis aktualisiert.
    Beim Szenen-Generieren MUSS dieser Stand abgefragt werden.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="knowledge_states",
    )
    character_id = models.UUIDField(
        help_text="WeltenHub-Referenz der Figur",
    )
    as_of_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.CASCADE,
        related_name="knowledge_states",
        verbose_name="Wissensstand nach diesem Kapitel/Szene",
    )

    # Wissensstand
    knows = models.JSONField(
        default=list,
        verbose_name="Weiß",
        help_text="Liste von Informationen, die die Figur jetzt weiß.",
    )
    does_not_know = models.JSONField(
        default=list,
        verbose_name="Weiß nicht",
        help_text="Wichtige Informationen, die der Figur noch verborgen sind.",
    )
    suspects = models.JSONField(
        default=list,
        verbose_name="Vermutet",
        help_text="Was vermutet die Figur (ohne Gewissheit)?",
    )

    # Delta zur vorherigen Node
    newly_learned = models.JSONField(
        default=list,
        verbose_name="Neu erfahren",
        help_text="Was hat sie in diesem Kapitel/Szene neu erfahren?",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_character_knowledge_states"
        unique_together = [["project", "character_id", "as_of_node"]]
        ordering = ["project", "character_id", "as_of_node__order"]
        verbose_name = "Figur-Wissensstand"

    def to_prompt_context(self) -> str:
        """Gibt Wissensstand als Prompt-Kontext zurück."""
        lines = []
        if self.knows:
            lines.append(f"WEISSPUNKT: {'; '.join(self.knows)}")
        if self.does_not_know:
            lines.append(f"NOCH UNBEKANNT: {'; '.join(self.does_not_know)}")
        if self.suspects:
            lines.append(f"VERMUTET: {'; '.join(self.suspects)}")
        return "\n".join(lines)
```

---

## O4.2 — Migration `0009_master_timeline.py` (Kurzform)

```python
"""Migration 0009: MasterTimeline, TimelineEntry, CharacterKnowledgeState."""
# ... Standard-CreateModel für alle 4 Models
# Abhängigkeit: projects/0008_essay_structure
```

---

## O4.3 — Deployment

```bash
python manage.py migrate projects 0009_master_timeline
python manage.py seed_drama_lookups  # NarrativeModelLookup
```

---
---

# O5 — Alle Formate: `ContentTypeProfile` (Format-Config DB-getrieben)

> `BookProject.content_type` hat 5 Werte (novel/nonfiction/short_story/
> screenplay/essay) — aber keinerlei formatspezifische Generierungs-Config.
> Dieses Model macht Formatregeln DB-getrieben und ohne Code-Änderung anpassbar.

---

## O5.1 — Model (in `apps/projects/models.py` ergänzen)

```python
class ContentTypeProfile(models.Model):
    """
    Format-spezifische Generierungs-Konfiguration — DB-getrieben.

    Bindet an ContentTypeLookup und erweitert es um:
        - Empfohlenes Strukturmodell (outlinefw-Framework-Key)
        - Standard-Wortanzahl
        - Aktivierte Features (Drama-Felder, Essay-Felder, etc.)
        - authoringfw.get_format()-Key

    Admin-verwaltbar: Neue Formate ohne Code-Deployment.
    """
    content_type_lookup = models.OneToOneField(
        ContentTypeLookup,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # outlinefw
    default_framework_key = models.CharField(
        max_length=50, blank=True, default="three_act",
        help_text="outlinefw FRAMEWORKS-Key (three_act, save_the_cat, heros_journey, ...)",
    )
    default_chapter_count = models.PositiveSmallIntegerField(default=20)
    default_word_count = models.PositiveIntegerField(default=80000)

    # authoringfw
    authoringfw_format_key = models.CharField(
        max_length=30, blank=True, default="roman",
        help_text="authoringfw.get_format() Key (roman, essay, serie, scientific)",
    )

    # Feature-Flags (welche Module sind für dieses Format relevant?)
    has_dramatic_arc = models.BooleanField(
        default=True,
        help_text="Roman/Serie: OutlineNode.outcome, emotion, tension",
    )
    has_essay_outline = models.BooleanField(
        default=False,
        help_text="Essay/Sachbuch: EssayOutline + ArgumentNode",
    )
    has_world_building = models.BooleanField(
        default=True,
        help_text="Roman/Fantasy: WeltenHub-Integration aktiv",
    )
    has_series_arc = models.BooleanField(
        default=False,
        help_text="Serie: SeriesArc-Features aktiv",
    )
    has_narrative_voice = models.BooleanField(
        default=True,
        help_text="NarrativeVoice-Model anlegen beim Projekt-Start",
    )
    has_theme = models.BooleanField(
        default=True,
        help_text="ProjectTheme aktiv",
    )

    # Qualitäts-Dimensionen
    quality_dimension_codes = models.JSONField(
        default=list,
        help_text="QualityDimension codes, die für dieses Format relevant sind",
    )

    # LLM-Prompting
    system_prompt_prefix = models.TextField(
        blank=True, default="",
        help_text="Format-spezifischer System-Prompt-Prefix für alle Generierungen",
    )

    class Meta:
        db_table = "wh_content_type_profiles"
        verbose_name = "Format-Profil"
        verbose_name_plural = "Format-Profile"

    def __str__(self):
        return f"Profil: {self.content_type_lookup.name}"

    def get_authoringfw_format(self):
        """Gibt authoringfw FormatProfile zurück."""
        from authoringfw.formats.base import get_format
        try:
            return get_format(self.authoringfw_format_key)
        except Exception:
            return None
```

---

## O5.2 — Seed: ContentTypeProfile

```python
# In seed_drama_lookups.py:
from projects.models import ContentTypeLookup, ContentTypeProfile

CONTENT_TYPE_PROFILES = [
    dict(
        slug="roman",
        profile=dict(
            default_framework_key="three_act",
            default_chapter_count=20,
            default_word_count=90000,
            authoringfw_format_key="roman",
            has_dramatic_arc=True, has_essay_outline=False,
            has_world_building=True, has_series_arc=False,
            has_narrative_voice=True, has_theme=True,
            quality_dimension_codes=["style", "pacing", "dialogue", "character", "scene"],
        ),
    ),
    dict(
        slug="kurzgeschichte",
        profile=dict(
            default_framework_key="dan_harmon",
            default_chapter_count=5,
            default_word_count=8000,
            authoringfw_format_key="roman",
            has_dramatic_arc=True, has_essay_outline=False,
            quality_dimension_codes=["style", "pacing", "scene"],
        ),
    ),
    dict(
        slug="essay",
        profile=dict(
            default_framework_key="",  # kein outlinefw-Framework für Essays
            default_chapter_count=8,
            default_word_count=4000,
            authoringfw_format_key="essay",
            has_dramatic_arc=False, has_essay_outline=True,
            has_world_building=False, has_narrative_voice=True, has_theme=True,
            quality_dimension_codes=["style", "clarity", "argument_strength"],
        ),
    ),
    dict(
        slug="sachbuch",
        profile=dict(
            default_framework_key="",
            default_chapter_count=15,
            default_word_count=60000,
            authoringfw_format_key="scientific",
            has_dramatic_arc=False, has_essay_outline=True,
            has_world_building=False, has_narrative_voice=True, has_theme=True,
            quality_dimension_codes=["clarity", "argument_strength", "style"],
        ),
    ),
]

for item in CONTENT_TYPE_PROFILES:
    ct = ContentTypeLookup.objects.filter(slug=item["slug"]).first()
    if ct:
        ContentTypeProfile.objects.update_or_create(
            content_type_lookup=ct, defaults=item["profile"]
        )
```

---
---

# O6 — Gesamtübersicht: Alle Optimierungen

## O6.1 — Vollständige Tabellen-Übersicht (Prio-1 + O1–O5)

```
PRIO-1 (A–D) — bereits spezifiziert:
    wh_scene_outcome_lookup          ← ja
    wh_pov_type_lookup               ← ja
    wh_tension_level_lookup          ← ja
    wh_character_arc_type_lookup     ← ja
    wh_tempus_lookup                 ← ja
    wh_narrative_distance_lookup     ← ja
    wh_vocabulary_level_lookup       ← ja
    wh_narrative_voices              ← ja
    wh_project_themes                ← ja
    wh_motif_type_lookup             ← ja
    wh_project_motifs                ← ja
    wh_motif_appearances             ← ja

O1 — Spannungsarchitektur:
    wh_foreshadowing_type_lookup
    wh_foreshadowing_entries
    wh_turning_point_type_lookup
    wh_project_turning_points

O2 — Serie:
    wh_series_arc_type_lookup
    wh_series_arcs
    wh_series_volume_roles
    wh_series_character_continuities

O3 — Essay:
    wh_essay_structure_type_lookup
    wh_argument_node_type_lookup
    wh_essay_outlines
    wh_argument_nodes

O4 — Timeline:
    wh_narrative_model_lookup
    wh_master_timelines
    wh_timeline_entries
    wh_character_knowledge_states

O5 — ContentTypeProfile:
    wh_content_type_profiles
```

**Gesamt: 33 neue Tabellen** (alle `wh_`-prefixed, alle idempotent seedbar)

---

## O6.2 — Format-Matrix: Welche Features für welches Format?

```
FEATURE                        | Roman | Serie | Essay | Sachbuch | Kurzgeschichte
───────────────────────────────┼───────┼───────┼───────┼──────────┼───────────────
OutlineNode Drama-Felder       |  ✅   |  ✅   |  ❌   |   ❌     |  ✅
ProjectCharacterLink Arc       |  ✅   |  ✅   |  ❌   |   ❌     |  ✅
NarrativeVoice                 |  ✅   |  ✅   |  ✅   |   ✅     |  ✅
ProjectTheme                   |  ✅   |  ✅   |  ✅   |   ✅     |  ✅
ForeshadowingEntry             |  ✅   |  ✅   |  ❌   |   ❌     |  ⚡
ProjectTurningPoint            |  ✅   |  ✅   |  ❌   |   ❌     |  ✅
SeriesArc                      |  ❌   |  ✅   |  ❌   |   ❌     |  ❌
SeriesCharacterContinuity      |  ❌   |  ✅   |  ❌   |   ❌     |  ❌
EssayOutline + ArgumentNode    |  ❌   |  ❌   |  ✅   |   ✅     |  ❌
MasterTimeline                 |  ✅   |  ✅   |  ❌   |   ❌     |  ⚡
CharacterKnowledgeState        |  ✅   |  ✅   |  ❌   |   ❌     |  ❌
ContentTypeProfile             |  ✅   |  ✅   |  ✅   |   ✅     |  ✅
```
✅ voll | ⚡ optional | ❌ nicht relevant

---

## O6.3 — Empfohlene Deployment-Reihenfolge

```bash
# PRIO-1 (bereits spezifiziert)
python manage.py migrate projects 0004_dramaturgic_fields
python manage.py migrate worlds   0004_character_arc_fields
python manage.py migrate projects 0005_narrative_voice
python manage.py migrate projects 0006_theme_motif

# O1 — Spannung
python manage.py migrate projects 0007_tension_architecture

# O2 — Serie
python manage.py migrate series   0003_series_arc

# O3 — Essay
python manage.py migrate projects 0008_essay_structure

# O4 — Timeline
python manage.py migrate projects 0009_master_timeline

# O5 — ContentTypeProfile
python manage.py migrate projects 0010_content_type_profile

# Alles seeden (idempotent)
python manage.py seed_drama_lookups

# AIActionTypes in Admin (einmalig):
#   character_arc_generate
#   theme_generate
#   essay_outline_generate
#   series_continuity_extract
#   foreshadow_plan
#   turning_points_generate
```

---

## O6.4 — Impact-Zusammenfassung

| Optimierung | Löst | Für |
|------------|------|-----|
| O1 Spannung | Chekhov's Gun, Wendepunkte als DB-Objekte | Roman |
| O2 Serie | Band-übergreifende Kontinuität, Arc-Tracking | Serie |
| O3 Essay | Toulmin-Argumentationsstruktur | Essay, Sachbuch |
| O4 Timeline | Zeitkonsistenz, Figur-Wissensstand | Roman, Serie |
| O5 ContentTypeProfile | Format-spezifische Generierungs-Config DB-getrieben | Alle |

---

*writing-hub · O4–O6 · Timeline, ContentTypeProfile, Gesamtübersicht*
*Gesamt neue Tabellen: 33 | Gesamt neue Models: ~35 | Migrations: 0004–0010*
