from django.urls import path

from . import views

app_name = "authors"

urlpatterns = [
    path("", views.AuthorListView.as_view(), name="list"),
    path("neu/", views.AuthorCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.AuthorDetailView.as_view(), name="detail"),
    path("<uuid:pk>/bearbeiten/", views.AuthorUpdateView.as_view(), name="update"),
    path("<uuid:pk>/loeschen/", views.AuthorDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/stil/neu/", views.WritingStyleCreateView.as_view(), name="style_create"),
    path("<uuid:pk>/stil/import/", views.WritingStyleImportView.as_view(), name="style_import"),
    path("stil/<uuid:pk>/", views.WritingStyleDetailView.as_view(), name="style_detail"),
    path("stil/<uuid:pk>/bearbeiten/", views.WritingStyleUpdateView.as_view(), name="style_update"),
    path("stil/<uuid:pk>/analysieren/", views.WritingStyleAnalyzeView.as_view(), name="style_analyze"),
    path("stil/<uuid:pk>/status/", views.WritingStyleStatusView.as_view(), name="style_status"),
    path("stil/<uuid:pk>/regeln-extrahieren/", views.WritingStyleExtractRulesView.as_view(), name="style_extract_rules"),
    path("stil/<uuid:pk>/beispiele/", views.WritingStyleSamplesView.as_view(), name="style_samples"),
    path("stil/<uuid:pk>/beispiel/<str:situation>/bearbeiten/", views.SampleUpdateView.as_view(), name="sample_update"),
    path("stil/<uuid:pk>/loeschen/", views.WritingStyleDeleteView.as_view(), name="style_delete"),
    path("stil/<uuid:pk>/patch/", views.WritingStylePatchView.as_view(), name="style_patch"),
]
