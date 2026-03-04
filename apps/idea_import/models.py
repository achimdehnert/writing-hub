"""
Idea Import — Staging-Modell für KI-extrahierte Buchideen (ADR-081, ADR-083)

Portiert aus bfagent/apps/writing_hub/models_idea_import.py.
Angepasst für writing-hub: FK zu projects.BookProject statt bfagent.BookProjects.
"""
from __future__ import annotations

import uuid

from django.db import models


class IdeaImportDraft(models.Model):
    """
    Staging-Tabelle für KI-extrahierte Ideen vor dem Commit.

    Workflow: pending_review -> (committed | partial | discarded)

    Human Gate: Kein direktes Schreiben in Produktionstabellen.
    """

    class Status(models.TextChoices):
        PENDING_REVIEW = "pending_review", "Wartet auf Review"
        COMMITTED = "committed", "Vollständig committed"
        PARTIAL = "partial", "Teilweise committed"
        DISCARDED = "discarded", "Verworfen"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="idea_import_drafts",
        verbose_name="Buchprojekt",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="idea_import_drafts",
        verbose_name="Erstellt von",
    )

    source_filename = models.CharField(
        max_length=255, blank=True, verbose_name="Quelldatei",
        help_text="Originaler Dateiname (leer bei Freitext)",
    )
    source_format = models.CharField(
        max_length=10, blank=True, verbose_name="Quellformat",
        help_text="txt | md | docx | pdf | freetext",
    )
    source_text = models.TextField(
        blank=True, verbose_name="Normalisierter Quelltext",
        help_text="Normalisierter Quelltext (max. 20.000 Zeichen = Extraktions-Limit)",
    )

    extracted_data = models.JSONField(
        verbose_name="Extrahierte Daten",
        help_text="ExtractedIdea als JSON (Pydantic-Snapshot)",
    )
    extraction_model = models.CharField(
        max_length=100, blank=True, verbose_name="Verwendetes LLM",
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_REVIEW,
        db_index=True, verbose_name="Status",
    )
    committed_sections = models.JSONField(
        default=list, verbose_name="Committete Sektionen",
        help_text='z.B. ["metadata", "outline", "characters"]',
    )
    commit_notes = models.TextField(blank=True, verbose_name="Commit-Notizen")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    committed_at = models.DateTimeField(null=True, blank=True, verbose_name="Committed am")

    class Meta:
        db_table = "wh_idea_import_drafts"
        verbose_name = "Ideen-Import-Entwurf"
        verbose_name_plural = "Ideen-Import-Entwürfe"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        src = self.source_filename or "Freitext"
        return f"{self.project} — {src} ({self.get_status_display()})"

    @property
    def has_metadata(self) -> bool:
        data = self.extracted_data or {}
        return bool(data.get("title") or data.get("description"))

    @property
    def has_outline(self) -> bool:
        data = self.extracted_data or {}
        return bool(data.get("outline_beats") or data.get("chapters"))

    @property
    def has_characters(self) -> bool:
        data = self.extracted_data or {}
        return bool(data.get("characters"))

    @property
    def has_world(self) -> bool:
        data = self.extracted_data or {}
        return bool(data.get("world_elements"))

    @property
    def available_sections(self) -> list[str]:
        sections = []
        if self.has_metadata:
            sections.append("metadata")
        if self.has_outline:
            sections.append("outline")
        if self.has_characters:
            sections.append("characters")
        if self.has_world:
            sections.append("world")
        return sections

    @property
    def confidence_overall(self) -> float:
        scores = (self.extracted_data or {}).get("confidence_scores", {})
        if not scores:
            return 0.0
        return sum(scores.values()) / len(scores)
