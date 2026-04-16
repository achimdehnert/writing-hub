from django.urls import path

from . import views

app_name = "worlds"

urlpatterns = [
    path("", views.WorldListView.as_view(), name="list"),
    path("<uuid:pk>/", views.WorldDetailView.as_view(), name="detail"),
    path("<uuid:world_pk>/characters/", views.WorldCharacterListView.as_view(), name="characters"),
    path("<uuid:world_pk>/locations/", views.WorldLocationListView.as_view(), name="locations"),
    path("<uuid:pk>/outline-extract/", views.OutlineExtractView.as_view(), name="outline_extract"),
    path("characters/<uuid:pk>/refine/", views.CharacterRefineView.as_view(), name="character_refine"),
    path("locations/<uuid:pk>/refine/", views.LocationRefineView.as_view(), name="location_refine"),
]
