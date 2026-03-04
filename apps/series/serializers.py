from rest_framework import serializers

from .models import BookSeries, SeriesVolume


class SeriesVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesVolume
        fields = ["id", "volume_number", "subtitle", "project", "notes"]
        read_only_fields = ["id"]


class BookSeriesSerializer(serializers.ModelSerializer):
    volumes = SeriesVolumeSerializer(many=True, read_only=True)

    class Meta:
        model = BookSeries
        fields = ["id", "title", "description", "genre", "volumes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
