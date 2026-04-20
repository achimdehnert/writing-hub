"""
Versionierung — Manuskript-Snapshots (Komplettstand sichern)

Ein Snapshot speichert den kompletten Inhalt aller Kapitel des aktiven
Outlines als JSON. Max. 10 Snapshots pro Projekt (FIFO).
"""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView

from .models import BookProject, ManuscriptSnapshot, OutlineVersion

MAX_SNAPSHOTS = 10


def _collect_snapshot_data(project: BookProject) -> dict:
    """Sammelt aktuellen Stand aller Kapitel des aktiven Outlines."""
    active_outline = OutlineVersion.objects.filter(project=project, is_active=True).order_by("-created_at").first()

    if not active_outline:
        return {"outline_id": None, "outline_name": "", "chapters": [], "word_count": 0}

    chapters = []
    total_words = 0
    for node in active_outline.nodes.order_by("order"):
        wc = node.word_count or (len(node.content.split()) if node.content else 0)
        total_words += wc
        chapters.append(
            {
                "id": str(node.pk),
                "order": node.order,
                "title": node.title,
                "description": node.description,
                "beat_type": node.beat_type,
                "content": node.content,
                "word_count": wc,
            }
        )

    return {
        "outline_id": str(active_outline.pk),
        "outline_name": active_outline.name,
        "chapters": chapters,
        "word_count": total_words,
    }


class ProjectVersionsView(LoginRequiredMixin, DetailView):
    """Uebersicht aller Snapshots eines Projekts."""

    model = BookProject
    template_name = "projects/versions.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        data = _collect_snapshot_data(self.object)
        snapshots = ManuscriptSnapshot.objects.filter(project=self.object)
        ctx["snapshots"] = snapshots
        ctx["snapshot_count"] = snapshots.count()
        ctx["max_snapshots"] = MAX_SNAPSHOTS
        ctx["current_chapter_count"] = len(data["chapters"])
        ctx["current_word_count"] = data["word_count"]
        ctx["can_create"] = snapshots.count() < MAX_SNAPSHOTS
        return ctx


class SnapshotCreateView(LoginRequiredMixin, View):
    """POST — erstellt neuen Snapshot vom aktuellen Stand."""

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        name = request.POST.get("name", "").strip()
        notes = request.POST.get("notes", "").strip()

        # FIFO: aeltesten loeschen wenn Limit erreicht
        existing = ManuscriptSnapshot.objects.filter(project=project).order_by("created_at")
        while existing.count() >= MAX_SNAPSHOTS:
            existing.first().delete()
            existing = ManuscriptSnapshot.objects.filter(project=project).order_by("created_at")

        data = _collect_snapshot_data(project)

        if not name:
            from django.utils.timezone import now

            name = f"Snapshot {now().strftime('%d.%m.%Y %H:%M')}"

        ManuscriptSnapshot.objects.create(
            project=project,
            created_by=request.user,
            name=name,
            notes=notes,
            chapter_count=len(data["chapters"]),
            word_count=data["word_count"],
            data=data,
        )
        return redirect("projects:versions", pk=pk)


class SnapshotDeleteView(LoginRequiredMixin, View):
    """POST — loescht einen Snapshot (AJAX oder normal)."""

    def post(self, request, pk, snapshot_pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        snapshot = get_object_or_404(ManuscriptSnapshot, pk=snapshot_pk, project=project)
        snapshot.delete()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True})
        return redirect("projects:versions", pk=pk)


class SnapshotDetailView(LoginRequiredMixin, DetailView):
    """Zeigt gespeicherten Snapshot-Inhalt."""

    model = ManuscriptSnapshot
    template_name = "projects/snapshot_detail.html"
    context_object_name = "snapshot"
    pk_url_kwarg = "snapshot_pk"

    def get_object(self, queryset=None):
        return get_object_or_404(
            ManuscriptSnapshot,
            pk=self.kwargs["snapshot_pk"],
            project__owner=self.request.user,
            project__pk=self.kwargs["pk"],
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        ctx["chapters"] = self.object.data.get("chapters", [])
        return ctx
