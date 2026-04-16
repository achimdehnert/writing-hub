"""
Citation Views — DOI/ISBN Lookup, BibTeX Import, Bibliography
für akademische/wissenschaftliche BookProjects.

Quellen werden in ProjectCitation (DB) gespeichert (Issue #8).
"""
from __future__ import annotations

import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .constants import (
    BIBLIOGRAPHY_STYLES,
    FORMAT_PROFILES,
    SEARCH_SOURCES,
    VALID_SEARCH_SOURCES,
)
from .models import BookProject, OutlineNode, OutlineVersion, ProjectCitation
from .services.citation_service import (
    export_bibtex,
    format_bibliography,
    parse_bibtex,
    resolve_doi,
    resolve_isbn,
    search_papers,
    smart_search_papers,
)

logger = logging.getLogger(__name__)


def _model_to_dict(c: ProjectCitation) -> dict:
    """Convert ProjectCitation model to dict for format_bibliography compatibility."""
    return {
        "title": c.title,
        "authors": c.authors_json or [],
        "year": c.year,
        "source_type": c.source_type,
        "journal": c.journal,
        "volume": c.volume,
        "issue": c.issue,
        "pages": c.pages,
        "publisher": c.publisher,
        "doi": c.doi,
        "url": c.url,
        "abstract": c.abstract,
        "keywords": c.keywords or [],
    }


def _create_citation_from_dict(project, data, added_via="manual"):
    """Create ProjectCitation from a citation dict. Returns (citation, created)."""
    doi = data.get("doi") or ""
    title = data.get("title") or ""

    if doi:
        existing = ProjectCitation.objects.filter(project=project, doi=doi).first()
        if existing:
            return existing, False
    if title:
        existing = ProjectCitation.objects.filter(project=project, title=title).first()
        if existing:
            return existing, False

    if not title:
        return None, False

    authors = data.get("authors") or []
    year_raw = data.get("year")
    if year_raw is None and data.get("publication_date"):
        y = str(data["publication_date"])[:4]
        year_raw = int(y) if y.isdigit() else None

    try:
        citation = ProjectCitation.objects.create(
            project=project,
            title=title,
            authors_json=authors if authors else [],
            year=int(year_raw) if year_raw else None,
            doi=doi,
            url=data.get("url") or "",
            abstract=data.get("abstract") or "",
            source_type=data.get("source_type") or "journal",
            journal=data.get("journal") or "",
            volume=data.get("volume") or "",
            issue=data.get("issue") or "",
            pages=data.get("pages") or "",
            publisher=data.get("publisher") or "",
            keywords=data.get("keywords") or [],
            added_via=added_via,
        )
        return citation, True
    except IntegrityError:
        existing = ProjectCitation.objects.filter(project=project, doi=doi).first()
        return existing, False


class CitationDashboardView(LoginRequiredMixin, View):
    """Zitations-Dashboard für ein akademisches/wissenschaftliches Projekt."""

    template_name = "projects/citations.html"

    def _get_project(self, request, pk):
        return get_object_or_404(
            BookProject, pk=pk, owner=request.user, is_active=True
        )

    def _get_chapters(self, project):
        """Return active outline nodes for chapter assignment."""
        active_outline = OutlineVersion.objects.filter(
            project=project, is_active=True
        ).order_by("-created_at").first()
        if not active_outline:
            return [], False
        nodes = list(
            active_outline.nodes.order_by("order")
            .values_list("pk", "order", "title", "research_queries")
        )
        has_queries = any(rq for _, _, _, rq in nodes)
        return nodes, has_queries

    def _render(self, request, project, style=None):
        """Render citations dashboard with current DB state."""
        citations_qs = ProjectCitation.objects.filter(
            project=project
        ).select_related("node")
        citations_dicts = [_model_to_dict(c) for c in citations_qs]
        profile = FORMAT_PROFILES.get(project.content_type, {})
        default_style = profile.get("default_bib_style", "apa")
        style = style or request.GET.get("style", default_style)
        bibliography = format_bibliography(citations_dicts, style=style) if citations_dicts else ""
        chapters, has_research_queries = self._get_chapters(project)
        return render(request, self.template_name, {
            "project": project,
            "citations": citations_qs,
            "citations_dicts": citations_dicts,
            "bibliography": bibliography,
            "citation_styles": BIBLIOGRAPHY_STYLES,
            "active_style": style,
            "bibtex_export": export_bibtex(citations_dicts) if citations_dicts else "",
            "search_sources": SEARCH_SOURCES,
            "chapters": chapters,
            "has_research_queries": has_research_queries,
        })

    def get(self, request, pk):
        project = self._get_project(request, pk)
        return self._render(request, project)

    def post(self, request, pk):
        project = self._get_project(request, pk)
        action = request.POST.get("action", "")

        if action == "resolve_doi":
            doi = request.POST.get("doi", "").strip()
            if not doi:
                messages.error(request, "Bitte einen DOI eingeben.")
            else:
                result = resolve_doi(doi)
                if result:
                    _, created = _create_citation_from_dict(project, result, added_via="doi")
                    if created:
                        messages.success(request, f"Quelle gefunden: {result.get('title', doi)}")
                    else:
                        messages.warning(request, "Diese Quelle ist bereits in der Liste.")
                else:
                    messages.error(request, f"DOI nicht gefunden: {doi}")

        elif action == "resolve_isbn":
            isbn = request.POST.get("isbn", "").strip()
            if not isbn:
                messages.error(request, "Bitte eine ISBN eingeben.")
            else:
                result = resolve_isbn(isbn)
                if result:
                    _, created = _create_citation_from_dict(project, result, added_via="isbn")
                    if created:
                        messages.success(request, f"Buch gefunden: {result.get('title', isbn)}")
                    else:
                        messages.warning(request, "Dieses Buch ist bereits in der Liste.")
                else:
                    messages.error(request, f"ISBN nicht gefunden: {isbn}")

        elif action == "import_bibtex":
            bibtex_str = request.POST.get("bibtex", "").strip()
            if not bibtex_str:
                messages.error(request, "Bitte BibTeX-Inhalt einfügen.")
            else:
                imported = parse_bibtex(bibtex_str)
                added = 0
                for c in imported:
                    _, created = _create_citation_from_dict(project, c, added_via="bibtex")
                    if created:
                        added += 1
                messages.success(request, f"{added} Quellen aus BibTeX importiert.")

        elif action == "remove":
            citation_id = request.POST.get("citation_id", "")
            if citation_id:
                deleted, _ = ProjectCitation.objects.filter(
                    pk=citation_id, project=project
                ).delete()
                if deleted:
                    messages.success(request, "Quelle entfernt.")

        elif action == "add_from_search":
            paper_json = request.POST.get("paper", "")
            node_id = request.POST.get("node_id", "") or None
            try:
                paper = json.loads(paper_json)
                authors_raw = paper.get("authors", [])
                if authors_raw and isinstance(authors_raw[0], str):
                    paper["authors"] = [
                        {"family": a.split()[-1] if a.split() else a,
                         "given": " ".join(a.split()[:-1]) if len(a.split()) > 1 else "",
                         "orcid": ""}
                        for a in authors_raw
                    ]
                citation, created = _create_citation_from_dict(project, paper, added_via="search")
                if created and node_id:
                    node = OutlineNode.objects.filter(
                        pk=node_id, outline_version__project=project,
                    ).first()
                    if node:
                        citation.node = node
                        citation.save(update_fields=["node"])
                if created:
                    messages.success(request, f"Quelle hinzugefügt: {paper.get('title', '')[:60]}")
                else:
                    messages.warning(request, "Diese Quelle ist bereits in der Liste.")
            except (json.JSONDecodeError, KeyError):
                messages.error(request, "Fehler beim Hinzufügen der Quelle.")

        elif action == "assign_chapter":
            citation_id = request.POST.get("citation_id", "")
            node_id = request.POST.get("node_id", "") or None
            if citation_id:
                citation = ProjectCitation.objects.filter(
                    pk=citation_id, project=project
                ).first()
                if citation:
                    if node_id:
                        node = OutlineNode.objects.filter(
                            pk=node_id,
                            outline_version__project=project,
                        ).first()
                        citation.node = node
                    else:
                        citation.node = None
                    citation.save(update_fields=["node"])
                    messages.success(request, "Kapitelzuordnung aktualisiert.")

        elif action == "clear_all":
            count, _ = ProjectCitation.objects.filter(project=project).delete()
            messages.success(request, f"{count} Quellen entfernt.")

        style = request.POST.get("style", request.GET.get("style", "apa"))
        return self._render(request, project, style=style)


class CitationDOILookupAjaxView(LoginRequiredMixin, View):
    """AJAX: DOI → Citation JSON (für Live-Preview ohne Seitenreload)."""

    def get(self, request, pk):
        doi = request.GET.get("doi", "").strip()
        if not doi:
            return JsonResponse({"ok": False, "error": "DOI fehlt"})
        result = resolve_doi(doi)
        if result:
            return JsonResponse({"ok": True, "citation": result})
        return JsonResponse({"ok": False, "error": f"DOI nicht gefunden: {doi}"})


class CitationISBNLookupAjaxView(LoginRequiredMixin, View):
    """AJAX: ISBN → Citation JSON (für Live-Preview ohne Seitenreload)."""

    def get(self, request, pk):
        isbn = request.GET.get("isbn", "").strip()
        if not isbn:
            return JsonResponse({"ok": False, "error": "ISBN fehlt"})
        result = resolve_isbn(isbn)
        if result:
            return JsonResponse({"ok": True, "citation": result})
        return JsonResponse({"ok": False, "error": f"ISBN nicht gefunden: {isbn}"})


class ResearchQueriesAjaxView(LoginRequiredMixin, View):
    """
    AJAX: KI-generierte Recherchefragen pro Kapitel.

    GET  → liefert gespeicherte Queries aus OutlineNode.research_queries
    POST → generiert neue Queries via LLM und speichert sie in DB
    """

    def _get_outline_chapters(self, project):
        active_outline = OutlineVersion.objects.filter(
            project=project, is_active=True
        ).order_by("-created_at").first()
        if not active_outline:
            return None, []
        return active_outline, list(active_outline.nodes.order_by("order"))

    def get(self, request, pk):
        """Return cached research queries from DB."""
        project = get_object_or_404(
            BookProject, pk=pk, owner=request.user, is_active=True
        )
        _, chapters = self._get_outline_chapters(project)
        result = []
        for ch in chapters:
            if ch.research_queries:
                result.append({
                    "chapter_id": str(ch.pk),
                    "chapter_order": ch.order,
                    "chapter_title": ch.title,
                    "queries": ch.research_queries,
                })
        return JsonResponse({"ok": True, "chapters": result, "from_cache": True})

    def post(self, request, pk):
        """Generate new research queries via LLM and save to DB."""
        project = get_object_or_404(
            BookProject, pk=pk, owner=request.user, is_active=True
        )
        _, chapters = self._get_outline_chapters(project)
        if not chapters:
            return JsonResponse({"ok": False, "error": "Kein Outline mit Kapiteln vorhanden."})

        chapters_block = "\n".join(
            f"{ch.order}. {ch.title}\n   {(ch.description or '')[:200]}"
            for ch in chapters
        )
        chapter_map = {str(ch.pk): ch for ch in chapters}
        order_map = {ch.order: ch for ch in chapters}

        from apps.core.prompt_utils import render_prompt
        from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

        try:
            messages = render_prompt(
                "projects/research_queries",
                project_title=project.title,
                project_description=project.description or "",
                content_type=project.content_type or "novel",
                chapters_block=chapters_block,
            )
            router = LLMRouter()
            raw = router.completion(
                action_code="research_queries",
                messages=messages,
                priority="fast",
                timeout=60,
            )
            from promptfw.parsing import extract_json_list
            result = extract_json_list(raw)
            if not result:
                return JsonResponse({"ok": False, "error": "Keine Ergebnisse generiert."})

            for item in result:
                queries = item.get("queries", [])
                if not queries:
                    continue
                node = chapter_map.get(str(item.get("chapter_id", "")))
                if not node:
                    node = order_map.get(item.get("chapter_order"))
                if node:
                    node.research_queries = queries[:5]
                    node.save(update_fields=["research_queries"])

            saved = []
            for ch in chapters:
                ch.refresh_from_db(fields=["research_queries"])
                if ch.research_queries:
                    saved.append({
                        "chapter_id": str(ch.pk),
                        "chapter_order": ch.order,
                        "chapter_title": ch.title,
                        "queries": ch.research_queries,
                    })
            return JsonResponse({"ok": True, "chapters": saved})
        except LLMRoutingError as exc:
            return JsonResponse({"ok": False, "error": str(exc)})
        except Exception as exc:
            logger.exception("ResearchQueriesAjaxView error for project %s", pk)
            return JsonResponse({"ok": False, "error": f"Fehler: {exc}"})


class LiteraturrechercheAjaxView(LoginRequiredMixin, View):
    """
    AJAX: KI-gestützte Literaturrecherche.

    POST-Parameter:
        query       — Suchbegriff / Forschungsfrage
        sources     — komma-getrennt: arxiv,semantic_scholar,pubmed,openalex
        max_results — int, Standard 20
    """

    def post(self, request, pk):
        query = request.POST.get("query", "").strip()
        if not query:
            return JsonResponse({"ok": False, "error": "Suchbegriff fehlt"})

        sources_raw = request.POST.get("sources", "")
        if sources_raw:
            sources = [
                s.strip() for s in sources_raw.split(",")
                if s.strip() in VALID_SEARCH_SOURCES
            ] or None
        else:
            sources = None

        try:
            max_results = int(request.POST.get("max_results", 20))
            max_results = max(5, min(max_results, 50))
        except (ValueError, TypeError):
            max_results = 20

        result = smart_search_papers(query, sources=sources, max_results=max_results)
        return JsonResponse({
            "ok": True,
            "papers": result["papers"],
            "count": len(result["papers"]),
            "queries_used": result["queries_used"],
            "total_found": result["total_found"],
            "total_after_filter": result["total_after_filter"],
        })
