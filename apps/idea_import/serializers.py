from rest_framework import serializers

from .models import IdeaImportDraft


class IdeaImportDraftSerializer(serializers.ModelSerializer):
    available_sections = serializers.ReadOnlyField()
    confidence_overall = serializers.ReadOnlyField()

    class Meta:
        model = IdeaImportDraft
        fields = [
            "id",
            "project",
            "source_filename",
            "source_format",
            "extracted_data",
            "extraction_model",
            "status",
            "committed_sections",
            "commit_notes",
            "available_sections",
            "confidence_overall",
            "created_at",
            "committed_at",
        ]
        read_only_fields = ["id", "status", "created_at", "committed_at", "committed_sections"]


class IdeaImportCommitSerializer(serializers.Serializer):
    approved_sections = serializers.ListField(
        child=serializers.ChoiceField(choices=["metadata", "outline", "characters", "world"]),
        min_length=1,
    )
    override_existing = serializers.BooleanField(default=False)
    commit_notes = serializers.CharField(required=False, default="")
