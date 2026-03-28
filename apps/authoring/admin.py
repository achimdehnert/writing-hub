from django.contrib import admin

from .models import (
    AuthorStyleDNA,
    AuthoringSession,
    ChapterDimensionScore,
    ChapterQualityScore,
    GateDecisionType,
    ProjectPhaseExecution,
    ProjectQualityConfig,
    QualityDimension,
)
from .models_jobs import BatchWriteJob, ChapterWriteJob


@admin.register(QualityDimension)
class QualityDimensionAdmin(admin.ModelAdmin):
    list_display = ["code", "name_de", "weight", "is_active", "sort_order"]
    list_filter = ["is_active"]
    search_fields = ["code", "name_de", "name_en"]
    ordering = ["sort_order", "code"]


@admin.register(GateDecisionType)
class GateDecisionTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name_de", "allows_commit", "color", "sort_order"]
    list_filter = ["allows_commit"]


@admin.register(ProjectQualityConfig)
class ProjectQualityConfigAdmin(admin.ModelAdmin):
    list_display = ["project", "min_overall_score", "auto_approve_threshold", "auto_reject_threshold"]
    raw_id_fields = ["project"]


@admin.register(ChapterQualityScore)
class ChapterQualityScoreAdmin(admin.ModelAdmin):
    list_display = ["chapter_ref", "project", "overall_score", "gate_decision", "scored_at"]
    list_filter = ["gate_decision", "scored_at"]
    search_fields = ["chapter_ref", "project__title"]
    readonly_fields = ["id", "chapter_ref", "overall_score", "findings", "scored_at"]
    ordering = ["-scored_at"]
    date_hierarchy = "scored_at"


@admin.register(ChapterDimensionScore)
class ChapterDimensionScoreAdmin(admin.ModelAdmin):
    list_display = ["quality_score", "dimension", "score"]
    list_filter = ["dimension"]


@admin.register(AuthorStyleDNA)
class AuthorStyleDNAAdmin(admin.ModelAdmin):
    list_display = ["author", "name", "is_primary", "created_at"]
    list_filter = ["is_primary"]
    search_fields = ["author__username", "name"]


@admin.register(AuthoringSession)
class AuthoringSessionAdmin(admin.ModelAdmin):
    list_display = ["project", "user", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active"]
    raw_id_fields = ["project", "user"]


@admin.register(ProjectPhaseExecution)
class ProjectPhaseExecutionAdmin(admin.ModelAdmin):
    list_display = ["project", "phase_key", "step_key", "status", "started_at"]
    list_filter = ["status", "phase_key"]
    raw_id_fields = ["project"]


@admin.register(ChapterWriteJob)
class ChapterWriteJobAdmin(admin.ModelAdmin):
    list_display = ["chapter_ref", "project", "status", "word_count", "created_at"]
    list_filter = ["status"]
    search_fields = ["chapter_ref"]
    readonly_fields = ["id", "chapter_ref", "content", "error", "created_at", "updated_at"]


@admin.register(BatchWriteJob)
class BatchWriteJobAdmin(admin.ModelAdmin):
    list_display = ["project", "status", "completed_count", "failed_count", "total", "created_at"]
    list_filter = ["status"]
    search_fields = ["project__title"]
    raw_id_fields = ["project", "requested_by"]
    readonly_fields = ["id", "completed_count", "failed_count", "error_log", "current_index", "created_at", "updated_at"]
