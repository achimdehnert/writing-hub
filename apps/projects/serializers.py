from rest_framework import serializers

from .models import BookProject, OutlineNode, OutlineVersion


class OutlineNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutlineNode
        fields = ["id", "title", "description", "beat_type", "order", "notes"]
        read_only_fields = ["id"]


class OutlineVersionSerializer(serializers.ModelSerializer):
    nodes = OutlineNodeSerializer(many=True, read_only=True)

    class Meta:
        model = OutlineVersion
        fields = ["id", "name", "source", "is_active", "notes", "nodes", "created_at"]
        read_only_fields = ["id", "created_at"]


class BookProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookProject
        fields = [
            "id",
            "bfagent_id",
            "title",
            "description",
            "content_type",
            "genre",
            "target_audience",
            "target_word_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
