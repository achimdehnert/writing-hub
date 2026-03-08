"""
outlinefw.django_adapter -- writing-hub Django bridge for outlinefw.

Implements OutlineServiceBase ABC for writing-hub:
  - get_tenant_id: extracts user.id from request (no multi-tenancy in writing-hub)
  - persist_outline: saves OutlineVersion + OutlineNodes to DB
  - get_llm_router: returns WritingHubLLMRouterAdapter

Also provides standalone helpers for legacy callers:
  - project_context_from_db(project_id) -> ProjectContext
  - save_outline_to_db(project_id, nodes, ...) -> str | None
"""
from __future__ import annotations

import logging
from typing import Any

from outlinefw._base import InMemoryOutlineService, OutlineServiceBase  # noqa: F401
from outlinefw.schemas import LLMQuality, OutlineNode, OutlineResult, ProjectContext

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standalone helpers (used by legacy outline_service.py callers)
# ---------------------------------------------------------------------------


def project_context_from_db(project_id: str) -> ProjectContext:
    """Load ProjectContext from writing-hub BookProject."""
    from apps.projects.models import BookProject

    try:
        p = BookProject.objects.get(pk=project_id)
    except BookProject.DoesNotExist:
        logger.warning("project_context_from_db: Projekt %s nicht gefunden", project_id)
        return ProjectContext(
            title="Unbekannt", genre="Unbekannt",
            logline="Kein Kontext verfuegbar.", protagonist="Unbekannt", setting="Unbekannt",
        )

    return ProjectContext(
        title=p.title or "Unbekannt",
        genre=p.genre or "Roman",
        logline=p.description[:500] if p.description else "Kein Kontext.",
        protagonist="Protagonist",
        setting="Unbekannt",
        target_word_count=p.target_word_count,
        language_code="de",
    )


def save_outline_to_db(
    project_id: str,
    nodes: list[OutlineNode],
    name: str = "KI-generiert",
    framework: str = "",
    user: Any = None,
) -> str | None:
    """Persist OutlineVersion + OutlineNodes for writing-hub."""
    from apps.projects.models import BookProject
    from apps.projects.models import OutlineNode as DBNode
    from apps.projects.models import OutlineVersion

    try:
        project = BookProject.objects.get(pk=project_id)
        OutlineVersion.objects.filter(project=project, is_active=True).update(is_active=False)

        version = OutlineVersion.objects.create(
            project=project,
            name=name,
            source="ai_generated",
            is_active=True,
            created_by=user,
            notes=f"Framework: {framework}" if framework else "",
        )

        DBNode.objects.bulk_create([
            DBNode(
                outline_version=version,
                title=node.title,
                description=node.description,
                beat_type=node.beat_type,
                order=node.order or (i + 1),
                notes="\n".join(filter(None, [
                    node.notes,
                    f"Beat: {node.beat}" if node.beat else "",
                    f"Emotional Arc: {node.emotional_arc}" if node.emotional_arc else "",
                ])),
            )
            for i, node in enumerate(nodes)
        ])

        logger.info(
            "save_outline_to_db: %d Nodes in Version %s gespeichert",
            len(nodes), version.pk,
        )
        return str(version.pk)

    except Exception as exc:
        logger.error("save_outline_to_db Fehler: %s", exc)
        return None


class WritingHubLLMRouterAdapter:
    """
    Adaptiert writing-hub LLMRouter → outlinefw LLMRouter Protocol.

    Wrapper damit outlinefw kein direktes Import auf writing-hub braucht.
    """

    def __init__(self):
        from apps.authoring.services.llm_router import LLMRouter
        self._router = LLMRouter()

    def completion(
        self,
        action_code: str,
        messages: list[dict],
        quality_level: int | None = None,
        priority: str = "balanced",
    ) -> str:
        return self._router.completion(
            action_code,
            messages,
            quality_level=quality_level,
            priority=priority,
        )
