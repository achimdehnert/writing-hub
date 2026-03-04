from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.BookProjectListView.as_view(), name="list"),
    path("<uuid:pk>/", views.BookProjectDetailView.as_view(), name="detail"),
    path("<uuid:project_pk>/outline/", views.ProjectOutlineView.as_view(), name="outline"),
]
