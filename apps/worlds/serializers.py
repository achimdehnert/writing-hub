"""
Worlds Serializers — writing-hub

Lokale Link-Models + lokale Charakter-/Ort-Daten.
WeltenHub-IDs optional (leer = nur lokal gespeichert).
"""
from rest_framework import serializers

from .models import ProjectCharacterLink, ProjectLocationLink, ProjectWorldLink


class ProjectWorldLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectWorldLink
        fields = ["id", "project", "weltenhub_world_id", "role", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProjectCharacterLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCharacterLink
        fields = [
            "id", "project", "weltenhub_character_id",
            "name", "description", "personality", "backstory", "is_protagonist",
            "narrative_role", "source",
            "want", "need", "flaw", "ghost", "false_belief", "true_belief",
            "voice_pattern", "secret_what",
            "character_status", "first_appearance",
            "project_arc", "project_role", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectLocationLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectLocationLink
        fields = [
            "id", "project", "weltenhub_location_id",
            "name", "description", "atmosphere", "significance",
            "source", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
