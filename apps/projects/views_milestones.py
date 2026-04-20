"""
Projects — Milestone & Deadline Views (UC 6.3)
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .models import BookProject, ProjectMilestone

logger = logging.getLogger(__name__)


class ProjectMilestonesView(LoginRequiredMixin, View):
    """GET: Meilenstein-Übersicht. POST: Neuen Meilenstein anlegen."""

    template_name = "projects/milestones.html"

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        milestones = project.milestones.all()
        upcoming = milestones.filter(is_completed=False).order_by("due_date")
        completed = milestones.filter(is_completed=True).order_by("-completed_at")
        return render(
            request,
            self.template_name,
            {
                "project": project,
                "upcoming": upcoming,
                "completed": completed,
            },
        )

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        title = request.POST.get("title", "").strip()
        due_date = request.POST.get("due_date", "").strip()
        phase = request.POST.get("phase", "")
        notes = request.POST.get("notes", "").strip()

        if not title or not due_date:
            messages.error(request, "Titel und Fälligkeitsdatum sind Pflicht.")
            return redirect("projects:milestones", pk=pk)

        ProjectMilestone.objects.create(
            project=project,
            title=title,
            due_date=due_date,
            phase=phase,
            notes=notes,
        )
        messages.success(request, f'Meilenstein "{title}" angelegt.')
        return redirect("projects:milestones", pk=pk)


class MilestoneToggleView(LoginRequiredMixin, View):
    """POST: Meilenstein als erledigt/offen markieren."""

    def post(self, request, pk, milestone_pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        milestone = get_object_or_404(ProjectMilestone, pk=milestone_pk, project=project)
        if milestone.is_completed:
            milestone.is_completed = False
            milestone.completed_at = None
        else:
            milestone.is_completed = True
            milestone.completed_at = timezone.now()
        milestone.save(update_fields=["is_completed", "completed_at"])
        return redirect("projects:milestones", pk=pk)


class MilestoneDeleteView(LoginRequiredMixin, View):
    """POST: Meilenstein löschen."""

    def post(self, request, pk, milestone_pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        milestone = get_object_or_404(ProjectMilestone, pk=milestone_pk, project=project)
        milestone.delete()
        messages.success(request, "Meilenstein gelöscht.")
        return redirect("projects:milestones", pk=pk)
