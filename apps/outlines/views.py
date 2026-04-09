"""
Outlines — HTML Views
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from apps.projects.models import OutlineFramework, OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)


class OutlineListView(LoginRequiredMixin, ListView):
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
    template_name = "outlines/outline_detail.html"
    context_object_name = "outline"

    def get_queryset(self):
        return OutlineVersion.objects.filter(
            project__owner=self.request.user
        ).select_related("project")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        outline = self.object
        project = outline.project
        nodes = list(outline.nodes.order_by("order"))

        ctx["nodes"] = nodes
        ctx["node_count"] = len(nodes)
        ctx["project"] = project
        ctx["all_versions"] = OutlineVersion.objects.filter(
            project=project
        ).order_by("-created_at")

        frameworks = list(
            OutlineFramework.objects
            .filter(is_active=True)
            .prefetch_related("beats")
            .order_by("order", "name")
        )
        ctx["frameworks"] = frameworks
        active_fw = next((f for f in frameworks if f.key == outline.source), None)
        ctx["active_fw"] = active_fw

        total_words = sum(n.word_count for n in nodes if n.word_count)
        written = sum(1 for n in nodes if n.word_count and n.word_count > 0)
        ctx["stat_words"] = total_words
        ctx["stat_written"] = written
        ctx["stat_total"] = len(nodes)
        target = project.target_word_count or 0
        ctx["progress_pct"] = min(100, round(total_words / target * 100)) if target > 0 else 0

        described = sum(1 for n in nodes if n.description and n.description.strip())

        if written == len(nodes) and len(nodes) > 0:
            ctx["workflow_status"] = "fertig"
            ctx["next_step"] = "Kapitel schreiben"
        elif described > 0 and len(nodes) > 0:
            ctx["workflow_status"] = "pruefung"
            ctx["next_step"] = "Outline prüfen & bearbeiten"
        elif len(nodes) > 0:
            ctx["workflow_status"] = "entwurf"
            ctx["next_step"] = "Outline fertigstellen"
        else:
            ctx["workflow_status"] = "leer"
            ctx["next_step"] = "Framework wählen & generieren"
        ctx["has_outline_content"] = described > 0

        return ctx


class OutlineDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        outline = get_object_or_404(OutlineVersion, pk=pk, project__owner=request.user)
        project_pk = outline.project.pk
        name = outline.name
        outline.delete()
        messages.success(request, f'Outline „{name}" gelöscht.')
        return redirect("projects:detail", pk=project_pk)


class OutlineSetActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        outline = get_object_or_404(OutlineVersion, pk=pk, project__owner=request.user)
        OutlineVersion.objects.filter(
            project=outline.project, is_active=True
        ).update(is_active=False)
        outline.is_active = True
        outline.save(update_fields=["is_active"])
        messages.success(request, f'„{outline.name}" ist jetzt die aktive Version.')
        return redirect("outlines:detail", pk=pk)


class OutlineSaveVersionView(LoginRequiredMixin, View):
    """Aktuelle Outline als neue benannte Version speichern."""

    def post(self, request, pk):
        outline = get_object_or_404(OutlineVersion, pk=pk, project__owner=request.user)
        name = request.POST.get("version_name", "").strip()
        label = request.POST.get("version_label", "").strip()
        if not name:
            name = f"{outline.name} v{outline.project.outline_versions.count() + 1}"
        new_version = outline.save_as_new_version(name=name, label=label, user=request.user)
        messages.success(request, f'Version „{new_version.name}" gespeichert.')
        return redirect("outlines:detail", pk=new_version.pk)


class OutlineNodeUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from django.template.loader import render_to_string
        from django.http import HttpResponse

        node = get_object_or_404(
            OutlineNode, pk=pk, outline_version__project__owner=request.user
        )
        node.title = request.POST.get("title", node.title).strip() or node.title
        node.description = request.POST.get("description", node.description)
        node.notes = request.POST.get("notes", node.notes)
        node.beat_type = request.POST.get("beat_type", node.beat_type)
        node.beat_phase = request.POST.get("beat_phase", node.beat_phase)
        node.act = request.POST.get("act", node.act)
        node.emotional_arc = request.POST.get("emotional_arc", node.emotional_arc)
        tw = request.POST.get("target_words", "")
        if tw:
            try:
                node.target_words = int(tw)
            except ValueError:
                pass
        node.save(update_fields=[
            "title", "description", "notes", "beat_type",
            "beat_phase", "act", "emotional_arc", "target_words",
        ])

        if request.headers.get("HX-Request"):
            html = render_to_string(
                "outlines/partials/node_row.html",
                {"node": node, "saved": True},
                request=request,
            )
            return HttpResponse(html)

        messages.success(request, f'Kapitel „{node.title}" gespeichert.')
        return redirect("outlines:detail", pk=node.outline_version.pk)


class OutlineNodeFilterView(LoginRequiredMixin, View):
    """HTMX: Filtert Kapitel-Liste nach beat_type und/oder act (Partial-Response)."""

    def get(self, request, pk):
        from django.template.loader import render_to_string
        from django.http import HttpResponse

        outline = get_object_or_404(OutlineVersion, pk=pk, project__owner=request.user)
        qs = outline.nodes.order_by("order")

        beat_type = request.GET.get("beat_type", "").strip()
        act = request.GET.get("act", "").strip()
        search = request.GET.get("q", "").strip()

        if beat_type:
            qs = qs.filter(beat_type=beat_type)
        if act:
            qs = qs.filter(act__icontains=act)
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(description__icontains=search)

        nodes = list(qs)
        html = render_to_string(
            "outlines/partials/node_list.html",
            {"nodes": nodes, "outline": outline},
            request=request,
        )
        return HttpResponse(html)


class OutlineNodeAddView(LoginRequiredMixin, View):
    def post(self, request, pk):
        outline = get_object_or_404(OutlineVersion, pk=pk, project__owner=request.user)
        max_order = outline.nodes.count()
        title = request.POST.get("title", "").strip() or f"Kapitel {max_order + 1}"
        OutlineNode.objects.create(
            outline_version=outline,
            title=title,
            beat_type="chapter",
            order=max_order + 1,
        )
        messages.success(request, f'Kapitel „{title}" hinzugefügt.')
        return redirect("outlines:detail", pk=pk)


class OutlineNodeDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        node = get_object_or_404(
            OutlineNode, pk=pk, outline_version__project__owner=request.user
        )
        outline_pk = node.outline_version.pk
        name = node.title
        node.delete()
        messages.success(request, f'Kapitel „{name}" gelöscht.')
        return redirect("outlines:detail", pk=outline_pk)


class OutlineGenerateFullView(LoginRequiredMixin, View):
    """
    Vollständige 2-Schritt-Generierung:
    Schritt 1: Kapitel-Struktur (Beat-Phase, Akt, Zielwörter)
    Schritt 2: Pro Kapitel detailliertes Outline (description, emotional_arc)
    """

    def post(self, request, pk):
        from apps.outlines.services import OutlineGenerationService

        outline = get_object_or_404(OutlineVersion, pk=pk, project__owner=request.user)
        detail_level = request.POST.get("detail_level", "full")

        svc = OutlineGenerationService()
        result = svc.generate_full(outline, detail_level=detail_level)

        if result["total"] == 0:
            messages.warning(request, "Keine Kapitel vorhanden. Zuerst Outline anlegen.")
        else:
            messages.success(
                request,
                f'Outline vollständig generiert: {result["updated"]}/{result["total"]} Kapitel mit Details.'
            )
        return redirect("outlines:detail", pk=pk)


class OutlineNodeEnrichView(LoginRequiredMixin, View):
    """KI-Verfeinerung eines einzelnen Outline-Nodes."""

    def post(self, request, pk):
        from apps.outlines.services import OutlineGenerationService

        node = get_object_or_404(
            OutlineNode, pk=pk, outline_version__project__owner=request.user
        )

        svc = OutlineGenerationService()
        result = svc.enrich_node(node)

        if result["success"]:
            messages.success(request, f'Kapitel „{node.title}" KI-verfeinert.')
        else:
            messages.warning(request, result["error"])

        return redirect("outlines:detail", pk=node.outline_version.pk)
