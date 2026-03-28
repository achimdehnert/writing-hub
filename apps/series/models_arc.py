"""
Serien-Dramaturgie — SeriesArc, SeriesVolumeRole, SeriesCharacterContinuity (ADR-155)
"""
from __future__ import annotations

import uuid

from django.db import models


class SeriesArc(models.Model):
    """
    Übergreifender dramaturgischer Arc einer Buchserie. 1:1 zu BookSeries (ADR-155).

    Speichert den SERIEN-WEITEN want/need/false_belief/true_belief —
    tiefer als die Band-spezifischen Felder auf ProjectCharacterLink.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series = models.OneToOneField(
        "series.BookSeries",
        on_delete=models.CASCADE,
        related_name="arc",
    )
    arc_type = models.ForeignKey(
        "core.SeriesArcTypeLookup",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="series_arcs",
    )
    series_want = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Want",
        help_text="Was verfolgt die Hauptfigur über ALLE Bände hinweg?",
    )
    series_need = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Need",
        help_text="Was braucht sie wirklich — wird erst im letzten Band klar.",
    )
    series_false_belief = models.TextField(
        blank=True, default="",
        verbose_name="Überzeugung Serien-Beginn",
    )
    series_true_belief = models.TextField(
        blank=True, default="",
        verbose_name="Erkenntnis Serien-Ende",
    )
    overarching_conflict = models.TextField(
        blank=True, default="",
        verbose_name="Übergreifender Konflikt",
        help_text="Antagonist / Hindernis, das über alle Bände aktiv ist.",
    )
    series_theme_question = models.TextField(
        blank=True, default="",
        verbose_name="Serien-Themen-Frage",
        help_text="Die Frage, die die gesamte Serie stellt.",
    )
    total_volumes_planned = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="Geplante Bände",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_series_arcs"
        verbose_name = "Serien-Arc"
        verbose_name_plural = "Serien-Arcs"

    def __str__(self):
        return f"Arc — {self.series.title}"


class SeriesVolumeRole(models.Model):
    """
    Dramaturgische Rolle eines Bandes im Serien-Bogen. 1:1 zu SeriesVolume (ADR-155).
    """

    VOLUME_ARC_POSITION = [
        ("opening",     "Eröffnung — Welt und Figuren einführen"),
        ("escalation",  "Eskalation — Einsätze erhöhen"),
        ("midpoint",    "Serien-Midpoint — alles dreht sich"),
        ("darkest",     "Dunkelster Band — alles scheint verloren"),
        ("climax_prep", "Climax-Vorbereitung"),
        ("finale",      "Finale — Serien-Arc auflösen"),
        ("standalone",  "Eigenständig (Anthologie)"),
    ]
    CLIFFHANGER_TYPES = [
        ("none",          "Kein Cliffhanger"),
        ("question",      "Offene Frage"),
        ("revelation",    "Enthüllung"),
        ("status_change", "Figurenstatus verändert"),
        ("threat",        "Neue Bedrohung etabliert"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volume = models.OneToOneField(
        "series.SeriesVolume",
        on_delete=models.CASCADE,
        related_name="role",
    )
    arc_position = models.CharField(
        max_length=20, choices=VOLUME_ARC_POSITION, default="escalation",
        verbose_name="Arc-Position im Serien-Bogen",
    )
    series_arc_contribution = models.TextField(
        blank=True, default="",
        verbose_name="Beitrag zum Serien-Arc",
        help_text="Welchen Teil des Serien-Arcs trägt dieser Band?",
    )
    promise_to_reader = models.TextField(
        blank=True, default="",
        verbose_name="Versprechen an den Leser",
        help_text="Was verspricht dieses Buch für den nächsten Band?",
    )
    promise_fulfilled_from = models.TextField(
        blank=True, default="",
        verbose_name="Eingelöstes Versprechen",
        help_text="Welches Versprechen aus dem Vorgänger-Band wird hier eingelöst?",
    )
    cliffhanger_type = models.CharField(
        max_length=20, choices=CLIFFHANGER_TYPES, default="none",
    )
    cliffhanger_description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_series_volume_roles"
        verbose_name = "Serien-Band-Rolle"
        verbose_name_plural = "Serien-Band-Rollen"

    def __str__(self):
        return f"{self.volume} — {self.get_arc_position_display()}"


class SeriesCharacterContinuity(models.Model):
    """
    Figur-Zustand am Ende eines Bandes — Übergabe-Vertrag zwischen Bänden (ADR-155).

    Ohne dieses Modell generiert das LLM Band N+1 ohne zu wissen was in Band N
    passiert ist → Figur-Widersprüche, Wissens-Fehler, Arc-Brüche.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series = models.ForeignKey(
        "series.BookSeries",
        on_delete=models.CASCADE,
        related_name="character_continuities",
    )
    volume = models.ForeignKey(
        "series.SeriesVolume",
        on_delete=models.CASCADE,
        related_name="character_continuities",
        verbose_name="Am Ende von Band",
    )
    character_id = models.UUIDField(verbose_name="Figur (WeltenHub UUID)")
    character_name = models.CharField(
        max_length=200,
        verbose_name="Figurenname (Cache)",
        help_text="Gecacht — vermeidet API-Call bei jeder Anzeige",
    )
    physical_state = models.TextField(blank=True, default="", verbose_name="Physischer Zustand")
    emotional_state = models.TextField(blank=True, default="", verbose_name="Emotionaler Zustand")
    arc_progress = models.TextField(blank=True, default="", verbose_name="Arc-Fortschritt")
    knowledge_gained = models.JSONField(default=list, verbose_name="Neu erworbenes Wissen")
    relationships_changed = models.JSONField(default=dict, verbose_name="Veränderte Beziehungen")
    unresolved_threads = models.JSONField(default=list, verbose_name="Offene Fäden")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_series_character_continuities"
        unique_together = [("series", "volume", "character_id")]
        ordering = ["series", "volume__volume_number", "character_name"]
        verbose_name = "Figur-Kontinuität"
        verbose_name_plural = "Figur-Kontinuitäten"

    def __str__(self):
        return f"{self.character_name} — Ende Band {self.volume.volume_number}"

    def to_next_volume_context(self) -> str:
        lines = [
            f"FIGUR: {self.character_name}",
            f"PHYSISCH: {self.physical_state}",
            f"EMOTIONAL: {self.emotional_state}",
            f"ARC-STAND: {self.arc_progress}",
        ]
        if self.knowledge_gained:
            lines.append(f"WISSENSPUNKTE: {'; '.join(self.knowledge_gained)}")
        if self.unresolved_threads:
            lines.append(f"OFFENE FÄDEN: {'; '.join(self.unresolved_threads)}")
        return "\n".join(lines)
