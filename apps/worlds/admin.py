from django.contrib import admin

from .models import ProjectCharacterLink, ProjectWorldLink


@admin.register(ProjectWorldLink)
class ProjectWorldLinkAdmin(admin.ModelAdmin):
    list_display = ["project", "weltenhub_world_id", "role", "created_at"]
    list_filter = ["role"]
    search_fields = ["weltenhub_world_id", "notes"]
    readonly_fields = ["id", "created_at"]


@admin.register(ProjectCharacterLink)
class ProjectCharacterLinkAdmin(admin.ModelAdmin):
    list_display = ["project", "weltenhub_character_id", "project_role", "created_at"]
    list_filter = ["project_role"]
    search_fields = ["weltenhub_character_id", "project_arc", "notes"]
    readonly_fields = ["id", "created_at"]
