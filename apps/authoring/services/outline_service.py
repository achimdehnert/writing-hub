"""
Outline Generator Service
==========================

Thin wrapper um outlinefw.OutlineGenerator.
Kein inline LLM/Parse-Code mehr — alles in src/outlinefw/.

Öffentliche API bleibt kompatibel mit bestehenden Aufrufern:
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
from outlinefw.schemas import OutlineNode, OutlineResult as OutlineGenerationResult

logger = logging.getLogger(__name__)

__all__ = [
    "OutlineGeneratorService",
    "OutlineNode",
    "OutlineGenerationResult",
    "FRAMEWORKS",
    "list_frameworks",
]


class OutlineGeneratorService:
    """
    Facade um outlinefw.OutlineGenerator für writing-hub.

    Verwendung:
        svc = OutlineGeneratorService()
        result = svc.generate_outline(project_id, framework="save_the_cat")
        version_id = svc.save_outline(project_id, result.nodes, name="KI-Draft", user=user)
    """

    def __init__(self):
        self._gen = OutlineGenerator(WritingHubLLMRouterAdapter())

    def generate_outline(
        self,
        project_id: str,
        framework: str = "three_act",
        chapter_count: int = 12,
        quality_level: int | None = None,
    ) -> OutlineGenerationResult:
        ctx = project_context_from_db(project_id)
        return self._gen.generate(
            context=ctx,
            framework=framework,
            chapter_count=chapter_count,
            quality_level=quality_level,
        )

    def expand_beat(
        self,
        project_id: str,
        beat_title: str,
        beat_description: str = "",
        sub_chapter_count: int = 3,
        quality_level: int | None = None,
    ) -> OutlineGenerationResult:
        ctx = project_context_from_db(project_id)
        return self._gen.expand_beat(
            context=ctx,
            beat_title=beat_title,
            beat_description=beat_description,
            sub_count=sub_chapter_count,
            quality_level=quality_level,
        )

    def save_outline(
        self,
        project_id: str,
        nodes: list[OutlineNode],
        name: str = "KI-generiert",
        user=None,
    ) -> str | None:
        return save_outline_to_db(
            project_id=project_id,
            nodes=nodes,
            name=name,
            user=user,
        )
