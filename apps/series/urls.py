from django.urls import path

from . import views

app_name = "series"

urlpatterns = [
    path("", views.BookSeriesListView.as_view(), name="list"),
    path("<uuid:pk>/", views.BookSeriesDetailView.as_view(), name="detail"),
]
