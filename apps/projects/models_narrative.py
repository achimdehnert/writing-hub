"""
Projects App — Narrative Models (ADR-157)

SubplotArc: B-Story/C-Story-Tracking.
"""
from __future__ import annotations

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SubplotArc(models.Model):
    """
    Dramaturgischer Nebenstrang (B-Story, C-Story).

    Die B-Story ist NICHT optional — sie ist das thematische Herz
    des Romans. Sie beginnt typischerweise bei ~37% (Save-the-Cat /
    Drei-Akte-Modell).

    story_label:
        a_story → Haupthandlung
        b_story → Thematischer Spiegel (Liebesinteresse/Mentor-Typ)
        c_story → Weiterer Subplot (nur bei Bedarf, > 80k Wörter)
    """

    STORY_LABELS = [
        ("a_story", "A-Story — Haupthandlung"),
        ("b_story", "B-Story — Thematischer Spiegel"),
        ("c_story", "C-Story — Weiterer Subplot"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="subplot_arcs",
    )
    story_label = models.CharField(
        max_length=10, choices=STORY_LABELS, default="b_story",
        db_index=True,
    )
    title = models.CharField(max_length=200, verbose_name="Subplot-Bezeichnung")

    carried_by_character_id = models.UUIDField(
        null=True, blank=True,
        verbose_name="Träger-Figur (WeltenHub UUID)",
    )
    carried_by_name = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Träger-Figur (Cache)",
    )

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

    begins_at_percent = models.PositiveSmallIntegerField(
        default=37,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Beginn (%)",
        help_text="Empfehlung Drei-Akte/Save-the-Cat: 37%.",
    )
    ends_at_percent = models.PositiveSmallIntegerField(
        default=95,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Ende (%)",
    )

    begins_at_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subplot_begins",
        verbose_name="Beginnt in Kapitel/Szene",
    )
    ends_at_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subplot_ends",
        verbose_name="Endet in Kapitel/Szene",
    )

    intersection_nodes = models.ManyToManyField(
        "projects.OutlineNode",
        blank=True,
        related_name="subplot_intersections",
        help_text="Kapitel/Szenen, in denen dieser Subplot die A-Story kreuzt.",
    )
    intersection_notes = models.TextField(
        blank=True, default="",
        verbose_name="Kreuzungspunkte — Anmerkungen",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_subplot_arcs"
        ordering = ["project", "story_label"]
        verbose_name = "Subplot-Arc"
        verbose_name_plural = "Subplot-Arcs"

    def __str__(self):
        return f"{self.get_story_label_display()}: {self.title}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.begins_at_percent >= self.ends_at_percent:
            raise ValidationError(
                "begins_at_percent muss kleiner als ends_at_percent sein."
            )

    def b_story_phase(self, current_percent: int) -> str:
        """Aktuelle Phase der B-Story für LLM-Kontext."""
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
