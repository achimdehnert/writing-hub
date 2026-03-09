"""
Worlds — HTML Frontend Views
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import ProjectWorldLink


class WorldListView(LoginRequiredMixin, ListView):
    model = ProjectWorldLink
    template_name = "worlds/world_list.html"
    context_object_name = "world_links"

    def get_queryset(self):
        return (
            ProjectWorldLink.objects
            .filter(project__owner=self.request.user)
            .select_related("project")
            .order_by("project__title", "role")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total"] = self.get_queryset().count()
        return ctx
