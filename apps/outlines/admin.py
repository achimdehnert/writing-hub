"""
Outlines Admin — Prompt-Template Management + Quality Ratings
"""

from django.contrib import admin

from apps.outlines.models import OutlinePromptTemplate, OutlineQualityRating


@admin.register(OutlinePromptTemplate)
class OutlinePromptTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "content_type_group",
        "template_key",
        "version",
        "is_active",
        "rating_summary",
        "updated_at",
    ]
    list_filter = ["content_type_group", "template_key", "is_active"]
    search_fields = ["system_prompt", "user_prompt_template", "notes"]
    readonly_fields = ["version", "created_at", "updated_at"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "content_type_group",
                    "template_key",
                    "is_active",
                    "version",
                ],
            },
        ),
        (
            "Prompts",
            {
                "fields": ["system_prompt", "user_prompt_template"],
                "classes": ["wide"],
            },
        ),
        (
            "Meta",
            {
                "fields": ["notes", "created_by", "created_at", "updated_at"],
            },
        ),
    ]
    actions = ["activate_selected"]

    def rating_summary(self, obj):
        from django.db.models import Avg, Count

        stats = obj.ratings.aggregate(
            count=Count("id"),
            avg=Avg("rating"),
        )
        if stats["count"]:
            return f"{stats['avg']:.1f}★ ({stats['count']}x)"
        return "—"

    rating_summary.short_description = "Bewertung"

    @admin.action(description="Ausgewählte aktivieren (deaktiviert andere gleiche Keys)")
    def activate_selected(self, request, queryset):
        for tpl in queryset:
            tpl.activate()
        self.message_user(request, f"{queryset.count()} Template(s) aktiviert.")


@admin.register(OutlineQualityRating)
class OutlineQualityRatingAdmin(admin.ModelAdmin):
    list_display = [
        "outline_node",
        "rating",
        "prompt_template",
        "created_by",
        "created_at",
    ]
    list_filter = ["rating", "created_at"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["outline_node", "prompt_template", "created_by"]
