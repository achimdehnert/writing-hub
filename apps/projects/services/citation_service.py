"""
CitationService — wraps iil-researchfw for academic writing projects.

Provides sync Django wrappers around the async researchfw CitationService.
Used by academic/scientific BookProject views for DOI/ISBN lookup,
BibTeX import, and bibliography formatting.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from iil_researchfw import Citation, CitationService, CitationStyle, Author, SourceType
    from iil_researchfw.search import AcademicSearchService
    from iil_researchfw.analysis.summary import AISummaryService, make_together_llm
    from iil_researchfw.analysis.relevance import RelevanceScorer
    _RESEARCHFW_AVAILABLE = True
except ImportError:
    _RESEARCHFW_AVAILABLE = False
    logger.warning("iil-researchfw not installed — citation features disabled")


def _run_async(coro: Any) -> Any:
    """Run an async coroutine synchronously (Django context)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=15)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def resolve_doi(doi: str) -> dict[str, Any] | None:
    """
    Resolve a DOI via CrossRef API and return citation as dict.

    Returns None if researchfw not available or DOI not found.
    """
    if not _RESEARCHFW_AVAILABLE:
        return None
    svc = CitationService()
    citation = _run_async(svc.from_doi(doi))
    if citation is None:
        return None
    return _citation_to_dict(citation)


def resolve_isbn(isbn: str) -> dict[str, Any] | None:
    """
    Resolve an ISBN via OpenLibrary API and return citation as dict.

    Returns None if researchfw not available or ISBN not found.
    """
    if not _RESEARCHFW_AVAILABLE:
        return None
    svc = CitationService()
    citation = _run_async(svc.from_isbn(isbn))
    if citation is None:
        return None
    return _citation_to_dict(citation)


def parse_bibtex(bibtex_str: str) -> list[dict[str, Any]]:
    """
    Parse a BibTeX string and return list of citation dicts.

    Returns empty list if researchfw not available.
    """
    if not _RESEARCHFW_AVAILABLE:
        return []
    citations = CitationService.parse_bibtex(bibtex_str)
    return [_citation_to_dict(c) for c in citations]


def format_bibliography(
    citations_data: list[dict[str, Any]],
    style: str = "apa",
) -> str:
    """
    Format a list of citation dicts as a formatted bibliography string.

    Args:
        citations_data: List of dicts from resolve_doi/resolve_isbn/parse_bibtex.
        style: Citation style — 'apa', 'mla', 'chicago', 'harvard', 'ieee', 'vancouver'.

    Returns empty string if researchfw not available.
    """
    if not _RESEARCHFW_AVAILABLE:
        return ""
    try:
        citation_style = CitationStyle(style.lower())
    except ValueError:
        citation_style = CitationStyle.APA
    citations = [_dict_to_citation(d) for d in citations_data]
    svc = CitationService()
    return svc.format_bibliography(citations, style=citation_style)


def format_single(citation_data: dict[str, Any], style: str = "apa") -> str:
    """Format a single citation dict as a formatted string."""
    if not _RESEARCHFW_AVAILABLE:
        return ""
    try:
        citation_style = CitationStyle(style.lower())
    except ValueError:
        citation_style = CitationStyle.APA
    citation = _dict_to_citation(citation_data)
    return citation.format(citation_style)


def export_bibtex(citations_data: list[dict[str, Any]]) -> str:
    """Export list of citation dicts as BibTeX string."""
    if not _RESEARCHFW_AVAILABLE:
        return ""
    citations = [_dict_to_citation(d) for d in citations_data]
    svc = CitationService()
    return svc.export_bibtex(citations)


def search_papers(
    query: str,
    sources: list[str] | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """
    KI-gestützte Literaturrecherche über mehrere akademische Datenbanken.

    Sucht parallel in: arXiv, Semantic Scholar, PubMed, OpenAlex.
    Gibt deduplizierte Liste von Paper-Dicts zurück.

    Args:
        query: Suchbegriff (Thema, Forschungsfrage, Stichworte)
        sources: Optional — Teilmenge aus ['arxiv','semantic_scholar','pubmed','openalex']
        max_results: Max. Treffer gesamt (Standard: 20)

    Returns empty list if researchfw not available.
    """
    if not _RESEARCHFW_AVAILABLE:
        return []
    svc = AcademicSearchService()
    papers = _run_async(svc.search(query, sources=sources, max_results=max_results))
    return [_paper_to_dict(p) for p in papers]


def summarize_papers(
    papers: list[dict[str, Any]],
    query: str = "",
    style: str = "scientific",
    citation_style: str = "inline",
    llm_api_key: str | None = None,
) -> dict[str, Any]:
    """
    Analysiert eine Liste von Paper-Dicts und erstellt eine KI-Zusammenfassung.

    Args:
        papers: Ergebnisse aus search_papers()
        query: Ursprünglicher Suchbegriff (für Kontext)
        style: 'scientific' | 'complex' | 'medium' | 'simple'
        citation_style: 'inline' | 'bibliography' | 'none'
        llm_api_key: Together AI API Key (fallback: TOGETHER_API_KEY env var)

    Returns dict mit 'summary', 'key_points', 'top_papers', 'ai_generated'.
    """
    if not _RESEARCHFW_AVAILABLE or not papers:
        return {
            "summary": "",
            "key_points": [],
            "top_papers": [],
            "ai_generated": False,
        }

    scorer = RelevanceScorer()
    scored = scorer.score(
        query or "research",
        [{"title": p.get("title", ""), "abstract": p.get("abstract", "")}
         for p in papers],
        fields=["title", "abstract"],
    )
    scored_top = scored[:10]
    top_papers = papers[:min(10, len(papers))]
    if scored_top:
        idx_map = {
            id(papers[i]): i
            for i in range(len(papers))
        }
        top_papers = [
            papers[idx_map[id(s.item)]]
            for s in scored_top
            if id(s.item) in idx_map
        ] or top_papers

    findings = [
        {
            "title": p.get("title", ""),
            "content": p.get("abstract", ""),
            "source": p.get("source", ""),
            "doi": p.get("doi", ""),
            "year": (p.get("publication_date") or "")[:4],
        }
        for p in top_papers
    ]

    from django.conf import settings
    key = llm_api_key or getattr(settings, "TOGETHER_API_KEY", "")
    llm_fn = make_together_llm(api_key=key) if key else None
    svc = AISummaryService(llm_fn=llm_fn)
    result = _run_async(
        svc.summarize_findings(
            findings,
            max_length=400,
            style=style,
            citation_style=citation_style,
        )
    )
    result["top_papers"] = top_papers
    return result


def research_outline_node(
    node_title: str,
    node_description: str = "",
    target_words: int | None = None,
    project_topic: str = "",
    style: str = "scientific",
    llm_api_key: str | None = None,
) -> dict[str, Any]:
    """
    Recherchiert für ein Outline-Kapitel und erstellt Schreib-Grundlage.

    Kombiniert Literatursuche + Zusammenfassung + Schreibumfang-Hinweis.

    Args:
        node_title: Kapitel-Titel aus dem Outline
        node_description: Beschreibung / Beat des Kapitels
        target_words: Zielumfang in Wörtern (aus OutlineNode.target_words)
        project_topic: Übergeordnetes Projekt-Thema für Kontext
        style: Zusammenfassungsstil
        llm_api_key: Together AI Key

    Returns dict mit 'papers', 'summary', 'key_points', 'writing_brief'.
    """
    if not _RESEARCHFW_AVAILABLE:
        return {"papers": [], "summary": "", "key_points": [], "writing_brief": ""}

    query_parts = [node_title]
    if project_topic:
        query_parts.append(project_topic)
    query = " ".join(query_parts)

    papers = search_papers(query, max_results=15)
    if not papers:
        return {
            "papers": [],
            "summary": "",
            "key_points": [],
            "writing_brief": f"Keine Quellen für '{node_title}' gefunden.",
        }

    summary_result = summarize_papers(
        papers,
        query=query,
        style=style,
        citation_style="inline",
        llm_api_key=llm_api_key,
    )

    word_hint = ""
    if target_words:
        word_hint = (
            f"\n\n**Zielumfang:** {target_words:,} Wörter. "
            f"Plane entsprechend ca. {max(1, target_words // 200)} Absätze "
            f"à {min(200, target_words)} Wörter."
        )

    description_hint = ""
    if node_description:
        description_hint = f"\n\n**Kapitel-Anforderung:** {node_description}"

    writing_brief = (
        f"## Schreib-Grundlage: {node_title}\n\n"
        + summary_result.get("summary", "")
        + description_hint
        + word_hint
    )

    return {
        "papers": summary_result.get("top_papers", []),
        "summary": summary_result.get("summary", ""),
        "key_points": summary_result.get("key_points", []),
        "writing_brief": writing_brief,
        "ai_generated": summary_result.get("ai_generated", False),
        "source_count": summary_result.get("source_count", 0),
    }


def _fix_paper_url(url: str) -> str:
    """Fix API URLs to web URLs (e.g. Semantic Scholar api→www)."""
    if url and "api.semanticscholar.org/paper/" in url:
        return url.replace("api.semanticscholar.org/paper/", "www.semanticscholar.org/paper/")
    return url


def _paper_to_dict(p: Any) -> dict[str, Any]:
    return {
        "title": p.title,
        "authors": p.authors,
        "abstract": p.abstract,
        "url": _fix_paper_url(p.url),
        "source": p.source,
        "doi": p.doi,
        "arxiv_id": p.arxiv_id,
        "publication_date": p.publication_date,
        "journal": p.journal,
        "citation_count": p.citation_count,
        "pdf_url": p.pdf_url,
        "categories": p.categories,
    }


def _citation_to_dict(c: Any) -> dict[str, Any]:
    return {
        "title": c.title,
        "authors": [
            {"family": a.family, "given": a.given, "orcid": a.orcid}
            for a in c.authors
        ],
        "year": c.year,
        "source_type": c.source_type.value if hasattr(c.source_type, "value") else str(c.source_type),
        "journal": c.journal,
        "volume": c.volume,
        "issue": c.issue,
        "pages": c.pages,
        "publisher": c.publisher,
        "place": c.place,
        "doi": c.doi,
        "url": c.url,
        "abstract": c.abstract,
        "keywords": c.keywords,
    }


def _dict_to_citation(d: dict[str, Any]) -> Any:
    if not _RESEARCHFW_AVAILABLE:
        return None
    authors = [
        Author(
            family=a.get("family", ""),
            given=a.get("given", ""),
            orcid=a.get("orcid", ""),
        )
        for a in d.get("authors", [])
    ]
    try:
        source_type = SourceType(d.get("source_type", "journal"))
    except ValueError:
        source_type = SourceType.JOURNAL
    return Citation(
        title=d.get("title", ""),
        authors=authors,
        year=d.get("year"),
        source_type=source_type,
        journal=d.get("journal", ""),
        volume=d.get("volume", ""),
        issue=d.get("issue", ""),
        pages=d.get("pages", ""),
        publisher=d.get("publisher", ""),
        place=d.get("place", ""),
        doi=d.get("doi", ""),
        url=d.get("url", ""),
        abstract=d.get("abstract", ""),
        keywords=d.get("keywords", []),
    )
