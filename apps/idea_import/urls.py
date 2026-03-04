from django.urls import path

from . import views

app_name = "idea_import"

urlpatterns = [
    path("", views.IdeaImportDraftListView.as_view(), name="list"),
    path("<uuid:pk>/", views.IdeaImportDraftDetailView.as_view(), name="detail"),
    path("<uuid:pk>/commit/", views.IdeaImportCommitView.as_view(), name="commit"),
    path("<uuid:pk>/discard/", views.IdeaImportDiscardView.as_view(), name="discard"),
]
