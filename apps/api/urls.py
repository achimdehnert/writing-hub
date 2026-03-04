from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("health/", views.HealthApiView.as_view(), name="health"),
    path("worlds/", views.WorldsApiView.as_view(), name="worlds"),
    path("worlds/<uuid:world_id>/characters/", views.WorldCharactersApiView.as_view(), name="world-characters"),
    path("projects/<uuid:project_id>/outline/", views.ProjectOutlineApiView.as_view(), name="project-outline"),
    path("idea-import/", views.IdeaImportApiView.as_view(), name="idea-import"),
]
