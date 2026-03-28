from django.contrib import admin

from .models import BookSeries, SeriesVolume
from .models_arc import SeriesArc, SeriesCharacterContinuity, SeriesVolumeRole


class SeriesArcInline(admin.StackedInline):
    model = SeriesArc
    extra = 0
    fields = [
        "arc_type", "total_volumes_planned",
        "series_want", "series_need",
        "series_false_belief", "series_true_belief",
        "overarching_conflict", "series_theme_question",
    ]
    readonly_fields = ["id"]


class SeriesCharacterContinuityInline(admin.TabularInline):
    model = SeriesCharacterContinuity
    extra = 0
    fields = ["character_name", "physical_state", "emotional_state", "arc_progress"]
    readonly_fields = ["id"]


@admin.register(BookSeries)
class BookSeriesAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "genre", "has_arc", "created_at"]
    list_filter = ["genre"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [SeriesArcInline]

    def has_arc(self, obj):
        return hasattr(obj, "arc")
    has_arc.boolean = True
    has_arc.short_description = "Arc"


class SeriesVolumeRoleInline(admin.StackedInline):
    model = SeriesVolumeRole
    extra = 0
    fields = [
        "arc_position", "series_arc_contribution",
        "promise_to_reader", "promise_fulfilled_from",
        "cliffhanger_type", "cliffhanger_description",
    ]
    readonly_fields = ["id"]


@admin.register(SeriesVolume)
class SeriesVolumeAdmin(admin.ModelAdmin):
    list_display = ["series", "volume_number", "project", "has_role"]
    list_filter = ["series"]
    readonly_fields = ["id"]
    inlines = [SeriesVolumeRoleInline, SeriesCharacterContinuityInline]

    def has_role(self, obj):
        return hasattr(obj, "role")
    has_role.boolean = True
    has_role.short_description = "Rolle"


@admin.register(SeriesCharacterContinuity)
class SeriesCharacterContinuityAdmin(admin.ModelAdmin):
    list_display = ["character_name", "series", "volume", "updated_at"]
    list_filter = ["series"]
    search_fields = ["character_name", "series__title"]
    raw_id_fields = ["series", "volume"]
    readonly_fields = ["id", "created_at", "updated_at"]
