"""
Projects App — Buchprojekte, Outline, Kapitel, Review, Editing, Lektorat, Snapshots, Publishing (ADR-083)
"""
from __future__ import annotations

import datetime
import uuid

from django.conf import settings
from django.db import models


def _import_timeline_models():
    from apps.projects import models_timeline  # noqa: F401


_import_timeline_models()


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
        verbose_name="Prim\u00e4rer Schreibstil",
        related_name="projects",
    )
    writing_styles = models.ManyToManyField(
        "authors.WritingStyle",
        blank=True,
        verbose_name="Schreibstile (mehrere m\u00f6glich)",
        related_name="projects_m2m",
    )

    class ContentType(models.TextChoices):
        NOVEL = "novel", "Roman"
        NONFICTION = "nonfiction", "Sachbuch"
        SHORT_STORY = "short_story", "Kurzgeschichte"
        SCREENPLAY = "screenplay", "Drehbuch"
        ESSAY = "essay", "Essay"
        ACADEMIC = "academic", "Akademische Arbeit (Monographie, Dissertation)"
        SCIENTIFIC = "scientific", "Wissenschaftliches Paper (IMRaD)"

    content_type = models.CharField(
        max_length=30, choices=ContentType.choices, default=ContentType.NOVEL
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
    version_label = models.CharField(max_length=200, blank=True, default="")
    source = models.CharField(max_length=80, default="manual")
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


class ProjectTurningPoint(models.Model):
    """
    Wendepunkt-Markierung auf der Spannungskurve (ADR-154).

    Verknüpft einen semantischen Wendepunkt-Typ (core.TurningPointTypeLookup)
    mit einer Position im Projekt und optional einer konkreten Szene.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "BookProject",
        on_delete=models.CASCADE,
        related_name="turning_points",
    )
    turning_point_type = models.ForeignKey(
        "core.TurningPointTypeLookup",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="project_turning_points",
    )
    node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="turning_point_markers",
        verbose_name="Verknüpfte Szene",
    )
    label = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name="Bezeichnung (Override)",
        help_text="Leer = Typ-Label verwenden",
    )
    position_percent = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Position (%)",
        help_text="0–100, relativer Buchfortschritt",
    )
    description = models.TextField(blank=True, default="")
    mirrors_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="mirrored_by_turning_points",
        verbose_name="Gespiegelte Szene",
        help_text="Nur für closing_image: die OutlineNode des Opening Image.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_turning_points"
        ordering = ["project", "position_percent"]
        verbose_name = "Wendepunkt"
        verbose_name_plural = "Wendepunkte"

    def __str__(self):
        lbl = self.label or (self.turning_point_type.label if self.turning_point_type else "?")
        return f"{lbl} @ {self.position_percent}%"

    def get_label(self):
        if self.label:
            return self.label
        if self.turning_point_type:
            return self.turning_point_type.label
        return "Wendepunkt"


class OutlineSequence(models.Model):
    """
    Mesostruktur-Zwischenebene zwischen Akt und Kapitel (ADR-156).

    Hierarchie: OutlineVersion → OutlineSequence → OutlineNode
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    outline_version = models.ForeignKey(
        "OutlineVersion",
        on_delete=models.CASCADE,
        related_name="sequences",
    )
    act = models.CharField(
        max_length=20, blank=True, default="",
        verbose_name="Akt-Zugehörigkeit",
        help_text="z.B. 'act_1', 'act_2a', 'act_3'",
    )
    title = models.CharField(max_length=200)
    goal = models.TextField(
        verbose_name="Sequenz-Ziel",
        help_text="Was versucht die Figur in dieser Sequenz zu erreichen?",
    )
    start_state = models.TextField(blank=True, default="", verbose_name="Ausgangslage")
    end_state = models.TextField(
        blank=True, default="",
        verbose_name="Endzustand",
        help_text="Positiv (Ziel erreicht) oder negativ (Komplikation)?",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "wh_outline_sequences"
        ordering = ["outline_version", "sort_order"]
        verbose_name = "Sequenz"
        verbose_name_plural = "Sequenzen"

    def __str__(self):
        return f"Seq {self.sort_order}: {self.title}"


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
    emotional_arc = models.TextField(blank=True, default="")
    writing_style = models.ForeignKey(
        "authors.WritingStyle",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Schreibstil f\u00fcr dieses Kapitel",
        related_name="outline_nodes",
    )
    sequence = models.ForeignKey(
        "projects.OutlineSequence",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="nodes",
        verbose_name="Sequenz-Zugehörigkeit",
    )
    OUTCOME_CHOICES = [
        ("yes",     "Yes (Ziel erreicht)"),
        ("no",      "No (Ziel verfehlt)"),
        ("yes_but", "Yes, but (mit Komplikation)"),
        ("no_and",  "No, and (Lage verschlechtert)"),
    ]
    outcome = models.CharField(
        max_length=10, choices=OUTCOME_CHOICES, blank=True, default="",
        verbose_name="Szenen-Outcome",
    )
    tension_numeric = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Spannungswert (1–10)",
        help_text="Subjektiver Spannungswert 1–10 für die Spannungskurve",
    )
    emotion_start = models.CharField(
        max_length=100, blank=True, default="",
        verbose_name="Emotion Beginn",
        help_text="Dominante Emotion zu Szenen-Beginn (z.B. 'Hoffnung')",
    )
    emotion_end = models.CharField(
        max_length=100, blank=True, default="",
        verbose_name="Emotion Ende",
        help_text="Dominante Emotion am Szenen-Ende (z.B. 'Verzweiflung')",
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
        if self.writing_style:
            return self.writing_style
        return self.outline_version.project.writing_style


class ChapterReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(
        OutlineNode, on_delete=models.CASCADE, related_name="reviews",
        verbose_name="Kapitel",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    reviewer = models.CharField(max_length=200, default="Autor", verbose_name="Reviewer")
    FEEDBACK_TYPES = [
        ("positive", "Positiv"),
        ("suggestion", "Vorschlag"),
        ("issue", "Problem"),
        ("question", "Frage"),
    ]
    feedback_type = models.CharField(
        max_length=20, choices=FEEDBACK_TYPES, default="suggestion"
    )
    feedback = models.TextField(verbose_name="Feedback")
    text_reference = models.TextField(blank=True, verbose_name="Textreferenz")
    is_resolved = models.BooleanField(default=False)
    is_ai_generated = models.BooleanField(default=False)
    ai_agent = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_chapter_reviews"
        ordering = ["-created_at"]
        verbose_name = "Kapitel-Review"
        verbose_name_plural = "Kapitel-Reviews"

    def __str__(self):
        return f"{self.node.title} — {self.reviewer}"


class ChapterEditing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(
        OutlineNode, on_delete=models.CASCADE, related_name="editings",
        verbose_name="Kapitel",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    SUGGESTION_TYPES = [
        ("style", "Stil"),
        ("clarity", "Kl\u00e4rung"),
        ("consistency", "Konsistenz"),
        ("grammar", "Grammatik"),
        ("pacing", "Pacing"),
        ("character", "Charakter"),
    ]
    suggestion_type = models.CharField(
        max_length=30, choices=SUGGESTION_TYPES, default="style"
    )
    original_text = models.TextField(blank=True)
    suggestion = models.TextField(verbose_name="Vorschlag")
    explanation = models.TextField(blank=True)
    is_accepted = models.BooleanField(null=True, blank=True)
    is_ai_generated = models.BooleanField(default=True)
    ai_agent = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_chapter_editings"
        ordering = ["-created_at"]
        verbose_name = "Kapitel-Editing"
        verbose_name_plural = "Kapitel-Editings"

    def __str__(self):
        return f"{self.node.title} — {self.suggestion_type}"


class LektoratSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject, on_delete=models.CASCADE, related_name="lektorat_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    name = models.CharField(max_length=200, default="Lektorat")
    STATUS = [
        ("pending", "Ausstehend"),
        ("running", "Wird gepr\u00fcft"),
        ("done", "Abgeschlossen"),
        ("error", "Fehler"),
    ]
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    chapter_count = models.PositiveIntegerField(default=0)
    issues_found = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    summary = models.TextField(blank=True)

    class Meta:
        db_table = "wh_lektorat_sessions"
        ordering = ["-created_at"]
        verbose_name = "Lektorats-Session"
        verbose_name_plural = "Lektorats-Sessions"

    def __str__(self):
        return f"{self.project.title} — {self.name}"


class LektoratIssue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        LektoratSession, on_delete=models.CASCADE, related_name="issues",
    )
    node = models.ForeignKey(
        OutlineNode, on_delete=models.CASCADE, related_name="lektorat_issues",
    )
    ISSUE_TYPES = [
        ("consistency", "Konsistenz"),
        ("logic", "Logik"),
        ("style", "Stil"),
        ("character", "Charakter"),
        ("timeline", "Zeitlinie"),
        ("pacing", "Pacing"),
    ]
    issue_type = models.CharField(max_length=30, choices=ISSUE_TYPES, default="consistency")
    SEVERITY = [
        ("info", "Info"),
        ("warning", "Warnung"),
        ("error", "Fehler"),
    ]
    severity = models.CharField(max_length=10, choices=SEVERITY, default="warning")
    description = models.TextField()
    suggestion = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_lektorat_issues"
        ordering = ["session", "node__order", "-severity"]
        verbose_name = "Lektorats-Problem"
        verbose_name_plural = "Lektorats-Probleme"

    def __str__(self):
        return f"{self.session.name} — {self.node.title}: {self.issue_type}"


class ManuscriptSnapshot(models.Model):
    """
    Snapshot des kompletten Manuskript-Stands zu einem Zeitpunkt.
    Speichert alle Kapitel-Inhalte als JSON (FIFO, max. 10 pro Projekt).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject, on_delete=models.CASCADE, related_name="snapshots",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    chapter_count = models.PositiveIntegerField(default=0)
    word_count = models.PositiveIntegerField(default=0)
    data = models.JSONField(default=dict, help_text="Serialisierter Stand aller Kapitel")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_manuscript_snapshots"
        ordering = ["-created_at"]
        verbose_name = "Manuskript-Snapshot"
        verbose_name_plural = "Manuskript-Snapshots"

    def __str__(self):
        return f"{self.project.title} — {self.name}"


class PublishingProfile(models.Model):
    """
    Publishing-Profil eines Buchprojekts:
    ISBN/ASIN, Verlag, Sprache, Keywords, Cover, Front-/Backmatter.
    """

    STATUS_CHOICES = [
        ("draft", "Entwurf"),
        ("review", "In Review"),
        ("ready", "Druckfertig"),
        ("published", "Ver\u00f6ffentlicht"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        BookProject, on_delete=models.CASCADE, related_name="publishing_profile",
    )
    # Identifiers
    isbn = models.CharField(max_length=20, blank=True)
    asin = models.CharField(max_length=20, blank=True)
    # Publisher
    publisher_name = models.CharField(max_length=200, blank=True, default="Selbstverlag")
    imprint = models.CharField(max_length=200, blank=True)
    copyright_year = models.CharField(max_length=4, blank=True)
    copyright_holder = models.CharField(max_length=200, blank=True)
    # Language & Categories
    language = models.CharField(max_length=10, blank=True, default="de")
    age_rating = models.CharField(max_length=30, blank=True, default="0")
    bisac_category = models.CharField(max_length=200, blank=True)
    # Keywords
    keywords = models.TextField(blank=True, help_text="Komma-getrennt, max. 7")
    # Publication dates & status
    first_published = models.DateField(null=True, blank=True)
    this_edition = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    # Cover
    cover_image_url = models.URLField(blank=True)
    cover_notes = models.TextField(blank=True)
    # Frontmatter
    dedication = models.TextField(blank=True)
    foreword = models.TextField(blank=True)
    preface = models.TextField(blank=True)
    # Backmatter
    afterword = models.TextField(blank=True)
    acknowledgements = models.TextField(blank=True)
    about_author = models.TextField(blank=True)
    bibliography = models.TextField(blank=True)
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_publishing_profiles"
        verbose_name = "Publishing Profile"
        verbose_name_plural = "Publishing Profiles"

    def __str__(self):
        return f"{self.project.title} — Publishing"

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class ProjectGenrePromise(models.Model):
    """
    Verknüpft ein BookProject mit einem GenrePromiseLookup (ADR-158).

    Ein Projekt kann mehrere Genre-Versprechen haben (z.B. Thriller + Romance).
    is_primary markiert das Haupt-Genre.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject,
        on_delete=models.CASCADE,
        related_name="genre_promises",
    )
    genre_promise = models.ForeignKey(
        "core.GenrePromiseLookup",
        on_delete=models.CASCADE,
        related_name="project_links",
        verbose_name="Genre-Versprechen",
    )
    is_primary = models.BooleanField(
        default=True,
        help_text="Haupt-Genre-Versprechen (für LLM-Layer 10)",
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_genre_promises"
        unique_together = ["project", "genre_promise"]
        ordering = ["project", "-is_primary"]
        verbose_name = "Projekt-Genre-Versprechen"
        verbose_name_plural = "Projekt-Genre-Versprechen"

    def __str__(self):
        return f"{self.project.title} → {self.genre_promise}"


class SubplotArc(models.Model):
    """
    Dramaturgischer Nebenstrang — B-Story / C-Story-Tracking (ADR-157).

    story_label:
        b_story → Thematischer Spiegel (Liebesinteresse/Mentor-Typ)
        c_story → Weiterer Subplot (nur > 80k Wörter sinnvoll)
    """

    STORY_LABELS = [
        ("a_story", "A-Story — Haupthandlung"),
        ("b_story", "B-Story — Thematischer Spiegel"),
        ("c_story", "C-Story — Weiterer Subplot"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject,
        on_delete=models.CASCADE,
        related_name="subplot_arcs",
    )
    story_label = models.CharField(
        max_length=10, choices=STORY_LABELS, default="b_story", db_index=True,
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
    )

    begins_at_percent = models.PositiveSmallIntegerField(
        default=37,
        verbose_name="Beginn (%)",
        help_text="Empfehlung Drei-Akte/Save-the-Cat: 37%.",
    )
    ends_at_percent = models.PositiveSmallIntegerField(
        default=95,
        verbose_name="Ende (%)",
    )

    begins_at_node = models.ForeignKey(
        "OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subplot_begins",
        verbose_name="Beginnt in Kapitel/Szene",
    )
    ends_at_node = models.ForeignKey(
        "OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subplot_ends",
        verbose_name="Endet in Kapitel/Szene",
    )

    intersection_nodes = models.ManyToManyField(
        "OutlineNode",
        blank=True,
        related_name="subplot_intersections",
        help_text="Kapitel/Szenen, in denen dieser Subplot die A-Story kreuzt.",
    )
    intersection_notes = models.TextField(blank=True, default="")

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


class TextAnalysisSnapshot(models.Model):
    """
    Gecachter struktureller Analyse-Snapshot eines Manuskripts (ADR-161).

    Berechnet regelbasiert (kein LLM):
        - Dead Scenes (emotion_start == emotion_end, beide befüllt)
        - Character Screen Time (POV-Auftritte pro Figur)
        - Pacing-Verteilung (Wortanzahl-Varianz)
        - Dialogue-Ratio-Schätzung (Regex-Heuristik)

    Optional (LLM, teuer):
        - Voice Drift (check_voice_drift=True)

    Speicher-Strategie: max. 5 Snapshots pro Projekt (FIFO),
    analog zu ManuscriptSnapshot.
    """

    TRIGGERED_BY = [
        ("manual",   "Manuell ausgelöst"),
        ("lektorat", "Nach Lektorat"),
        ("save",     "Nach Kapitel-Speichern"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject,
        on_delete=models.CASCADE,
        related_name="analysis_snapshots",
    )

    dead_scene_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Anzahl Nodes mit emotion_start == emotion_end (beide befüllt)",
    )
    dead_scene_node_ids = models.JSONField(
        default=list,
        help_text="UUIDs der betroffenen OutlineNodes",
    )

    character_screen_time = models.JSONField(
        default=dict,
        help_text="{character_uuid: {chapters: int, percent: float, last_seen_order: int, role: str}}",
    )

    chapter_word_counts = models.JSONField(
        default=list,
        help_text="[{order: int, word_count: int, title: str}]",
    )
    pacing_variance = models.FloatField(
        null=True, blank=True,
        help_text="Standardabweichung der Kapitel-Wortanzahlen",
    )
    pacing_issues = models.JSONField(
        default=list,
        help_text="[{type: str, severity: str, description: str, chapter_orders: []}]",
    )

    dialogue_ratios = models.JSONField(
        default=dict,
        help_text="{chapter_order: float} — geschätzter Dialog-Anteil 0.0–1.0",
    )

    voice_drift_checked = models.BooleanField(default=False)
    voice_drift_detected = models.BooleanField(default=False)
    voice_drift_chapters = models.JSONField(
        default=list,
        help_text="[{order: int, reason: str}]",
    )

    chapters_analyzed = models.PositiveSmallIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)
    triggered_by = models.CharField(
        max_length=20, choices=TRIGGERED_BY, default="manual",
    )

    class Meta:
        db_table = "wh_text_analysis_snapshots"
        ordering = ["-computed_at"]
        get_latest_by = "computed_at"
        verbose_name = "Text-Analyse-Snapshot"
        verbose_name_plural = "Text-Analyse-Snapshots"

    def __str__(self):
        return f"Analyse {self.project.title} — {self.computed_at:%Y-%m-%d %H:%M}"

    @property
    def has_issues(self) -> bool:
        return (
            self.dead_scene_count > 0
            or bool(self.pacing_issues)
            or self.voice_drift_detected
        )

    @property
    def antagonist_underrepresented(self) -> bool:
        if self.chapters_analyzed < 8:
            return False
        for data in self.character_screen_time.values():
            if data.get("role") == "antagonist" and data.get("percent", 100) < 25:
                return True
        return False


class ComparableTitle(models.Model):
    """
    Comparable Title (Comp) für Verlagsanfragen (ADR-159).

    Verlegerische Regeln für gute Comps:
        - Erschienen in den letzten 5 Jahren (Markt-Relevanz)
        - Kein Mega-Bestseller (Harry Potter, Hunger Games)
        - Gleiches Genre + Zielgruppe
    """

    COMP_RELATION = [
        ("similar_theme",     "Ähnliches Thema"),
        ("similar_tone",      "Ähnlicher Ton"),
        ("similar_structure", "Ähnliche Struktur"),
        ("same_audience",     "Gleiche Zielgruppe"),
        ("same_subgenre",     "Gleiches Subgenre"),
        ("contrast",          "Kontrast — 'wie X, aber Y'"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject,
        on_delete=models.CASCADE,
        related_name="comparable_titles",
    )
    title = models.CharField(max_length=300, verbose_name="Buchtitel")
    author = models.CharField(max_length=200, verbose_name="Autor")
    publisher = models.CharField(max_length=200, blank=True, default="")
    publication_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Erscheinungsjahr",
        help_text="Für Validierung: Comps sollten < 5 Jahre alt sein.",
    )
    relation_type = models.CharField(
        max_length=20, choices=COMP_RELATION, default="similar_theme",
    )
    similarity_note = models.TextField(blank=True, default="", verbose_name="Worin ähnlich")
    difference_note = models.TextField(blank=True, default="", verbose_name="Worin anders")
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_comparable_titles"
        ordering = ["project", "sort_order"]
        verbose_name = "Comparable Title"
        verbose_name_plural = "Comparable Titles"

    def __str__(self):
        year = f" ({self.publication_year})" if self.publication_year else ""
        return f"{self.author}: {self.title}{year}"

    @property
    def age_warning(self) -> bool:
        if not self.publication_year:
            return False
        return (datetime.date.today().year - self.publication_year) > 5

    def to_comp_string(self) -> str:
        year = f" ({self.publication_year})" if self.publication_year else ""
        rel = self.get_relation_type_display()
        result = f"{self.author}: {self.title}{year} [{rel}]"
        if self.difference_note:
            result += f" — {self.difference_note[:100]}"
        return result


class PitchDocument(models.Model):
    """
    Pitch-Dokument — Logline, Exposé, Synopsis oder Query Letter (ADR-159).

    Versionierung: Jede Neu-Generierung inkrementiert version.
    is_current=True markiert die aktive Version pro Typ.
    """

    PITCH_TYPES = [
        ("logline",   "Logline — 1 Satz"),
        ("one_pager", "One-Pager — EN"),
        ("expose_de", "Exposé — DE Verlagsstandard"),
        ("synopsis",  "Synopsis — vollständige Handlung"),
        ("query",     "Query Letter — US/UK"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject,
        on_delete=models.CASCADE,
        related_name="pitch_documents",
    )
    pitch_type = models.CharField(max_length=20, choices=PITCH_TYPES, db_index=True)
    content = models.TextField(verbose_name="Inhalt")
    word_count = models.PositiveIntegerField(default=0)
    is_ai_generated = models.BooleanField(default=False)
    ai_agent = models.CharField(max_length=100, blank=True, default="")
    is_current = models.BooleanField(
        default=True, db_index=True,
        help_text="Aktive Version dieses Typs (nur eine gleichzeitig).",
    )
    version = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_pitch_documents"
        ordering = ["project", "pitch_type", "-version"]
        verbose_name = "Pitch-Dokument"
        verbose_name_plural = "Pitch-Dokumente"

    def __str__(self):
        return f"{self.get_pitch_type_display()} v{self.version} — {self.project.title}"

    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)


class ResearchNote(models.Model):
    """
    Recherche-Notiz — verifizierter Fakt, offene Frage oder Atmosphäre-Detail (ADR-160).

    is_verified=True → wird in LLM-Prompts injiziert.
    is_open_question=True → wird im Health-Score als offene Frage gezählt.
    """

    NOTE_TYPES = [
        ("fact",       "Fakt — verifiziert"),
        ("question",   "Offene Frage"),
        ("rule",       "Regel / Gesetz / Technologie"),
        ("atmosphere", "Atmosphäre / Detail"),
        ("quote",      "Zitat"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject,
        on_delete=models.CASCADE,
        related_name="research_notes",
    )
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default="fact")
    title = models.CharField(max_length=300, verbose_name="Bezeichnung")
    content = models.TextField(verbose_name="Inhalt")
    source = models.CharField(
        max_length=500, blank=True, default="",
        help_text="URL, Buchtitel, Experteninterview",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Nur verifizierte Notizen werden in LLM-Prompts injiziert.",
    )
    is_open_question = models.BooleanField(
        default=False,
        help_text="Noch unbeantwortet — wird im Health-Score gezählt.",
    )
    relevant_nodes = models.ManyToManyField(
        "OutlineNode",
        blank=True,
        related_name="research_notes",
        help_text="Welche Kapitel/Szenen brauchen diese Notiz?",
    )
    tags = models.JSONField(default=list)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_research_notes"
        ordering = ["project", "-is_verified", "note_type", "sort_order"]
        verbose_name = "Recherche-Notiz"
        verbose_name_plural = "Recherche-Notizen"

    def __str__(self):
        verified = " ✓" if self.is_verified else " ?"
        return f"[{self.get_note_type_display()}]{verified} {self.title}"

    def to_prompt_context(self) -> str:
        lines = [
            f"[{self.get_note_type_display().upper()}] {self.title}",
            self.content[:800],
        ]
        if self.source:
            lines.append(f"Quelle: {self.source}")
        return "\n".join(lines)


class GenreConventionProfile(models.Model):
    """
    Genre-Konventions-Profil — maschinenlesbare Vertrags-Regeln (ADR-160).

    1:1 zu GenreLookup. Admin-verwaltbar.
    conventions JSON-Schema: [{label, description, check_type, check_by_percent, weight, outlinefw_beat}]
    """

    genre_lookup = models.OneToOneField(
        "GenreLookup",
        on_delete=models.CASCADE,
        related_name="convention_profile",
    )
    conventions = models.JSONField(
        default=list,
        help_text="Liste von Konventions-Checks (check_type: turning_point_exists, b_story_exists, happy_end_required, fair_play)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_genre_convention_profiles"
        verbose_name = "Genre-Konventions-Profil"
        verbose_name_plural = "Genre-Konventions-Profile"

    def __str__(self):
        return f"Konventionen: {self.genre_lookup.name}"


class BetaReaderSession(models.Model):
    """
    Beta-Leser-Runde — strukturiertes Testleser-Feedback (ADR-160).

    Unterschied zu ChapterReview: Externe Person reagiert als Leser,
    nicht als Strukturanalytiker.
    """

    ANON_CHOICES = [
        ("open",      "Offen — alles sichtbar"),
        ("anon_meta", "Text only — keine Metadaten"),
        ("anon_full", "Vollständig anonym"),
    ]
    FEEDBACK_FOCUS = [
        ("general",   "Allgemein"),
        ("pacing",    "Pacing & Tempo"),
        ("character", "Figuren-Sympathie"),
        ("clarity",   "Verständlichkeit"),
        ("tension",   "Spannungsverlauf"),
        ("ending",    "Schluss / Auflösung"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject,
        on_delete=models.CASCADE,
        related_name="beta_sessions",
    )
    name = models.CharField(max_length=200)
    anonymization = models.CharField(max_length=20, choices=ANON_CHOICES, default="anon_meta")
    feedback_focus = models.CharField(max_length=20, choices=FEEDBACK_FOCUS, default="general")
    manuscript_snapshot = models.ForeignKey(
        "ManuscriptSnapshot",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="beta_sessions",
    )
    reader_name = models.CharField(max_length=200, blank=True, default="")
    reader_note = models.TextField(blank=True, default="")
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "wh_beta_reader_sessions"
        ordering = ["-created_at"]
        verbose_name = "Beta-Leser-Session"
        verbose_name_plural = "Beta-Leser-Sessions"

    def __str__(self):
        return f"{self.name} — {self.project.title}"

    @property
    def open_feedback_count(self) -> int:
        return self.feedbacks.filter(is_addressed=False).count()


class BetaReaderFeedback(models.Model):
    """
    Einzelnes Feedback-Item einer Beta-Leser-Session (ADR-160).

    feedback_type='confusion' hat höchste Priorität.
    """

    FEEDBACK_TYPES = [
        ("confusion",    "Unklarheit / Verwirrung"),
        ("boredom",      "Langeweile / Tempo zu langsam"),
        ("tension_drop", "Spannungsabfall"),
        ("highlight",    "Besonders gut"),
        ("character_ok", "Figur sympathisch"),
        ("char_problem", "Figur-Problem"),
        ("general",      "Allgemeines Feedback"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        BetaReaderSession,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    node = models.ForeignKey(
        "OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="beta_feedbacks",
    )
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default="general")
    text = models.TextField(verbose_name="Feedback-Text")
    text_reference = models.TextField(blank=True, default="")
    chapter_order = models.PositiveSmallIntegerField(null=True, blank=True)
    is_addressed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_beta_reader_feedbacks"
        ordering = ["session", "chapter_order", "feedback_type"]
        verbose_name = "Beta-Reader-Feedback"
        verbose_name_plural = "Beta-Reader-Feedbacks"

    def __str__(self):
        return f"[{self.get_feedback_type_display()}] {self.text[:60]}"


class PeerReviewSession(models.Model):
    """
    KI-gestütztes wissenschaftliches Peer Review — Gesamtsitzung.

    Orchestriert mehrere Review-Agenten (Methodik, Argumentation,
    Quellen, Struktur) und erzeugt ein Gesamtgutachten.
    Nur für content_type in (academic, scientific, essay).
    """

    STATUS_CHOICES = [
        ("pending", "Ausstehend"),
        ("running", "Läuft"),
        ("done", "Abgeschlossen"),
        ("error", "Fehler"),
    ]
    VERDICT_CHOICES = [
        ("accept", "Accept"),
        ("minor_revisions", "Minor Revisions"),
        ("major_revisions", "Major Revisions"),
        ("reject", "Reject"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        BookProject, on_delete=models.CASCADE, related_name="peer_reviews",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    verdict = models.CharField(
        max_length=20, choices=VERDICT_CHOICES, blank=True, default="",
    )
    summary = models.TextField(blank=True, default="")
    strengths = models.JSONField(default=list)
    main_issues = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    scores = models.JSONField(
        default=dict,
        help_text="Dimension scores: originality, methodology, argumentation, sources, structure (1-10)",
    )
    agents_used = models.JSONField(default=list)
    chapter_count = models.PositiveSmallIntegerField(default=0)
    finding_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "wh_peer_review_sessions"
        ordering = ["-created_at"]
        verbose_name = "Peer Review Session"
        verbose_name_plural = "Peer Review Sessions"

    def __str__(self):
        verdict = f" [{self.get_verdict_display()}]" if self.verdict else ""
        return f"Peer Review: {self.project.title}{verdict}"

    @property
    def avg_score(self):
        if not self.scores:
            return 0
        vals = [v for v in self.scores.values() if isinstance(v, (int, float))]
        return round(sum(vals) / len(vals), 1) if vals else 0


class PeerReviewFinding(models.Model):
    """
    Einzelnes Finding eines Peer-Review-Agenten.

    Jeder Agent (methodology, argumentation, sources, structure) erzeugt
    mehrere Findings pro Kapitel/Abschnitt.
    """

    FINDING_TYPES = [
        ("strength", "Stärke"),
        ("weakness", "Schwäche"),
        ("suggestion", "Vorschlag"),
        ("concern", "Bedenken"),
    ]
    SEVERITY_CHOICES = [
        ("minor", "Minor"),
        ("major", "Major"),
        ("critical", "Critical"),
    ]
    AGENT_CHOICES = [
        ("methodology", "Methodik-Prüfer"),
        ("argumentation", "Argumentations-Prüfer"),
        ("sources", "Quellen-Prüfer"),
        ("structure", "Struktur-Prüfer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        PeerReviewSession, on_delete=models.CASCADE, related_name="findings",
    )
    node = models.ForeignKey(
        OutlineNode, on_delete=models.CASCADE, related_name="peer_findings",
    )
    agent = models.CharField(max_length=30, choices=AGENT_CHOICES)
    finding_type = models.CharField(max_length=20, choices=FINDING_TYPES, default="suggestion")
    category = models.CharField(max_length=50, blank=True, default="")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="minor")
    feedback = models.TextField()
    text_reference = models.TextField(blank=True, default="")
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_peer_review_findings"
        ordering = ["session", "node__order", "-severity", "agent"]
        verbose_name = "Peer Review Finding"
        verbose_name_plural = "Peer Review Findings"

    def __str__(self):
        return f"[{self.get_agent_display()}] {self.feedback[:60]}"


# ADR-158: DialogueScene discoverable machen
from apps.projects.models_narrative import DialogueScene  # noqa: E402, F401

