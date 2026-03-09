from django.urls import path
from . import views_html

app_name = "ideas"

urlpatterns = [
    path("", views_html.IdeaListView.as_view(), name="list"),
    path("upload/", views_html.IdeaUploadView.as_view(), name="upload"),
    path("<uuid:pk>/review/", views_html.IdeaReviewView.as_view(), name="review"),
]
