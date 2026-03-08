"""
outlinefw.django_adapter — Django-Bridge für outlinefw

Kapselt:
- DB-Speicherung (OutlineVersion + OutlineNode)
- ProjectContext aus BookProject laden
- LLMRouter-Adapter (writing-hub LLMRouter → outlinefw LLMRouter Protocol)

Nur diese Datei hat Django-Abhängigkeiten.
"""
from __future__ import annotations

import logging

from .schemas import OutlineNode, ProjectContext

logger = logging.getLogger(__name__)


def project_context_from_db(project_id: str) -> ProjectContext:
    """BookProject → ProjectContext (ohne weltenfw-Calls, nur lokale DB)."""
    from apps.projects.models import BookProject

    try:
        p = BookProject.objects.get(pk=project_id)
    except BookProject.DoesNotExist:
        logger.warning("project_context_from_db: Projekt %s nicht gefunden", project_id)
        return ProjectContext()

    return ProjectContext(
        title=p.title or "",
        genre=p.genre or "",
        description=p.description or "",
        target_audience=p.target_audience or "",
        target_word_count=p.target_word_count or 0,
    )


def save_outline_to_db(
    project_id: str,
    nodes: list[OutlineNode],
    name: str = "KI-generiert",
    framework: str = "",
    user=None,
) -> str | None:
    """
    OutlineVersion + OutlineNodes in DB speichern.

    - Deaktiviert vorherige aktive Version.
    - Gibt neue OutlineVersion-UUID zurück.
    """
    from apps.projects.models import BookProject, OutlineNode as DBNode, OutlineVersion

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
