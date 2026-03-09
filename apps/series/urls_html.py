from django.urls import path

from .views import (
    SeriesCreateView,
    SeriesDeleteView,
    SeriesListView,
    SeriesUpdateView,
)

app_name = "series_html"

urlpatterns = [
    path("", SeriesListView.as_view(), name="list"),
    path("neu/", SeriesCreateView.as_view(), name="create"),
    path("<uuid:pk>/bearbeiten/", SeriesUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/loeschen/", SeriesDeleteView.as_view(), name="delete"),
]
