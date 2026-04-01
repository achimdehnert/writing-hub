"""
Ideen-Studio — Kreativagent-Modelle (ADR-083)

Workflow:
  CreativeSession (Brainstorming → Refining → Premise → Done)
    └─ BookIdea (3-5 KI-generierte Buchideen pro Session)
"""
import uuid

from django.conf import settings
from django.db import models


class CreativeSession(models.Model):
    """Eine Brainstorming-Session des Kreativagenten."""

    class Phase(models.TextChoices):
        BRAINSTORMING = "brainstorming", "Brainstorming"
        REFINING = "refining", "Verfeinern"
        PREMISE = "premise", "Premise"
        DONE = "done", "Abgeschlossen"

    class SessionType(models.TextChoices):
        LITERARY = "literary", "Belletristik"
        SCIENTIFIC = "scientific", "Wissenschaftlich"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="creative_sessions",
    )
    title = models.CharField(
        max_length=200,
        help_text="Arbeitstitel der Session (z.B. Projektname oder Ideen-Thema)",
    )
    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        default=SessionType.LITERARY,
        help_text="Belletristik oder Wissenschaftlich",
    )
    inspiration = models.TextField(
        blank=True,
        help_text="Initiale Idee, Genre-Wunsch oder freier Inspirationstext",
    )
    genre = models.CharField(max_length=100, blank=True)
    research_field = models.CharField(
        max_length=200,
        blank=True,
        help_text="Fachgebiet / Disziplin (nur für wissenschaftliche Sessions)",
    )
    style_dna_hint = models.TextField(
        blank=True,
        help_text="Optionaler Stil-Hinweis für die KI-Generierung",
    )
    phase = models.CharField(
        max_length=20, choices=Phase.choices, default=Phase.BRAINSTORMING
    )
    selected_idea = models.ForeignKey(
        "BookIdea",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="selected_for_sessions",
    )
    premise = models.TextField(
        blank=True,
        help_text="KI-generierte vollständige Premise",
    )
    created_project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="creative_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_creative_sessions"
        ordering = ["-updated_at"]
        verbose_name = "Kreativ-Session"
        verbose_name_plural = "Kreativ-Sessions"

    def __str__(self):
        return f"{self.title} ({self.get_phase_display()})"

    @property
    def idea_count(self):
        return self.ideas.count()


class BookIdea(models.Model):
    """Eine KI-generierte Buchidee innerhalb einer Kreativ-Session."""

    class Rating(models.IntegerChoices):
        UNRATED = 0, "Nicht bewertet"
        MEH = 1, "♥ Schwach"
        OK = 2, "♥♥ Ok"
        GOOD = 3, "♥♥♥ Gut"
        GREAT = 4, "♥♥♥♥ Toll"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        CreativeSession,
        on_delete=models.CASCADE,
        related_name="ideas",
    )
    title = models.CharField(max_length=300)
    logline = models.TextField(
        help_text="1-2 Sätze: Wer will was und scheitert woran?",
    )
    hook = models.TextField(
        blank=True,
        help_text="Was macht diese Idee besonders/einzigartig?",
    )
    genre = models.CharField(max_length=100, blank=True)
    themes = models.JSONField(default=list, help_text="Themen als Liste")
    rating = models.SmallIntegerField(
        choices=Rating.choices, default=Rating.UNRATED
    )
    is_refined = models.BooleanField(default=False)
    refined_logline = models.TextField(blank=True)
    premise = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_book_ideas"
        ordering = ["session", "order"]
        verbose_name = "Buchidee"
        verbose_name_plural = "Buchideen"

    def __str__(self):
        return f"{self.session.title} — {self.title}"
