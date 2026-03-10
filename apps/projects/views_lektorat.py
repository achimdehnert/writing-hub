"""
Lektorat — Prüfungs-Framework (ADR-083)
"""
import json
import logging
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView

from .models import BookProject, OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)


def _get_chapters_with_content(project):
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
        from .models import LektoratSession
        project = self.object
        chapters = _get_chapters_with_content(project)
        chapters_with_content = [c for c in chapters if c.content and c.content.strip()]
        sessions = LektoratSession.objects.filter(project=project).order_by("-created_at")
        ctx["chapters"] = chapters
        ctx["chapter_count"] = len(chapters)
        ctx["chapters_with_content"] = len(chapters_with_content)
        ctx["sessions"] = sessions
        ctx["session_count"] = sessions.count()
        ctx["next_session_name"] = f"Lektorat {sessions.count() + 1}"
        return ctx


class LektoratSessionDetailView(LoginRequiredMixin, DetailView):
    model = BookProject
    template_name = "projects/lektorat_session.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import LektoratSession
        session = get_object_or_404(
            LektoratSession,
            pk=self.kwargs["session_pk"],
            project=self.object,
        )
        issues = session.issues.select_related("node").order_by("node__order", "-severity")
        ctx["session"] = session
        ctx["issues"] = issues
        ctx["open_issues"] = issues.filter(is_resolved=False)
        ctx["resolved_issues"] = issues.filter(is_resolved=True)
        by_chapter = {}
        for issue in issues:
            by_chapter.setdefault(str(issue.node_id), []).append(issue)
        ctx["issues_by_chapter"] = by_chapter
        return ctx


class LektoratSessionStartView(LoginRequiredMixin, View):
    """Startet eine neue Lektorats-Prüfung."""

    def post(self, request, pk):
        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
        from .models import LektoratIssue, LektoratSession

        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip() or "Lektorat"
        chapters = _get_chapters_with_content(project)
        chapters_with_content = [c for c in chapters if c.content and c.content.strip()]

        if not chapters_with_content:
            messages.warning(request, "Keine Kapitel mit Inhalt vorhanden.")
            return redirect("projects:lektorat", pk=pk)

        session = LektoratSession.objects.create(
            project=project,
            created_by=request.user,
            name=name,
            status="running",
            chapter_count=len(chapters_with_content),
        )

        SYSTEM_PROMPT = (
            "Du bist ein professioneller Lektor der ein Manuskript pr\u00fcft.\n"
            "Analysiere das Kapitel auf: Konsistenz, Logikfehler, Charakterkonsistenz, "
            "Zeitlinie, Pacing, Stilprobleme.\n"
            "Antworte AUSSCHLIESSLICH als JSON-Array:\n"
            "[{\"type\": \"consistency|logic|style|character|timeline|pacing\",\n"
            "  \"severity\": \"info|warning|error\",\n"
            "  \"description\": \"Was ist das Problem...\",\n"
            "  \"suggestion\": \"Wie k\u00f6nnte es behoben werden...\"}]\n"
            "Wenn keine Probleme gefunden werden, antworte mit leerem Array: []"
        )

        total_issues = 0
        errors = []

        try:
            router = LLMRouter()
            for chapter in chapters_with_content:
                user_prompt = (
                    f"Kapitel {chapter.order}: {chapter.title}\n"
                    f"Beat: {chapter.beat_phase or ''}\n\n"
                    f"{chapter.content[:6000]}"
                )
                try:
                    raw = router.completion(
                        action_code="chapter_analyze",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    )
                    match = re.search(r"\[.*?\]", raw, re.DOTALL)
                    if match:
                        items = json.loads(match.group())
                        for item in items[:8]:
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
                                node=chapter,
                                issue_type=itype,
                                severity=sev,
                                description=desc,
                                suggestion=item.get("suggestion", ""),
                            )
                            total_issues += 1
                except Exception as exc:
                    logger.warning("Lektorat chapter %s error: %s", chapter.order, exc)
                    errors.append(f"Kapitel {chapter.order}: {exc}")

            session.status = "done"
            session.issues_found = total_issues
            session.finished_at = timezone.now()
            if errors:
                session.summary = f"{total_issues} Probleme gefunden. Fehler bei: {', '.join(errors[:3])}"
            else:
                session.summary = f"{total_issues} Probleme in {len(chapters_with_content)} Kapiteln gefunden."
            session.save()
            messages.success(request, f'„{name}\u201c abgeschlossen: {total_issues} Probleme gefunden.')

        except LLMRoutingError as exc:
            session.status = "error"
            session.save()
            messages.warning(request, f"KI nicht verf\u00fcgbar: {exc}")
        except Exception as exc:
            logger.exception("LektoratSessionStart error pk=%s: %s", pk, exc)
            session.status = "error"
            session.save()
            messages.error(request, f"Fehler: {exc}")

        return redirect("projects:lektorat_session", pk=pk, session_pk=session.pk)


class LektoratIssueResolveView(LoginRequiredMixin, View):
    def post(self, request, pk, issue_pk):
        from .models import LektoratIssue
        issue = get_object_or_404(
            LektoratIssue,
            pk=issue_pk,
            session__project__owner=request.user,
        )
        issue.is_resolved = not issue.is_resolved
        issue.save(update_fields=["is_resolved"])
        return JsonResponse({"ok": True, "is_resolved": issue.is_resolved})
