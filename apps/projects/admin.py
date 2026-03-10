from django.contrib import admin

from .models import (
    AudienceLookup, AuthorStyleLookup, BookProject,
    ContentTypeLookup, GenreLookup, OutlineFramework,
    OutlineFrameworkBeat, OutlineNode, OutlineVersion,
)


@admin.register(ContentTypeLookup)
class ContentTypeLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "icon", "subtitle"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(GenreLookup)
class GenreLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]


@admin.register(AudienceLookup)
class AudienceLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]


@admin.register(AuthorStyleLookup)
class AuthorStyleLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]
    fields = ["name", "description", "style_prompt", "order", "is_active"]


class OutlineFrameworkBeatInline(admin.TabularInline):
    model = OutlineFrameworkBeat
    extra = 1
    fields = ["order", "name", "position_start", "position_end", "description"]


@admin.register(OutlineFramework)
class OutlineFrameworkAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "subtitle", "beat_count", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"key": ["name"]}
    inlines = [OutlineFrameworkBeatInline]

    def beat_count(self, obj):
        return obj.beats.count()
    beat_count.short_description = "Beats"


@admin.register(BookProject)
class BookProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "content_type_lookup", "genre_lookup", "is_active", "created_at"]
    list_filter = ["is_active", "content_type_lookup", "genre_lookup"]
    search_fields = ["title", "owner__username"]
    raw_id_fields = ["owner"]


@admin.register(OutlineVersion)
class OutlineVersionAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "source", "is_active", "created_at"]
    list_filter = ["is_active", "source"]
    search_fields = ["name", "project__title"]


@admin.register(OutlineNode)
class OutlineNodeAdmin(admin.ModelAdmin):
    list_display = ["title", "outline_version", "beat_type", "order", "word_count"]
    list_filter = ["beat_type"]
    search_fields = ["title"]
