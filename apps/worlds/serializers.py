from rest_framework import serializers

from .models import World, WorldCharacter, WorldLocation, WorldRule


class WorldLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorldLocation
        fields = ["id", "name", "location_type", "description", "parent"]


class WorldRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorldRule
        fields = ["id", "category", "rule", "explanation", "importance"]


class WorldCharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorldCharacter
        fields = [
            "id", "world", "name", "role", "description",
            "background", "motivation", "arc", "is_template",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorldSerializer(serializers.ModelSerializer):
    locations = WorldLocationSerializer(many=True, read_only=True)
    rules = WorldRuleSerializer(many=True, read_only=True)

    class Meta:
        model = World
        fields = [
            "id", "name", "slug", "description", "language",
            "is_public", "is_template", "tags",
            "locations", "rules",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
