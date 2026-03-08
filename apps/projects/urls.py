from django.urls import path

from . import views, views_html

app_name = "projects"

urlpatterns = [
    # HTML Frontend
    path("", views_html.ProjectListView.as_view(), name="list"),
    path("new/", views_html.ProjectCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views_html.ProjectDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views_html.ProjectUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/write/", views_html.ChapterWriterView.as_view(), name="chapter_writer"),
    path("<uuid:pk>/outline/create/", views_html.OutlineCreateView.as_view(), name="outline_create"),
    path("<uuid:pk>/outline/generate/", views_html.OutlineGenerateView.as_view(), name="outline_generate"),
    # REST API
    path("api/", views.BookProjectListView.as_view(), name="api_list"),
    path("api/<uuid:pk>/", views.BookProjectDetailView.as_view(), name="api_detail"),
    path("api/<uuid:project_pk>/outline/", views.ProjectOutlineView.as_view(), name="outline"),
]
