"""
Projects — HTML Frontend Views (ADR-083)
"""
import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView

from apps.series.models import BookSeries
from .models import (
    AudienceLookup, AuthorStyleLookup, BookProject,
    ContentTypeLookup, GenreLookup, OutlineFramework,
    OutlineNode, OutlineVersion,
)

logger = logging.getLogger(__name__)

# Fallback-Beats wenn DB leer (nur für KI-Generierung)
FW_BEATS_FALLBACK = {
    "three_act": 6, "save_the_cat": 15, "heros_journey": 12,
    "five_act": 5, "dan_harmon": 8, "blank": 0,
}

FW_LABELS_FALLBACK = {
    "three_act": "Drei-Akt-Struktur",
    "save_the_cat": "Save the Cat",
    "heros_journey": "Heldenreise",
    "five_act": "Fünf-Akt-Struktur",
    "dan_harmon": "Dan Harmon Story Circle",
    "blank": "Leere Kapitel",
}

DEFAULT_CONTENT_TYPES = [
    {"slug": "roman", "name": "Roman", "icon": "bi-book",
     "subtitle": "Erzählung mit Charakteren & Weltenbau",
     "workflow_hint": "Konzept → Charaktere → Outline → Schreiben"},
    {"slug": "sachbuch", "name": "Sachbuch", "icon": "bi-journal-text",
     "subtitle": "Ratgeber, Biographie, How-To oder Sachtext",
     "workflow_hint": "Thema → Struktur → Kapitel → Schreiben"},
    {"slug": "essay", "name": "Essay", "icon": "bi-pencil-square",
     "subtitle": "Argumentativer Text zu einem Thema",
     "workflow_hint": "These → Recherche → Gliederung → Schreiben"},
]


def _get_frameworks():
    """Frameworks aus DB laden; Fallback auf leere Liste wenn DB leer."""
    return list(
        OutlineFramework.objects
        .filter(is_active=True)
        .prefetch_related("beats")
        .order_by("order", "name")
    )


def _fw_label(fw_key, frameworks):
    for fw in frameworks:
        if fw.key == fw_key:
            return fw.name
    return FW_LABELS_FALLBACK.get(fw_key, fw_key)


def _fw_beat_count(fw_key, frameworks):
    for fw in frameworks:
        if fw.key == fw_key:
            return fw.beat_count
    return FW_BEATS_FALLBACK.get(fw_key, 12)


class ProjectListView(LoginRequiredMixin, ListView):
    model = BookProject
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        qs = BookProject.objects.filter(
            owner=self.request.user, is_active=True
        ).select_related("genre_lookup", "content_type_lookup", "series")
        series_id = self.request.GET.get("serie")
        genre_id = self.request.GET.get("genre")
        ct_id = self.request.GET.get("typ")
        q = self.request.GET.get("q", "").strip()
        if series_id == "none":
            qs = qs.filter(series__isnull=True)
        elif series_id:
            qs = qs.filter(series_id=series_id)
        if genre_id:
            qs = qs.filter(genre_lookup_id=genre_id)
        if ct_id:
            qs = qs.filter(content_type_lookup_id=ct_id)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["series_options"] = BookSeries.objects.filter(
            owner=self.request.user
        ).order_by("title")
        ctx["genre_options"] = GenreLookup.objects.all().order_by("order", "name")
        ctx["ct_options"] = ContentTypeLookup.objects.all().order_by("order", "name")
        ctx["filter_serie"] = self.request.GET.get("serie", "")
        ctx["filter_genre"] = self.request.GET.get("genre", "")
        ctx["filter_typ"] = self.request.GET.get("typ", "")
        ctx["filter_q"] = self.request.GET.get("q", "")
        return ctx


class ProjectCreateView(LoginRequiredMixin, View):
    template_name = "projects/project_form.html"

    def _context(self, post_data=None):
        return {
            "content_types": ContentTypeLookup.objects.all().order_by("order", "name"),
            "default_content_types": DEFAULT_CONTENT_TYPES,
            "genres": GenreLookup.objects.all().order_by("order", "name"),
            "audiences": AudienceLookup.objects.all().order_by("order", "name"),
            "author_styles": AuthorStyleLookup.objects.filter(
                is_active=True
            ).order_by("order", "name"),
            "series_options": BookSeries.objects.filter(
                owner=self.request.user
            ).order_by("title"),
            "post": post_data or {},
            "is_edit": False,
        }

    def get(self, request):
        return render(request, self.template_name, self._context())

    def post(self, request):
        title = request.POST.get("title", "").strip()
        if not title:
            ctx = self._context(request.POST)
            ctx["error"] = "Bitte einen Arbeitstitel eingeben."
            return render(request, self.template_name, ctx)
        ct_id = request.POST.get("content_type_lookup") or None
        genre_id = request.POST.get("genre_lookup") or None
        audience_id = request.POST.get("audience_lookup") or None
        author_style_id = request.POST.get("author_style") or None
        series_id = request.POST.get("series") or None
        target_word_count = request.POST.get("target_word_count") or None
        if target_word_count:
            try:
                target_word_count = int(target_word_count)
            except ValueError:
                target_word_count = None
        project = BookProject.objects.create(
            owner=request.user,
            title=title,
            description=request.POST.get("description", ""),
            content_type_lookup_id=ct_id,
            genre_lookup_id=genre_id,
            audience_lookup_id=audience_id,
            author_style_id=author_style_id,
            series_id=series_id,
            target_word_count=target_word_count,
        )
        messages.success(request, f'Projekt „{project.title}“ angelegt.')
        return redirect("projects:detail", pk=project.pk)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object

        outlines = OutlineVersion.objects.filter(project=project).order_by("-created_at")
        ctx["outlines"] = outlines
        selected_id = self.request.GET.get("outline")
        if selected_id:
            try:
                selected = outlines.get(pk=selected_id)
            except OutlineVersion.DoesNotExist:
                selected = outlines.filter(is_active=True).first() or outlines.first()
        else:
            selected = outlines.filter(is_active=True).first() or outlines.first()
        ctx["selected_outline"] = selected
        ctx["outline_nodes"] = selected.nodes.order_by("order") if selected else []

        # Framework aus DB
        frameworks = _get_frameworks()
        ctx["frameworks"] = frameworks
        active_fw_key = selected.source if selected else "three_act"
        ctx["selected_outline_framework"] = active_fw_key
        ctx["selected_fw_beat_count"] = _fw_beat_count(active_fw_key, frameworks)

        from apps.idea_import.models import IdeaImportDraft
        ctx["idea_drafts"] = IdeaImportDraft.objects.filter(
            project=project
        ).exclude(status=IdeaImportDraft.Status.DISCARDED).order_by("-created_at")[:10]

        from apps.worlds.models import ProjectWorldLink, ProjectCharacterLink
        ctx["world_links"] = ProjectWorldLink.objects.filter(project=project)
        characters = ProjectCharacterLink.objects.filter(project=project).select_related()
        ctx["characters"] = characters
        ctx["character_count"] = characters.count()

        all_nodes = OutlineNode.objects.filter(
            outline_version__project=project,
            outline_version__is_active=True,
        )
        total_words = sum(n.word_count for n in all_nodes if n.word_count)
        written_chapters = all_nodes.filter(word_count__gt=0).count()
        total_chapters = all_nodes.count()
        ctx["stat_words"] = total_words
        ctx["stat_chapters_written"] = written_chapters
        ctx["stat_chapters_total"] = total_chapters
        ctx["stat_characters"] = characters.count()
        ctx["stat_worlds"] = ctx["world_links"].count()
        target = project.target_word_count or 0
        ctx["progress_pct"] = min(100, round(total_words / target * 100)) if target > 0 else 0
        ctx["chapter_progress_pct"] = (
            min(100, round(written_chapters / total_chapters * 100)) if total_chapters > 0 else 0
        )
        return ctx


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = BookProject
    template_name = "projects/project_form.html"
    fields = [
        "title", "description", "series",
        "content_type_lookup", "genre_lookup", "audience_lookup",
        "author_style", "target_word_count",
    ]

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["series"].queryset = BookSeries.objects.filter(owner=self.request.user)
        form.fields["series"].empty_label = "— keine Serie —"
        form.fields["content_type_lookup"].empty_label = "— bitte wählen —"
        form.fields["genre_lookup"].empty_label = "— bitte wählen —"
        form.fields["audience_lookup"].empty_label = "— bitte wählen —"
        form.fields["author_style"].empty_label = "— kein Stil —"
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["author_styles"] = AuthorStyleLookup.objects.filter(is_active=True).order_by("order", "name")
        ctx["audiences"] = AudienceLookup.objects.all().order_by("order", "name")
        return ctx

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})


class OutlineCreateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        return redirect("projects:detail", pk=pk)

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip()
        notes = request.POST.get("notes", "")
        chapter_count = int(request.POST.get("chapter_count", 0) or 0)
        framework_key = request.POST.get("framework_template", "").strip()
        logger.info("OutlineCreateView.post pk=%s fw=%s user=%s", pk, framework_key, request.user)

        if not framework_key:
            messages.warning(request, "Bitte ein Framework auswählen.")
            return redirect("projects:detail", pk=pk)

        # Framework aus DB laden
        frameworks = _get_frameworks()
        fw_obj = next((f for f in frameworks if f.key == framework_key), None)
        fw_label = fw_obj.name if fw_obj else FW_LABELS_FALLBACK.get(framework_key, framework_key)
        if not name:
            name = fw_label

        try:
            OutlineVersion.objects.filter(project=project, is_active=True).update(is_active=False)
            version = OutlineVersion.objects.create(
                project=project,
                created_by=request.user,
                name=name,
                source=framework_key,
                notes=notes,
                is_active=True,
            )
            beats = list(fw_obj.beats.order_by("order")) if fw_obj else []
            if beats:
                OutlineNode.objects.bulk_create([
                    OutlineNode(
                        outline_version=version,
                        title=b.name,
                        beat_type="chapter",
                        order=b.order,
                    )
                    for b in beats
                ])
                messages.success(request, f'Outline „{name}" mit {len(beats)} Beats angelegt.')
            elif chapter_count > 0:
                OutlineNode.objects.bulk_create([
                    OutlineNode(
                        outline_version=version,
                        title=f"Kapitel {i + 1}",
                        beat_type="chapter",
                        order=i + 1,
                    )
                    for i in range(min(chapter_count, 50))
                ])
                messages.success(request, f'Outline „{name}" mit {chapter_count} leeren Kapiteln angelegt.')
            else:
                messages.success(request, f'Outline „{name}" angelegt.')
            url = reverse("projects:detail", kwargs={"pk": pk}) + f"?outline={version.pk}"
            return redirect(url)
        except Exception as exc:
            logger.exception("OutlineCreateView error pk=%s: %s", pk, exc)
            messages.error(request, f"Fehler beim Anlegen: {exc}")
        return redirect("projects:detail", pk=pk)


class OutlineGenerateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        return redirect("projects:detail", pk=pk)

    def post(self, request, pk):
        from apps.authoring.services.outline_service import OutlineGeneratorService
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        framework = request.POST.get("framework", "three_act").strip()
        chapter_count = int(request.POST.get("chapter_count", 12) or 12)
        logger.info("OutlineGenerateView.post pk=%s fw=%s user=%s", pk, framework, request.user)
        try:
            svc = OutlineGeneratorService()
            result = svc.generate_outline(
                project_id=str(project.pk),
                framework=framework,
                chapter_count=chapter_count,
            )
            if result.success and result.nodes:
                OutlineVersion.objects.filter(project=project, is_active=True).update(is_active=False)
                frameworks = _get_frameworks()
                fw_label = _fw_label(framework, frameworks)
                version_id = svc.save_outline(
                    project_id=str(project.pk),
                    nodes=result.nodes,
                    name=f"KI: {fw_label}",
                    framework=framework,
                    user=request.user,
                )
                messages.success(
                    request,
                    f"KI-Outline ({fw_label}, {len(result.nodes)} Beats) generiert."
                )
                url = reverse("projects:detail", kwargs={"pk": pk})
                if version_id:
                    url += f"?outline={version_id}"
                return redirect(url)
            else:
                err = getattr(result, "error_message", "") or ""
                messages.warning(request, f"KI-Fehler: {err}" if err else "KI konnte kein Outline generieren.")
        except Exception as exc:
            logger.exception("OutlineGenerateView error pk=%s: %s", pk, exc)
            messages.error(request, f"KI-Fehler: {exc}")
        return redirect("projects:detail", pk=pk)


class ChapterWriterView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "authoring/chapter_writer.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.worlds.models import ProjectCharacterLink
        active_outline = OutlineVersion.objects.filter(
            project=self.object, is_active=True
        ).order_by("-created_at").first()
        chapters = list(active_outline.nodes.order_by("order")) if active_outline else []
        ctx["chapters"] = chapters
        ctx["chapter_count"] = len(chapters)
        ctx["active_outline"] = active_outline
        ctx["characters"] = ProjectCharacterLink.objects.filter(
            project=self.object
        ).select_related()
        return ctx


class ChapterContentView(LoginRequiredMixin, View):
    """
    GET  /projects/node/<uuid>/content/  -> JSON {content, word_count, updated_at}
    POST /projects/node/<uuid>/content/  -> Speichert content in DB
    """

    def _get_node(self, request, node_pk):
        return get_object_or_404(
            OutlineNode,
            pk=node_pk,
            outline_version__project__owner=request.user,
        )

    def get(self, request, node_pk):
        node = self._get_node(request, node_pk)
        return JsonResponse({
            "content": node.content,
            "word_count": node.word_count,
            "updated_at": node.content_updated_at.isoformat() if node.content_updated_at else None,
        })

    def post(self, request, node_pk):
        node = self._get_node(request, node_pk)
        try:
            body = json.loads(request.body)
            content = body.get("content", "")
        except (json.JSONDecodeError, AttributeError):
            content = request.POST.get("content", "")
        node.content = content
        node.content_updated_at = timezone.now()
        node.save(update_fields=["content", "word_count", "content_updated_at"])
        return JsonResponse({
            "ok": True,
            "word_count": node.word_count,
            "updated_at": node.content_updated_at.isoformat(),
        })
