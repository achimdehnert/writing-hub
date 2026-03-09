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
from outlinefw.schemas import LLMQuality, OutlineNode, OutlineResult, ProjectContext

from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
from apps.authoring.services.project_context_service import ProjectContextService

logger = logging.getLogger(__name__)

__all__ = [
    "OutlineGeneratorService",
    "OutlineNode",
    "OutlineResult",
    "FRAMEWORKS",
    "list_frameworks",
]

_FALLBACK_ACTION_CODES = [
    "outline.generate",
    "outline_generate",
    "chapter_outline",
]


class _OutlineLLMRouterAdapter:
    """
    Wraps writing-hub's LLMRouter to satisfy outlinefw's LLMRouter protocol.

    Tries action_codes in order until one succeeds:
      1. outline.generate  (registered in AIActionType)
      2. outline_generate  (fallback slug variant)
      3. chapter_outline   (always present as final fallback)
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
        ql = self._quality_level or (quality.value if hasattr(quality, "value") else None)

        codes_to_try = [action_code]
        for fb in _FALLBACK_ACTION_CODES:
            if fb not in codes_to_try:
                codes_to_try.append(fb)

        last_exc: Exception | None = None
        for code in codes_to_try:
            try:
                result = self._router.completion(
                    action_code=code,
                    messages=messages,
                    quality_level=ql,
                    priority=priority,
                )
                if code != action_code:
                    logger.info(
                        "_OutlineLLMRouterAdapter: fallback '%s' -> '%s' succeeded",
                        action_code, code,
                    )
                return result
            except LLMRoutingError as exc:
                last_exc = exc
                logger.debug(
                    "_OutlineLLMRouterAdapter: action_code '%s' failed: %s", code, exc
                )
                continue

        raise LLMRoutingError(
            f"Kein action_code verf\u00fcgbar f\u00fcr outline generation. "
            f"Versucht: {codes_to_try}. Letzter Fehler: {last_exc}"
        ) from last_exc


def _project_context_from_db(project_id: str) -> ProjectContext:
    """
    Build outlinefw.ProjectContext from writing-hub DB.

    Loads full context via ProjectContextService:
    - title, genre, description, premise, logline, themes
    - characters (name, role, description)
    - worlds (name, description)

    Provides safe fallbacks for non-empty fields required by outlinefw.
    """
    svc = ProjectContextService()
    local_ctx = svc.get_context(project_id)

    title = local_ctx.title or "Unbekanntes Projekt"
    genre = local_ctx.genre or "Allgemein"

    description = local_ctx.description or ""
    logline = (local_ctx.logline or local_ctx.premise or description[:200]).strip()
    if len(logline) < 10:
        logline = f"{title} \u2014 ein {genre}-Werk."

    protagonist = next(
        (c["name"] for c in local_ctx.characters if c.get("role") in ("protagonist", "main")),
        "",
    ).strip()
    if not protagonist and local_ctx.characters:
        protagonist = local_ctx.characters[0].get("name", "").strip()
    if not protagonist:
        protagonist = "Protagonist"

    world_names = [w.get("name", "") for w in local_ctx.worlds if w.get("name")]
    setting = (getattr(local_ctx, "setting", "") or "").strip()
    if not setting and world_names:
        setting = world_names[0]
    if not setting:
        setting = genre

    themes = local_ctx.themes or []

    ctx = ProjectContext(
        title=title,
        genre=genre,
        logline=logline,
        protagonist=protagonist,
        setting=setting,
        themes=themes,
        tone=getattr(local_ctx, "tone", "") or "",
        language_code="de",
    )

    logger.info(
        "_project_context_from_db project=%s title=%r protagonist=%r setting=%r "
        "themes=%s characters=%d worlds=%d",
        project_id, title, protagonist, setting,
        themes, len(local_ctx.characters), len(local_ctx.worlds),
    )
    return ctx


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
        OutlineVersion.objects.filter(project=project, is_active=True).update(is_active=False)
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
        logger.info(
            "generate_outline project=%s framework=%s ctx_title=%s logline=%r",
            project_id, framework, ctx.title, ctx.logline[:60],
        )
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
