"""
URL configuration for Writing Hub.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # REST API für bfagent-Integration (ADR-083 Phase 3)
    path("api/v1/", include("apps.api.urls", namespace="api")),
    # Domain-spezifische Endpunkte
    path("api/v1/worlds/", include("apps.worlds.urls", namespace="worlds")),
    path("api/v1/projects/", include("apps.projects.urls", namespace="projects")),
    path("api/v1/series/", include("apps.series.urls", namespace="series")),
    path("api/v1/idea-import/", include("apps.idea_import.urls", namespace="idea_import")),
    # Authoring: ChapterWriter + QualityGate (ADR-083 Phase 3)
    path("api/v1/authoring/", include("apps.authoring.urls", namespace="authoring")),
    # Health
    path("health/", include("apps.core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
