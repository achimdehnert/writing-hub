from django.urls import path

from . import views_creative, views_html

app_name = "ideas"

urlpatterns = [
    # Ideen-Import (Datei-Upload)
    path("", views_html.IdeaListView.as_view(), name="list"),
    path("upload/", views_html.IdeaUploadView.as_view(), name="upload"),
    path("<uuid:pk>/review/", views_html.IdeaReviewView.as_view(), name="review"),
    # Ideen-Studio / Kreativagent
    path("studio/", views_creative.CreativeDashboardView.as_view(), name="creative_dashboard"),
    path("studio/neu/", views_creative.CreativeSessionStartView.as_view(), name="creative_start"),
    path("studio/<uuid:pk>/", views_creative.CreativeSessionView.as_view(), name="creative_session"),
    path("studio/<uuid:pk>/brainstorm/", views_creative.CreativeBrainstormView.as_view(), name="creative_brainstorm"),
    path(
        "studio/<uuid:pk>/idee/<uuid:idea_pk>/verfeinern/",
        views_creative.CreativeRefineView.as_view(),
        name="creative_refine",
    ),
    path(
        "studio/<uuid:pk>/idee/<uuid:idea_pk>/bewerten/",
        views_creative.CreativeRateView.as_view(),
        name="creative_rate",
    ),
    path(
        "studio/<uuid:pk>/idee/<uuid:idea_pk>/premise/",
        views_creative.CreativePremiseView.as_view(),
        name="creative_premise",
    ),
    path(
        "studio/<uuid:pk>/projekt-anlegen/",
        views_creative.CreativeCreateProjectView.as_view(),
        name="creative_create_project",
    ),
    path("studio/<uuid:pk>/loeschen/", views_creative.CreativeSessionDeleteView.as_view(), name="creative_delete"),
]
