from django.urls import path

from . import views

app_name = "authoring"

urlpatterns = [
    # Chapter Write Pipeline
    path(
        "projects/<uuid:project_id>/chapters/<str:chapter_ref>/write/",
        views.chapter_write_start.as_view(),
        name="chapter-write-start",
    ),
    path(
        "projects/<uuid:project_id>/chapters/<str:chapter_ref>/refine/",
        views.chapter_refine_start.as_view(),
        name="chapter-refine-start",
    ),
    path(
        "jobs/<uuid:job_id>/status/",
        views.chapter_write_status.as_view(),
        name="chapter-write-status",
    ),
    path(
        "projects/<uuid:project_id>/chapters/<str:chapter_ref>/quality/",
        views.chapter_quality_score.as_view(),
        name="chapter-quality-score",
    ),
    # Outline
    path(
        "projects/<uuid:project_id>/outline/generate/",
        views.OutlineGenerateView.as_view(),
        name="outline-generate",
    ),
    path(
        "projects/<uuid:project_id>/outline/beat/<str:beat_id>/expand/",
        views.OutlineBeatExpandView.as_view(),
        name="outline-beat-expand",
    ),
    # Idea Import
    path(
        "ideas/generate/",
        views.IdeaGenerateView.as_view(),
        name="idea-generate",
    ),
    path(
        "ideas/<uuid:idea_id>/to-premise/",
        views.IdeaToPremiseView.as_view(),
        name="idea-to-premise",
    ),
]
