"""
URL configuration for Writing Hub.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/worlds/", include("apps.worlds.urls", namespace="worlds")),
    path("api/v1/projects/", include("apps.projects.urls", namespace="projects")),
    path("api/v1/series/", include("apps.series.urls", namespace="series")),
    path("api/v1/idea-import/", include("apps.idea_import.urls", namespace="idea_import")),
    path("health/", include("apps.core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
