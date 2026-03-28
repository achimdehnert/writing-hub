"""
Analysis + Budget Views — TextAnalysisSnapshot + BudgetService (ADR-161)
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import BookProject, TextAnalysisSnapshot


class ProjectAnalysisView(LoginRequiredMixin, View):
    """Strukturelle Manuskript-Analyse — Dead Scenes, Pacing, Screen Time (ADR-161)."""

    template_name = "projects/analysis.html"

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        snapshots = TextAnalysisSnapshot.objects.filter(
            project=project
        ).order_by("-computed_at")[:5]
        latest = snapshots.first()
        return render(request, self.template_name, {
            "project": project,
            "latest": latest,
            "snapshots": snapshots,
        })

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        check_voice = bool(request.POST.get("check_voice_drift"))
        try:
            from .services.text_analysis_service import compute_text_analysis
            compute_text_analysis(
                project,
                check_voice_drift=check_voice,
                triggered_by="manual",
            )
            messages.success(request, "Analyse abgeschlossen.")
        except Exception as exc:
            messages.error(request, f"Analyse fehlgeschlagen: {exc}")
        return redirect("projects:analysis", pk=pk)


class ProjectBudgetView(LoginRequiredMixin, View):
    """Wortanzahl-Budget pro Akt + Kapitel (ADR-161)."""

    template_name = "projects/budget.html"

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        allocation = None
        error = None
        try:
            from .services.budget_service import compute_budget
            allocation = compute_budget(project)
        except Exception as exc:
            error = str(exc)

        version = project.outline_versions.filter(is_active=True).first()
        nodes = []
        if version:
            nodes = list(version.nodes.order_by("order"))

        return render(request, self.template_name, {
            "project": project,
            "allocation": allocation,
            "nodes": nodes,
            "error": error,
        })
