"""
Quick Project Views — Autonome Essay-Pipeline mit Web-UI.

Form → Celery Task → Progress-Polling → Projekt-Detail.
"""
from __future__ import annotations

import json

from apps.authoring.defaults import (
    DEFAULT_AUDIENCE,
    DEFAULT_FRAMEWORK,
    DEFAULT_PROJECT_TARGET_WORDS,
)
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .constants import FRAMEWORK_TO_CONTENT_TYPE
from .models import BookProject, ContentTypeLookup, OutlineFramework


class QuickProjectView(LoginRequiredMixin, View):
    """GET: Quick-Project-Formular anzeigen."""

    template_name = "projects/quick_project.html"

    def get(self, request):
        frameworks = OutlineFramework.objects.all().order_by("order", "name")

        fw_beats = {}
        for fw in frameworks:
            beats = list(fw.beats.order_by("order").values_list("name", flat=True))
            fw_beats[fw.key] = beats

        return render(request, self.template_name, {
            "frameworks": frameworks,
            "fw_beats_json": json.dumps(fw_beats),
            "default_target_words": DEFAULT_PROJECT_TARGET_WORDS,
        })


class QuickProjectStartView(LoginRequiredMixin, View):
    """POST: Projekt erstellen + Pipeline-Task starten."""

    def get(self, request):
        return redirect("projects:quick_project")

    def post(self, request):
        title = request.POST.get("title", "").strip()
        if not title:
            messages.error(request, "Bitte einen Titel eingeben.")
            return redirect("projects:quick_project")

        topic = request.POST.get("topic", "").strip()
        framework = request.POST.get("framework", DEFAULT_FRAMEWORK)
        target_words = request.POST.get("target_words", str(DEFAULT_PROJECT_TARGET_WORDS))
        audience = request.POST.get("audience", DEFAULT_AUDIENCE)
        do_research = bool(request.POST.get("do_research"))
        do_review = bool(request.POST.get("do_review"))

        try:
            target_words = int(target_words)
        except ValueError:
            target_words = DEFAULT_PROJECT_TARGET_WORDS

        content_type = FRAMEWORK_TO_CONTENT_TYPE.get(framework, "academic")
        ct_slug_map = {
            "novel": "roman",
            "nonfiction": "sachbuch",
            "short_story": "kurzgeschichte",
            "essay": "essay",
            "academic": "academic",
            "scientific": "scientific",
        }
        ct_slug = ct_slug_map.get(content_type, "sachbuch")
        ct_lookup = ContentTypeLookup.objects.filter(slug=ct_slug).first()

        project = BookProject.objects.create(
            owner=request.user,
            title=title,
            description=topic or title,
            content_type=content_type,
            content_type_lookup=ct_lookup,
            target_word_count=target_words,
            target_audience=audience,
            is_active=True,
        )

        from apps.authoring.models_jobs import EssayPipelineJob
        from apps.authoring.tasks import run_essay_pipeline

        job = EssayPipelineJob.objects.create(
            project=project,
            requested_by=request.user,
            framework=framework,
            do_research=do_research,
            do_review=do_review,
        )
        job.add_log(f"Projekt erstellt: {title}")

        run_essay_pipeline.delay(str(job.pk))

        return redirect("projects:quick_project_progress", pk=project.pk, job_id=job.pk)


class QuickProjectProgressView(LoginRequiredMixin, View):
    """GET: Progress-Seite mit Auto-Polling."""

    template_name = "projects/quick_project_progress.html"

    def get(self, request, pk, job_id):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        from apps.authoring.models_jobs import EssayPipelineJob
        job = get_object_or_404(EssayPipelineJob, pk=job_id, project=project)
        return render(request, self.template_name, {
            "project": project,
            "job": job,
        })


class QuickProjectStatusView(LoginRequiredMixin, View):
    """GET: JSON-Status fuer Polling."""

    def get(self, request, pk, job_id):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        from apps.authoring.models_jobs import EssayPipelineJob
        job = get_object_or_404(EssayPipelineJob, pk=job_id, project=project)
        return JsonResponse({
            "status": job.status,
            "step": job.current_step,
            "step_label": job.get_current_step_display(),
            "progress": job.progress_pct,
            "total_chapters": job.total_chapters,
            "completed_chapters": job.completed_chapters,
            "current_chapter": job.current_chapter_title,
            "log": job.log_messages[-10:],
            "error": job.error,
            "is_done": job.is_terminal,
        })
