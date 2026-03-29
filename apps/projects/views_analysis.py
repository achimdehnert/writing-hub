"""
Analysis + Budget + Batch Views — ADR-161
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
        nodes_with_budget = []
        if version and allocation:
            node_budgets = allocation.node_budgets or {}
            over = set(allocation.over_budget_nodes or [])
            under = set(allocation.under_budget_nodes or [])
            for n in version.nodes.order_by("order"):
                key = str(n.id)
                nodes_with_budget.append({
                    "node": n,
                    "budget": node_budgets.get(key),
                    "over": key in over,
                    "under": key in under,
                })

        return render(request, self.template_name, {
            "project": project,
            "allocation": allocation,
            "nodes_with_budget": nodes_with_budget,
            "error": error,
        })


class ProjectBatchView(LoginRequiredMixin, View):
    """Batch-Generierung mehrerer Kapitel starten (ADR-161 Teil D)."""

    template_name = "projects/batch.html"

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        from apps.authoring.models_jobs import BatchWriteJob
        jobs = BatchWriteJob.objects.filter(
            project=project
        ).order_by("-created_at")[:10]
        version = project.outline_versions.filter(is_active=True).first()
        nodes = list(version.nodes.order_by("order")) if version else []
        return render(request, self.template_name, {
            "project": project,
            "jobs": jobs,
            "nodes": nodes,
        })

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        node_ids = request.POST.getlist("node_ids")
        if not node_ids:
            messages.error(request, "Keine Kapitel ausgewählt.")
            return redirect("projects:batch", pk=pk)
        max_chapters = min(int(request.POST.get("max_chapters", 10)), 10)
        from apps.authoring.models_jobs import BatchWriteJob
        from apps.authoring.tasks import run_batch_write
        job = BatchWriteJob.objects.create(
            project=project,
            requested_by=request.user,
            node_ids=node_ids[:max_chapters],
            max_chapters=max_chapters,
        )
        run_batch_write.delay(str(job.id))
        messages.success(
            request,
            f"Batch-Job gestartet ({job.total} Kapitel).",
        )
        return redirect("projects:batch", pk=pk)


class ProjectBatchStatusView(LoginRequiredMixin, View):
    """HTMX-Polling: Job-Status als HTML-Partial (ADR-161 Teil D)."""

    def get(self, request, pk, job_id):
        project = get_object_or_404(BookProject, pk=pk)
        from apps.authoring.models_jobs import BatchWriteJob
        job = get_object_or_404(
            BatchWriteJob, pk=job_id, project=project
        )
        is_done = job.status in ("done", "failed", "canceled")
        return render(request, "projects/batch_status_partial.html", {
            "job": job,
            "is_done": is_done,
        })
