"""
Worlds Serializers — writing-hub

Nur lokale Link-Models werden serialisiert.
Welt/Charakter-Daten kommen von WeltenHub via iil-weltenfw.
"""
from rest_framework import serializers

from .models import ProjectCharacterLink, ProjectWorldLink


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
            "project_arc", "project_role", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
