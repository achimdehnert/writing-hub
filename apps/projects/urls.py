from django.urls import path

from . import views, views_html, views_review, views_lektorat

app_name = "projects"

urlpatterns = [
    path("", views_html.ProjectListView.as_view(), name="list"),
    path("new/", views_html.ProjectCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views_html.ProjectDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views_html.ProjectUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/write/", views_html.ChapterWriterView.as_view(), name="chapter_writer"),
    path("<uuid:pk>/outline/create/", views_html.OutlineCreateView.as_view(), name="outline_create"),
    path("<uuid:pk>/outline/generate/", views_html.OutlineGenerateView.as_view(), name="outline_generate"),
    path("node/<uuid:node_pk>/content/", views_html.ChapterContentView.as_view(), name="node_content"),
    path("node/<uuid:node_pk>/style/", views_html.ChapterNodeStyleView.as_view(), name="node_style"),
    # Review
    path("<uuid:pk>/review/", views_review.ProjectReviewView.as_view(), name="review"),
    path("<uuid:pk>/review/<uuid:node_pk>/", views_review.ProjectReviewChapterView.as_view(), name="review_chapter"),
    path("<uuid:pk>/review/<uuid:node_pk>/add/", views_review.ChapterReviewAddView.as_view(), name="review_add"),
    path("<uuid:pk>/review/<uuid:node_pk>/ai/", views_review.ChapterAIReviewView.as_view(), name="review_ai"),
    path("<uuid:pk>/review/resolve/<uuid:review_pk>/", views_review.ChapterReviewResolveView.as_view(), name="review_resolve"),
    # Redaktion / Editing
    path("<uuid:pk>/editing/", views_review.ProjectEditingView.as_view(), name="editing"),
    path("<uuid:pk>/editing/<uuid:node_pk>/", views_review.ChapterEditingView.as_view(), name="editing_chapter"),
    path("<uuid:pk>/editing/<uuid:node_pk>/ai/", views_review.ChapterAIEditingView.as_view(), name="editing_ai"),
    path("<uuid:pk>/editing/suggest/<uuid:editing_pk>/", views_review.ChapterEditingSuggestionView.as_view(), name="editing_suggest"),
    # Lektorat
    path("<uuid:pk>/lektorat/", views_lektorat.ProjectLektoratView.as_view(), name="lektorat"),
    path("<uuid:pk>/lektorat/start/", views_lektorat.LektoratSessionStartView.as_view(), name="lektorat_start"),
    path("<uuid:pk>/lektorat/<uuid:session_pk>/", views_lektorat.LektoratSessionDetailView.as_view(), name="lektorat_session"),
    path("<uuid:pk>/lektorat/issue/<uuid:issue_pk>/resolve/", views_lektorat.LektoratIssueResolveView.as_view(), name="lektorat_resolve"),
    # REST API
    path("api/", views.BookProjectListView.as_view(), name="api_list"),
    path("api/<uuid:pk>/", views.BookProjectDetailView.as_view(), name="api_detail"),
    path("api/<uuid:project_pk>/outline/", views.ProjectOutlineView.as_view(), name="outline"),
]
