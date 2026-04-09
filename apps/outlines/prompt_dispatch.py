"""
Outline Prompt Dispatch — Content-Type-aware Template Resolution

Resolution order:
  1. DB: OutlinePromptTemplate (active version for content_type_group × template_key)
  2. File: .jinja2 frontmatter files in templates/prompts/outlines/
  3. Error: PromptRenderError

This replaces direct render_prompt() calls in views/services with
content-type-aware dispatch that uses the correct prompt for
fiction vs. academic vs. nonfiction outlines.
"""
import logging

from apps.core.prompt_utils import PromptRenderError, render_prompt

logger = logging.getLogger(__name__)


def render_outline_prompt(
    template_key: str,
    content_type: str,
    **context,
) -> list[dict]:
    """
    Content-type-aware prompt rendering for outline operations.

    Args:
        template_key: One of "enrich_node", "detail_pass", "structure_pass"
        content_type: BookProject.content_type value (e.g. "scientific", "novel")
        **context: Template variables (context_block, order, title, etc.)

    Returns:
        List of message dicts: [{"role": "system", ...}, {"role": "user", ...}]

    Resolution:
        1. DB: OutlinePromptTemplate with matching group + key + is_active
        2. File: templates/prompts/outlines/{template_key}.jinja2 (with content_type in context)
        3. Error
    """
    from apps.outlines.models import OutlinePromptTemplate, get_content_type_group

    group = get_content_type_group(content_type)

    # 1. Try DB-backed template
    try:
        db_template = OutlinePromptTemplate.objects.get(
            content_type_group=group,
            template_key=template_key,
            is_active=True,
        )
        messages = db_template.render_messages(content_type=content_type, **context)
        if messages:
            logger.debug(
                "Outline prompt from DB: group=%s key=%s v%s",
                group, template_key, db_template.version,
            )
            return messages
        logger.warning(
            "DB template rendered empty: group=%s key=%s v%s",
            group, template_key, db_template.version,
        )
    except OutlinePromptTemplate.DoesNotExist:
        logger.debug(
            "No DB prompt for group=%s key=%s, using file fallback",
            group, template_key,
        )
    except OutlinePromptTemplate.MultipleObjectsReturned:
        logger.error(
            "Multiple active prompts for group=%s key=%s! Using first.",
            group, template_key,
        )
        db_template = OutlinePromptTemplate.objects.filter(
            content_type_group=group,
            template_key=template_key,
            is_active=True,
        ).first()
        if db_template:
            messages = db_template.render_messages(content_type=content_type, **context)
            if messages:
                return messages
    except Exception as exc:
        logger.warning("DB prompt lookup failed: %s", exc)

    # 2. File fallback (with content_type in context for Jinja2 conditionals)
    return render_prompt(
        f"outlines/{template_key}",
        content_type=content_type,
        **context,
    )


def get_active_template(
    template_key: str,
    content_type: str,
):
    """
    Get the active OutlinePromptTemplate for a content_type + key.

    Returns None if no DB template exists (file fallback will be used).
    Useful for linking quality ratings to the template version that
    generated the content.
    """
    from apps.outlines.models import OutlinePromptTemplate, get_content_type_group

    group = get_content_type_group(content_type)
    try:
        return OutlinePromptTemplate.objects.get(
            content_type_group=group,
            template_key=template_key,
            is_active=True,
        )
    except OutlinePromptTemplate.DoesNotExist:
        return None


def get_template_stats(content_type_group: str = None) -> dict:
    """
    Quality stats per template version for prompt-tuning feedback loop.

    Returns:
        {
            "templates": [
                {
                    "id": 1, "group": "academic", "key": "enrich_node",
                    "version": 2, "is_active": True,
                    "rating_count": 15, "avg_rating": 3.8,
                }
            ]
        }
    """
    from django.db.models import Avg, Count

    from apps.outlines.models import OutlinePromptTemplate

    qs = OutlinePromptTemplate.objects.annotate(
        rating_count=Count("ratings"),
        avg_rating=Avg("ratings__rating"),
    )
    if content_type_group:
        qs = qs.filter(content_type_group=content_type_group)

    return {
        "templates": [
            {
                "id": t.pk,
                "group": t.content_type_group,
                "key": t.template_key,
                "version": t.version,
                "is_active": t.is_active,
                "rating_count": t.rating_count,
                "avg_rating": round(t.avg_rating, 2) if t.avg_rating else None,
            }
            for t in qs
        ]
    }
