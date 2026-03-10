"""
Projects App — Buchprojekte, Outline, Kapitel (ADR-083)
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class ContentTypeLookup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True, default="")
    subtitle = models.CharField(max_length=200, blank=True, default="")
    workflow_hint = models.CharField(max_length=300, blank=True, default="")
    planning_action_code = models.CharField(max_length=100, blank=True, default="")
    planning_prompt_template = models.CharField(max_length=128, blank=True, default="")
    planning_system_prompt = models.TextField(blank=True, default="")
    planning_user_template = models.TextField(blank=True, default="")

    class Meta:
        db_table = "wh_content_type_lookup"
        ordering = ["order", "name"]
        verbose_name = "Inhaltstyp"
        verbose_name_plural = "Inhaltstypen"

    def __str__(self):
        return self.name


class GenreLookup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_genre_lookup"
        ordering = ["order", "name"]
        verbose_name = "Genre"
        verbose_name_plural = "Genres"

    def __str__(self):
        return self.name


class AudienceLookup(models.Model):
    name = models.CharField(max_length=200, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_audience_lookup"
        ordering = ["order", "name"]
        verbose_name = "Zielgruppe"
        verbose_name_plural = "Zielgruppen"

    def __str__(self):
        return self.name


class AuthorStyleLookup(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    style_prompt = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "wh_author_style_lookup"
        ordering = ["order", "name"]
        verbose_name = "Autor / Schreibstil"
        verbose_name_plural = "Autoren / Schreibstile"

    def __str__(self):
        return self.name


class OutlineFramework(models.Model):
    """
    Story-Framework (Drei-Akt, Save the Cat, etc.) — DB-driven, via Admin pflegbar.
    Beliebig erweiterbar ohne Codeänderungen.
    """
    key = models.SlugField(
        max_length=80, unique=True,
        help_text="Eindeutiger Schlüssel, z.B. 'save_the_cat' (wird in OutlineVersion.source gespeichert)",
    )
    name = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    icon = models.CharField(
        max_length=60, blank=True, default="bi-list-ol",
        help_text="Bootstrap-Icon-Klasse, z.B. 'bi-star'",
    )
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "wh_outline_framework"
        ordering = ["order", "name"]
        verbose_name = "Outline-Framework"
        verbose_name_plural = "Outline-Frameworks"

    def __str__(self):
        return self.name

    @property
    def beat_count(self):
        return self.beats.count()


class OutlineFrameworkBeat(models.Model):
    """
    Einzelner Beat innerhalb eines OutlineFramework.
    """
    framework = models.ForeignKey(
        OutlineFramework,
        on_delete=models.CASCADE,
        related_name="beats",
    )
    order = models.PositiveSmallIntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    position_start = models.PositiveSmallIntegerField(
        default=0,
        help_text="Prozent-Position im Manuskript (Anfang), 0-100",
    )
    position_end = models.PositiveSmallIntegerField(
        default=100,
        help_text="Prozent-Position im Manuskript (Ende), 0-100",
    )

    class Meta:
        db_table = "wh_outline_framework_beat"
        ordering = ["framework", "order"]
        verbose_name = "Framework Beat"
        verbose_name_plural = "Framework Beats"

    def __str__(self):
        return f"{self.framework.name} — {self.order}. {self.name}"


class BookProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_projects",
    )
    bfagent_id = models.IntegerField(null=True, blank=True, db_index=True)
    series = models.ForeignKey(
        "series.BookSeries",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="projects",
        verbose_name="Serie",
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    content_type_lookup = models.ForeignKey(
        ContentTypeLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Inhaltstyp",
        related_name="projects",
    )
    genre_lookup = models.ForeignKey(
        GenreLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Genre",
        related_name="projects",
    )
    audience_lookup = models.ForeignKey(
        AudienceLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Zielgruppe",
        related_name="projects",
    )
    author_style = models.ForeignKey(
        AuthorStyleLookup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Autor / Schreibstil",
        related_name="projects",
    )

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
        max_length=80, default="manual",
        help_text="Framework-Key (OutlineFramework.key) oder 'manual'/'ai'",
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

    content = models.TextField(
        blank=True,
        help_text="Kapitelinhalt (von Autor oder KI geschrieben)",
    )
    word_count = models.PositiveIntegerField(
        default=0,
        help_text="Anzahl Wörter im content-Feld (automatisch berechnet)",
    )
    content_updated_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Zeitpunkt der letzten Inhalt-Änderung",
    )

    class Meta:
        db_table = "wh_outline_nodes"
        ordering = ["outline_version", "order"]
        verbose_name = "Outline Node"
        verbose_name_plural = "Outline Nodes"

    def __str__(self):
        return f"{self.outline_version} — {self.order}. {self.title}"

    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        else:
            self.word_count = 0
        super().save(*args, **kwargs)
