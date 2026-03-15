"""
URL configuration for Writing Hub.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.healthz import liveness, readiness

urlpatterns = [
    path("livez/", liveness, name="livez"),
    path("healthz/", readiness, name="healthz"),
    path("readyz/", readiness, name="readyz"),
    path("admin/", admin.site.urls),
        path("oidc/", include("mozilla_django_oidc.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.core.urls", namespace="core")),
    path("projects/", include("apps.projects.urls", namespace="projects")),
    path("outlines/", include("apps.outlines.urls", namespace="outlines")),
    path("serien/", include("apps.series.urls_html", namespace="series_html")),
    path("ideen/", include("apps.idea_import.urls_html", namespace="ideas")),
    path("welten/", include("apps.worlds.urls_html", namespace="worlds_html")),
    path("autoren/", include("apps.authors.urls", namespace="authors")),
    path("api/v1/", include("apps.api.urls", namespace="api")),
    path("api/v1/worlds/", include("apps.worlds.urls", namespace="worlds")),
    path("api/v1/series/", include("apps.series.urls", namespace="series")),
    path("api/v1/idea-import/", include("apps.idea_import.urls", namespace="idea_import")),
    path("api/v1/authoring/", include("apps.authoring.urls", namespace="authoring")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
