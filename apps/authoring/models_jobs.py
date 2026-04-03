"""
ChapterWriteJob — Async Job-Tracking für Kapitel-Generierung.

Erstellt vom View, Status-Update durch Celery Task.
Polling-Endpunkt: GET /authoring/jobs/<chapter_ref>/status/
"""

import uuid

from django.conf import settings
from django.db import models


class JobStatus(models.TextChoices):
    PENDING  = "pending",  "Ausstehend"
    RUNNING  = "running",  "Läuft"
    DONE     = "done",     "Fertig"
    FAILED   = "failed",   "Fehlgeschlagen"
    CANCELED = "canceled", "Abgebrochen"


class ChapterWriteJob(models.Model):
    """
    Async Job für Kapitel-Generierung.
    Erstellt vom View, aktualisiert vom Celery Task.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="chapter_write_jobs",
    )
    chapter_ref = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Externe Referenz auf bfagent.BookChapters.id",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chapter_write_jobs",
    )
    status = models.CharField(
        max_length=10,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
        db_index=True,
    )
    content = models.TextField(blank=True, help_text="Generierter Kapiteltext (nach Fertigstellung)")
    word_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_chapter_write_jobs"
        ordering = ["-created_at"]
        verbose_name = "Chapter Write Job"
        verbose_name_plural = "Chapter Write Jobs"
        indexes = [
            models.Index(fields=["chapter_ref", "status"]),
        ]

    def __str__(self):
        return f"WriteJob {self.chapter_ref} ({self.status})"

    @property
    def is_done(self):
        return self.status == JobStatus.DONE

    @property
    def is_failed(self):
        return self.status == JobStatus.FAILED


class BatchWriteJob(models.Model):
    """
    Sequenzielle Batch-Generierung mehrerer Kapitel (ADR-161).

    Sicherheit: max_chapters=10 — kein blindes Vollmanuskript-Generieren.
    Sequenziell: jedes Kapitel bekommt den Inhalt des vorherigen als Kontext.
    Status-Tracking via HTMX-Polling (alle 3s).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="batch_write_jobs",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="batch_write_jobs",
    )
    node_ids = models.JSONField(
        help_text="Geordnete Liste von OutlineNode-UUIDs (strings)",
    )
    max_chapters = models.PositiveSmallIntegerField(
        default=10,
        help_text="Sicherheits-Limit pro Batch-Job",
    )
    status = models.CharField(
        max_length=10, choices=JobStatus.choices, default=JobStatus.PENDING,
        db_index=True,
    )
    current_index = models.PositiveSmallIntegerField(default=0)
    completed_count = models.PositiveSmallIntegerField(default=0)
    failed_count = models.PositiveSmallIntegerField(default=0)
    error_log = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_batch_write_jobs"
        ordering = ["-created_at"]
        verbose_name = "Batch-Write-Job"
        verbose_name_plural = "Batch-Write-Jobs"

    def __str__(self):
        return f"BatchJob {self.pk} ({self.status}) — {self.project}"

    @property
    def total(self) -> int:
        return min(len(self.node_ids or []), self.max_chapters)

    @property
    def progress_pct(self) -> int:
        return int(self.completed_count / self.total * 100) if self.total else 0

    @property
    def is_running(self) -> bool:
        return self.status == JobStatus.RUNNING


class EssayPipelineJob(models.Model):
    """
    Quick-Project Pipeline: Outline → Recherche → Schreiben → Review.

    Tracking-Model für die autonome Essay-Generierung.
    Status-Polling via JSON-Endpunkt (alle 3s).
    """

    class PipelineStep(models.TextChoices):
        CREATED     = "created",     "Projekt erstellt"
        OUTLINE     = "outline",     "Outline wird generiert"
        RESEARCH    = "research",    "Literaturrecherche"
        WRITING     = "writing",     "Kapitel werden geschrieben"
        REVIEW      = "review",      "Peer Review"
        DONE        = "done",        "Fertig"
        FAILED      = "failed",      "Fehlgeschlagen"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="essay_pipeline_jobs",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="essay_pipeline_jobs",
    )
    status = models.CharField(
        max_length=10, choices=JobStatus.choices, default=JobStatus.PENDING,
        db_index=True,
    )
    current_step = models.CharField(
        max_length=20, choices=PipelineStep.choices, default=PipelineStep.CREATED,
    )
    framework = models.CharField(max_length=50, default="academic_essay")
    do_research = models.BooleanField(default=False)
    do_review = models.BooleanField(default=False)
    total_chapters = models.PositiveSmallIntegerField(default=0)
    completed_chapters = models.PositiveSmallIntegerField(default=0)
    current_chapter_title = models.CharField(max_length=300, blank=True, default="")
    log_messages = models.JSONField(default=list)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_essay_pipeline_jobs"
        ordering = ["-created_at"]
        verbose_name = "Essay-Pipeline-Job"
        verbose_name_plural = "Essay-Pipeline-Jobs"

    def __str__(self):
        return f"EssayPipeline {self.pk} ({self.status}/{self.current_step}) — {self.project}"

    @property
    def progress_pct(self) -> int:
        step_weights = {
            "created": 5,
            "outline": 15,
            "research": 30,
            "writing": 85,
            "review": 95,
            "done": 100,
            "failed": 0,
        }
        base = step_weights.get(self.current_step, 0)
        if self.current_step == "writing" and self.total_chapters > 0:
            chapter_pct = self.completed_chapters / self.total_chapters
            base = 30 + int(chapter_pct * 55)
        elif self.current_step == "research" and self.total_chapters > 0:
            chapter_pct = self.completed_chapters / self.total_chapters
            base = 15 + int(chapter_pct * 15)
        return min(base, 100)

    @property
    def is_terminal(self) -> bool:
        return self.status in (JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELED)

    def add_log(self, message: str):
        self.log_messages.append(message)
        self.save(update_fields=["log_messages", "updated_at"])
