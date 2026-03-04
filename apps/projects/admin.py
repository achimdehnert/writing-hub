from django.contrib import admin

from .models import BookProject, OutlineNode, OutlineVersion


@admin.register(BookProject)
class BookProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "content_type", "is_active", "updated_at"]
    list_filter = ["content_type", "is_active"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


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
