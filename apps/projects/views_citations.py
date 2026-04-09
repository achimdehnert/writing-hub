"""
Citation Views — DOI/ISBN Lookup, BibTeX Import, Bibliography
für akademische/wissenschaftliche BookProjects.
"""
from __future__ import annotations

import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .constants import (
    BIBLIOGRAPHY_STYLES,
    FORMAT_PROFILES,
    SEARCH_SOURCES,
    VALID_SEARCH_SOURCES,
)
from .models import BookProject
from .services.citation_service import (
    export_bibtex,
    format_bibliography,
    parse_bibtex,
    resolve_doi,
    resolve_isbn,
    search_papers,
)

logger = logging.getLogger(__name__)


class CitationDashboardView(LoginRequiredMixin, View):
    """Zitations-Dashboard für ein akademisches/wissenschaftliches Projekt."""

    template_name = "projects/citations.html"

    def _get_project(self, request, pk):
        return get_object_or_404(
            BookProject, pk=pk, owner=request.user, is_active=True
        )

    def _get_citations(self, request):
        raw = request.session.get("citations", "[]")
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return []

    def _save_citations(self, request, citations):
        request.session["citations"] = json.dumps(citations)

    def get(self, request, pk):
        project = self._get_project(request, pk)
        citations = self._get_citations(request)
        profile = FORMAT_PROFILES.get(project.content_type, {})
        default_style = profile.get("default_bib_style", "apa")
        style = request.GET.get("style", default_style)
        bibliography = ""
        if citations:
            bibliography = format_bibliography(citations, style=style)
        return render(request, self.template_name, {
            "project": project,
            "citations": citations,
            "bibliography": bibliography,
            "citation_styles": BIBLIOGRAPHY_STYLES,
            "active_style": style,
            "bibtex_export": export_bibtex(citations) if citations else "",
            "search_sources": SEARCH_SOURCES,
        })

    def post(self, request, pk):
        project = self._get_project(request, pk)
        action = request.POST.get("action", "")
        citations = self._get_citations(request)

        if action == "resolve_doi":
            doi = request.POST.get("doi", "").strip()
            if not doi:
                messages.error(request, "Bitte einen DOI eingeben.")
            else:
                result = resolve_doi(doi)
                if result:
                    if not any(c.get("doi") == result.get("doi") for c in citations):
                        citations.append(result)
                        self._save_citations(request, citations)
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
                    if not any(c.get("title") == result.get("title") for c in citations):
                        citations.append(result)
                        self._save_citations(request, citations)
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
                    doi = c.get("doi", "")
                    title = c.get("title", "")
                    if doi and any(x.get("doi") == doi for x in citations):
                        continue
                    if title and any(x.get("title") == title for x in citations):
                        continue
                    citations.append(c)
                    added += 1
                self._save_citations(request, citations)
                messages.success(request, f"{added} Quellen aus BibTeX importiert.")

        elif action == "remove":
            idx_str = request.POST.get("index", "")
            try:
                idx = int(idx_str)
                if 0 <= idx < len(citations):
                    removed = citations.pop(idx)
                    self._save_citations(request, citations)
                    messages.success(request, f"Entfernt: {removed.get('title', '')}")
            except (ValueError, IndexError):
                pass

        elif action == "add_from_search":
            paper_json = request.POST.get("paper", "")
            try:
                paper = json.loads(paper_json)
                title = paper.get("title", "")
                doi = paper.get("doi", "")
                if doi and any(c.get("doi") == doi for c in citations):
                    messages.warning(request, "Diese Quelle ist bereits in der Liste.")
                elif title and any(c.get("title") == title for c in citations):
                    messages.warning(request, "Diese Quelle ist bereits in der Liste.")
                else:
                    authors_raw = paper.get("authors", [])
                    if authors_raw and isinstance(authors_raw[0], str):
                        authors = [
                            {"family": a.split()[-1] if a.split() else a,
                             "given": " ".join(a.split()[:-1]) if len(a.split()) > 1 else "",
                             "orcid": ""}
                            for a in authors_raw
                        ]
                    else:
                        authors = authors_raw
                    year = paper.get("publication_date", "")[:4] if paper.get("publication_date") else None
                    citation = {
                        "title": title,
                        "authors": authors,
                        "year": int(year) if year and year.isdigit() else None,
                        "source_type": "journal",
                        "journal": paper.get("journal", ""),
                        "volume": "", "issue": "", "pages": "",
                        "publisher": "", "place": "",
                        "doi": doi or "",
                        "url": paper.get("url", ""),
                        "abstract": paper.get("abstract", ""),
                        "keywords": paper.get("categories", []),
                    }
                    citations.append(citation)
                    self._save_citations(request, citations)
                    messages.success(request, f"Quelle hinzugefügt: {title[:60]}")
            except (json.JSONDecodeError, KeyError):
                messages.error(request, "Fehler beim Hinzufügen der Quelle.")

        elif action == "clear_all":
            self._save_citations(request, [])
            messages.success(request, "Alle Quellen entfernt.")

        style = request.POST.get("style", request.GET.get("style", "apa"))
        bibliography = format_bibliography(citations, style=style) if citations else ""
        return render(request, self.template_name, {
            "project": project,
            "citations": citations,
            "bibliography": bibliography,
            "citation_styles": BIBLIOGRAPHY_STYLES,
            "active_style": style,
            "bibtex_export": export_bibtex(citations) if citations else "",
            "search_sources": SEARCH_SOURCES,
        })


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

        papers = search_papers(query, sources=sources, max_results=max_results)
        return JsonResponse({"ok": True, "papers": papers, "count": len(papers)})
