"""
Projects — HTML Frontend Views (ADR-083)
"""
import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView

from apps.authoring.defaults import (
    DEFAULT_CONTENT_TYPE,
    DEFAULT_PROJECT_TARGET_WORDS,
    distribute_chapter_targets,
)
from apps.series.models import BookSeries
from .constants import (
    DEFAULT_CONTENT_TYPES,
    FORMAT_PROFILES,
    FW_BEATS_FALLBACK,
    FW_LABELS_FALLBACK,
)
from .models import (
    AudienceLookup, BookProject,
    ContentTypeLookup, GenreLookup, OutlineFramework,
    OutlineNode, OutlineVersion,
)

logger = logging.getLogger(__name__)


def _get_frameworks():
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


def _get_authors(user):
    try:
        from apps.authors.models import Author
        return list(
            Author.objects.filter(owner=user, is_active=True)
            .prefetch_related("writing_styles")
            .order_by("name")
        )
    except Exception:
        return []


def _get_all_styles(user):
    """Alle WritingStyles des Users, mit Author-Info."""
    try:
        from apps.authors.models import WritingStyle
        return list(
            WritingStyle.objects.filter(
                author__owner=user, is_active=True
            ).select_related("author").order_by("author__name", "name")
        )
    except Exception:
        return []


def _filter_projects(request):
    """Gemeinsame Filter-Logik für ProjectListView + ProjectListPartialView."""
    from django.db.models import Sum  # noqa: F811
    qs = BookProject.objects.filter(
        owner=request.user, is_active=True
    ).select_related("genre_lookup", "content_type_lookup", "series")
    series_id = request.GET.get("serie")
    genre_id = request.GET.get("genre")
    ct_id = request.GET.get("typ")
    q = request.GET.get("q", "").strip()
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
    # Wortanzahl pro Projekt annotieren (für Fortschrittsbalken)
    word_sums = {
        row["outline_version__project_id"]: row["total"]
        for row in OutlineNode.objects.filter(
            outline_version__project__in=qs,
            outline_version__is_active=True,
        ).values("outline_version__project_id").annotate(
            total=Sum("word_count")
        )
    }
    for p in qs:
        p.written_words = word_sums.get(p.pk, 0) or 0
        if p.target_word_count and p.target_word_count > 0:
            p.progress_pct = min(
                100, round(p.written_words / p.target_word_count * 100)
            )
        else:
            p.progress_pct = 0
    return qs


PAGE_SIZE = 12


def _paginate(qs, request):
    from django.core.paginator import Paginator
    paginator = Paginator(list(qs), PAGE_SIZE)
    page_number = request.GET.get("page", 1)
    return paginator.get_page(page_number)


class ProjectListView(LoginRequiredMixin, ListView):
    model = BookProject
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return _filter_projects(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["series_options"] = BookSeries.objects.filter(
            owner=self.request.user
        ).order_by("title")
        ctx["genre_options"] = GenreLookup.objects.all().order_by(
            "order", "name"
        )
        ctx["ct_options"] = ContentTypeLookup.objects.all().order_by(
            "order", "name"
        )
        ctx["filter_serie"] = self.request.GET.get("serie", "")
        ctx["filter_genre"] = self.request.GET.get("genre", "")
        ctx["filter_typ"] = self.request.GET.get("typ", "")
        ctx["filter_q"] = self.request.GET.get("q", "")
        ctx["page_obj"] = _paginate(ctx["projects"], self.request)
        ctx["projects"] = ctx["page_obj"]
        return ctx


class ProjectListPartialView(LoginRequiredMixin, View):
    """HTMX-Partial: Projektkarten-Grid ohne Layout, mit Paginierung."""

    def get(self, request):
        qs = _filter_projects(request)
        filter_active = any([
            request.GET.get("q"),
            request.GET.get("genre"),
            request.GET.get("typ"),
            request.GET.get("serie"),
        ])
        page_obj = _paginate(qs, request)
        return render(request, "projects/project_list_partial.html", {
            "projects": page_obj,
            "page_obj": page_obj,
            "filter_active": filter_active,
        })


class ProjectCreateView(LoginRequiredMixin, View):
    template_name = "projects/project_form.html"

    def _context(self, user, post_data=None):
        return {
            "content_types": ContentTypeLookup.objects.all().order_by("order", "name"),
            "default_content_types": DEFAULT_CONTENT_TYPES,
            "genres": GenreLookup.objects.all().order_by("order", "name"),
            "audiences": AudienceLookup.objects.all().order_by("order", "name"),
            "authors": _get_authors(user),
            "all_styles": _get_all_styles(user),
            "series_options": BookSeries.objects.filter(owner=user).order_by("title"),
            "post": post_data or {},
            "is_edit": False,
        }

    def get(self, request):
        return render(request, self.template_name, self._context(request.user))

    def post(self, request):
        title = request.POST.get("title", "").strip()
        if not title:
            ctx = self._context(request.user, request.POST)
            ctx["error"] = "Bitte einen Arbeitstitel eingeben."
            return render(request, self.template_name, ctx)
        ct_id = request.POST.get("content_type_lookup") or None
        genre_id = request.POST.get("genre_lookup") or None
        audience_id = request.POST.get("audience_lookup") or None
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
            series_id=series_id,
            target_word_count=target_word_count,
        )
        style_ids = request.POST.getlist("writing_styles")
        if style_ids:
            try:
                from apps.authors.models import WritingStyle
                styles = WritingStyle.objects.filter(
                    pk__in=style_ids, author__owner=request.user
                )
                project.writing_styles.set(styles)
                if styles:
                    project.writing_style = styles.first()
                    project.save(update_fields=["writing_style"])
            except Exception:
                pass
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

        frameworks = _get_frameworks()
        ctx["frameworks"] = frameworks
        _CT_DEFAULT_FW = {
            "nonfiction": "sachbuch",
            "academic": "scientific_essay",
            "scientific": "imrad",
            "essay": "scientific_essay",
        }
        active_fw_key = selected.source if selected else _CT_DEFAULT_FW.get(
            project.content_type, "three_act"
        )
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
            outline_version__project=project, outline_version__is_active=True,
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
        ctx["project_styles"] = project.get_all_styles()
        ctx["format_profile"] = FORMAT_PROFILES.get(project.content_type)
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["audiences"] = AudienceLookup.objects.all().order_by("order", "name")
        ctx["authors"] = _get_authors(self.request.user)
        ctx["all_styles"] = _get_all_styles(self.request.user)
        ctx["selected_style_ids"] = list(
            self.object.writing_styles.values_list("pk", flat=True)
        )
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        style_ids = self.request.POST.getlist("writing_styles")
        try:
            from apps.authors.models import WritingStyle
            styles = WritingStyle.objects.filter(
                pk__in=style_ids, author__owner=self.request.user
            )
            self.object.writing_styles.set(styles)
            first = styles.first()
            if first:
                self.object.writing_style = first
                self.object.save(update_fields=["writing_style"])
        except Exception:
            pass
        return response

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

        if not framework_key:
            messages.warning(request, "Bitte ein Framework auswählen.")
            return redirect("projects:detail", pk=pk)

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
            ct = getattr(project, "content_type", DEFAULT_CONTENT_TYPE) or DEFAULT_CONTENT_TYPE
            ptarget = project.target_word_count or DEFAULT_PROJECT_TARGET_WORDS
            if beats:
                targets = distribute_chapter_targets(ptarget, len(beats), ct)
                OutlineNode.objects.bulk_create([
                    OutlineNode(
                        outline_version=version,
                        title=b.name,
                        beat_type="chapter",
                        beat_phase=b.name,
                        order=b.order,
                        target_words=targets[i],
                    )
                    for i, b in enumerate(beats)
                ])
                messages.success(request, f'Outline „{name}“ mit {len(beats)} Beats angelegt.')
            elif chapter_count > 0:
                count = min(chapter_count, 50)
                targets = distribute_chapter_targets(ptarget, count, ct)
                OutlineNode.objects.bulk_create([
                    OutlineNode(
                        outline_version=version,
                        title=f"Kapitel {i + 1}",
                        beat_type="chapter",
                        order=i + 1,
                        target_words=targets[i],
                    )
                    for i in range(count)
                ])
                messages.success(request, f'Outline „{name}“ mit {chapter_count} leeren Kapiteln angelegt.')
            else:
                messages.success(request, f'Outline „{name}" angelegt.')
            if request.POST.get("ai_generate") == "1" and project.description:
                try:
                    from apps.authoring.services.outline_service import (
                        OutlineGeneratorService,
                    )
                    svc = OutlineGeneratorService()
                    result = svc.generate_outline(
                        project_id=str(project.pk),
                        framework=framework_key,
                        chapter_count=len(beats) if beats else (chapter_count or 12),
                    )
                    if result.success and result.nodes:
                        version.nodes.all().delete()
                        db_nodes = []
                        from apps.projects.models import OutlineNode as _ON
                        for i, node in enumerate(result.nodes):
                            beat = ""
                            try:
                                beat = node.act.value if hasattr(node.act, "value") else str(node.act)
                            except Exception:
                                beat = "chapter"
                            summary = ""
                            try:
                                summary = node.summary or node.description or ""
                            except Exception:
                                pass
                            db_nodes.append(_ON(
                                outline_version=version,
                                title=node.title,
                                description=summary,
                                beat_type=beat or "chapter",
                                order=i + 1,
                            ))
                        ai_targets = distribute_chapter_targets(ptarget, len(db_nodes), ct)
                        for idx, dn in enumerate(db_nodes):
                            dn.target_words = ai_targets[idx]
                        _ON.objects.bulk_create(db_nodes)
                        messages.success(
                            request,
                            f'KI-Outline „{name}" mit {len(result.nodes)} Kapiteln generiert.'
                        )
                    else:
                        err = getattr(result, "error_message", "") or ""
                        messages.warning(
                            request,
                            f"Outline angelegt, KI-Generierung fehlgeschlagen: {err}" if err
                            else "Outline angelegt, KI konnte keine Kapitel generieren."
                        )
                except Exception as ai_exc:
                    logger.exception("KI-Generierung beim Anlegen fehlgeschlagen: %s", ai_exc)
                    messages.warning(
                        request,
                        f"Outline angelegt, KI-Generierung fehlgeschlagen: {ai_exc}"
                    )
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
        from apps.worlds.models import ProjectCharacterLink, ProjectWorldLink
        active_outline = OutlineVersion.objects.filter(
            project=self.object, is_active=True
        ).order_by("-created_at").first()
        chapters = list(
            active_outline.nodes.select_related("writing_style", "writing_style__author")
            .order_by("order")
        ) if active_outline else []
        ctx["chapters"] = chapters
        ctx["chapter_count"] = len(chapters)
        ctx["active_outline"] = active_outline
        ctx["characters"] = ProjectCharacterLink.objects.filter(
            project=self.object
        ).select_related()
        ctx["world_links"] = ProjectWorldLink.objects.filter(
            project=self.object
        ).select_related()
        ctx["project_styles"] = self.object.get_all_styles()
        from apps.authoring.defaults import (
            AUTOSAVE_DELAY_MS,
            DEFAULT_TARGET_WORD_COUNT,
            POLL_INTERVAL_MS,
            POLL_MAX_COUNT,
            TOAST_DISPLAY_MS,
        )
        from apps.projects.services.preparation_service import get_preparation_status
        from .models import ProjectCitation
        ctx["project_citations"] = ProjectCitation.objects.filter(
            project=self.object
        ).select_related("node").order_by("node__order", "-created_at")
        ctx["prep_status"] = get_preparation_status(self.object, chapters)
        ctx["defaults"] = {
            "target_word_count": DEFAULT_TARGET_WORD_COUNT,
            "poll_interval_ms": POLL_INTERVAL_MS,
            "poll_max_count": POLL_MAX_COUNT,
            "autosave_delay_ms": AUTOSAVE_DELAY_MS,
            "toast_display_ms": TOAST_DISPLAY_MS,
        }
        return ctx


class ChapterNodeStyleView(LoginRequiredMixin, View):
    """Setzt den Schreibstil für ein einzelnes Kapitel."""

    def post(self, request, node_pk):
        node = get_object_or_404(
            OutlineNode, pk=node_pk, outline_version__project__owner=request.user
        )
        style_id = request.POST.get("writing_style") or None
        node.writing_style_id = style_id
        node.save(update_fields=["writing_style"])
        return JsonResponse({"ok": True, "style_id": str(style_id) if style_id else None})


class ChapterResearchView(LoginRequiredMixin, View):
    """Recherchiert Quellen für ein Kapitel und speichert in node.notes."""

    def post(self, request, node_pk):
        node = get_object_or_404(
            OutlineNode, pk=node_pk, outline_version__project__owner=request.user
        )
        from .services.citation_service import research_chapter_sources
        try:
            result = research_chapter_sources(str(node.pk), max_results=15)
        except Exception as exc:
            logger.exception("ChapterResearchView error for node %s", node_pk)
            return JsonResponse({"ok": False, "error": str(exc)})

        return JsonResponse({
            "ok": True,
            "paper_count": result.get("paper_count", 0),
            "notes_preview": result.get("notes_preview", ""),
            "citations_created": result.get("citations_created", 0),
        })


class ChapterContentView(LoginRequiredMixin, View):
    SAVEABLE_FIELDS = {
        "target_words": ("target_words", lambda v: int(v) if v else None),
        "description": ("description", str),
        "emotional_arc": ("emotional_arc", str),
    }

    def _get_node(self, request, node_pk):
        return get_object_or_404(
            OutlineNode,
            pk=node_pk,
            outline_version__project__owner=request.user,
        )

    def get(self, request, node_pk):
        node = self._get_node(request, node_pk)
        style = node.get_effective_style()
        return JsonResponse({
            "content": node.content,
            "word_count": node.word_count,
            "updated_at": node.content_updated_at.isoformat() if node.content_updated_at else None,
            "writing_style_id": str(node.writing_style_id) if node.writing_style_id else None,
            "writing_style_name": str(style) if style else None,
            "style_prompt": style.style_prompt if style else "",
        })

    def post(self, request, node_pk):
        node = self._get_node(request, node_pk)
        try:
            body = json.loads(request.body)
            content = body.get("content", "")
        except (json.JSONDecodeError, AttributeError):
            body = {}
            content = request.POST.get("content", "")
        node.content = content
        node.content_updated_at = timezone.now()
        update_fields = ["content", "word_count", "content_updated_at"]
        for json_key, (model_field, coerce) in self.SAVEABLE_FIELDS.items():
            if json_key in body:
                setattr(node, model_field, coerce(body[json_key]))
                update_fields.append(model_field)
        node.save(update_fields=update_fields)
        return JsonResponse({
            "ok": True,
            "word_count": node.word_count,
            "updated_at": node.content_updated_at.isoformat(),
        })


class DramaDashboardView(LoginRequiredMixin, View):
    """Drama-Dashboard: Spannungskurve + Wendepunkte + Health-Score (ADR-154)."""

    def get(self, request, pk):
        from apps.projects.services.drama_service import DramaDashboardService

        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        svc = DramaDashboardService(project)

        chart_json = svc.get_chart_json()
        chart_data = svc.get_tension_chart_data()
        turning_points = svc.get_turning_points()
        health = svc.get_health_data()

        turning_point_types = []
        try:
            from apps.core.models_lookups_drama import TurningPointTypeLookup
            turning_point_types = list(
                TurningPointTypeLookup.objects.order_by("sort_order")
            )
        except Exception:
            pass

        return render(request, "projects/drama_dashboard.html", {
            "project": project,
            "chart_json": chart_json,
            "chart_data": chart_data,
            "turning_points": turning_points,
            "turning_point_types": turning_point_types,
            "health": health,
        })


class DramaNodeUpdateView(LoginRequiredMixin, View):
    """HTMX: tension_numeric + outcome + emotion_start/end auf OutlineNode speichern."""

    def post(self, request, node_pk):
        from django.http import HttpResponse

        node = get_object_or_404(
            OutlineNode, pk=node_pk, outline_version__project__owner=request.user
        )
        tn = request.POST.get("tension_numeric", "")
        if tn:
            try:
                node.tension_numeric = max(1, min(10, int(tn)))
            except ValueError:
                pass
        outcome = request.POST.get("outcome", "")
        if outcome in ("yes", "no", "yes_but", "no_and", ""):
            node.outcome = outcome
        node.emotion_start = request.POST.get("emotion_start", node.emotion_start)
        node.emotion_end = request.POST.get("emotion_end", node.emotion_end)
        node.save(update_fields=["tension_numeric", "outcome", "emotion_start", "emotion_end"])

        if request.headers.get("HX-Request"):
            return HttpResponse(
                f'<span class="badge bg-success text-white ms-1 small">✓ {node.title[:20]}</span>'
            )
        return redirect("projects:drama_dashboard", pk=node.outline_version.project.pk)


class DramaTurningPointAddView(LoginRequiredMixin, View):
    """Wendepunkt anlegen — POST from Drama-Dashboard form."""

    def post(self, request, pk):
        from apps.projects.models import ProjectTurningPoint

        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        tp_type_pk = request.POST.get("turning_point_type", "").strip()
        label = request.POST.get("label", "").strip()
        pos = request.POST.get("position_percent", "0").strip()

        tp_type = None
        if tp_type_pk:
            try:
                from apps.core.models_lookups_drama import TurningPointTypeLookup
                tp_type = TurningPointTypeLookup.objects.filter(pk=tp_type_pk).first()
            except Exception:
                pass

        try:
            position = max(0, min(100, int(pos)))
        except (ValueError, TypeError):
            position = 0

        ProjectTurningPoint.objects.create(
            project=project,
            turning_point_type=tp_type,
            label=label,
            position_percent=position,
        )
        return redirect("projects:drama_dashboard", pk=pk)


class GenresByContentTypeView(LoginRequiredMixin, View):
    """AJAX: Genres gefiltert nach Inhaltstyp (oder alle bei ct_id=leer)."""

    def get(self, request):
        ct_id = request.GET.get("ct")
        if ct_id:
            genres = GenreLookup.objects.filter(
                models.Q(content_type_id=ct_id) | models.Q(content_type__isnull=True)
            ).order_by("order", "name")
        else:
            genres = GenreLookup.objects.all().order_by("order", "name")
        data = [{"id": g.pk, "name": g.name} for g in genres]
        return JsonResponse(data, safe=False)
