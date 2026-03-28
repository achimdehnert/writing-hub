from django.urls import path

from . import (
    views,
    views_export,
    views_health,
    views_html,
    views_import,
    views_knowledge,
    views_lektorat,
    views_manuscript,
    views_publishing,
    views_review,
    views_versions,
)

app_name = "projects"

urlpatterns = [
    path("", views_html.ProjectListView.as_view(), name="list"),
    path("new/", views_html.ProjectCreateView.as_view(), name="create"),
    path("import/", views_import.ProjectImportView.as_view(), name="import"),
    path("<uuid:pk>/", views_html.ProjectDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views_html.ProjectUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/write/", views_html.ChapterWriterView.as_view(), name="chapter_writer"),
    path("<uuid:pk>/outline/create/", views_html.OutlineCreateView.as_view(), name="outline_create"),
    path("<uuid:pk>/outline/generate/", views_html.OutlineGenerateView.as_view(), name="outline_generate"),
    path("node/<uuid:node_pk>/content/", views_html.ChapterContentView.as_view(), name="node_content"),
    path("node/<uuid:node_pk>/style/", views_html.ChapterNodeStyleView.as_view(), name="node_style"),
    # Manuskript
    path("<uuid:pk>/manuscript/", views_manuscript.ProjectManuscriptView.as_view(), name="manuscript"),
    # Publishing
    path("<uuid:pk>/publishing/", views_publishing.ProjectPublishingView.as_view(), name="publishing"),
    path("<uuid:pk>/publishing/keywords-ai/", views_publishing.PublishingKeywordsAIView.as_view(), name="publishing_keywords_ai"),
    # Export
    path("<uuid:pk>/export/", views_export.ProjectExportView.as_view(), name="export"),
    # Versionen / Snapshots
    path("<uuid:pk>/versions/", views_versions.ProjectVersionsView.as_view(), name="versions"),
    path("<uuid:pk>/versions/create/", views_versions.SnapshotCreateView.as_view(), name="snapshot_create"),
    path("<uuid:pk>/versions/<uuid:snapshot_pk>/", views_versions.SnapshotDetailView.as_view(), name="snapshot_detail"),
    path("<uuid:pk>/versions/<uuid:snapshot_pk>/delete/", views_versions.SnapshotDeleteView.as_view(), name="snapshot_delete"),
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
    # Health-Score (ADR-157)
    path("<uuid:pk>/health/", views_health.ProjectHealthView.as_view(), name="health"),
    path("<uuid:pk>/health/partial/", views_health.ProjectHealthPartialView.as_view(), name="health_partial"),
    # Wissens-Infrastruktur: Recherche + Beta-Leser (ADR-160)
    path("<uuid:pk>/research/", views_knowledge.ResearchDashboardView.as_view(), name="research_dashboard"),
    path("<uuid:pk>/beta/", views_knowledge.BetaReaderDashboardView.as_view(), name="beta_dashboard"),
    path("<uuid:pk>/beta/<uuid:session_pk>/", views_knowledge.BetaReaderSessionDetailView.as_view(), name="beta_session"),
    # Pitch-Paket / Publikationsvorbereitung (ADR-159)
    path("<uuid:pk>/pitch/", views_publishing.PitchDashboardView.as_view(), name="pitch_dashboard"),
    path("<uuid:pk>/pitch/<str:pitch_type>/generate/", views_publishing.GeneratePitchView.as_view(), name="pitch_generate"),
    # Drama-Dashboard (ADR-154)
    path("<uuid:pk>/drama/", views_html.DramaDashboardView.as_view(), name="drama_dashboard"),
    path("node/<uuid:node_pk>/drama-update/", views_html.DramaNodeUpdateView.as_view(), name="drama_node_update"),
    path("<uuid:pk>/drama/turning-point/add/", views_html.DramaTurningPointAddView.as_view(), name="drama_turning_point_add"),
    # REST API
    path("api/", views.BookProjectListView.as_view(), name="api_list"),
    path("api/<uuid:pk>/", views.BookProjectDetailView.as_view(), name="api_detail"),
    path("api/<uuid:project_pk>/outline/", views.ProjectOutlineView.as_view(), name="outline"),
]
