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
    list_display = ["project", "weltenhub_character_id", "narrative_role", "project_role", "created_at"]
    list_filter = ["narrative_role", "antagonist_type"]
    search_fields = ["weltenhub_character_id", "project_arc", "notes"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = [
        ("Verknüpfung", {"fields": ["id", "project", "weltenhub_character_id", "project_role", "notes"]}),
        ("Narrative Rolle (ADR-157)", {"fields": ["narrative_role"]}),
        ("Charakter-Arc (ADR-152)", {"fields": ["want", "need", "flaw", "ghost", "false_belief", "true_belief"]}),
        ("Antagonisten-Felder (ADR-157)", {"fields": [
            "antagonist_type", "antagonist_logic",
            "mirror_to_protagonist", "shared_trait_with_protagonist", "information_advantage",
        ]}),
        ("Meta", {"fields": ["created_at", "updated_at"]}),
    ]
