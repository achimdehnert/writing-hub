"""
Publishing — Publikations-Profil verwalten (ADR-083)

Tabs: Metadaten | Cover | Frontmatter | Backmatter | Export
"""

from __future__ import annotations

import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView

from .constants import (
    AGE_CHOICES,
    BISAC_CHOICES,
    LANGUAGE_CHOICES,
    PUBLISHING_STATUS_CHOICES,
    PUBLISHING_STATUS_COLORS,
)
from .models import BookProject, PublisherProfile, PublishingProfile


def _get_or_create_profile(project: BookProject) -> PublishingProfile:
    pub = PublisherProfile.objects.filter(owner=project.owner, is_default=True).first()
    defaults = {
        "publisher_name": pub.name if pub else "Selbstverlag",
        "imprint": pub.imprint if pub else "",
        "language": pub.default_language if pub else "de",
        "age_rating": pub.default_age_rating if pub else "0",
        "bisac_category": pub.default_bisac_category if pub else "",
        "copyright_year": str(datetime.date.today().year),
        "copyright_holder": (
            pub.default_copyright_holder
            if pub and pub.default_copyright_holder
            else project.owner.get_full_name() or project.owner.username
        ),
    }
    profile, _ = PublishingProfile.objects.get_or_create(
        project=project,
        defaults=defaults,
    )
    return profile


class ProjectPublishingView(LoginRequiredMixin, DetailView):
    """GET — zeigt Publishing-Profil mit Tab-Navigation."""

    model = BookProject
    template_name = "projects/publishing.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = _get_or_create_profile(self.object)
        ctx["profile"] = profile
        ctx["active_tab"] = self.request.GET.get("tab", "metadata")
        ctx["language_choices"] = LANGUAGE_CHOICES
        ctx["age_choices"] = AGE_CHOICES
        ctx["bisac_choices"] = BISAC_CHOICES
        ctx["status_choices"] = PUBLISHING_STATUS_CHOICES
        ctx["status_color"] = PUBLISHING_STATUS_COLORS.get(profile.status, "#64748b")
        return ctx

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        profile = _get_or_create_profile(project)
        tab = request.POST.get("tab", "metadata")

        if tab == "metadata":
            profile.isbn = request.POST.get("isbn", "").strip()
            profile.asin = request.POST.get("asin", "").strip()
            profile.publisher_name = request.POST.get("publisher_name", "").strip()
            profile.imprint = request.POST.get("imprint", "").strip()
            profile.copyright_year = request.POST.get("copyright_year", "").strip()
            profile.copyright_holder = request.POST.get("copyright_holder", "").strip()
            profile.language = request.POST.get("language", "de")
            profile.age_rating = request.POST.get("age_rating", "0")
            profile.bisac_category = request.POST.get("bisac_category", "").strip()
            profile.keywords = request.POST.get("keywords", "").strip()
            first_pub = request.POST.get("first_published", "").strip()
            this_ed = request.POST.get("this_edition", "").strip()
            profile.first_published = first_pub or None
            profile.this_edition = this_ed or None
            profile.status = request.POST.get("status", "draft")

        elif tab == "cover":
            profile.cover_image_url = request.POST.get("cover_image_url", "").strip()
            profile.cover_notes = request.POST.get("cover_notes", "").strip()

        elif tab == "frontmatter":
            profile.dedication = request.POST.get("dedication", "").strip()
            profile.foreword = request.POST.get("foreword", "").strip()
            profile.preface = request.POST.get("preface", "").strip()

        elif tab == "backmatter":
            profile.afterword = request.POST.get("afterword", "").strip()
            profile.acknowledgements = request.POST.get("acknowledgements", "").strip()
            profile.about_author = request.POST.get("about_author", "").strip()
            profile.bibliography = request.POST.get("bibliography", "").strip()

        profile.save()
        messages.success(request, "Gespeichert.")
        return redirect(f"{request.path}?tab={tab}")


class PublishingKeywordsAIView(LoginRequiredMixin, View):
    """POST — generiert Keywords via LLM."""

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        try:
            from apps.authoring.services.llm_router import LLMRouter

            router = LLMRouter()
            genre = ""
            if hasattr(project, "genre_lookup") and project.genre_lookup:
                genre = project.genre_lookup.name
            elif project.genre:
                genre = project.genre

            from apps.core.prompt_utils import render_prompt

            messages = render_prompt(
                "projects/generate_keywords",
                title=project.title,
                genre=genre,
                description=project.description or "",
            )
            result = router.completion(
                action_code="chapter_analyze",
                messages=messages,
            )
            return JsonResponse({"ok": True, "keywords": result.strip()})
        except Exception as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=500)


class PitchDashboardView(LoginRequiredMixin, View):
    """Pitch-Dashboard: Logline, Comps, Exposé, Query Letter (ADR-159)."""

    template_name = "projects/pitch_dashboard.html"

    def get(self, request, pk):
        from .models import ComparableTitle, PitchDocument

        project = get_object_or_404(BookProject, pk=pk)
        comps = ComparableTitle.objects.filter(project=project).order_by("sort_order")
        pitch_docs = {}
        for pitch_type, _ in PitchDocument.PITCH_TYPES:
            pitch_docs[pitch_type] = PitchDocument.objects.filter(
                project=project, pitch_type=pitch_type, is_current=True
            ).first()
        return self._render(request, project, comps, pitch_docs)

    def post(self, request, pk):
        from .models import ComparableTitle, PitchDocument

        project = get_object_or_404(BookProject, pk=pk)
        action = request.POST.get("action", "")

        if action == "add_comp":
            ComparableTitle.objects.create(
                project=project,
                title=request.POST.get("title", ""),
                author=request.POST.get("author", ""),
                publisher=request.POST.get("publisher", ""),
                publication_year=request.POST.get("publication_year") or None,
                relation_type=request.POST.get("relation_type", "similar_theme"),
                similarity_note=request.POST.get("similarity_note", ""),
                difference_note=request.POST.get("difference_note", ""),
                sort_order=ComparableTitle.objects.filter(project=project).count(),
            )
            messages.success(request, "Comp hinzugefügt.")
        elif action == "delete_comp":
            comp_id = request.POST.get("comp_id")
            ComparableTitle.objects.filter(project=project, pk=comp_id).delete()
            messages.success(request, "Comp entfernt.")
        elif action == "save_pitch":
            pitch_type = request.POST.get("pitch_type", "")
            content = request.POST.get("content", "")
            if pitch_type and content:
                PitchDocument.objects.filter(project=project, pitch_type=pitch_type, is_current=True).update(
                    is_current=False
                )
                last = PitchDocument.objects.filter(project=project, pitch_type=pitch_type).order_by("-version").first()
                PitchDocument.objects.create(
                    project=project,
                    pitch_type=pitch_type,
                    content=content,
                    is_current=True,
                    version=(last.version + 1) if last else 1,
                )
                messages.success(request, "Pitch-Dokument gespeichert.")

        return redirect("projects:pitch_dashboard", pk=pk)

    def _render(self, request, project, comps, pitch_docs):
        from .models import ComparableTitle

        return render(
            request,
            self.template_name,
            {
                "project": project,
                "comps": comps,
                "pitch_docs": pitch_docs,
                "comp_relation_choices": ComparableTitle.COMP_RELATION,
            },
        )


class GeneratePitchView(LoginRequiredMixin, View):
    """HTMX/POST: Generiert ein Pitch-Dokument via LLM (ADR-159)."""

    def post(self, request, pk, pitch_type):
        from .services.pitch_service import (
            generate_expose_de,
            generate_logline,
            generate_query,
        )

        project = get_object_or_404(BookProject, pk=pk)

        generators = {
            "logline": generate_logline,
            "expose_de": generate_expose_de,
            "query": generate_query,
        }
        generator = generators.get(pitch_type)
        if not generator:
            messages.error(request, f"Unbekannter Pitch-Typ: {pitch_type}")
            return redirect("projects:pitch_dashboard", pk=pk)

        try:
            generator(project)
            messages.success(request, f"{pitch_type} erfolgreich generiert.")
        except Exception as exc:
            messages.error(request, f"Generierung fehlgeschlagen: {exc}")

        return redirect("projects:pitch_dashboard", pk=pk)
