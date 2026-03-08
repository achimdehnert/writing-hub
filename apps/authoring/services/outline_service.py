"""
Outline Generator Service
==========================

Thin wrapper around outlinefw.OutlineGenerator for writing-hub.

Public API:
    svc = OutlineGeneratorService()
    result = svc.generate_outline(project_id, framework="save_the_cat")
    version_id = svc.save_outline(project_id, result.nodes, name="...", user=user)
"""

import logging

from outlinefw import OutlineGenerator
from outlinefw.frameworks import FRAMEWORKS, list_frameworks
from outlinefw.schemas import GenerationStatus, LLMQuality, OutlineNode, OutlineResult, ProjectContext

from apps.authoring.services.llm_router import LLMRouter
from apps.authoring.services.project_context_service import ProjectContextService

logger = logging.getLogger(__name__)

__all__ = [
    "OutlineGeneratorService",
    "OutlineNode",
    "OutlineResult",
    "FRAMEWORKS",
    "list_frameworks",
]


class _OutlineLLMRouterAdapter:
    """
    Wraps writing-hub's LLMRouter to satisfy outlinefw's LLMRouter protocol.
    outlinefw expects: completion(action_code, messages, quality, priority) -> str
    """

    def __init__(self, quality_level: int | None = None) -> None:
        self._router = LLMRouter()
        self._quality_level = quality_level

    def completion(
        self,
        action_code: str,
        messages: list[dict],
        quality: LLMQuality = LLMQuality.STANDARD,
        priority: str = "balanced",
    ) -> str:
        ql = self._quality_level or quality.value if hasattr(quality, "value") else self._quality_level
        return self._router.completion(
            action_code=action_code,
            messages=messages,
            quality_level=ql,
            priority=priority,
        )


def _project_context_from_db(project_id: str) -> ProjectContext:
    """Build outlinefw.ProjectContext from writing-hub DB."""
    svc = ProjectContextService()
    local_ctx = svc.get_context(project_id)
    return ProjectContext(
        title=local_ctx.title,
        genre=local_ctx.genre,
        logline=local_ctx.logline or local_ctx.description[:200] if local_ctx.description else "",
        protagonist=next(
            (c["name"] for c in local_ctx.characters if c.get("role") in ("protagonist", "main")),
            "",
        ),
        setting="",
        themes=local_ctx.themes or [],
        tone="",
        language_code="de",
    )


def _save_outline_to_db(
    project_id: str,
    nodes: list[OutlineNode],
    name: str = "KI-generiert",
    framework: str = "",
    user=None,
) -> str | None:
    """Persist outlinefw OutlineNodes to writing-hub DB."""
    from apps.projects.models import BookProject, OutlineVersion, OutlineNode as DBOutlineNode

    try:
        project = BookProject.objects.get(pk=project_id)
        version = OutlineVersion.objects.create(
            project=project,
            created_by=user,
            name=name,
            source="ai",
            notes=f"Framework: {framework}" if framework else "",
            is_active=True,
        )
        DBOutlineNode.objects.bulk_create([
            DBOutlineNode(
                outline_version=version,
                title=node.title,
                description=node.summary,
                beat_type=node.act.value if hasattr(node.act, "value") else str(node.act),
                order=i + 1,
            )
            for i, node in enumerate(nodes)
        ])
        return str(version.pk)
    except Exception:
        logger.exception("save_outline_to_db failed for project %s", project_id)
        return None


class OutlineGeneratorService:
    """
    Facade around outlinefw.OutlineGenerator for writing-hub.

    Usage:
        svc = OutlineGeneratorService()
        result = svc.generate_outline(project_id, framework="save_the_cat")
        if result.success:
            version_id = svc.save_outline(project_id, result.nodes, framework="save_the_cat", user=user)
    """

    def __init__(self) -> None:
        self._adapter = _OutlineLLMRouterAdapter()
        self._gen = OutlineGenerator(self._adapter)

    def generate_outline(
        self,
        project_id: str,
        framework: str = "three_act",
        chapter_count: int = 12,
        quality_level: int | None = None,
    ) -> OutlineResult:
        self._adapter._quality_level = quality_level
        ctx = _project_context_from_db(project_id)
        quality = LLMQuality(quality_level) if quality_level else LLMQuality.STANDARD
        return self._gen.generate(
            framework_key=framework,
            context=ctx,
            quality=quality,
        )

    def save_outline(
        self,
        project_id: str,
        nodes: list[OutlineNode],
        name: str = "KI-generiert",
        framework: str = "",
        user=None,
    ) -> str | None:
        return _save_outline_to_db(
            project_id=project_id,
            nodes=nodes,
            name=name,
            framework=framework,
            user=user,
        )
