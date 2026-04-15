"""
Lektorat — Prüfungs-Framework (ADR-083)
"""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from promptfw.parsing import extract_json_list

from .models import BookProject, LektoratIssue, LektoratSession, OutlineVersion

logger = logging.getLogger(__name__)


def _get_chapters(project):
    version = OutlineVersion.objects.filter(
        project=project, is_active=True
    ).order_by("-created_at").first()
    if not version:
        return []
    return list(version.nodes.order_by("order"))


class ProjectLektoratView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/lektorat.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        sessions = LektoratSession.objects.filter(project=project).order_by("-created_at")
        chapters = _get_chapters(project)
        ctx["sessions"] = sessions
        ctx["chapters"] = chapters
        ctx["chapter_count"] = len(chapters)
        ctx["latest_session"] = sessions.first()
        return ctx


class LektoratSessionStartView(LoginRequiredMixin, View):
    """Startet eine neue Lektorats-Session per LLM."""

    def post(self, request, pk):
        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        chapters = _get_chapters(project)
        if not chapters:
            messages.warning(request, "Keine Kapitel vorhanden zum Lektorieren.")
            return redirect("projects:lektorat", pk=pk)

        session = LektoratSession.objects.create(
            project=project,
            created_by=request.user,
            name=f"Lektorat {timezone.now().strftime('%d.%m.%Y %H:%M')}",
            status="running",
            chapter_count=len(chapters),
        )

        try:
            router = LLMRouter()
            total_issues = 0
            checked_count = 0

            for node in chapters:
                if not node.content or not node.content.strip():
                    continue
                checked_count += 1
                from apps.core.prompt_utils import render_prompt
                prompt_msgs = render_prompt(
                    "projects/lektorat_analyze",
                    order=node.order,
                    title=node.title,
                    content=node.content,
                )
                try:
                    raw = router.completion(
                        action_code="chapter_analyze",
                        messages=prompt_msgs,
                    )
                    items = extract_json_list(raw)
                    if items:
                        for item in items[:10]:
                            desc = item.get("description", "").strip()
                            if not desc:
                                continue
                            itype = item.get("type", "consistency")
                            if itype not in ("consistency", "logic", "style", "character", "timeline", "pacing"):
                                itype = "consistency"
                            sev = item.get("severity", "warning")
                            if sev not in ("info", "warning", "error"):
                                sev = "warning"
                            LektoratIssue.objects.create(
                                session=session,
                                node=node,
                                issue_type=itype,
                                severity=sev,
                                description=desc,
                                suggestion=item.get("suggestion", ""),
                            )
                            total_issues += 1
                except (LLMRoutingError, Exception) as exc:
                    logger.warning("Lektorat node=%s error: %s", node.pk, exc)
                    continue

            session.status = "done"
            session.issues_found = total_issues
            session.finished_at = timezone.now()
            if checked_count == 0:
                session.summary = (
                    f"Keine Kapitel mit Inhalt gefunden ({len(chapters)} Kapitel vorhanden, "
                    f"aber keines hat Text). Bitte zuerst Kapitel schreiben."
                )
                session.save(update_fields=["status", "issues_found", "finished_at", "summary"])
                messages.warning(request, "Lektorat: Keine Kapitel mit Text gefunden — bitte zuerst Kapitel schreiben.")
            else:
                session.summary = f"{total_issues} Probleme in {checked_count}/{len(chapters)} Kapiteln gefunden."
                session.save(update_fields=["status", "issues_found", "finished_at", "summary"])
                messages.success(request, f"Lektorat abgeschlossen: {total_issues} Probleme in {checked_count} Kapiteln gefunden.")

        except Exception as exc:
            logger.exception("LektoratSessionStart error: %s", exc)
            session.status = "error"
            session.save(update_fields=["status"])
            messages.error(request, f"Fehler beim Lektorat: {exc}")

        return redirect("projects:lektorat_session", pk=pk, session_pk=session.pk)


class LektoratSessionDetailView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/lektorat_session.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session_pk = self.kwargs["session_pk"]
        session = get_object_or_404(LektoratSession, pk=session_pk, project=self.object)
        issues = LektoratIssue.objects.filter(session=session).select_related("node").order_by(
            "node__order", "-severity"
        )
        issue_map = {}
        for issue in issues:
            issue_map.setdefault(str(issue.node_id), []).append(issue)
        ctx["session"] = session
        ctx["issues"] = issues
        ctx["issue_map"] = issue_map
        ctx["open_count"] = issues.filter(is_resolved=False).count()
        ctx["resolved_count"] = issues.filter(is_resolved=True).count()
        ctx["error_count"] = issues.filter(severity="error", is_resolved=False).count()
        ctx["warning_count"] = issues.filter(severity="warning", is_resolved=False).count()
        return ctx


class LektoratIssueResolveView(LoginRequiredMixin, View):
    """Problem als gelöst markieren (AJAX toggle)."""

    def post(self, request, pk, issue_pk):
        issue = get_object_or_404(
            LektoratIssue, pk=issue_pk,
            session__project__owner=request.user,
        )
        issue.is_resolved = not issue.is_resolved
        issue.save(update_fields=["is_resolved"])
        return JsonResponse({"ok": True, "is_resolved": issue.is_resolved})
