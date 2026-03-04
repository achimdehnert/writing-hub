from django.urls import path

from . import views

app_name = "worlds"

urlpatterns = [
    path("", views.WorldListView.as_view(), name="list"),
    path("<uuid:pk>/", views.WorldDetailView.as_view(), name="detail"),
    path("<uuid:world_pk>/characters/", views.WorldCharacterListView.as_view(), name="characters"),
]
