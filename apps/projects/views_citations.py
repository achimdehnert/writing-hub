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
from .models import BookProject, ProjectCitation
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

    def _render(self, request, project, style=None):
        """Render citations dashboard with current DB state."""
        citations_qs = ProjectCitation.objects.filter(project=project)
        citations_dicts = [_model_to_dict(c) for c in citations_qs]
        profile = FORMAT_PROFILES.get(project.content_type, {})
        default_style = profile.get("default_bib_style", "apa")
        style = style or request.GET.get("style", default_style)
        bibliography = format_bibliography(citations_dicts, style=style) if citations_dicts else ""
        return render(request, self.template_name, {
            "project": project,
            "citations": citations_qs,
            "citations_dicts": citations_dicts,
            "bibliography": bibliography,
            "citation_styles": BIBLIOGRAPHY_STYLES,
            "active_style": style,
            "bibtex_export": export_bibtex(citations_dicts) if citations_dicts else "",
            "search_sources": SEARCH_SOURCES,
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
                _, created = _create_citation_from_dict(project, paper, added_via="search")
                if created:
                    messages.success(request, f"Quelle hinzugefügt: {paper.get('title', '')[:60]}")
                else:
                    messages.warning(request, "Diese Quelle ist bereits in der Liste.")
            except (json.JSONDecodeError, KeyError):
                messages.error(request, "Fehler beim Hinzufügen der Quelle.")

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
