"""
Outlines — HTML Views

Eigenständiger Outline-Bereich: Liste, Detail/Editor, Node-Edit, Delete.
Nutzt apps.projects.models (OutlineVersion, OutlineNode, OutlineFramework).
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
    """Outline Editor — BFAgent-style mit DB-Frameworks, Listbox, Beats-Preview."""
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

        # Frameworks aus DB
        frameworks = list(
            OutlineFramework.objects
            .filter(is_active=True)
            .prefetch_related("beats")
            .order_by("order", "name")
        )
        ctx["frameworks"] = frameworks

        # Aktives Framework anhand outline.source
        active_fw = None
        for fw in frameworks:
            if fw.key == outline.source:
                active_fw = fw
                break
        ctx["active_fw"] = active_fw

        # Statistiken
        total_words = sum(n.word_count for n in nodes if n.word_count)
        written = sum(1 for n in nodes if n.word_count and n.word_count > 0)
        ctx["stat_words"] = total_words
        ctx["stat_written"] = written
        ctx["stat_total"] = len(nodes)
        target = project.target_word_count or 0
        ctx["progress_pct"] = min(100, round(total_words / target * 100)) if target > 0 else 0

        if written == len(nodes) and len(nodes) > 0:
            ctx["workflow_status"] = "fertig"
            ctx["next_step"] = "Kapitel schreiben"
        elif len(nodes) > 0:
            ctx["workflow_status"] = "entwurf"
            ctx["next_step"] = "Outline fertigstellen"
        else:
            ctx["workflow_status"] = "leer"
            ctx["next_step"] = "Framework wählen & generieren"

        return ctx


class OutlineDeleteView(LoginRequiredMixin, View):
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
        messages.success(request, f'Kapitel „{node.title}" gespeichert.')
        return redirect("outlines:detail", pk=node.outline_version.pk)


class OutlineNodeAddView(LoginRequiredMixin, View):
    def post(self, request, pk):
        outline = get_object_or_404(
            OutlineVersion, pk=pk, project__owner=request.user
        )
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
            OutlineNode,
            pk=pk,
            outline_version__project__owner=request.user,
        )
        outline_pk = node.outline_version.pk
        name = node.title
        node.delete()
        messages.success(request, f'Kapitel „{name}" gelöscht.')
        return redirect("outlines:detail", pk=outline_pk)


class OutlineNodeEnrichView(LoginRequiredMixin, View):
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
            system_prompt = (
                "Du bist ein erfahrener Romanautor und Story-Entwickler.\n"
                "Du erweiterst kurze Kapitel-Outlines zu detaillierten Szenenplanungen.\n"
                "Antworte auf Deutsch, nur mit dem Outline-Text, keine Erklärungen."
            )
            user_prompt = (
                f"Projekt-Kontext:\n{context_block}\n\n"
                f"Kapitel {node.order}: {node.title}\n\n"
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
