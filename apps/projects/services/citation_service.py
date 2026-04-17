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


class SearchError(Exception):
    """User-facing search error (rate limit, timeout, etc.)."""

try:
    from iil_researchfw import Citation, CitationService, CitationStyle, Author, SourceType
    from iil_researchfw.search import AcademicSearchService
    _RESEARCHFW_AVAILABLE = True
except ImportError:
    _RESEARCHFW_AVAILABLE = False
    logger.warning("iil-researchfw not installed — citation features disabled")

# Optional: advanced features (SmartSearch, AI Summary) — may not exist in all versions
_SMART_SEARCH_AVAILABLE = False
try:
    from iil_researchfw.search.smart import SmartSearchService
    from iil_researchfw.analysis.summary import AISummaryService, make_together_llm
    from iil_researchfw.analysis.relevance import RelevanceScorer
    _SMART_SEARCH_AVAILABLE = True
except ImportError:
    logger.info("iil-researchfw smart search/analysis not available — using basic search")

_BRAVE_AVAILABLE = False
try:
    from iil_researchfw.search.brave import BraveSearchService
    _BRAVE_AVAILABLE = True
except ImportError:
    logger.info("iil-researchfw brave search not available")


def _run_async(coro: Any, timeout: int = 60) -> Any:
    """Run an async coroutine synchronously (Django context) with timeout."""
    async def _with_timeout():
        return await asyncio.wait_for(coro, timeout=timeout)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _with_timeout())
                return future.result(timeout=timeout + 5)
        return loop.run_until_complete(_with_timeout())
    except RuntimeError:
        return asyncio.run(_with_timeout())
    except (asyncio.TimeoutError, TimeoutError) as exc:
        logger.warning("_run_async timeout after %ds: %s", timeout, exc)
        raise TimeoutError(f"Recherche-Timeout nach {timeout}s") from exc


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


def search_web(
    query: str,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """
    Web-Recherche über Brave Search API.

    Gibt Paper-kompatible Dicts zurück (title, url, abstract=snippet, source=brave).
    Nützlich für Romane, Sachbücher und nicht-akademische Inhalte.
    """
    if not _BRAVE_AVAILABLE:
        logger.warning("search_web: BraveSearchService not available")
        return []
    from decouple import config as dconfig
    api_key = dconfig("BRAVE_API_KEY", default="")
    if not api_key:
        logger.warning("search_web: BRAVE_API_KEY not configured")
        return []
    svc = BraveSearchService(api_key=api_key)
    try:
        results = _run_async(svc.search(query, count=min(max_results, 20)))
    except Exception as exc:
        exc_str = str(exc)
        if "429" in exc_str or "rate limit" in exc_str.lower():
            logger.warning("Brave rate limit for query: %s", query[:80])
            raise SearchError(
                "Brave API Rate-Limit erreicht. Bitte 1–2 Sekunden warten und erneut versuchen."
            ) from exc
        logger.exception("Brave web search failed for query: %s", query[:80])
        return []
    return [
        {
            "title": r.title,
            "url": r.url,
            "abstract": r.snippet,
            "source": "brave",
            "authors": [],
            "publication_date": r.age or "",
            "doi": "",
            "journal": r.domain,
        }
        for r in results
    ]


def search_papers(
    query: str,
    sources: list[str] | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """
    Literaturrecherche über akademische Datenbanken + optionale Web-Suche.

    Sucht parallel in: arXiv, Semantic Scholar, PubMed, OpenAlex, Brave Web.
    Gibt deduplizierte Liste von Paper-Dicts zurück.

    Args:
        query: Suchbegriff (Thema, Forschungsfrage, Stichworte)
        sources: Optional — Teilmenge aus ['arxiv','semantic_scholar','pubmed','openalex','brave']
        max_results: Max. Treffer gesamt (Standard: 20)

    Returns empty list if researchfw not available.
    """
    from apps.projects.constants import ACADEMIC_SOURCES

    results = []
    has_explicit_sources = bool(sources)
    source_set = set(sources) if sources else set()
    want_brave = "brave" in source_set or not has_explicit_sources

    if want_brave:
        brave_only = source_set == {"brave"}
        web_results = search_web(query, max_results=max_results if brave_only else max_results // 2)
        results.extend(web_results)

    academic_requested = list(source_set & ACADEMIC_SOURCES)
    if has_explicit_sources and not academic_requested:
        return results[:max_results]

    if _RESEARCHFW_AVAILABLE:
        svc = AcademicSearchService()
        papers = _run_async(svc.search(
            query,
            sources=academic_requested if academic_requested else None,
            max_results=max_results,
        ))
        results.extend([_paper_to_dict(p) for p in papers])

    return results[:max_results]


def smart_search_papers(
    topic: str,
    sources: list[str] | None = None,
    max_results: int = 20,
    relevance_threshold: float = 7.0,
    expand_citations: bool = False,
    search_rounds: int = 1,
) -> dict[str, Any]:
    """
    LLM-gesteuerte Literaturrecherche (ADR-160).

    Nutzt SmartSearchService für:
    1. LLM-Query-Expansion (3-4 optimierte Suchbegriffe)
    2. Multi-Source-Suche (arXiv, Semantic Scholar, PubMed, OpenAlex)
    3. LLM-Relevanz-Scoring (Batch à 10, Score 0-10)
    4. Filter auf relevance_threshold
    5. (Optional) Citation Graph Expansion via Semantic Scholar
    6. (Optional) Iterative Gap Analysis mit LLM

    Fallback: Bei fehlendem LLM-Key -> normales search_papers().

    Returns dict mit 'papers', 'queries_used', 'total_found', 'total_after_filter'.
    """
    if not _RESEARCHFW_AVAILABLE:
        return {"papers": [], "queries_used": [], "total_found": 0, "total_after_filter": 0}

    from django.conf import settings
    api_key = getattr(settings, "TOGETHER_API_KEY", "") or getattr(settings, "OPENAI_API_KEY", "")

    from apps.projects.constants import ACADEMIC_SOURCES

    has_explicit_sources = bool(sources)
    source_set = set(sources) if sources else set()
    want_brave = "brave" in source_set or not has_explicit_sources
    academic_requested = list(source_set & ACADEMIC_SOURCES)

    web_results = []
    if want_brave:
        brave_only = has_explicit_sources and not academic_requested
        web_count = max_results if brave_only else max_results // 3
        web_results = search_web(topic, max_results=web_count)

    if has_explicit_sources and not academic_requested:
        return {
            "papers": web_results[:max_results],
            "queries_used": [topic],
            "total_found": len(web_results),
            "total_after_filter": len(web_results),
        }

    academic_sources = academic_requested if academic_requested else None

    if not _SMART_SEARCH_AVAILABLE or not api_key:
        logger.info("smart_search_papers: no LLM key configured, falling back to search_papers()")
        academic_papers = search_papers(topic, sources=academic_sources, max_results=max_results)
        papers = web_results + academic_papers
        return {
            "papers": papers[:max_results],
            "queries_used": [topic],
            "total_found": len(papers),
            "total_after_filter": len(papers),
        }

    llm_fn = make_together_llm(api_key=api_key)
    svc = SmartSearchService(
        llm_fn=llm_fn,
        relevance_threshold=relevance_threshold,
        expand_citations=expand_citations,
        search_rounds=search_rounds,
    )
    result = _run_async(svc.search(topic, max_results=max_results, sources=academic_sources))

    papers = [_paper_to_dict(sp.paper) for sp in result.papers]
    for paper_dict, scored in zip(papers, result.papers):
        paper_dict["relevance_score"] = scored.relevance_score
        paper_dict["relevance_reason"] = scored.relevance_reason

    combined = web_results + papers
    return {
        "papers": combined[:max_results],
        "queries_used": result.queries_used,
        "total_found": result.total_found + len(web_results),
        "total_after_filter": result.total_after_filter + len(web_results),
    }


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
    if not _RESEARCHFW_AVAILABLE or not _SMART_SEARCH_AVAILABLE or not papers:
        return {
            "summary": "",
            "key_points": [],
            "top_papers": papers[:10] if papers else [],
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


def research_chapter_sources(
    node_id: str,
    max_results: int = 15,
) -> dict[str, Any]:
    """
    Recherchiert Quellen für ein OutlineNode und speichert als Notizen.

    Liest Titel, Beschreibung und Projekt-Thema aus dem Node,
    ruft search_papers() auf und formatiert die Ergebnisse als
    strukturierte Recherche-Notizen in node.notes.

    Args:
        node_id: UUID des OutlineNode
        max_results: Max. Treffer (Standard: 15)

    Returns dict mit 'paper_count', 'notes_preview', 'papers'.
    """
    from apps.projects.models import OutlineNode

    node = OutlineNode.objects.select_related(
        "outline_version__project"
    ).get(pk=node_id)
    project = node.outline_version.project

    query_parts = [node.title]
    if node.description:
        keywords = node.description[:200]
        query_parts.append(keywords)
    if project.title:
        query_parts.append(project.title)
    topic = " ".join(query_parts)

    result = smart_search_papers(topic, max_results=max_results, search_rounds=2)
    papers = result["papers"]
    if not papers:
        return {"paper_count": 0, "notes_preview": "", "papers": []}

    notes = format_research_notes(papers, node.title)
    node.notes = notes
    node.save(update_fields=["notes"])

    return {
        "paper_count": len(papers),
        "notes_preview": notes[:500],
        "papers": papers,
    }


def format_research_notes(papers: list[dict[str, Any]], chapter_title: str) -> str:
    """
    Formatiert Paper-Ergebnisse als strukturierte Recherche-Notizen.

    Format für LLM-Kontext (wird vom Brief-Generator gelesen):
    - Quellenübersicht mit Autoren, Jahr, DOI
    - Kurze Abstracts für Kontext
    """
    lines = [f"## Recherche-Quellen: {chapter_title}\n"]
    lines.append(f"{len(papers)} Quellen gefunden.\n")

    for i, p in enumerate(papers, 1):
        title = p.get("title", "Ohne Titel")
        authors = p.get("authors", [])
        if isinstance(authors, list) and authors:
            if isinstance(authors[0], str):
                author_str = "; ".join(authors[:3])
            else:
                author_str = "; ".join(
                    a.get("family", "") for a in authors[:3]
                )
            if len(authors) > 3:
                author_str += " et al."
        else:
            author_str = ""
        year = (p.get("publication_date") or "")[:4]
        doi = p.get("doi", "")
        source = p.get("source", "")
        abstract = (p.get("abstract") or "")[:300]

        lines.append(f"### [{i}] {title}")
        meta_parts = []
        if author_str:
            meta_parts.append(author_str)
        if year:
            meta_parts.append(f"({year})")
        if source:
            meta_parts.append(f"[{source}]")
        if doi:
            meta_parts.append(f"DOI: {doi}")
        if meta_parts:
            lines.append(" ".join(meta_parts))
        if abstract:
            lines.append(f"  {abstract}{'…' if len(p.get('abstract', '')) > 300 else ''}")
        lines.append("")

    return "\n".join(lines)


def _fix_paper_url(url: str) -> str:
    """Fix API URLs to web URLs (e.g. Semantic Scholar api→www).

    NOTE: Fixed upstream in iil-researchfw>=0.4.0 — this remains as safety net.
    """
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
