"""
Outlines — HTML Views
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from promptfw.parsing import extract_json, extract_json_list

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
        import json
        import re

        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
        from apps.authoring.services.project_context_service import ProjectContextService

        outline = get_object_or_404(OutlineVersion, pk=pk, project__owner=request.user)
        project = outline.project
        detail_level = request.POST.get("detail_level", "full")

        try:
            ctx_svc = ProjectContextService()
            proj_ctx = ctx_svc.get_context(str(project.pk))
            context_block = proj_ctx.to_prompt_block()
        except Exception:
            context_block = f"Projekt: {project.title}\nGenre: {project.genre}"

        nodes = list(outline.nodes.order_by("order"))
        if not nodes:
            messages.warning(request, "Keine Kapitel vorhanden. Zuerst Outline anlegen.")
            return redirect("outlines:detail", pk=pk)

        router = LLMRouter()
        fw_name = outline.source
        total = len(nodes)
        updated = 0

        # Schritt 1: Struktur-Pass
        try:
            target_per_chapter = (
                round(project.target_word_count / total)
                if project.target_word_count else 3000
            )
            from apps.core.prompt_utils import render_prompt
            chapters_list = [{"order": n.order, "title": n.title} for n in nodes]
            prompt_msgs = render_prompt(
                "outlines/structure_pass",
                context_block=context_block,
                framework=fw_name,
                chapters=chapters_list,
                total=total,
                target_word_count=project.target_word_count or total * target_per_chapter,
            )
            if not prompt_msgs:
                prompt_msgs = [
                    {"role": "system", "content": "Du bist ein Story-Struktur-Experte. Antworte nur mit JSON."},
                    {"role": "user", "content": f"Struktur für {total} Kapitel erstellen."},
                ]
            raw = router.completion(
                action_code="chapter_outline",
                messages=prompt_msgs,
            )
            structure = extract_json_list(raw)
            if structure:
                struct_map = {item["order"]: item for item in structure}
                for node in nodes:
                    s = struct_map.get(node.order, {})
                    node.beat_phase = s.get("beat_phase", node.beat_phase)
                    node.act = s.get("act", node.act)
                    node.target_words = s.get("target_words") or node.target_words
                    node.save(update_fields=["beat_phase", "act", "target_words"])
        except (LLMRoutingError, Exception) as exc:
            logger.warning("OutlineGenerateFull Step1 error: %s", exc)

        # Schritt 2: Detail-Pass
        if detail_level in ("full", "detail"):
            for node in nodes:
                try:
                    prompt_msgs = render_prompt(
                        "outlines/detail_pass",
                        context_block=context_block,
                        beat_phase=node.beat_phase or "",
                        act=node.act or "",
                        order=node.order,
                        title=node.title,
                        target_words=node.target_words or 3000,
                        description=node.description or "(leer)",
                    )
                    if not prompt_msgs:
                        prompt_msgs = [
                            {"role": "system", "content": "Du bist ein Romanautor. Antworte nur mit JSON."},
                            {"role": "user", "content": f"Detail für Kapitel {node.order}: {node.title}"},
                        ]
                    raw = router.completion(
                        action_code="chapter_outline",
                        messages=prompt_msgs,
                    )
                    data = extract_json(raw)
                    if data:
                        node.description = data.get("description", raw)
                        node.emotional_arc = data.get("emotional_arc", "")
                    else:
                        node.description = raw
                    node.save(update_fields=["description", "emotional_arc"])
                    updated += 1
                except (LLMRoutingError, Exception) as exc:
                    logger.warning("OutlineGenerateFull Step2 node=%s: %s", node.order, exc)
                    continue

        messages.success(
            request,
            f'Outline vollständig generiert: {updated}/{total} Kapitel mit Details.'
        )
        return redirect("outlines:detail", pk=pk)


class OutlineNodeEnrichView(LoginRequiredMixin, View):
    """KI-Verfeinerung eines einzelnen Outline-Nodes."""

    def post(self, request, pk):
        import json
        import re

        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
        from apps.authoring.services.project_context_service import ProjectContextService

        node = get_object_or_404(
            OutlineNode, pk=pk, outline_version__project__owner=request.user
        )
        project = node.outline_version.project

        try:
            ctx_svc = ProjectContextService()
            ctx = ctx_svc.get_context(str(project.pk))
            context_block = ctx.to_prompt_block()
            existing = node.description.strip() or "(noch kein Inhalt)"
            from apps.core.prompt_utils import render_prompt
            prompt_msgs = render_prompt(
                "outlines/enrich_node",
                context_block=context_block,
                beat_phase=node.beat_phase or "",
                act=node.act or "",
                order=node.order,
                title=node.title,
                target_words=node.target_words or 3000,
                description=existing,
            )
            if not prompt_msgs:
                prompt_msgs = [
                    {"role": "system", "content": "Du bist ein Romanautor. Antworte als JSON."},
                    {"role": "user", "content": f"Erweitere Kapitel {node.order}: {node.title}"},
                ]
            router = LLMRouter()
            raw = router.completion(
                action_code="chapter_outline",
                messages=prompt_msgs,
            )
            data = extract_json(raw)
            if data:
                node.description = data.get("description", raw)
                node.emotional_arc = data.get("emotional_arc", node.emotional_arc)
            else:
                node.description = raw
            node.save(update_fields=["description", "emotional_arc"])
            messages.success(request, f'Kapitel „{node.title}" KI-verfeinert.')
        except LLMRoutingError as exc:
            logger.warning("OutlineNodeEnrich LLMRoutingError node=%s: %s", pk, exc)
            messages.warning(request, f"KI nicht verfügbar: {exc}")
        except Exception as exc:
            logger.exception("OutlineNodeEnrich error node=%s: %s", pk, exc)
            messages.error(request, f"Fehler: {exc}")

        return redirect("outlines:detail", pk=node.outline_version.pk)
