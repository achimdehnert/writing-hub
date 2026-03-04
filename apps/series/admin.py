from django.contrib import admin

from .models import BookSeries, SeriesVolume


@admin.register(BookSeries)
class BookSeriesAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "genre", "created_at"]
    list_filter = ["genre"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SeriesVolume)
class SeriesVolumeAdmin(admin.ModelAdmin):
    list_display = ["series", "volume_number", "project"]
    list_filter = ["series"]
    readonly_fields = ["id"]
