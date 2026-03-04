from django.contrib import admin

from .models import IdeaImportDraft


@admin.register(IdeaImportDraft)
class IdeaImportDraftAdmin(admin.ModelAdmin):
    list_display = [
        "project", "source_filename", "source_format", "status",
        "confidence_overall_display", "created_at",
    ]
    list_filter = ["status", "source_format", "created_at"]
    search_fields = ["project__title", "source_filename", "commit_notes"]
    readonly_fields = [
        "id", "extracted_data", "source_text", "created_at",
        "committed_at", "extraction_model",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    @admin.display(description="Ø Konfidenz")
    def confidence_overall_display(self, obj) -> str:
        score = obj.confidence_overall
        return f"{score:.0%}" if score else "—"
