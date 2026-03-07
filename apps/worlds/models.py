"""
Worlds App Models — writing-hub

Keine Django-ORM-Models für Welten/Charaktere.
SSoT ist WeltenHub via iil-weltenfw REST Client.

für Welten/Charaktere: weltenfw.django.get_client()

Diese Datei enthält nur die ProjectWorld-Verknüpfung (lokales FK auf BookProject).
"""
from __future__ import annotations

import uuid

from django.db import models


class ProjectWorldLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einer WeltenHub-Welt (UUID).

    Die Welt-Daten selbst liegen in WeltenHub — hier nur die Referenz.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="world_links",
    )
    weltenhub_world_id = models.UUIDField(
        db_index=True,
        help_text="UUID der Welt in WeltenHub (via iil-weltenfw)",
    )
    role = models.CharField(
        max_length=20,
        default="primary",
        choices=[
            ("primary", "Primärwelt"),
            ("secondary", "Nebenwelt"),
            ("parallel", "Parallelwelt"),
        ],
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_world_links"
        unique_together = ["project", "weltenhub_world_id"]
        ordering = ["project", "role"]
        verbose_name = "Project World Link"
        verbose_name_plural = "Project World Links"

    def __str__(self):
        return f"{self.project} → world:{self.weltenhub_world_id} ({self.role})"

    def get_world(self):
        """Welt-Daten von WeltenHub laden."""
        from weltenfw.django import get_client
        return get_client().worlds.get(self.weltenhub_world_id)


class ProjectCharacterLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einem WeltenHub-Charakter (UUID).
    Projekt-spezifische Überschreibungen (arc, role) werden lokal gespeichert.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="character_links",
    )
    weltenhub_character_id = models.UUIDField(
        db_index=True,
        help_text="UUID des Charakters in WeltenHub (via iil-weltenfw)",
    )
    project_arc = models.TextField(
        blank=True,
        help_text="Projekt-spezifischer Charakterbogen (override)",
    )
    project_role = models.CharField(
        max_length=50,
        blank=True,
        help_text="Rolle in diesem Projekt (override)",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_character_links"
        unique_together = ["project", "weltenhub_character_id"]
        ordering = ["project"]
        verbose_name = "Project Character Link"
        verbose_name_plural = "Project Character Links"

    def __str__(self):
        return f"{self.project} → char:{self.weltenhub_character_id}"

    def get_character(self):
        """Charakter-Daten von WeltenHub laden."""
        from weltenfw.django import get_client
        return get_client().characters.get(self.weltenhub_character_id)
