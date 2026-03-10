"""
Manuscript — Lese-Ansicht des kompletten Manuskripts (ADR-083)

Zeigt: Hero-Header, Statistiken, Inhaltsverzeichnis, Kapitel-Inhalt.
Kapiteltext liegt in OutlineNode.content.
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from .models import BookProject, OutlineVersion


class ProjectManuscriptView(LoginRequiredMixin, DetailView):
    """Manuskript-Lese-Ansicht: komplettes Buch auf einer Seite."""

    model = BookProject
    template_name = "projects/manuscript.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object

        active_outline = OutlineVersion.objects.filter(
            project=project, is_active=True
        ).order_by("-created_at").first()

        chapters = []
        total_words = 0

        if active_outline:
            for node in active_outline.nodes.order_by("order"):
                wc = node.word_count or (len(node.content.split()) if node.content else 0)
                total_words += wc
                chapters.append({
                    "id": str(node.pk),
                    "order": node.order,
                    "title": node.title,
                    "description": node.description,
                    "content": node.content,
                    "word_count": wc,
                    "has_content": bool(node.content and node.content.strip()),
                })

        pages = max(1, total_words // 250) if total_words else 0
        reading_minutes = max(1, total_words // 200) if total_words else 0

        ctx["chapters"] = chapters
        ctx["chapter_count"] = len(chapters)
        ctx["total_words"] = total_words
        ctx["pages"] = pages
        ctx["reading_minutes"] = reading_minutes
        ctx["chapters_written"] = sum(1 for c in chapters if c["has_content"])
        ctx["active_outline"] = active_outline

        genre = ""
        if hasattr(project, "genre_lookup") and project.genre_lookup:
            genre = project.genre_lookup.name
        elif project.genre:
            genre = project.genre
        ctx["genre"] = genre

        return ctx
