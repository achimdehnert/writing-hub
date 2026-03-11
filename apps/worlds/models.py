"""
Worlds App Models — writing-hub

SSoT ist WeltenHub via iil-weltenfw REST Client.
Lokal werden nur Referenz-Links (UUIDs) gespeichert.
"""
from __future__ import annotations

import uuid

from django.db import models


class ProjectWorldLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einer WeltenHub-Welt (UUID).
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
        max_length=20, default="primary",
        choices=[("primary", "Primärwelt"), ("secondary", "Nebenwelt"), ("parallel", "Parallelwelt")],
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
        from weltenfw.django import get_client
        return get_client().worlds.get(self.weltenhub_world_id)


class ProjectCharacterLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einem WeltenHub-Charakter (UUID).
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
    project_arc = models.TextField(blank=True, help_text="Projekt-spezifischer Charakterbogen (override)")
    project_role = models.CharField(max_length=50, blank=True, help_text="Rolle in diesem Projekt (override)")
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
        from weltenfw.django import get_client
        return get_client().characters.get(self.weltenhub_character_id)


class ProjectLocationLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einem WeltenHub-Ort (UUID).
    SSoT: WeltenHub. Hier nur UUID-Referenz + projektspezifische Notizen.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="location_links",
    )
    weltenhub_location_id = models.UUIDField(
        db_index=True,
        help_text="UUID des Ortes in WeltenHub (via iil-weltenfw)",
    )
    notes = models.TextField(blank=True, help_text="Projekt-spezifische Notizen zum Ort")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_location_links"
        unique_together = ["project", "weltenhub_location_id"]
        ordering = ["project"]
        verbose_name = "Project Location Link"
        verbose_name_plural = "Project Location Links"

    def __str__(self):
        return f"{self.project} → location:{self.weltenhub_location_id}"

    def get_location(self):
        from weltenfw.django import get_client
        return get_client().locations.get(self.weltenhub_location_id)


class ProjectSceneLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einer WeltenHub-Szene (UUID).
    SSoT: WeltenHub. Hier nur UUID-Referenz + lokaler Kapitel-Bezug.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="scene_links",
    )
    weltenhub_scene_id = models.UUIDField(
        db_index=True,
        help_text="UUID der Szene in WeltenHub (via iil-weltenfw)",
    )
    outline_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="scene_links",
        help_text="Lokales Kapitel das dieser Szene entspricht",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_scene_links"
        unique_together = ["project", "weltenhub_scene_id"]
        ordering = ["project"]
        verbose_name = "Project Scene Link"
        verbose_name_plural = "Project Scene Links"

    def __str__(self):
        return f"{self.project} → scene:{self.weltenhub_scene_id}"

    def get_scene(self):
        from weltenfw.django import get_client
        return get_client().scenes.get(self.weltenhub_scene_id)
