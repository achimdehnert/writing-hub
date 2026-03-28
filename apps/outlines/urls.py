from django.urls import path

from . import views

app_name = "outlines"

urlpatterns = [
    path("", views.OutlineListView.as_view(), name="list"),
    path("<uuid:pk>/", views.OutlineDetailView.as_view(), name="detail"),
    path("<uuid:pk>/delete/", views.OutlineDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/set-active/", views.OutlineSetActiveView.as_view(), name="set_active"),
    path("<uuid:pk>/save-version/", views.OutlineSaveVersionView.as_view(), name="save_version"),
    path("<uuid:pk>/generate-full/", views.OutlineGenerateFullView.as_view(), name="generate_full"),
    path("<uuid:pk>/node/add/", views.OutlineNodeAddView.as_view(), name="node_add"),
    path("node/<uuid:pk>/update/", views.OutlineNodeUpdateView.as_view(), name="node_update"),
    path("node/<uuid:pk>/delete/", views.OutlineNodeDeleteView.as_view(), name="node_delete"),
    path("node/<uuid:pk>/enrich/", views.OutlineNodeEnrichView.as_view(), name="node_enrich"),
    path("<uuid:pk>/filter/", views.OutlineNodeFilterView.as_view(), name="node_filter"),
]
