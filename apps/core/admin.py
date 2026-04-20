from django.contrib import admin

from .models_lookups_drama import GenrePromiseLookup, TurningPointTypeLookup


@admin.register(TurningPointTypeLookup)
class TurningPointTypeLookupAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "default_position_percent", "sort_order"]
    list_editable = ["sort_order"]
    search_fields = ["code", "label"]
    readonly_fields = ["id"]
    fieldsets = [
        ("Kern", {"fields": ["code", "label", "description"]}),
        (
            "Position",
            {
                "fields": [
                    "default_position_percent",
                    "default_position_normalized",
                    "outlinefw_beat_name",
                ]
            },
        ),
        ("Spiegel & Sortierung", {"fields": ["mirrors_type_code", "sort_order"]}),
    ]


@admin.register(GenrePromiseLookup)
class GenrePromiseLookupAdmin(admin.ModelAdmin):
    list_display = ["genre_label", "genre_slug", "sort_order", "updated_at"]
    list_editable = ["sort_order"]
    search_fields = ["genre_slug", "genre_label", "core_promise"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        ("Genre", {"fields": ["genre_slug", "genre_label", "sort_order"]}),
        (
            "Versprechen",
            {
                "fields": [
                    "core_promise",
                    "reader_expectation",
                    "must_haves",
                    "must_not_haves",
                ]
            },
        ),
        ("LLM-Prompt", {"fields": ["llm_prompt_block"]}),
        ("Meta", {"fields": ["created_at", "updated_at"]}),
    ]
