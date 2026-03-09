from django.urls import path
from . import views_html

app_name = "ideas"

urlpatterns = [
    path("", views_html.IdeaListView.as_view(), name="list"),
]
