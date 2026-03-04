"""
Series App — Buchserien, SharedCharacter, SharedWorld (ADR-083)

Extrahiert aus bfagent/apps/writing_hub/models_series.py (relevante Teile).
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class BookSeries(models.Model):
    """
    Buchserie — übergreifender Container für mehrteilige Werke.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_series",
    )

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_book_series"
        ordering = ["title"]
        verbose_name = "Book Series"
        verbose_name_plural = "Book Series"

    def __str__(self):
        return self.title


class SeriesVolume(models.Model):
    """
    Band einer Buchserie — verknüpft BookProject mit BookSeries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series = models.ForeignKey("BookSeries", on_delete=models.CASCADE, related_name="volumes")
    project = models.ForeignKey(
        "projects.BookProject", on_delete=models.CASCADE, related_name="series_volumes"
    )

    volume_number = models.PositiveIntegerField(default=1)
    subtitle = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "wh_series_volumes"
        ordering = ["series", "volume_number"]
        unique_together = ["series", "volume_number"]
        verbose_name = "Series Volume"
        verbose_name_plural = "Series Volumes"

    def __str__(self):
        return f"{self.series.title} Band {self.volume_number}: {self.project.title}"
