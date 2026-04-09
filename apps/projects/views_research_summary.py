"""
Research Summary Views — KI-Zusammenfassung von Suchergebnissen
und outline-getriebene Kapitel-Recherche für wissenschaftliche Projekte.
"""
from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .constants import SUMMARY_CITATION_FORMATS, SUMMARY_STYLES
from .models import BookProject, OutlineNode, OutlineVersion
from .services.citation_service import (
    research_outline_node,
    summarize_papers,
)

logger = logging.getLogger(__name__)


class ResearchSummarizeAjaxView(LoginRequiredMixin, View):
    """
    AJAX: Zusammenfassung einer Paper-Liste via LLM.

    POST:
        papers_json  — JSON-String einer Liste von paper-dicts
        query        — Original-Suchbegriff
        style        — scientific | complex | medium | simple
        citation_style — inline | bibliography | none
    """

    def post(self, request, pk):
        get_object_or_404(BookProject, pk=pk, owner=request.user, is_active=True)

        papers_json = request.POST.get("papers_json", "[]")
        query = request.POST.get("query", "")
        style = request.POST.get("style", "scientific")
        citation_style = request.POST.get("citation_style", "inline")

        try:
            papers = json.loads(papers_json)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({"ok": False, "error": "Ungültiges Papers-JSON"})

        if not papers:
            return JsonResponse({"ok": False, "error": "Keine Papers übergeben"})

        valid_styles = {s[0] for s in SUMMARY_STYLES}
        if style not in valid_styles:
            style = "scientific"

        llm_key = getattr(settings, "TOGETHER_API_KEY", "")
        result = summarize_papers(
            papers,
            query=query,
            style=style,
            citation_style=citation_style,
            llm_api_key=llm_key or None,
        )

        return JsonResponse({
            "ok": True,
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "ai_generated": result.get("ai_generated", False),
            "source_count": result.get("source_count", len(papers)),
            "top_papers": result.get("top_papers", [])[:5],
        })


class OutlineResearchView(LoginRequiredMixin, View):
    """
    Outline-getriebene Literaturrecherche.

    GET  — zeigt alle OutlineNodes des aktiven Outlines mit Recherche-Button
    POST — startet Recherche für einen Node (AJAX)
    """

    template_name = "projects/outline_research.html"

    def _get_project(self, request, pk):
        return get_object_or_404(
            BookProject, pk=pk, owner=request.user, is_active=True
        )

    def get(self, request, pk):
        project = self._get_project(request, pk)
        outline = (
            OutlineVersion.objects.filter(project=project)
            .prefetch_related("nodes")
            .order_by("-created_at")
            .first()
        )
        nodes = []
        if outline:
            nodes = list(
                outline.nodes.order_by("order").values(
                    "id", "title", "description",
                    "beat_type", "target_words", "order",
                )
            )
        return render(request, self.template_name, {
            "project": project,
            "outline": outline,
            "nodes": nodes,
            "summary_styles": SUMMARY_STYLES,
            "citation_styles_list": SUMMARY_CITATION_FORMATS,
            "has_llm": bool(getattr(settings, "TOGETHER_API_KEY", "")),
        })


class OutlineNodeResearchAjaxView(LoginRequiredMixin, View):
    """
    AJAX: Recherche + Zusammenfassung für einen einzelnen OutlineNode.

    POST:
        node_id      — UUID des OutlineNode
        style        — Zusammenfassungsstil
        project_topic — Übergeordnetes Thema (optional override)
    """

    def post(self, request, pk):
        project = get_object_or_404(
            BookProject, pk=pk, owner=request.user, is_active=True
        )

        node_id = request.POST.get("node_id", "")
        style = request.POST.get("style", "scientific")
        topic_override = request.POST.get("project_topic", "").strip()

        node = get_object_or_404(
            OutlineNode,
            id=node_id,
            outline_version__project=project,
        )

        project_topic = topic_override or project.title or ""
        llm_key = getattr(settings, "TOGETHER_API_KEY", "")

        result = research_outline_node(
            node_title=node.title,
            node_description=node.description or "",
            target_words=node.target_words,
            project_topic=project_topic,
            style=style,
            llm_api_key=llm_key or None,
        )

        return JsonResponse({
            "ok": True,
            "node_title": node.title,
            "target_words": node.target_words,
            "writing_brief": result.get("writing_brief", ""),
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "papers": result.get("papers", [])[:8],
            "ai_generated": result.get("ai_generated", False),
            "source_count": result.get("source_count", 0),
        })
