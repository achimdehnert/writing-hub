from django.urls import path

from . import views

app_name = "outlines"

urlpatterns = [
    path("", views.OutlineListView.as_view(), name="list"),
    path("<uuid:pk>/", views.OutlineDetailView.as_view(), name="detail"),
    path("<uuid:pk>/delete/", views.OutlineDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/set-active/", views.OutlineSetActiveView.as_view(), name="set_active"),
    path("node/<uuid:pk>/update/", views.OutlineNodeUpdateView.as_view(), name="node_update"),
]
