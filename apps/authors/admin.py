from django.contrib import admin

from .models import (
    Author,
    GenreProfile,
    SituationType,
    WritingStyle,
    WritingStyleSample,
)

# --- Genre / SituationType ---


class SituationTypeInline(admin.TabularInline):
    model = SituationType
    extra = 0
    fields = ["slug", "label", "sort_order", "is_active"]
    ordering = ["sort_order"]


@admin.register(GenreProfile)
class GenreProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "icon", "situation_count", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name_short",)}
    inlines = [SituationTypeInline]

    def situation_count(self, obj):
        return obj.situation_count

    situation_count.short_description = "Typen"


@admin.register(SituationType)
class SituationTypeAdmin(admin.ModelAdmin):
    list_display = ["label", "genre_profile", "slug", "sort_order", "is_active"]
    list_filter = ["genre_profile", "is_active"]
    search_fields = ["label", "slug"]


# --- Author / WritingStyle ---


class WritingStyleInline(admin.TabularInline):
    model = WritingStyle
    extra = 0
    fields = ["name", "genre_profile", "status", "is_active"]
    show_change_link = True


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "style_count", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "owner__username"]
    inlines = [WritingStyleInline]

    def style_count(self, obj):
        return obj.style_count

    style_count.short_description = "Stile"


class WritingStyleSampleInline(admin.TabularInline):
    model = WritingStyleSample
    extra = 0
    fields = ["situation_type", "situation", "text", "notes"]


@admin.register(WritingStyle)
class WritingStyleAdmin(admin.ModelAdmin):
    list_display = ["name", "author", "genre_profile", "status", "sample_count", "is_active"]
    list_filter = ["status", "is_active", "genre_profile"]
    search_fields = ["name", "author__name"]
    readonly_fields = ["status", "style_profile", "style_prompt", "error_message"]
    inlines = [WritingStyleSampleInline]

    def sample_count(self, obj):
        return obj.sample_count

    sample_count.short_description = "Beispiele"
