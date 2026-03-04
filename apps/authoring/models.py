"""
Authoring App Models — writing-hub (ADR-083 Phase 3)

Portiert aus bfagent.writing_hub.models_authoring + models_quality.
FKs auf bfagent.BookProjects → projects.BookProject (UUID PK).

Model-Gruppen:
  1. AuthoringSession       — aktive Schreibsitzung pro Projekt
  2. ProjectPhaseExecution  — Workflow-Phasen-Fortschritt
  3. QualityDimension       — Lookup: Bewertungsdimensionen
  4. GateDecisionType       — Lookup: Gate-Entscheidungstypen
  5. ProjectQualityConfig   — Konfiguration pro Projekt
  6. ChapterQualityScore    — Kapitel-Qualitätsbewertung
  7. ChapterDimensionScore  — Dimension-Score (M2M)
  8. AuthorStyleDNA         — Stil-Profil pro Autor/Projekt
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# =============================================================================
# 1. AuthoringSession
# =============================================================================


class AuthoringSession(models.Model):
    """Aktive Schreibsitzung für ein Projekt — speichert Kontext-Fenster."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="authoring_sessions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authoring_sessions",
        help_text="Autor der Session (null = systemgeneriert)",
    )
    current_node_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Aktuell bearbeiteter OutlineNode (UUID)",
    )
    context_window = models.JSONField(
        default=list,
        help_text="Letzte N KI-Interaktionen für Kontext-Kontinuität",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_authoring_sessions"
        verbose_name = "Authoring Session"
        verbose_name_plural = "Authoring Sessions"
        ordering = ["-updated_at"]

    def __str__(self):
        user_str = self.user.username if self.user else "system"
        return f"Session {self.pk} — {self.project} ({user_str})"


# =============================================================================
# 2. ProjectPhaseExecution
# =============================================================================


class PhaseExecutionStatus(models.TextChoices):
    PENDING = "pending", "Ausstehend"
    ACTIVE = "active", "Aktiv"
    WAITING = "waiting", "Wartet auf Gate-Freigabe"
    COMPLETED = "completed", "Abgeschlossen"
    SKIPPED = "skipped", "Übersprungen"


class ProjectPhaseExecution(models.Model):
    """
    Ausführungszustand einer Workflow-Phase pro Projekt.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="phase_executions",
    )
    phase_key = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Phase-Identifier (z.B. 'outline', 'characters', 'writing')",
    )
    step_key = models.CharField(
        max_length=100,
        blank=True,
        help_text="Schritt innerhalb der Phase (optional)",
    )
    status = models.CharField(
        max_length=15,
        choices=PhaseExecutionStatus.choices,
        default=PhaseExecutionStatus.PENDING,
    )
    gate_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_phase_executions",
    )
    gate_approved_at = models.DateTimeField(null=True, blank=True)
    gate_notes = models.TextField(blank=True)
    context = models.JSONField(
        default=dict,
        help_text="Phasen-übergreifender Kontext (KI-Ergebnisse, Notizen)",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "wh_project_phase_executions"
        verbose_name = "Projekt-Phasen-Ausführung"
        verbose_name_plural = "Projekt-Phasen-Ausführungen"
        unique_together = [["project", "phase_key", "step_key"]]
        ordering = ["project", "phase_key"]

    def __str__(self):
        return f"{self.project} — {self.phase_key} ({self.status})"


# =============================================================================
# 3. QualityDimension (Lookup)
# =============================================================================


class QualityDimension(models.Model):
    """
    Lookup: Qualitätsdimensionen für Kapitel-Bewertung.
    Beispiele: style, genre, scene, serial_logic, pacing, dialogue
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name_de = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weight = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.0,
        help_text="Gewichtung für Overall-Score Berechnung",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_quality_dimensions"
        ordering = ["sort_order", "code"]
        verbose_name = "Quality Dimension"
        verbose_name_plural = "Quality Dimensions"

    def __str__(self):
        return f"{self.name_de} ({self.code})"


# =============================================================================
# 4. GateDecisionType (Lookup)
# =============================================================================


class GateDecisionType(models.Model):
    """
    Lookup: Quality Gate Entscheidungen.
    Beispiele: approve, review, revise, reject
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True, db_index=True)
    name_de = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default="secondary")
    icon = models.CharField(max_length=50, default="bi-question-circle")
    allows_commit = models.BooleanField(
        default=False, help_text="Erlaubt Kapitel-Commit/Lock"
    )
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_gate_decision_types"
        ordering = ["sort_order"]
        verbose_name = "Gate Decision Type"
        verbose_name_plural = "Gate Decision Types"

    def __str__(self):
        return f"{self.name_de} ({self.code})"


# =============================================================================
# 5. ProjectQualityConfig
# =============================================================================


class ProjectQualityConfig(models.Model):
    """Quality Gate Konfiguration pro Projekt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="quality_config",
    )
    min_overall_score = models.DecimalField(
        max_digits=4, decimal_places=2, default="7.50",
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    auto_approve_threshold = models.DecimalField(
        max_digits=4, decimal_places=2, default="8.50",
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    auto_reject_threshold = models.DecimalField(
        max_digits=4, decimal_places=2, default="5.00",
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    require_manual_approval = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_project_quality_configs"
        verbose_name = "Project Quality Config"
        verbose_name_plural = "Project Quality Configs"

    def __str__(self):
        return f"QualityConfig — {self.project}"


# =============================================================================
# 6. ChapterQualityScore
# =============================================================================


class ChapterQualityScore(models.Model):
    """Qualitätsbewertung für ein Kapitel."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    chapter_ref = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Externe Referenz: bfagent.BookChapters.id (int oder UUID)",
    )
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="quality_scores",
    )
    scored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chapter_scores",
    )
    scored_at = models.DateTimeField(auto_now_add=True)
    gate_decision = models.ForeignKey(
        GateDecisionType,
        on_delete=models.PROTECT,
        related_name="chapter_scores",
    )
    overall_score = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Gewichteter Durchschnitt aller Dimension-Scores",
    )
    findings = models.JSONField(
        default=dict, blank=True,
        help_text="Strukturierte Findings: {deviations: [], suggestions: []}",
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "wh_chapter_quality_scores"
        ordering = ["-scored_at"]
        verbose_name = "Chapter Quality Score"
        verbose_name_plural = "Chapter Quality Scores"
        get_latest_by = "scored_at"

    def __str__(self):
        return f"Score {self.overall_score} — chapter_ref={self.chapter_ref}"

    @property
    def is_approved(self):
        return self.gate_decision.allows_commit


# =============================================================================
# 7. ChapterDimensionScore
# =============================================================================


class ChapterDimensionScore(models.Model):
    """Einzelne Dimension-Bewertung für einen ChapterQualityScore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quality_score = models.ForeignKey(
        ChapterQualityScore, on_delete=models.CASCADE, related_name="dimension_scores"
    )
    dimension = models.ForeignKey(
        QualityDimension, on_delete=models.PROTECT, related_name="chapter_scores"
    )
    score = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "wh_chapter_dimension_scores"
        unique_together = ["quality_score", "dimension"]
        verbose_name = "Chapter Dimension Score"
        verbose_name_plural = "Chapter Dimension Scores"

    def __str__(self):
        return f"{self.dimension.code}: {self.score}"


# =============================================================================
# 8. AuthorStyleDNA
# =============================================================================


class AuthorStyleDNA(models.Model):
    """
    Stil-Profil eines Autors — wird bei Kapitel-Generierung injiziert.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="style_dnas",
    )
    name = models.CharField(max_length=200, help_text="Name des Stilprofils")
    is_primary = models.BooleanField(
        default=False, help_text="Primäres Profil des Autors"
    )
    signature_moves = models.JSONField(
        default=list, help_text="Charakteristische Stilmittel (Liste von Strings)"
    )
    do_list = models.JSONField(
        default=list, help_text="Erlaubte/empfohlene Stilmittel"
    )
    dont_list = models.JSONField(
        default=list, help_text="Verbotene Stilmittel"
    )
    taboo_list = models.JSONField(
        default=list, help_text="Tabu-Wörter (niemals verwenden)"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_author_style_dnas"
        unique_together = [["author", "name"]]
        verbose_name = "Author Style DNA"
        verbose_name_plural = "Author Style DNAs"

    def __str__(self):
        primary = " (primary)" if self.is_primary else ""
        return f"{self.author.username} — {self.name}{primary}"
