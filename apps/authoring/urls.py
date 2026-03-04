from django.urls import path

from . import views

app_name = "authoring"

urlpatterns = [
    path(
        "projects/<uuid:project_id>/chapters/<str:chapter_ref>/write/",
        views.chapter_write_start,
        name="chapter-write-start",
    ),
    path(
        "jobs/<uuid:job_id>/status/",
        views.chapter_write_status,
        name="chapter-write-status",
    ),
    path(
        "projects/<uuid:project_id>/chapters/<str:chapter_ref>/quality/",
        views.chapter_quality_score,
        name="chapter-quality-score",
    ),
]
