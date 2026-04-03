"""
Peer Review — KI-gestütztes wissenschaftliches Peer Review (Views).

Multi-Agent Review für akademische/wissenschaftliche Projekte:
  - Methodik, Argumentation, Quellen, Struktur
  - Gesamtgutachten mit Verdict + Scores
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView

from .models import BookProject, PeerReviewFinding, PeerReviewSession
from .services.peer_review_service import (
    PEER_REVIEW_AGENTS,
    SCIENTIFIC_CONTENT_TYPES,
    is_peer_review_eligible,
    run_peer_review,
)

logger = logging.getLogger(__name__)


class PeerReviewDashboardView(LoginRequiredMixin, DetailView):
    """Dashboard: alle bisherigen Peer Reviews + neues starten."""

    model = BookProject
    template_name = "projects/peer_review.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        sessions = PeerReviewSession.objects.filter(
            project=project,
        ).order_by("-created_at")
        ctx["sessions"] = sessions
        ctx["latest_session"] = sessions.first()
        ctx["agents"] = PEER_REVIEW_AGENTS
        ctx["is_eligible"] = is_peer_review_eligible(project)
        ctx["scientific_types"] = SCIENTIFIC_CONTENT_TYPES
        return ctx


class PeerReviewStartView(LoginRequiredMixin, View):
    """POST: Startet ein neues Peer Review."""

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)

        if not is_peer_review_eligible(project):
            messages.warning(
                request,
                "Peer Review ist nur für wissenschaftliche, akademische oder Essay-Projekte verfügbar.",
            )
            return redirect("projects:peer_review", pk=pk)

        selected_agents = request.POST.getlist("agents")
        session_id = run_peer_review(
            project=project,
            user=request.user,
            agents=selected_agents or None,
        )

        if not session_id:
            messages.error(request, "Peer Review konnte nicht gestartet werden. Bitte Outline prüfen.")
            return redirect("projects:peer_review", pk=pk)

        session = PeerReviewSession.objects.get(pk=session_id)
        if session.status == "error":
            messages.error(request, f"Fehler: {session.summary}")
        elif session.status == "done":
            verdict_label = session.get_verdict_display() if session.verdict else "—"
            messages.success(
                request,
                f"Peer Review abgeschlossen: {session.finding_count} Findings, "
                f"Verdict: {verdict_label}",
            )

        return redirect("projects:peer_review_session", pk=pk, session_pk=session_id)


class PeerReviewSessionView(LoginRequiredMixin, DetailView):
    """Detail-Ansicht einer Peer Review Session mit Findings."""

    model = BookProject
    template_name = "projects/peer_review_session.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session_pk = self.kwargs["session_pk"]
        session = get_object_or_404(
            PeerReviewSession, pk=session_pk, project=self.object,
        )
        findings = PeerReviewFinding.objects.filter(
            session=session,
        ).select_related("node").order_by("node__order", "-severity", "agent")

        findings_by_agent = {}
        findings_by_chapter = {}
        for f in findings:
            findings_by_agent.setdefault(f.agent, []).append(f)
            findings_by_chapter.setdefault(str(f.node_id), []).append(f)

        ctx["session"] = session
        ctx["findings"] = findings
        ctx["findings_by_agent"] = findings_by_agent
        ctx["findings_by_chapter"] = findings_by_chapter
        ctx["agents"] = PEER_REVIEW_AGENTS
        ctx["agent_map"] = {a["key"]: a for a in PEER_REVIEW_AGENTS}
        ctx["critical_count"] = findings.filter(severity="critical").count()
        ctx["major_count"] = findings.filter(severity="major").count()
        ctx["minor_count"] = findings.filter(severity="minor").count()
        ctx["resolved_count"] = findings.filter(is_resolved=True).count()
        ctx["open_count"] = findings.filter(is_resolved=False).count()
        return ctx


class PeerReviewFindingResolveView(LoginRequiredMixin, View):
    """AJAX: Finding als gelöst/offen markieren."""

    def post(self, request, pk, finding_pk):
        finding = get_object_or_404(
            PeerReviewFinding,
            pk=finding_pk,
            session__project__owner=request.user,
        )
        finding.is_resolved = not finding.is_resolved
        finding.save(update_fields=["is_resolved"])
        return JsonResponse({"ok": True, "is_resolved": finding.is_resolved})
