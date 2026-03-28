"""
Zeitstruktur, Foreshadowing, OutlineSequence (ADR-156)

MasterTimeline + TimelineEntry: Story-Chronologie
ForeshadowingEntry: Chekhov's Guns (Setup-Payoff-Paare)
PlannedFlashback: Rückblenden-Planung
OutlineSequence: Mesostruktur-Zwischenebene
"""
from __future__ import annotations

import uuid

from django.db import models


class NarrativeModelLookup(models.Model):
    """
    Lookup: Erzähl-Zeitmodelle (ADR-156).

    Seed-Werte:
        linear        | Linear
        in_medias_res | In medias res
        non_linear    | Nicht-linear
        parallel      | Parallel
    """

    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_narrative_model_lookup"
        ordering = ["sort_order"]
        verbose_name = "Erzähl-Zeitmodell"
        verbose_name_plural = "Erzähl-Zeitmodelle"

    def __str__(self):
        return f"{self.code} — {self.label}"


class MasterTimeline(models.Model):
    """
    Story-Chronologie eines Buchprojekts. 1:1 zu BookProject (ADR-156).

    Trennt Story Time (was wirklich passiert) von Discourse Time (wie erzählt).
    story_start_date ist CharField — fiktive Zeitangaben passen nicht in DateField.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="master_timeline",
    )
    narrative_model = models.ForeignKey(
        NarrativeModelLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="timelines",
        verbose_name="Erzähl-Zeitmodell",
    )
    story_time_span = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Story-Zeitraum",
        help_text="z.B. '3 Wochen', 'Sommer 1989', '200 Jahre Zukunft'",
    )
    story_start_date = models.CharField(
        max_length=100, blank=True, default="",
        verbose_name="Story-Startpunkt",
        help_text="Narrativer Startpunkt (kein DateField — kann fiktiv sein).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_master_timelines"
        verbose_name = "Master-Chronologie"
        verbose_name_plural = "Master-Chronologien"

    def __str__(self):
        return f"Timeline — {self.project.title}"


class TimelineEntry(models.Model):
    """
    Ein Ereignis auf der Story-Chronologie (ADR-156).

    entry_type:
        pre_story  → Vorgeschichte (Ghost, Traumata)
        story      → Handlung (verknüpft mit OutlineNode)
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
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="timeline_entries",
        verbose_name="Verknüpfte Szene/Kapitel",
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default="story")
    story_date = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Narrativer Zeitpunkt z.B. 'Tag 3, 14:00'",
    )
    event_description = models.TextField(verbose_name="Ereignis-Beschreibung")
    characters_involved = models.JSONField(
        default=list,
        help_text="WeltenHub-UUIDs der beteiligten Figuren",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "wh_timeline_entries"
        ordering = ["timeline", "order"]
        verbose_name = "Chronologie-Eintrag"
        verbose_name_plural = "Chronologie-Einträge"

    def __str__(self):
        date = self.story_date or "—"
        return f"{self.get_entry_type_display()} | {date}: {self.event_description[:60]}"


class ForeshadowingTypeLookup(models.Model):
    """
    Lookup: Typen von Foreshadowing (ADR-156).

    Seed-Werte:
        objekt     | Objekt
        dialog     | Dialog
        bild       | Bild/Symbol
        name       | Name
        verhalten  | Verhalten
        atmosphaere | Atmosphäre
    """

    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_foreshadowing_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Foreshadowing-Typ"
        verbose_name_plural = "Foreshadowing-Typen"

    def __str__(self):
        return f"{self.code} — {self.label}"


class ForeshadowingEntry(models.Model):
    """
    Eine Chekhov's Gun: Setup-Payoff-Paar (ADR-156).

    Kritische LLM-Funktion: Beim Generieren von Szenen nahe `resolved_in`
    MUSS das LLM alle offenen ForeshadowingEntries (status=planted) kennen.

    Status-Übergänge:
        open → planted (Setup eingebaut) → resolved (Payoff eingebaut)
        planted → abandoned (bewusst aufgegeben)
    """

    STATUS = [
        ("open",      "Geplant (noch nicht eingebaut)"),
        ("planted",   "Eingebaut (wartet auf Auflösung)"),
        ("resolved",  "Aufgelöst"),
        ("abandoned", "Aufgegeben"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="foreshadowing_entries",
    )
    foreshadow_type = models.ForeignKey(
        ForeshadowingTypeLookup,
        on_delete=models.SET_NULL, null=True, blank=True,
    )
    label = models.CharField(
        max_length=200,
        verbose_name="Bezeichner",
        help_text="Kurzer Name: 'Die Narbe an seiner Hand'",
    )
    setup_description = models.TextField(
        verbose_name="Setup",
        help_text="Was wird eingeführt? Wie? In welchem Kontext?",
    )
    payoff_description = models.TextField(
        blank=True, default="",
        verbose_name="Payoff",
        help_text="Wie wird es aufgelöst?",
    )
    thematic_meaning = models.TextField(
        blank=True, default="",
        verbose_name="Thematische Bedeutung",
    )
    introduced_in = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="foreshadowing_setups",
        verbose_name="Eingeführt in",
    )
    resolved_in = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="foreshadowing_payoffs",
        verbose_name="Aufgelöst in",
    )
    status = models.CharField(max_length=20, choices=STATUS, default="open")
    abandonment_reason = models.TextField(
        blank=True, default="",
        verbose_name="Grund für Aufgabe",
    )
    is_planted = models.BooleanField(
        default=False,
        help_text="Shortcut-Flag: True wenn status='planted' oder 'resolved'",
    )
    setup_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="foreshadowing_setups_alt",
        verbose_name="Setup-Node (Fair-Play-Check)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_foreshadowing_entries"
        ordering = ["project", "status", "label"]
        verbose_name = "Foreshadowing-Eintrag"
        verbose_name_plural = "Foreshadowing-Einträge"

    def __str__(self):
        return f"{self.label} [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        self.is_planted = self.status in ("planted", "resolved")
        if self.setup_node is None and self.introduced_in is not None:
            self.setup_node = self.introduced_in
        super().save(*args, **kwargs)


class PlannedFlashback(models.Model):
    """
    Geplante Rückblende: Wo, wie und warum (ADR-156).

    Unterschied zu TimelineEntry:
        TimelineEntry = Was passiert chronologisch (Story Time)
        PlannedFlashback = Wie wird ein vergangenes Ereignis erzählt (Discourse Time)
    """

    TECHNIQUES = [
        ("hard_cut",      "Hard Cut (abrupter Wechsel)"),
        ("trigger",       "Trigger (Sinneseindruck)"),
        ("chapter_break", "Kapitelwechsel (ganzes Kapitel als Rückblende)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="planned_flashbacks",
    )
    trigger_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="flashback_triggers",
        verbose_name="Ausgelöst in Szene",
    )
    content_summary = models.TextField(verbose_name="Inhalt der Rückblende")
    dramatic_purpose = models.TextField(
        verbose_name="Dramaturgischer Zweck",
        help_text="Warum jetzt? Was trägt dieser Flashback zur Szene/Arc bei?",
    )
    technique = models.CharField(max_length=20, choices=TECHNIQUES, default="trigger")
    return_technique = models.TextField(
        blank=True, default="",
        verbose_name="Rückkehr-Technik",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_planned_flashbacks"
        verbose_name = "Geplante Rückblende"
        verbose_name_plural = "Geplante Rückblenden"

    def __str__(self):
        return f"Flashback ({self.get_technique_display()}) — {self.project.title}"


def get_open_foreshadowing_context(project, current_node) -> str:
    """
    Layer-8-Kontext (ADR-150): alle offenen Foreshadowing-Einträge
    die vor der aktuellen Szene eingeführt wurden und noch nicht aufgelöst sind.
    """
    entries = ForeshadowingEntry.objects.filter(
        project=project,
        status="planted",
        introduced_in__order__lt=current_node.order,
    ).select_related("foreshadow_type")

    if not entries.exists():
        return ""

    lines = ["OFFENE CHEKHOV'S GUNS (müssen irgendwann aufgelöst werden):"]
    for e in entries:
        ftype = e.foreshadow_type.label if e.foreshadow_type else "?"
        lines.append(f"  - [{ftype}] {e.label}: {e.setup_description[:100]}")
    return "\n".join(lines)
