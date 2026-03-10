"""
Projects — HTML Frontend Views (ADR-083)
"""
import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.series.models import BookSeries
from .models import BookProject, OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)

OUTLINE_FRAMEWORKS = {
    "three_act": [
        "Akt I: Einführung", "Wendepunkt 1", "Akt II: Konfrontation",
        "Mittelpunkt", "Wendepunkt 2", "Akt III: Auflösung",
    ],
    "save_the_cat": [
        "Opening Image", "Theme Stated", "Set-Up", "Catalyst", "Debate",
        "Break into Two", "B Story", "Fun and Games", "Midpoint", "Bad Guys Close In",
        "All Is Lost", "Dark Night of the Soul", "Break into Three", "Finale", "Final Image",
    ],
    "heros_journey": [
        "Gewöhnliche Welt", "Ruf zum Abenteuer", "Weigerung", "Mentor",
        "Überschreiten der Schwelle", "Prüfungen & Verbündete", "Die innerste Höhle",
        "Die große Prüfung", "Belohnung", "Der Rückweg", "Auferstehung", "Rückkehr mit dem Elixier",
    ],
    "five_act": [
        "Akt I: Exposition", "Akt II: Steigende Handlung", "Akt III: Höhepunkt",
        "Akt IV: Fallende Handlung", "Akt V: Katastrophe / Auflösung",
    ],
    "dan_harmon": [
        "You (Held in Komfortzone)", "Need (Etwas fehlt)", "Go (Unbekannte Zone betreten)",
        "Search (Anpassung / Suche)", "Find (Was gesucht wurde finden)",
        "Take (Preis zahlen)", "Return (Zurückkehren)", "Change (Veränderung)",
    ],
}

FW_LABELS = {
    "three_act": "Drei-Akt-Struktur",
    "save_the_cat": "Save the Cat",
    "heros_journey": "Heldenreise",
    "five_act": "Fünf-Akt-Struktur",
    "dan_harmon": "Dan Harmon Story Circle",
    "blank": "Leere Kapitel",
}

KNOWN_FRAMEWORKS = set(OUTLINE_FRAMEWORKS.keys()) | {"blank"}


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
        from apps.projects.models import ContentTypeLookup, GenreLookup
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


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = BookProject
    template_name = "projects/project_form.html"
    fields = [
        "title", "description", "series",
        "content_type_lookup", "genre_lookup", "audience_lookup",
        "target_word_count",
    ]
    success_url = reverse_lazy("projects:list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["series"].queryset = BookSeries.objects.filter(owner=self.request.user)
        form.fields["series"].empty_label = "— keine Serie —"
        form.fields["content_type_lookup"].empty_label = "— bitte wählen —"
        form.fields["genre_lookup"].empty_label = "— bitte wählen —"
        form.fields["audience_lookup"].empty_label = "— bitte wählen —"
        return form

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        outlines = OutlineVersion.objects.filter(
            project=self.object
        ).order_by("-created_at")
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
        ctx["outline_frameworks"] = list(OUTLINE_FRAMEWORKS.keys())
        if selected and selected.source in KNOWN_FRAMEWORKS:
            ctx["selected_outline_framework"] = selected.source
        else:
            ctx["selected_outline_framework"] = "three_act"
        from apps.idea_import.models import IdeaImportDraft
        from apps.worlds.models import ProjectWorldLink
        ctx["idea_drafts"] = IdeaImportDraft.objects.filter(
            project=self.object
        ).exclude(
            status=IdeaImportDraft.Status.DISCARDED
        ).order_by("-created_at")[:10]
        ctx["world_links"] = ProjectWorldLink.objects.filter(project=self.object)
        return ctx


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = BookProject
    template_name = "projects/project_form.html"
    fields = [
        "title", "description", "series",
        "content_type_lookup", "genre_lookup", "audience_lookup",
        "target_word_count",
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
        return form

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})


class OutlineCreateView(LoginRequiredMixin, View):
    """Manuell Outline via Framework anlegen."""

    def get(self, request, pk):
        return redirect("projects:detail", pk=pk)

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip()
        notes = request.POST.get("notes", "")
        chapter_count = int(request.POST.get("chapter_count", 0) or 0)
        framework_template = request.POST.get("framework_template", "").strip()
        logger.info(
            "OutlineCreateView.post pk=%s framework=%s chapter_count=%s user=%s",
            pk, framework_template, chapter_count, request.user,
        )
        if not framework_template:
            messages.warning(request, "Bitte ein Framework auswählen.")
            return redirect("projects:detail", pk=pk)
        if not name:
            name = FW_LABELS.get(framework_template, framework_template)
        try:
            OutlineVersion.objects.filter(project=project, is_active=True).update(is_active=False)
            version = OutlineVersion.objects.create(
                project=project,
                created_by=request.user,
                name=name,
                source=framework_template,
                notes=notes,
                is_active=True,
            )
            beats = OUTLINE_FRAMEWORKS.get(framework_template, [])
            if beats:
                OutlineNode.objects.bulk_create([
                    OutlineNode(
                        outline_version=version,
                        title=beat,
                        beat_type="chapter",
                        order=i + 1,
                    )
                    for i, beat in enumerate(beats)
                ])
                messages.success(request, f'Outline „{name}" mit {len(beats)} Kapiteln angelegt.')
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
                messages.success(request, f'Outline-Struktur „{name}" angelegt.')
            url = reverse("projects:detail", kwargs={"pk": pk}) + f"?outline={version.pk}"
            return redirect(url)
        except Exception as exc:
            logger.exception("OutlineCreateView error pk=%s: %s", pk, exc)
            messages.error(request, f"Fehler beim Anlegen: {exc}")
        return redirect("projects:detail", pk=pk)


class OutlineGenerateView(LoginRequiredMixin, View):
    """KI-Outline generieren."""

    def get(self, request, pk):
        return redirect("projects:detail", pk=pk)

    def post(self, request, pk):
        from apps.authoring.services.outline_service import OutlineGeneratorService
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        framework = request.POST.get("framework", "three_act").strip()
        chapter_count = int(request.POST.get("chapter_count", 12) or 12)
        logger.info(
            "OutlineGenerateView.post pk=%s framework=%s chapter_count=%s user=%s",
            pk, framework, chapter_count, request.user,
        )
        try:
            svc = OutlineGeneratorService()
            result = svc.generate_outline(
                project_id=str(project.pk),
                framework=framework,
                chapter_count=chapter_count,
            )
            if result.success and result.nodes:
                OutlineVersion.objects.filter(project=project, is_active=True).update(is_active=False)
                version_id = svc.save_outline(
                    project_id=str(project.pk),
                    nodes=result.nodes,
                    name=f"KI: {FW_LABELS.get(framework, framework)}",
                    framework=framework,
                    user=request.user,
                )
                messages.success(
                    request,
                    f"KI-Outline ({FW_LABELS.get(framework, framework)}, {len(result.nodes)} Beats) generiert."
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
    POST /projects/node/<uuid>/content/  -> Speichert content in DB, gibt {ok, word_count} zurück
    """

    def _get_node(self, request, node_pk):
        """Gibt OutlineNode zurück — prüft Ownership via Outline -> Projekt."""
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
