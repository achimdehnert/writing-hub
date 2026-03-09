from django.urls import path
from . import views_html

app_name = "worlds_html"

urlpatterns = [
    path("", views_html.WorldListView.as_view(), name="list"),
]
