from django.contrib import admin

from .models import Author, WritingStyle, WritingStyleSample


class WritingStyleInline(admin.TabularInline):
    model = WritingStyle
    extra = 0
    fields = ["name", "status", "is_active"]
    show_change_link = True


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "style_count", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "owner__username"]
    inlines = [WritingStyleInline]

    def style_count(self, obj):
        return obj.style_count
    style_count.short_description = "Stile"


class WritingStyleSampleInline(admin.TabularInline):
    model = WritingStyleSample
    extra = 0
    fields = ["situation", "text", "notes"]


@admin.register(WritingStyle)
class WritingStyleAdmin(admin.ModelAdmin):
    list_display = ["name", "author", "status", "sample_count", "is_active"]
    list_filter = ["status", "is_active"]
    search_fields = ["name", "author__name"]
    readonly_fields = ["status", "style_profile", "style_prompt", "error_message"]
    inlines = [WritingStyleSampleInline]

    def sample_count(self, obj):
        return obj.sample_count
    sample_count.short_description = "Beispiele"
