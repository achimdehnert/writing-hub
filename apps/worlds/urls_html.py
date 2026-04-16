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
]
