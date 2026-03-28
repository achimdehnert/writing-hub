from django.contrib import admin

from .models import (
    AudienceLookup, AuthorStyleLookup, BetaReaderFeedback,
    BetaReaderSession, BookProject, ComparableTitle,
    ContentTypeLookup, GenreConventionProfile, GenreLookup,
    OutlineFramework, OutlineFrameworkBeat, OutlineNode,
    OutlineSequence, OutlineVersion, PitchDocument,
    ProjectGenrePromise, ProjectTurningPoint,
    ResearchNote, SubplotArc, TextAnalysisSnapshot,
)
from .models_narrative import DialogueScene
from .models_timeline import (
    ForeshadowingEntry, ForeshadowingTypeLookup,
    MasterTimeline, NarrativeModelLookup,
    PlannedFlashback, TimelineEntry,
)


@admin.register(ContentTypeLookup)
class ContentTypeLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "icon", "subtitle"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(GenreLookup)
class GenreLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]


@admin.register(AudienceLookup)
class AudienceLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]


@admin.register(AuthorStyleLookup)
class AuthorStyleLookupAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]
    fields = ["name", "description", "style_prompt", "order", "is_active"]


class OutlineFrameworkBeatInline(admin.TabularInline):
    model = OutlineFrameworkBeat
    extra = 1
    fields = ["order", "name", "position_start", "position_end", "description"]


@admin.register(OutlineFramework)
class OutlineFrameworkAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "subtitle", "beat_count", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"key": ["name"]}
    inlines = [OutlineFrameworkBeatInline]

    def beat_count(self, obj):
        return obj.beats.count()
    beat_count.short_description = "Beats"


@admin.register(BookProject)
class BookProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "content_type_lookup", "genre_lookup", "is_active", "created_at"]
    list_filter = ["is_active", "content_type_lookup", "genre_lookup"]
    search_fields = ["title", "owner__username"]
    raw_id_fields = ["owner"]


@admin.register(OutlineVersion)
class OutlineVersionAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "source", "is_active", "created_at"]
    list_filter = ["is_active", "source"]
    search_fields = ["name", "project__title"]


@admin.register(OutlineNode)
class OutlineNodeAdmin(admin.ModelAdmin):
    list_display = ["title", "outline_version", "beat_type", "order", "word_count"]
    list_filter = ["beat_type"]
    search_fields = ["title"]


class SubplotArcIntersectionInline(admin.TabularInline):
    model = SubplotArc.intersection_nodes.through
    extra = 0
    verbose_name = "Kreuzungspunkt"
    verbose_name_plural = "Kreuzungspunkte"


@admin.register(SubplotArc)
class SubplotArcAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "story_label", "begins_at_percent", "ends_at_percent", "created_at"]
    list_filter = ["story_label", "embodies_need"]
    search_fields = ["title", "project__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["project", "begins_at_node", "ends_at_node"]
    inlines = [SubplotArcIntersectionInline]
    fieldsets = [
        ("Allgemein", {"fields": ["id", "project", "story_label", "title"]}),
        ("Träger-Figur", {"fields": ["carried_by_character_id", "carried_by_name"]}),
        ("Dramaturgik", {"fields": ["thematic_mirror", "embodies_need"]}),
        ("Position", {"fields": [
            "begins_at_percent", "ends_at_percent",
            "begins_at_node", "ends_at_node",
        ]}),
        ("Anmerkungen", {"fields": ["intersection_notes"]}),
        ("Meta", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(ProjectGenrePromise)
class ProjectGenrePromiseAdmin(admin.ModelAdmin):
    list_display = ["project", "genre_promise", "is_primary", "created_at"]
    list_filter = ["is_primary"]
    search_fields = ["project__title"]
    raw_id_fields = ["project", "genre_promise"]
    readonly_fields = ["id", "created_at"]


@admin.register(ComparableTitle)
class ComparableTitleAdmin(admin.ModelAdmin):
    list_display = ["author", "title", "publication_year", "project", "relation_type", "sort_order"]
    list_filter = ["relation_type"]
    search_fields = ["title", "author", "project__title"]
    raw_id_fields = ["project"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = [
        ("Comp", {"fields": ["id", "project", "title", "author", "publisher", "publication_year"]}),
        ("Beziehung", {"fields": ["relation_type", "similarity_note", "difference_note"]}),
        ("Meta", {"fields": ["sort_order", "created_at", "updated_at"]}),
    ]


@admin.register(PitchDocument)
class PitchDocumentAdmin(admin.ModelAdmin):
    list_display = ["project", "pitch_type", "version", "word_count", "is_current", "is_ai_generated", "created_at"]
    list_filter = ["pitch_type", "is_current", "is_ai_generated"]
    search_fields = ["project__title"]
    raw_id_fields = ["project"]
    readonly_fields = ["id", "word_count", "created_at", "updated_at"]


class ResearchNoteNodesInline(admin.TabularInline):
    model = ResearchNote.relevant_nodes.through
    extra = 0
    verbose_name = "Verknüpfter Kapitel-Node"


@admin.register(ResearchNote)
class ResearchNoteAdmin(admin.ModelAdmin):
    list_display = ["title", "note_type", "project", "is_verified", "is_open_question", "created_at"]
    list_filter = ["note_type", "is_verified", "is_open_question"]
    search_fields = ["title", "project__title"]
    raw_id_fields = ["project"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [ResearchNoteNodesInline]
    fieldsets = [
        ("Notiz", {"fields": ["id", "project", "note_type", "title", "content", "source"]}),
        ("Status", {"fields": ["is_verified", "is_open_question", "tags", "sort_order"]}),
        ("Meta", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(GenreConventionProfile)
class GenreConventionProfileAdmin(admin.ModelAdmin):
    list_display = ["genre_lookup", "convention_count", "created_at"]
    search_fields = ["genre_lookup__name"]
    readonly_fields = ["created_at", "updated_at"]

    def convention_count(self, obj):
        return len(obj.conventions or [])
    convention_count.short_description = "Konventionen"


class BetaReaderFeedbackInline(admin.TabularInline):
    model = BetaReaderFeedback
    extra = 0
    fields = ["feedback_type", "chapter_order", "text", "is_addressed"]
    readonly_fields = ["id"]


@admin.register(BetaReaderSession)
class BetaReaderSessionAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "feedback_focus", "is_completed", "open_feedback_count", "created_at"]
    list_filter = ["feedback_focus", "is_completed"]
    search_fields = ["name", "project__title"]
    raw_id_fields = ["project", "manuscript_snapshot"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [BetaReaderFeedbackInline]

    def open_feedback_count(self, obj):
        return obj.open_feedback_count
    open_feedback_count.short_description = "Offen"


@admin.register(TextAnalysisSnapshot)
class TextAnalysisSnapshotAdmin(admin.ModelAdmin):
    list_display = ["project", "chapters_analyzed", "dead_scene_count", "triggered_by", "computed_at"]
    list_filter = ["triggered_by"]
    search_fields = ["project__title"]
    raw_id_fields = ["project"]
    readonly_fields = [
        "id", "dead_scene_count", "dead_scene_node_ids",
        "character_screen_time", "chapter_word_counts",
        "pacing_variance", "pacing_issues", "dialogue_ratios",
        "voice_drift_checked", "voice_drift_detected", "voice_drift_chapters",
        "chapters_analyzed", "computed_at",
    ]


@admin.register(OutlineSequence)
class OutlineSequenceAdmin(admin.ModelAdmin):
    list_display = ["title", "outline_version", "act", "sort_order"]
    list_filter = ["act"]
    search_fields = ["title", "outline_version__project__title"]
    raw_id_fields = ["outline_version"]
    readonly_fields = ["id"]


@admin.register(NarrativeModelLookup)
class NarrativeModelLookupAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "sort_order"]
    list_editable = ["sort_order"]
    prepopulated_fields = {"code": ["label"]}


@admin.register(ForeshadowingTypeLookup)
class ForeshadowingTypeLookupAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "sort_order"]
    list_editable = ["sort_order"]


class TimelineEntryInline(admin.TabularInline):
    model = TimelineEntry
    extra = 0
    fields = ["entry_type", "story_date", "event_description", "node", "order"]
    readonly_fields = ["id"]


@admin.register(MasterTimeline)
class MasterTimelineAdmin(admin.ModelAdmin):
    list_display = ["project", "narrative_model", "story_time_span"]
    search_fields = ["project__title"]
    raw_id_fields = ["project"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [TimelineEntryInline]


@admin.register(ForeshadowingEntry)
class ForeshadowingEntryAdmin(admin.ModelAdmin):
    list_display = ["label", "project", "foreshadow_type", "status", "introduced_in"]
    list_filter = ["status", "foreshadow_type"]
    search_fields = ["label", "project__title"]
    raw_id_fields = ["project", "introduced_in", "resolved_in", "setup_node"]
    readonly_fields = ["id", "is_planted", "created_at", "updated_at"]


@admin.register(PlannedFlashback)
class PlannedFlashbackAdmin(admin.ModelAdmin):
    list_display = ["project", "technique", "trigger_node", "created_at"]
    list_filter = ["technique"]
    search_fields = ["project__title"]
    raw_id_fields = ["project", "trigger_node"]
    readonly_fields = ["id", "created_at"]


@admin.register(ProjectTurningPoint)
class ProjectTurningPointAdmin(admin.ModelAdmin):
    list_display = ["project", "get_label", "position_percent", "turning_point_type"]
    list_filter = ["turning_point_type"]
    search_fields = ["project__title", "label"]
    raw_id_fields = ["project", "node"]
    readonly_fields = ["id", "created_at"]


class DialogueSceneInline(admin.TabularInline):
    model = DialogueScene
    extra = 0
    fields = [
        "speaker_a_name", "speaker_b_name",
        "dialogue_outcome", "sort_order",
    ]


@admin.register(DialogueScene)
class DialogueSceneAdmin(admin.ModelAdmin):
    list_display = [
        "node", "speaker_a_name", "speaker_b_name",
        "dialogue_outcome", "sort_order",
    ]
    list_filter = ["dialogue_outcome"]
    search_fields = ["speaker_a_name", "speaker_b_name", "node__title"]
    raw_id_fields = ["node"]
    readonly_fields = ["id"]


