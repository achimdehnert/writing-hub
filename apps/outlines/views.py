"""
Outlines — HTML Views

Eigenständiger Outline-Bereich: Liste, Detail, Node-Edit, Delete.
Nutzt apps.projects.models (OutlineVersion, OutlineNode).
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from apps.projects.models import OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)


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
    """Einzelnen Node per POST aktualisieren."""
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


class OutlineNodeEnrichView(LoginRequiredMixin, View):
    """
    KI-Verfeinerung eines einzelnen Outline-Nodes (Kapitel).
    Ruft LLM mit vollem Projektkontext auf und erweitert description.
    """

    def post(self, request, pk):
        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
        from apps.authoring.services.project_context_service import ProjectContextService

        node = get_object_or_404(
            OutlineNode,
            pk=pk,
            outline_version__project__owner=request.user,
        )
        project = node.outline_version.project

        try:
            ctx_svc = ProjectContextService()
            ctx = ctx_svc.get_context(str(project.pk))
            context_block = ctx.to_prompt_block()

            existing = node.description.strip() or "(noch kein Inhalt)"
            beat_name = node.title

            system_prompt = (
                "Du bist ein erfahrener Romanautor und Story-Entwickler.\n"
                "Du erweiterst kurze Kapitel-Outlines zu detaillierten Szenenplanungen.\n"
                "Antworte auf Deutsch, nur mit dem Outline-Text, keine Erklärungen."
            )
            user_prompt = (
                f"Projekt-Kontext:\n{context_block}\n\n"
                f"Kapitel {node.order}: {beat_name}\n\n"
                f"Bisheriger Inhalt:\n{existing}\n\n"
                "Erstelle ein DETAILLIERTES Kapitel-Outline mit:\n"
                "- Was passiert in diesem Kapitel (konkrete Handlung)\n"
                "- Welche Charaktere sind involviert\n"
                "- Emotionaler Bogen des Protagonisten\n"
                "- Cliffhanger / Hook am Ende\n\n"
                "2-4 Szenen, jeweils mit Ort und konkreter Beschreibung."
            )

            router = LLMRouter()
            enriched = router.completion(
                action_code="chapter_outline",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            node.description = enriched
            node.save(update_fields=["description"])
            messages.success(request, f'Kapitel „{node.title}" wurde KI-verfeinert.')

        except LLMRoutingError as exc:
            logger.warning("OutlineNodeEnrich LLMRoutingError node=%s: %s", pk, exc)
            messages.warning(request, f"KI nicht verfügbar: {exc}")
        except Exception as exc:
            logger.exception("OutlineNodeEnrich error node=%s: %s", pk, exc)
            messages.error(request, f"Fehler bei KI-Verfeinerung: {exc}")

        return redirect("outlines:detail", pk=node.outline_version.pk)
