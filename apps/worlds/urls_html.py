from django.urls import path

from . import views_html

app_name = "worlds_html"

urlpatterns = [
    path("", views_html.WorldListView.as_view(), name="list"),
    path("<uuid:pk>/", views_html.ProjectWorldDetailView.as_view(), name="detail"),
    path("generate/", views_html.WorldGenerateView.as_view(), name="generate"),
    path("<uuid:pk>/characters/generate/", views_html.WorldCharacterGenerateView.as_view(), name="characters_generate"),
    path("<uuid:pk>/characters/create/", views_html.CharacterCreateView.as_view(), name="character_create"),
    path("<uuid:pk>/characters/link/", views_html.CharacterLinkView.as_view(), name="character_link"),
    path("<uuid:pk>/locations/generate/", views_html.WorldLocationGenerateView.as_view(), name="locations_generate"),
    path("<uuid:pk>/outline-extract/", views_html.OutlineExtractView.as_view(), name="outline_extract"),
    path("characters/<uuid:pk>/", views_html.CharacterDetailView.as_view(), name="character_detail"),
    path("characters/<uuid:pk>/refine/", views_html.CharacterRefineView.as_view(), name="character_refine"),
    path("characters/<uuid:pk>/relationships/add/", views_html.RelationshipAddView.as_view(), name="relationship_add"),
    path("locations/<uuid:pk>/", views_html.LocationDetailView.as_view(), name="location_detail"),
    path("locations/<uuid:pk>/refine/", views_html.LocationRefineView.as_view(), name="location_refine"),
    path("relationships/<uuid:pk>/delete/", views_html.RelationshipDeleteView.as_view(), name="relationship_delete"),
]
