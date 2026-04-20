"""
Project Import — Markdown-Dateien als Buchprojekt importieren (ADR-083)

Unterstützte Formate:
  - Manuskript:    Kapitel mit "# KAPITEL X: Titel" oder "## Chapter X" Markern
  - Planungsdok:  Beat-Sheets, Charakterbögen, Story-Arcs (Heading-Struktur)
  - Gemischt:     Kombination aus Prosa und Metadaten
"""

from __future__ import annotations

import logging
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from .models import BookProject, OutlineNode, OutlineVersion

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Markdown Parser
# ---------------------------------------------------------------------------

_CH_PATTERNS = [
    re.compile(r"^#{1,3}\s+KAPITEL\s+(\d+)\s*[:\-\u2013\u2014]?\s*(.*)$", re.IGNORECASE),
    re.compile(r"^#{1,3}\s+Kapitel\s+(\d+)\s*[:\-\u2013\u2014]?\s*(.*)$", re.IGNORECASE),
    re.compile(r"^#{1,3}\s+Chapter\s+(\d+)\s*[:\-\u2013\u2014]?\s*(.*)$", re.IGNORECASE),
    re.compile(r"^#{1,3}\s+(\d+)\.\s+(.+)$"),
]


def _detect_format(text: str) -> str:
    lines = text.splitlines()
    chapter_hits = 0
    plan_hits = 0
    has_prose = False
    for line in lines:
        if any(p.match(line) for p in _CH_PATTERNS):
            chapter_hits += 1
        elif re.match(r"^#{1,4}\s+(.+)$", line):
            plan_hits += 1
        elif len(line.strip()) > 60:
            has_prose = True
    if chapter_hits >= 2:
        return "manuscript"
    if plan_hits >= 3 and not has_prose:
        return "planning"
    return "mixed"


def _extract_title_from_filename(filename: str) -> str:
    name = filename
    for ext in (".md", ".txt", ".markdown"):
        name = name.replace(ext, "")
    name = re.sub(r"_\d{8}_\d{6}$", "", name)
    name = re.sub(r"_complete$", "", name, flags=re.IGNORECASE)
    name = name.replace("_", " ").replace("-", " ").strip()
    return name.title() if name.islower() else name


def _parse_manuscript(text: str) -> list[dict]:
    chapters = []
    current_title = None
    current_order = 0
    current_lines = []

    for line in text.splitlines():
        matched = None
        for p in _CH_PATTERNS:
            m = p.match(line)
            if m:
                matched = m
                break

        if matched:
            if current_title is not None:
                chapters.append(
                    {
                        "order": current_order,
                        "title": current_title,
                        "content": "\n".join(current_lines).strip(),
                    }
                )
            try:
                current_order = int(matched.group(1))
            except (IndexError, ValueError):
                current_order = len(chapters) + 1
            title_part = matched.group(2).strip() if matched.lastindex >= 2 else ""
            current_title = title_part or f"Kapitel {current_order}"
            current_lines = []
        else:
            if current_title is not None:
                current_lines.append(line)

    if current_title is not None:
        chapters.append(
            {
                "order": current_order,
                "title": current_title,
                "content": "\n".join(current_lines).strip(),
            }
        )

    return chapters


def _parse_planning(text: str) -> list[dict]:
    sections = []
    current_title = None
    current_lines = []
    order = 1

    for line in text.splitlines():
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            depth = len(m.group(1))
            if depth <= 2:
                if current_title is not None:
                    sections.append(
                        {
                            "order": order,
                            "title": current_title,
                            "content": "\n".join(current_lines).strip(),
                        }
                    )
                    order += 1
                current_title = m.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)
        else:
            if current_title is not None:
                current_lines.append(line)

    if current_title is not None:
        sections.append(
            {
                "order": order,
                "title": current_title,
                "content": "\n".join(current_lines).strip(),
            }
        )

    return sections


def parse_markdown(filename: str, text: str) -> dict:
    fmt = _detect_format(text)
    if fmt == "manuscript":
        chapters = _parse_manuscript(text)
    elif fmt == "planning":
        chapters = _parse_planning(text)
    else:
        chapters = _parse_manuscript(text)
        if len(chapters) < 2:
            chapters = _parse_planning(text)

    title = _extract_title_from_filename(filename)

    if not chapters:
        chapters = [{"order": 1, "title": title or "Inhalt", "content": text.strip()}]

    return {
        "title": title,
        "format": fmt,
        "chapters": chapters,
        "word_count": sum(len(ch["content"].split()) for ch in chapters),
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class ProjectImportView(LoginRequiredMixin, View):
    """
    GET  — zeigt Import-Formular
    POST — verarbeitet hochgeladene .md Dateien und legt Projekt an
    """

    template_name = "projects/import.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        action = request.POST.get("action", "create")
        if action == "preview":
            return self._handle_preview(request)
        return self._handle_create(request)

    def _handle_preview(self, request):
        files = request.FILES.getlist("files")
        if not files:
            return JsonResponse({"ok": False, "error": "Keine Dateien hochgeladen."})

        results = []
        for f in files:
            try:
                text = f.read().decode("utf-8", errors="replace")
                parsed = parse_markdown(f.name, text)
                results.append(
                    {
                        "filename": f.name,
                        "title": parsed["title"],
                        "format": parsed["format"],
                        "chapter_count": len(parsed["chapters"]),
                        "word_count": parsed["word_count"],
                        "chapters": [
                            {
                                "order": ch["order"],
                                "title": ch["title"],
                                "preview": ch["content"][:200] + "..." if len(ch["content"]) > 200 else ch["content"],
                            }
                            for ch in parsed["chapters"]
                        ],
                    }
                )
            except Exception as exc:
                logger.warning("Import preview error file=%s: %s", f.name, exc)
                results.append({"filename": f.name, "error": str(exc)})
        return JsonResponse({"ok": True, "files": results})

    def _handle_create(self, request):
        files = request.FILES.getlist("files")
        if not files:
            messages.warning(request, "Keine Dateien hochgeladen.")
            return redirect("projects:import")

        created_projects = []

        for f in files:
            try:
                text = f.read().decode("utf-8", errors="replace")
                parsed = parse_markdown(f.name, text)

                title = request.POST.get(f"title_{f.name}", parsed["title"]).strip()
                if not title:
                    title = parsed["title"] or f.name

                project = BookProject.objects.create(
                    owner=request.user,
                    title=title,
                    description=f"Importiert aus: {f.name}",
                )

                fmt_labels = {
                    "manuscript": "Manuskript",
                    "planning": "Planungsdokument",
                    "mixed": "Gemischt",
                }
                version = OutlineVersion.objects.create(
                    project=project,
                    created_by=request.user,
                    name=f"Import: {fmt_labels.get(parsed['format'], 'Import')}",
                    source="import",
                    is_active=True,
                    notes=f"Automatisch importiert aus {f.name}",
                )

                beat_type = "chapter" if parsed["format"] == "manuscript" else "beat"
                nodes = [
                    OutlineNode(
                        outline_version=version,
                        title=ch["title"][:300],
                        content=ch["content"],
                        beat_type=beat_type,
                        order=ch["order"],
                    )
                    for ch in parsed["chapters"]
                ]
                OutlineNode.objects.bulk_create(nodes)
                created_projects.append(project)
                logger.info(
                    "Import OK user=%s project=%s chapters=%d",
                    request.user.username,
                    project.pk,
                    len(parsed["chapters"]),
                )

            except Exception as exc:
                logger.exception("Import create error file=%s: %s", f.name, exc)
                messages.error(request, f"Fehler bei {f.name}: {exc}")

        if len(created_projects) == 1:
            messages.success(
                request,
                f"Projekt \u201e{created_projects[0].title}\u201c erfolgreich importiert.",
            )
            return redirect("projects:detail", pk=created_projects[0].pk)
        elif created_projects:
            messages.success(request, f"{len(created_projects)} Projekte importiert.")
        return redirect("projects:list")
