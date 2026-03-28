"""
Health-Score Views — ADR-157

GET  /projects/<pk>/health/          → vollständige Health-Seite
GET  /projects/<pk>/health/partial/  → HTMX-Partial (Score-Badge only)
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView

from .models import BookProject
from .services.health_service import compute_dramaturgic_health


class ProjectHealthView(LoginRequiredMixin, DetailView):
    """GET — zeigt vollständige Dramaturgik-Health-Seite."""

    model = BookProject
    template_name = "projects/health.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        result = compute_dramaturgic_health(self.object)
        ctx["health"] = result
        ctx["passed_checks"] = [c for c in result.checks if c.passed]
        ctx["failed_checks"] = [c for c in result.checks if not c.passed]
        ctx["top_issues"] = result.top_issues
        ctx["level_label"] = {
            "solid":      ("Solide", "success"),
            "developing": ("In Entwicklung", "warning"),
            "skeleton":   ("Grundriss", "danger"),
        }.get(result.level, (result.level, "secondary"))
        return ctx


class ProjectHealthPartialView(LoginRequiredMixin, View):
    """GET — HTMX-Partial: Score-Badge für Projekt-Header."""

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        result = compute_dramaturgic_health(project)
        color = {"solid": "#22c55e", "developing": "#f59e0b", "skeleton": "#ef4444"}[result.level]
        html = (
            f'<span class="health-badge" style="'
            f'background:{color}22;color:{color};border:1px solid {color}44;'
            f'display:inline-flex;align-items:center;gap:.35rem;'
            f'padding:.2rem .6rem;border-radius:999px;font-size:.78rem;font-weight:600;">'
            f'<i class="bi bi-heart-pulse"></i> {result.score}%'
            f'</span>'
        )
        return HttpResponse(html)
