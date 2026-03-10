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
        verbose_name = "Autor / Schreibstil (Legacy)"
        verbose_name_plural = "Autoren / Schreibstile (Legacy)"

    def __str__(self):
        return self.name


class OutlineFramework(models.Model):
    key = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    icon = models.CharField(max_length=60, blank=True, default="bi-list-ol")
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
    framework = models.ForeignKey(
        OutlineFramework, on_delete=models.CASCADE, related_name="beats"
    )
    order = models.PositiveSmallIntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    position_start = models.PositiveSmallIntegerField(default=0)
    position_end = models.PositiveSmallIntegerField(default=100)

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
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="book_projects"
    )
    bfagent_id = models.IntegerField(null=True, blank=True, db_index=True)
    series = models.ForeignKey(
        "series.BookSeries", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="projects", verbose_name="Serie",
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    content_type_lookup = models.ForeignKey(
        ContentTypeLookup, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Inhaltstyp", related_name="projects",
    )
    genre_lookup = models.ForeignKey(
        GenreLookup, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Genre", related_name="projects",
    )
    audience_lookup = models.ForeignKey(
        AudienceLookup, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Zielgruppe", related_name="projects",
    )
    writing_style = models.ForeignKey(
        "authors.WritingStyle", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Primärer Schreibstil",
        related_name="projects",
    )
    writing_styles = models.ManyToManyField(
        "authors.WritingStyle",
        blank=True,
        verbose_name="Schreibstile (mehrere möglich)",
        related_name="projects_m2m",
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

    def get_all_styles(self):
        """Alle zugeordneten Schreibstile (primär + M2M), dedupliziert."""
        styles = list(self.writing_styles.select_related("author").all())
        if self.writing_style and self.writing_style not in styles:
            styles.insert(0, self.writing_style)
        return styles


class OutlineVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "BookProject", on_delete=models.CASCADE, related_name="outline_versions"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    name = models.CharField(max_length=200)
    version_label = models.CharField(
        max_length=200, blank=True, default="",
        help_text="Optionales Label für diese Version",
    )
    source = models.CharField(
        max_length=80, default="manual",
        help_text="Framework-Key oder 'manual'/'ai'",
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

    def save_as_new_version(self, name=None, label=None, user=None):
        new = OutlineVersion.objects.create(
            project=self.project,
            created_by=user,
            name=name or f"{self.name} (Kopie)",
            version_label=label or "",
            source=self.source,
            notes=self.notes,
            is_active=False,
        )
        for node in self.nodes.order_by("order"):
            OutlineNode.objects.create(
                outline_version=new,
                title=node.title,
                description=node.description,
                beat_type=node.beat_type,
                beat_phase=node.beat_phase,
                act=node.act,
                target_words=node.target_words,
                emotional_arc=node.emotional_arc,
                writing_style=node.writing_style,
                order=node.order,
                notes=node.notes,
            )
        return new


class OutlineNode(models.Model):
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
    beat_phase = models.CharField(max_length=100, blank=True, default="")
    act = models.CharField(max_length=100, blank=True, default="")
    target_words = models.PositiveIntegerField(null=True, blank=True)
    emotional_arc = models.CharField(max_length=300, blank=True, default="")
    writing_style = models.ForeignKey(
        "authors.WritingStyle",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Schreibstil für dieses Kapitel",
        related_name="outline_nodes",
    )
    order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    content = models.TextField(blank=True)
    word_count = models.PositiveIntegerField(default=0)
    content_updated_at = models.DateTimeField(null=True, blank=True)

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

    def get_effective_style(self):
        """Effektiver Stil: Kapitel-Stil > Projekt-Primärstil."""
        if self.writing_style:
            return self.writing_style
        return self.outline_version.project.writing_style
