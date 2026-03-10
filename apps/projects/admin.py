from django.contrib import admin

from .models import (
    AudienceLookup,
    BookProject,
    ContentTypeLookup,
    GenreLookup,
    OutlineNode,
    OutlineVersion,
)


@admin.register(ContentTypeLookup)
class ContentTypeLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order"]
    ordering = ["order", "name"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        ("Grundinfo", {"fields": ("name", "slug", "order")}),
        (
            "Planning KI-Konfiguration (DB-driven)",
            {
                "fields": (
                    "planning_action_code",
                    "planning_prompt_template",
                    "planning_system_prompt",
                    "planning_user_template",
                ),
                "classes": ("collapse",),
                "description": (
                    "Steuert KI-Generierung fuer Praemisse, Themen und Logline. "
                    "planning_action_code: aifw action_code (z.B. 'planning_novel'). "
                    "planning_prompt_template: promptfw-Prefix (z.B. 'roman'). "
                    "Benutzerdefinierte Prompts ueberschreiben promptfw-Templates."
                ),
            },
        ),
    )


@admin.register(GenreLookup)
class GenreLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    ordering = ["order", "name"]


@admin.register(AudienceLookup)
class AudienceLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    ordering = ["order", "name"]


@admin.register(BookProject)
class BookProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "series", "content_type_lookup", "genre_lookup", "is_active", "updated_at"]
    list_filter = ["content_type_lookup", "genre_lookup", "is_active"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["series"]


@admin.register(OutlineVersion)
class OutlineVersionAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "source", "is_active", "created_at"]
    list_filter = ["source", "is_active"]
    search_fields = ["name", "project__title"]
    readonly_fields = ["id", "created_at"]


@admin.register(OutlineNode)
class OutlineNodeAdmin(admin.ModelAdmin):
    list_display = ["title", "outline_version", "beat_type", "order"]
    list_filter = ["beat_type"]
    search_fields = ["title", "description"]
    readonly_fields = ["id"]
