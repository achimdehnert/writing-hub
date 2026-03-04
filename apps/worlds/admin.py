from django.contrib import admin

from .models import World, WorldCharacter, WorldLocation, WorldRule


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "language", "is_public", "created_at"]
    list_filter = ["language", "is_public", "is_template"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(WorldCharacter)
class WorldCharacterAdmin(admin.ModelAdmin):
    list_display = ["name", "world", "role", "is_template", "created_at"]
    list_filter = ["role", "world", "is_template"]
    search_fields = ["name", "description", "world__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(WorldLocation)
class WorldLocationAdmin(admin.ModelAdmin):
    list_display = ["name", "world", "location_type", "parent"]
    list_filter = ["location_type", "world"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(WorldRule)
class WorldRuleAdmin(admin.ModelAdmin):
    list_display = ["rule", "world", "category", "importance"]
    list_filter = ["category", "importance", "world"]
    search_fields = ["rule", "explanation"]
    readonly_fields = ["id", "created_at", "updated_at"]
