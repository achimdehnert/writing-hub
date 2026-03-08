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
from outlinefw.django_adapter import (
    WritingHubLLMRouterAdapter,
    project_context_from_db,
    save_outline_to_db,
)
from outlinefw.frameworks import FRAMEWORKS, list_frameworks
from outlinefw.schemas import GenerationStatus, LLMQuality, OutlineNode, OutlineResult

logger = logging.getLogger(__name__)

__all__ = [
    "OutlineGeneratorService",
    "OutlineNode",
    "OutlineResult",
    "FRAMEWORKS",
    "list_frameworks",
]


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
        self._gen = OutlineGenerator(WritingHubLLMRouterAdapter())

    def generate_outline(
        self,
        project_id: str,
        framework: str = "three_act",
        chapter_count: int = 12,
        quality_level: int | None = None,
    ) -> OutlineResult:
        ctx = project_context_from_db(project_id)
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
        return save_outline_to_db(
            project_id=project_id,
            nodes=nodes,
            name=name,
            framework=framework,
            user=user,
        )
