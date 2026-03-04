"""
Projects App — Buchprojekte, Outline, Kapitel (ADR-083)

Extrahiert aus bfagent. BookProject ist der zentrale Anker für alle
Authoring-Aktivitäten im writing-hub.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class BookProject(models.Model):
    """
    Buchprojekt — zentrales Objekt des Writing Hub.

    Im Gegensatz zu bfagent.BookProjects ist dies die writing-hub-eigene
    Repräsentation. Sync via API (ADR-083 Phase 3).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_projects",
    )

    bfagent_id = models.IntegerField(
        null=True, blank=True, db_index=True,
        help_text="ID des entsprechenden bfagent.BookProjects (für API-Sync)",
    )

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    class ContentType(models.TextChoices):
        NOVEL = "novel", "Roman"
        NONFICTION = "nonfiction", "Sachbuch"
        SHORT_STORY = "short_story", "Kurzgeschichte"
        SCREENPLAY = "screenplay", "Drehbuch"
        ESSAY = "essay", "Essay"

    content_type = models.CharField(
        max_length=20, choices=ContentType.choices, default=ContentType.NOVEL
    )

    genre = models.CharField(max_length=100, blank=True)
    target_audience = models.CharField(max_length=200, blank=True)
    target_word_count = models.PositiveIntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_book_projects"
        ordering = ["-updated_at"]
        verbose_name = "Book Project"
        verbose_name_plural = "Book Projects"

    def __str__(self):
        return self.title


class OutlineVersion(models.Model):
    """
    Versionierter Outline-Stand eines Projekts.
    Nie überschreiben — immer neue Version anlegen.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "BookProject", on_delete=models.CASCADE, related_name="outline_versions"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    name = models.CharField(max_length=200)
    source = models.CharField(
        max_length=50, default="manual",
        help_text="z.B. 'idea_import', 'manual', 'ai_generated'",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_outline_versions"
        ordering = ["-created_at"]
        verbose_name = "Outline Version"
        verbose_name_plural = "Outline Versions"

    def __str__(self):
        return f"{self.project.title} — {self.name}"


class OutlineNode(models.Model):
    """
    Einzelner Beat/Kapitel innerhalb einer OutlineVersion.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    outline_version = models.ForeignKey(
        "OutlineVersion", on_delete=models.CASCADE, related_name="nodes"
    )

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    BEAT_TYPES = [
        ("chapter", "Kapitel"),
        ("scene", "Szene"),
        ("beat", "Beat"),
        ("act", "Akt"),
        ("part", "Teil"),
    ]
    beat_type = models.CharField(max_length=20, choices=BEAT_TYPES, default="chapter")
    order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "wh_outline_nodes"
        ordering = ["outline_version", "order"]
        verbose_name = "Outline Node"
        verbose_name_plural = "Outline Nodes"

    def __str__(self):
        return f"{self.outline_version} — {self.order}. {self.title}"
