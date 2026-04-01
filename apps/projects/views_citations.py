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

from .models import BookProject
from .services.citation_service import (
    export_bibtex,
    format_bibliography,
    parse_bibtex,
    resolve_doi,
    resolve_isbn,
)

logger = logging.getLogger(__name__)

CITATION_STYLES = [
    ("apa", "APA 7"),
    ("mla", "MLA 9"),
    ("chicago", "Chicago 17"),
    ("harvard", "Harvard"),
    ("ieee", "IEEE"),
    ("vancouver", "Vancouver"),
]


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
        style = request.GET.get("style", "apa")
        bibliography = ""
        if citations:
            bibliography = format_bibliography(citations, style=style)
        return render(request, self.template_name, {
            "project": project,
            "citations": citations,
            "bibliography": bibliography,
            "citation_styles": CITATION_STYLES,
            "active_style": style,
            "bibtex_export": export_bibtex(citations) if citations else "",
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

        elif action == "clear_all":
            self._save_citations(request, [])
            messages.success(request, "Alle Quellen entfernt.")

        style = request.POST.get("style", request.GET.get("style", "apa"))
        bibliography = format_bibliography(citations, style=style) if citations else ""
        return render(request, self.template_name, {
            "project": project,
            "citations": citations,
            "bibliography": bibliography,
            "citation_styles": CITATION_STYLES,
            "active_style": style,
            "bibtex_export": export_bibtex(citations) if citations else "",
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
