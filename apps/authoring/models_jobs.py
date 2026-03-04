"""
ChapterWriteJob — Async Job-Tracking für Kapitel-Generierung.

Erstellt vom View, Status-Update durch Celery Task.
Polling-Endpunkt: GET /authoring/jobs/<chapter_ref>/status/
"""

import uuid

from django.conf import settings
from django.db import models


class JobStatus(models.TextChoices):
    PENDING = "pending", "Ausstehend"
    RUNNING = "running", "Läuft"
    DONE = "done", "Fertig"
    FAILED = "failed", "Fehlgeschlagen"


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
