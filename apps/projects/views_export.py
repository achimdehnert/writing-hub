"""
Export — Manuskript-Export in verschiedene Formate (ADR-083)

Formate: Markdown, Text, HTML, PDF (weasyprint), EPUB (ebooklib)

Kapitelinhalt: OutlineNode.content (primär), ChapterWriteJob.content (Fallback).
"""
from __future__ import annotations

import io
import logging
import textwrap
from datetime import date

logger = logging.getLogger(__name__)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from .models import BookProject, OutlineVersion


def _get_chapters_with_content(project: BookProject) -> list[dict]:
    """
    Gibt alle Kapitel des aktiven Outlines zurück.
    Primärquelle: OutlineNode.content (dort schreibt der Chapter Writer hin).
    Fallback: ChapterWriteJob.content (Legacy-Pfad).
    """
    from apps.authoring.models_jobs import ChapterWriteJob

    active_outline = OutlineVersion.objects.filter(
        project=project, is_active=True
    ).order_by("-created_at").first()

    if not active_outline:
        return []

    nodes = list(active_outline.nodes.order_by("order"))

    done_jobs = {
        j.chapter_ref: j.content
        for j in ChapterWriteJob.objects.filter(
            project=project,
            status="done",
            chapter_ref__in=[str(n.pk) for n in nodes],
        )
    }

    result = []
    for node in nodes:
        content = node.content or done_jobs.get(str(node.pk), "")
        result.append({
            "order": node.order,
            "title": node.title,
            "description": node.description,
            "content": content,
            "has_content": bool(content),
        })
    return result


def _count_words(chapters: list[dict]) -> int:
    total = 0
    for ch in chapters:
        total += len(ch["content"].split()) if ch["content"] else 0
    return total


class ProjectExportView(LoginRequiredMixin, DetailView):
    """GET — zeigt Export-Seite, POST — liefert Download."""

    model = BookProject
    template_name = "projects/export.html"
    context_object_name = "project"

    def get_queryset(self):
        return BookProject.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        chapters = _get_chapters_with_content(self.object)
        ctx["chapters"] = chapters
        ctx["word_count"] = _count_words(chapters)
        ctx["chapter_count"] = len(chapters)
        ctx["page_count"] = max(1, _count_words(chapters) // 250)
        return ctx

    def post(self, request, pk):
        project = get_object_or_404(BookProject, pk=pk, owner=request.user)
        fmt = request.POST.get("format", "markdown")
        include_outline = request.POST.get("include_outline") == "on"
        include_title_page = request.POST.get("include_title_page") == "on"
        only_with_content = request.POST.get("all_chapters") != "on"

        chapters = _get_chapters_with_content(project)
        if only_with_content:
            chapters = [c for c in chapters if c["has_content"]]

        dispatch = {
            "markdown": self._export_markdown,
            "text": self._export_text,
            "html": self._export_html,
            "pdf": self._export_pdf,
            "epub": self._export_epub,
        }
        handler = dispatch.get(fmt, self._export_markdown)
        return handler(project, chapters, include_outline, include_title_page)

    # ------------------------------------------------------------------ #
    #  Markdown                                                            #
    # ------------------------------------------------------------------ #
    def _export_markdown(self, project, chapters, include_outline, include_title_page):
        lines = []
        if include_title_page:
            lines += [f"# {project.title}", ""]
            if project.genre:
                lines += [f"*Genre: {project.genre}*", ""]
            if project.description:
                lines += [project.description, ""]
            lines += [f"*Exportiert am {date.today().strftime('%d.%m.%Y')}*", "", "---", ""]

        for ch in chapters:
            lines += [f"## Kapitel {ch['order']}: {ch['title']}", ""]
            if include_outline and ch["description"]:
                lines += [f"> {ch['description']}", ""]
            if ch["content"]:
                lines += [ch["content"], ""]
            else:
                lines += ["*[Kein Text vorhanden]*", ""]
            lines.append("")

        content = "\n".join(lines)
        response = HttpResponse(content, content_type="text/markdown; charset=utf-8")
        filename = _safe_filename(project.title) + ".md"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # ------------------------------------------------------------------ #
    #  Plain Text                                                          #
    # ------------------------------------------------------------------ #
    def _export_text(self, project, chapters, include_outline, include_title_page):
        lines = []
        if include_title_page:
            lines += [
                project.title.upper(),
                "=" * min(len(project.title), 60),
                "",
            ]
            if project.genre:
                lines += [f"Genre: {project.genre}", ""]
            if project.description:
                lines += [project.description, ""]
            lines += [f"Exportiert am {date.today().strftime('%d.%m.%Y')}", "", ""]

        for ch in chapters:
            header = f"KAPITEL {ch['order']}: {ch['title'].upper()}"
            lines += [header, "-" * min(len(header), 60), ""]
            if include_outline and ch["description"]:
                lines += [f"[Outline: {ch['description']}]", ""]
            if ch["content"]:
                lines += [ch["content"], ""]
            else:
                lines += ["[Kein Text vorhanden]", ""]
            lines.append("")

        content = "\n".join(lines)
        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        filename = _safe_filename(project.title) + ".txt"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # ------------------------------------------------------------------ #
    #  HTML                                                                #
    # ------------------------------------------------------------------ #
    def _export_html(self, project, chapters, include_outline, include_title_page):
        content = self._build_html(project, chapters, include_outline, include_title_page)
        response = HttpResponse(content, content_type="text/html; charset=utf-8")
        filename = _safe_filename(project.title) + ".html"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


    # ------------------------------------------------------------------ #
    #  PDF (via weasyprint)                                               #
    # ------------------------------------------------------------------ #
    def _export_pdf(self, project, chapters, include_outline, include_title_page):
        html_content = self._build_html(project, chapters, include_outline, include_title_page)
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
        except ImportError:
            logger.warning("weasyprint not installed — PDF export unavailable")
            from django.contrib import messages
            messages.error(self.request, "PDF-Export nicht verfügbar (weasyprint fehlt).")
            from django.shortcuts import redirect
            return redirect("projects:export", pk=project.pk)
        except Exception as exc:
            logger.exception("PDF export error: %s", exc)
            from django.contrib import messages
            messages.error(self.request, f"PDF-Export fehlgeschlagen: {exc}")
            from django.shortcuts import redirect
            return redirect("projects:export", pk=project.pk)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = _safe_filename(project.title) + ".pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # ------------------------------------------------------------------ #
    #  EPUB (via ebooklib)                                                #
    # ------------------------------------------------------------------ #
    def _export_epub(self, project, chapters, include_outline, include_title_page):
        try:
            from ebooklib import epub
        except ImportError:
            logger.warning("ebooklib not installed — EPUB export unavailable")
            from django.contrib import messages
            messages.error(self.request, "EPUB-Export nicht verfügbar (ebooklib fehlt).")
            from django.shortcuts import redirect
            return redirect("projects:export", pk=project.pk)

        try:
            book = epub.EpubBook()
            book.set_identifier(f"writing-hub-{project.pk}")
            book.set_title(project.title)
            book.set_language("de")
            if project.owner:
                book.add_author(project.owner.get_full_name() or project.owner.username)

            style = epub.EpubItem(
                uid="style",
                file_name="style/default.css",
                media_type="text/css",
                content="body { font-family: Georgia, serif; line-height: 1.8; } "
                        "h1 { font-size: 2rem; margin-bottom: 1rem; } "
                        "h2 { font-size: 1.3rem; margin-top: 2rem; border-bottom: 1px solid #ccc; padding-bottom: .25rem; } "
                        "p { margin: 0 0 1rem; text-indent: 1.5rem; } "
                        ".outline { color: #555; font-style: italic; } "
                        ".no-content { color: #999; font-style: italic; }",
            )
            book.add_item(style)

            spine = ["nav"]
            toc = []

            if include_title_page:
                title_html = f"<h1>{_esc(project.title)}</h1>"
                if project.genre:
                    title_html += f'<p style="color:#555;">Genre: {_esc(project.genre)}</p>'
                if project.description:
                    title_html += f"<p>{_esc(project.description)}</p>"
                title_html += f'<p style="color:#777;font-size:.9rem;">Exportiert am {date.today().strftime("%d.%m.%Y")}</p>'
                title_ch = epub.EpubHtml(title="Titelseite", file_name="title.xhtml", lang="de")
                title_ch.content = title_html
                title_ch.add_item(style)
                book.add_item(title_ch)
                spine.append(title_ch)

            for idx, ch in enumerate(chapters, 1):
                body = f"<h2>Kapitel {ch['order']}: {_esc(ch['title'])}</h2>"
                if include_outline and ch["description"]:
                    body += f'<p class="outline">{_esc(ch["description"])}</p>'
                if ch["content"]:
                    for para in ch["content"].split("\n\n"):
                        para = para.strip()
                        if para:
                            body += f"<p>{_esc(para)}</p>"
                else:
                    body += '<p class="no-content">[Kein Text vorhanden]</p>'

                epub_ch = epub.EpubHtml(
                    title=f"Kapitel {ch['order']}: {ch['title']}",
                    file_name=f"chapter_{idx:03d}.xhtml",
                    lang="de",
                )
                epub_ch.content = body
                epub_ch.add_item(style)
                book.add_item(epub_ch)
                spine.append(epub_ch)
                toc.append(epub.Link(f"chapter_{idx:03d}.xhtml", f"Kapitel {ch['order']}: {ch['title']}", f"ch{idx}"))

            book.toc = toc
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = spine

            buf = io.BytesIO()
            epub.write_epub(buf, book)
            buf.seek(0)
        except Exception as exc:
            logger.exception("EPUB export error: %s", exc)
            from django.contrib import messages
            messages.error(self.request, f"EPUB-Export fehlgeschlagen: {exc}")
            from django.shortcuts import redirect
            return redirect("projects:export", pk=project.pk)

        response = HttpResponse(buf.read(), content_type="application/epub+zip")
        filename = _safe_filename(project.title) + ".epub"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # ------------------------------------------------------------------ #
    #  Shared HTML builder (used by HTML export + PDF)                     #
    # ------------------------------------------------------------------ #
    def _build_html(self, project, chapters, include_outline, include_title_page):
        parts = [textwrap.dedent(f"""\
            <!DOCTYPE html>
            <html lang="de">
            <head>
            <meta charset="UTF-8">
            <title>{_esc(project.title)}</title>
            <style>
              @page {{ size: A4; margin: 2.5cm; }}
              body {{ font-family: Georgia, serif; max-width: 780px; margin: 3rem auto; line-height: 1.8; color: #1a1a1a; }}
              h1 {{ font-size: 2.2rem; margin-bottom: .25rem; }}
              h2 {{ font-size: 1.4rem; margin-top: 3rem; border-bottom: 1px solid #ccc; padding-bottom: .25rem; }}
              .outline {{ color: #555; font-style: italic; margin-bottom: 1rem; }}
              .no-content {{ color: #999; font-style: italic; }}
              .meta {{ color: #777; font-size: .9rem; }}
              hr {{ border: none; border-top: 1px solid #ddd; margin: 2rem 0; }}
              p {{ margin: 0 0 1rem; text-indent: 1.5rem; }}
            </style>
            </head>
            <body>
        """)]

        if include_title_page:
            parts.append(f"<h1>{_esc(project.title)}</h1>")
            if project.genre:
                parts.append(f'<p class="meta">Genre: {_esc(project.genre)}</p>')
            if project.description:
                parts.append(f"<p>{_esc(project.description)}</p>")
            parts.append(f'<p class="meta">Exportiert am {date.today().strftime("%d.%m.%Y")}</p><hr>')

        for ch in chapters:
            parts.append(f"<h2>Kapitel {ch['order']}: {_esc(ch['title'])}</h2>")
            if include_outline and ch["description"]:
                parts.append(f'<p class="outline">{_esc(ch["description"])}</p>')
            if ch["content"]:
                for para in ch["content"].split("\n\n"):
                    para = para.strip()
                    if para:
                        parts.append(f"<p>{_esc(para)}</p>")
            else:
                parts.append('<p class="no-content">[Kein Text vorhanden]</p>')

        parts.append("</body></html>")
        return "\n".join(parts)


def _safe_filename(title: str) -> str:
    import re
    name = re.sub(r"[^\w\s-]", "", title).strip()
    name = re.sub(r"[\s]+", "_", name)
    return name[:60] or "manuskript"


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )
