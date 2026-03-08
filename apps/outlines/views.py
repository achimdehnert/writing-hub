"""
Outlines — HTML Views

Eigenständiger Outline-Bereich: Liste, Detail, Node-Edit, Delete.
Nutzt apps.projects.models (OutlineVersion, OutlineNode).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from apps.projects.models import OutlineNode, OutlineVersion


class OutlineListView(LoginRequiredMixin, ListView):
    """Alle Outlines des eingeloggten Users über alle Projekte."""
    template_name = "outlines/outline_list.html"
    context_object_name = "outlines"
    paginate_by = 20

    def get_queryset(self):
        return (
            OutlineVersion.objects
            .filter(project__owner=self.request.user)
            .select_related("project")
            .order_by("-created_at")
        )


class OutlineDetailView(LoginRequiredMixin, DetailView):
    """Outline mit allen Nodes anzeigen."""
    template_name = "outlines/outline_detail.html"
    context_object_name = "outline"

    def get_queryset(self):
        return OutlineVersion.objects.filter(project__owner=self.request.user).select_related("project")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nodes"] = self.object.nodes.order_by("order")
        ctx["node_count"] = ctx["nodes"].count()
        ctx["project"] = self.object.project
        return ctx


class OutlineDeleteView(LoginRequiredMixin, View):
    """Outline-Version löschen und zurück zur Projektdetailseite."""
    def post(self, request, pk):
        outline = get_object_or_404(
            OutlineVersion, pk=pk, project__owner=request.user
        )
        project_pk = outline.project.pk
        name = outline.name
        outline.delete()
        messages.success(request, f'Outline „{name}" gelöscht.')
        return redirect("projects:detail", pk=project_pk)


class OutlineSetActiveView(LoginRequiredMixin, View):
    """Outline als aktive Version markieren."""
    def post(self, request, pk):
        outline = get_object_or_404(
            OutlineVersion, pk=pk, project__owner=request.user
        )
        OutlineVersion.objects.filter(
            project=outline.project, is_active=True
        ).update(is_active=False)
        outline.is_active = True
        outline.save(update_fields=["is_active"])
        messages.success(request, f'„{outline.name}" ist jetzt die aktive Version.')
        return redirect("outlines:detail", pk=pk)


class OutlineNodeUpdateView(LoginRequiredMixin, View):
    """Einzelnen Node per POST aktualisieren (HTMX-ready)."""
    def post(self, request, pk):
        node = get_object_or_404(
            OutlineNode,
            pk=pk,
            outline_version__project__owner=request.user,
        )
        node.title = request.POST.get("title", node.title).strip() or node.title
        node.description = request.POST.get("description", node.description)
        node.notes = request.POST.get("notes", node.notes)
        node.beat_type = request.POST.get("beat_type", node.beat_type)
        node.save(update_fields=["title", "description", "notes", "beat_type"])
        return redirect("outlines:detail", pk=node.outline_version.pk)
