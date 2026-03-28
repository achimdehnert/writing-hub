"""
Knowledge Views — Recherche-Notizen + Beta-Leser (ADR-160)
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import (
    BetaReaderFeedback,
    BetaReaderSession,
    BookProject,
    ResearchNote,
)


class ResearchDashboardView(LoginRequiredMixin, View):
    """Recherche-Notizen eines Projekts verwalten (ADR-160)."""

    template_name = "projects/research_dashboard.html"

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        notes = ResearchNote.objects.filter(project=project).order_by(
            "-is_verified", "note_type", "sort_order"
        )
        return render(request, self.template_name, {
            "project": project,
            "notes": notes,
            "note_type_choices": ResearchNote.NOTE_TYPES,
        })

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        action = request.POST.get("action", "")

        if action == "add_note":
            ResearchNote.objects.create(
                project=project,
                note_type=request.POST.get("note_type", "fact"),
                title=request.POST.get("title", ""),
                content=request.POST.get("content", ""),
                source=request.POST.get("source", ""),
                is_verified=bool(request.POST.get("is_verified")),
                is_open_question=bool(request.POST.get("is_open_question")),
                sort_order=ResearchNote.objects.filter(project=project).count(),
            )
            messages.success(request, "Recherche-Notiz hinzugefügt.")

        elif action == "toggle_verified":
            note_id = request.POST.get("note_id")
            note = get_object_or_404(ResearchNote, pk=note_id, project=project)
            note.is_verified = not note.is_verified
            note.save(update_fields=["is_verified"])
            messages.success(request, "Status aktualisiert.")

        elif action == "delete_note":
            note_id = request.POST.get("note_id")
            ResearchNote.objects.filter(pk=note_id, project=project).delete()
            messages.success(request, "Notiz entfernt.")

        return redirect("projects:research_dashboard", pk=pk)


class BetaReaderDashboardView(LoginRequiredMixin, View):
    """Beta-Leser-Sessions verwalten (ADR-160)."""

    template_name = "projects/beta_dashboard.html"

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        sessions = BetaReaderSession.objects.filter(project=project).order_by(
            "-created_at"
        )
        return render(request, self.template_name, {
            "project": project,
            "sessions": sessions,
            "anon_choices": BetaReaderSession.ANON_CHOICES,
            "focus_choices": BetaReaderSession.FEEDBACK_FOCUS,
        })

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk)
        action = request.POST.get("action", "")

        if action == "add_session":
            BetaReaderSession.objects.create(
                project=project,
                name=request.POST.get("name", "Beta-Runde"),
                reader_name=request.POST.get("reader_name", ""),
                feedback_focus=request.POST.get("feedback_focus", "general"),
                anonymization=request.POST.get("anonymization", "anon_meta"),
            )
            messages.success(request, "Beta-Leser-Session erstellt.")

        return redirect("projects:beta_dashboard", pk=pk)


class BetaReaderSessionDetailView(LoginRequiredMixin, View):
    """Einzelne Beta-Leser-Session + Feedback (ADR-160)."""

    template_name = "projects/beta_session.html"

    def get(self, request, pk, session_pk):
        project = get_object_or_404(BookProject, pk=pk)
        session = get_object_or_404(BetaReaderSession, pk=session_pk, project=project)
        feedbacks = session.feedbacks.order_by("chapter_order", "feedback_type")
        return render(request, self.template_name, {
            "project": project,
            "session": session,
            "feedbacks": feedbacks,
            "feedback_type_choices": BetaReaderFeedback.FEEDBACK_TYPES,
        })

    def post(self, request, pk, session_pk):
        project = get_object_or_404(BookProject, pk=pk)
        session = get_object_or_404(BetaReaderSession, pk=session_pk, project=project)
        action = request.POST.get("action", "")

        if action == "add_feedback":
            BetaReaderFeedback.objects.create(
                session=session,
                feedback_type=request.POST.get("feedback_type", "general"),
                text=request.POST.get("text", ""),
                text_reference=request.POST.get("text_reference", ""),
                chapter_order=request.POST.get("chapter_order") or None,
            )
            messages.success(request, "Feedback hinzugefügt.")

        elif action == "toggle_addressed":
            fb_id = request.POST.get("feedback_id")
            fb = get_object_or_404(BetaReaderFeedback, pk=fb_id, session=session)
            fb.is_addressed = not fb.is_addressed
            fb.save(update_fields=["is_addressed"])

        elif action == "complete_session":
            from django.utils import timezone
            session.is_completed = True
            session.completed_at = timezone.now()
            session.save(update_fields=["is_completed", "completed_at"])
            messages.success(request, "Session als abgeschlossen markiert.")

        return redirect("projects:beta_session", pk=pk, session_pk=session_pk)
