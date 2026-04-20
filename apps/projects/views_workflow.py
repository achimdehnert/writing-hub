"""
Projects — Workflow Views (UC 6.1a Rollenwechsel, UC 6.4 Checkliste, UC 6.5 Notizen)
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .models import (
    BookProject,
    ChapterNote,
    OutlineNode,
    PhaseChecklistItem,
)

logger = logging.getLogger(__name__)

PHASE_DEFINITIONS = [
    {
        "key": "concept",
        "label": "Konzept & Planung",
        "icon": "bi-lightbulb",
        "role": "autor",
        "default_checklist": [
            "Prämisse formuliert",
            "Zielgruppe definiert",
            "Outline erstellt",
        ],
    },
    {
        "key": "research",
        "label": "Recherche",
        "icon": "bi-search",
        "role": "autor",
        "default_checklist": [
            "Quellen gesammelt",
            "Fakten geprüft",
            "Weltenbau/Charaktere angelegt",
        ],
    },
    {
        "key": "writing",
        "label": "Schreiben",
        "icon": "bi-pen",
        "role": "autor",
        "default_checklist": [
            "Alle Kapitel geschrieben",
            "Wortziel erreicht",
            "Batch-Durchlauf abgeschlossen",
        ],
    },
    {
        "key": "review",
        "label": "Lektorat & Review",
        "icon": "bi-chat-left-text",
        "role": "lektor",
        "default_checklist": [
            "KI-Lektorat durchgeführt",
            "Review-Findings bearbeitet",
            "Konsistenzprüfung bestanden",
        ],
    },
    {
        "key": "production",
        "label": "Publikation & Export",
        "icon": "bi-book",
        "role": "verleger",
        "default_checklist": [
            "Publishing-Profil geprüft",
            "PDF-Export erstellt",
            "EPUB-Export erstellt",
            "ISBN eingetragen",
        ],
    },
]

PHASE_MAP = {p["key"]: p for p in PHASE_DEFINITIONS}


def _ensure_checklist(project):
    """Legt Default-Checkliste an, falls noch keine Items existieren."""
    if project.checklist_items.exists():
        return
    items = []
    for phase_def in PHASE_DEFINITIONS:
        for i, label in enumerate(phase_def["default_checklist"]):
            items.append(
                PhaseChecklistItem(
                    project=project,
                    phase=phase_def["key"],
                    label=label,
                    order=i,
                )
            )
    PhaseChecklistItem.objects.bulk_create(items)


class ProjectWorkflowView(LoginRequiredMixin, View):
    """UC 6.1a: Phasen-Übersicht mit Rollenwechsel + Checkliste."""

    template_name = "projects/workflow.html"

    def get(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        _ensure_checklist(project)

        checklist = project.checklist_items.all()
        phases = []
        for phase_def in PHASE_DEFINITIONS:
            items = [c for c in checklist if c.phase == phase_def["key"]]
            total = len(items)
            checked = sum(1 for c in items if c.is_checked)
            phases.append(
                {
                    **phase_def,
                    "items": items,
                    "total": total,
                    "checked": checked,
                    "progress_pct": round(checked / total * 100) if total else 0,
                    "is_complete": total > 0 and checked == total,
                }
            )

        milestones = project.milestones.filter(is_completed=False).order_by("due_date")[:5]

        active_role = request.GET.get("role", "autor")
        active_phase = None
        for p in phases:
            if p["role"] == active_role and not p["is_complete"]:
                active_phase = p
                break
        if not active_phase and phases:
            active_phase = phases[0]

        return render(
            request,
            self.template_name,
            {
                "project": project,
                "phases": phases,
                "active_phase": active_phase,
                "active_role": active_role,
                "roles": [
                    ("autor", "Autor", "bi-pen"),
                    ("lektor", "Lektor", "bi-chat-left-text"),
                    ("verleger", "Verleger", "bi-book"),
                ],
                "milestones": milestones,
            },
        )


class ChecklistToggleView(LoginRequiredMixin, View):
    """POST: Checkpunkt umschalten."""

    def post(self, request, pk, item_pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        item = get_object_or_404(PhaseChecklistItem, pk=item_pk, project=project)
        if item.is_checked:
            item.is_checked = False
            item.checked_at = None
        else:
            item.is_checked = True
            item.checked_at = timezone.now()
        item.save(update_fields=["is_checked", "checked_at"])
        return redirect("projects:workflow", pk=pk)


class ChecklistAddView(LoginRequiredMixin, View):
    """POST: Eigenen Checkpunkt hinzufügen."""

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        label = request.POST.get("label", "").strip()
        phase = request.POST.get("phase", "writing")
        if label:
            max_order = (
                project.checklist_items.filter(phase=phase).order_by("-order").values_list("order", flat=True).first()
                or 0
            )
            PhaseChecklistItem.objects.create(
                project=project,
                phase=phase,
                label=label,
                order=max_order + 1,
            )
        return redirect("projects:workflow", pk=pk)


# =====================================================================
# UC 6.5: ChapterNote CRUD
# =====================================================================


class ChapterNoteAddView(LoginRequiredMixin, View):
    """POST: Notiz an Kapitel anhängen."""

    def post(self, request, pk, node_pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        node = get_object_or_404(
            OutlineNode,
            pk=node_pk,
            outline_version__project=project,
        )
        content = request.POST.get("content", "").strip()
        role = request.POST.get("role", "autor")
        if content:
            ChapterNote.objects.create(
                node=node,
                created_by=request.user,
                role=role,
                content=content,
            )
            messages.success(request, "Notiz gespeichert.")
        return redirect("projects:node_content", node_pk=node.pk)


class ChapterNoteResolveView(LoginRequiredMixin, View):
    """POST: Notiz als erledigt markieren."""

    def post(self, request, pk, note_pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        note = get_object_or_404(
            ChapterNote,
            pk=note_pk,
            node__outline_version__project=project,
        )
        note.is_resolved = not note.is_resolved
        note.save(update_fields=["is_resolved"])
        return redirect("projects:node_content", node_pk=note.node.pk)
