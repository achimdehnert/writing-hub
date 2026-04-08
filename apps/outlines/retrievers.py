"""
Outlines — fieldprefill Retrievers (ADR-107)

Registers data source retrievers and domain system prompt for AI field
enrichment of outline nodes. Called from OutlinesConfig.ready().

Pattern: same as risk-hub doc_template_retrievers.py — register retrievers
that provide existing project content as LLM context.
"""
import logging

from fieldprefill.prompts import register_system_prompt
from fieldprefill.retrievers import register_retriever

logger = logging.getLogger(__name__)


@register_retriever("project_context")
def _get_project_context(owner_id, instance=None):
    """Retrieve project context (genre, style, characters, world) for AI enrichment.

    Args:
        owner_id: User PK (used as tenant_id in fieldprefill).
        instance: BookProject model instance.

    Returns:
        List with a single context block string, or empty list.
    """
    if instance is None:
        return []
    try:
        from apps.authoring.services.project_context_service import ProjectContextService
        ctx_svc = ProjectContextService()
        proj_ctx = ctx_svc.get_context(str(instance.pk))
        block = proj_ctx.to_prompt_block()
        if block:
            return [block]
    except Exception as exc:
        logger.warning("project_context retriever failed: %s", exc)
    # Fallback: minimal context from model fields
    title = getattr(instance, "title", "Unbekannt")
    genre = getattr(instance, "genre", "")
    return [f"Projekt: {title}\nGenre: {genre}"]


@register_retriever("outline_siblings")
def _get_outline_siblings(owner_id, instance=None):
    """Retrieve sibling node summaries for cross-chapter context.

    Args:
        owner_id: User PK.
        instance: OutlineNode model instance (the node being enriched).

    Returns:
        List of sibling node summary strings.
    """
    if instance is None:
        return []
    try:
        from apps.projects.models import OutlineNode
        siblings = (
            OutlineNode.objects
            .filter(outline_version=instance.outline_version)
            .exclude(pk=instance.pk)
            .order_by("order")
            .values_list("order", "title", "description")[:20]
        )
        texts = []
        for order, title, desc in siblings:
            summary = (desc or "")[:200]
            texts.append(f"Kap. {order}: {title} — {summary}")
        return texts
    except Exception as exc:
        logger.warning("outline_siblings retriever failed: %s", exc)
    return []


def register_all():
    """Register domain system prompt for outline enrichment.

    Retrievers are auto-registered via @register_retriever decorators above.
    This function registers the domain-specific system prompt.
    """
    register_system_prompt(
        scope="writing.outline_enrichment",
        prompt=(
            "Du bist ein erfahrener Romanautor und Story-Entwickler. "
            "Du erweiterst kurze Kapitel-Outlines zu detaillierten Szenenplanungen. "
            "Antworte NUR mit dem angeforderten JSON, keine Erklärungen oder Einleitungen."
        ),
    )

    logger.info(
        "fieldprefill retrievers registered (project_context, outline_siblings) + "
        "system prompt for scope 'writing.outline_enrichment'"
    )
