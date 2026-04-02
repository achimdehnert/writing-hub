"""
outline_service.py — Facade für outlinefw.OutlineGenerator

Public API:
    svc = OutlineGeneratorService()
    result = svc.generate_outline(project_id, framework="save_the_cat")
    version_id = svc.save_outline(project_id, result.nodes, name="...", user=user)
"""

import logging

from apps.authoring.services.llm_router import LLMRouter

logger = logging.getLogger(__name__)

try:
    from outlinefw import OutlineGenerator, OutlineNode, ProjectContext
    _OUTLINEFW_AVAILABLE = True
except ImportError:
    _OUTLINEFW_AVAILABLE = False
    OutlineGenerator = None
    OutlineNode = None
    ProjectContext = None


class _OutlineLLMRouterAdapter:
    """
    Adapter: outlinefw erwartet ein LLM-Router-Interface mit .completion().
    Wir leiten an LLMRouter weiter und versuchen verschiedene action_codes.

    Parameter-Mapping:
    - outlinefw verwendet 'quality' (LLMQuality enum)
    - LLMRouter verwendet 'quality_level' (int)
    """

    def __init__(self):
        self._router = LLMRouter()

    def completion(self, messages, action_code="outline.generate", **kwargs):
        # Map outlinefw parameters to LLMRouter parameters
        router_kwargs = {}
        if "quality" in kwargs:
            # outlinefw.LLMQuality -> int (1=LOW, 2=STANDARD, 3=HIGH)
            quality = kwargs.pop("quality")
            if hasattr(quality, "value"):
                router_kwargs["quality_level"] = quality.value
            elif isinstance(quality, int):
                router_kwargs["quality_level"] = quality
        if "priority" in kwargs:
            router_kwargs["priority"] = kwargs.pop("priority")
        # Ignore unknown kwargs to prevent API errors
        # (don't pass remaining kwargs to LLMRouter)

        for code in [action_code, "outline.generate", "outline_generate", "chapter_outline"]:
            try:
                return self._router.completion(messages=messages, action_code=code, **router_kwargs)
            except Exception as exc:
                last_exc = exc
                logger.debug("LLM fallback from %s: %s", code, exc)
        raise last_exc


def _build_project_context(ctx):
    """
    Baut outlinefw.ProjectContext (v0.3.0+) aus dem lokalen ProjectContext.
    protagonist/setting sind optional (non-fiction), research_question wird
    fuer wissenschaftliche/akademische Projekte befuellt.
    """
    if ProjectContext is None:
        return None

    title = ctx.title or "Unbekanntes Projekt"
    genre = ctx.genre or ctx.content_type or "Allgemein"
    description = ctx.description or ""
    logline = ctx.logline if ctx.logline else (description[:200] if description else title)

    # Fiction-spezifische Felder (optional in v0.3.0)
    protagonist = ""
    if ctx.characters:
        first = ctx.characters[0]
        protagonist = first.get("name", "") or first.get("role", "") or ""

    setting = ""
    if ctx.worlds:
        setting = ctx.worlds[0].get("name", "") or ctx.worlds[0].get("description", "")[:100]
    if not setting:
        setting = description[:100] if description else ""

    # Non-Fiction: Forschungsfrage aus Logline/Beschreibung ableiten
    nonfiction_types = {"academic", "scientific", "nonfiction"}
    research_question = ""
    if getattr(ctx, "content_type", "") in nonfiction_types:
        research_question = ctx.logline or description[:300]

    try:
        return ProjectContext(
            title=title,
            genre=genre,
            logline=logline,
            protagonist=protagonist,
            setting=setting,
            research_question=research_question,
            themes=getattr(ctx, "themes", []) or [],
            additional_notes=description[:500] if description else "",
        )
    except Exception as exc:
        logger.debug("ProjectContext (full) failed: %s", exc)

    # Fallback: minimale Felder
    try:
        return ProjectContext(title=title, genre=genre, logline=logline)
    except Exception as exc:
        logger.error("Alle ProjectContext-Signaturen fehlgeschlagen fuer Projekt %s: %s", title, exc)
        return None


def _project_context_from_db(project_id: str):
    """Baut outlinefw.ProjectContext aus der writing-hub DB."""
    if not _OUTLINEFW_AVAILABLE:
        return None

    from apps.authoring.services.project_context_service import ProjectContextService
    svc = ProjectContextService()
    ctx = svc.get_context(project_id)
    return _build_project_context(ctx)


def _save_outline_to_db(
    project_id: str,
    nodes: list,
    name: str = "KI-generiert",
    framework: str = "",
    user=None,
) -> str | None:
    """Persist outlinefw OutlineNodes to writing-hub DB."""
    from apps.projects.models import BookProject, OutlineVersion
    from apps.projects.models import OutlineNode as DBOutlineNode

    try:
        project = BookProject.objects.get(pk=project_id)
        source = framework if framework else "ai"
        version = OutlineVersion.objects.create(
            project=project,
            created_by=user,
            name=name,
            source=source,
            notes=f"Framework: {framework}" if framework else "",
            is_active=True,
        )
        db_nodes = []
        for i, node in enumerate(nodes):
            beat = ""
            try:
                beat = node.act.value if hasattr(node.act, "value") else str(node.act)
            except Exception:
                beat = "chapter"
            summary = ""
            try:
                summary = node.summary or node.description or ""
            except Exception:
                pass
            db_nodes.append(DBOutlineNode(
                outline_version=version,
                title=node.title,
                description=summary,
                beat_type=beat or "chapter",
                order=i + 1,
            ))
        DBOutlineNode.objects.bulk_create(db_nodes)
        return str(version.pk)
    except Exception:
        logger.exception("save_outline_to_db failed for project %s", project_id)
        return None


class OutlineGeneratorService:
    """
    Facade für outlinefw.OutlineGenerator.

    Usage:
        svc = OutlineGeneratorService()
        result = svc.generate_outline(project_id, framework="save_the_cat")
        if result.success:
            version_id = svc.save_outline(project_id, result.nodes, framework="save_the_cat", user=user)
    """

    # Mapping von writing-hub Frameworks zu outlinefw-Keys (v0.3.0)
    # Fiction:     three_act, save_the_cat, heros_journey, five_act, dan_harmon
    # Non-Fiction: scientific_essay, academic_essay, imrad_article, essay
    FRAMEWORK_MAP = {
        # Fiction (1:1)
        "three_act": "three_act",
        "save_the_cat": "save_the_cat",
        "heros_journey": "heros_journey",
        "five_act": "five_act",
        "dan_harmon": "dan_harmon",
        # Non-Fiction (1:1, nativ in outlinefw v0.3.0)
        "scientific_essay": "scientific_essay",
        "academic_essay": "academic_essay",
        "imrad_article": "imrad_article",
        "essay": "essay",
        # Aliase
        "imrad": "imrad_article",
        "article": "imrad_article",
        "academic_paper": "academic_essay",
        # Fiction-Aliase
        "novella": "three_act",
        "short_story": "three_act",
    }
    DEFAULT_FRAMEWORK = "three_act"

    def __init__(self) -> None:
        self._adapter = _OutlineLLMRouterAdapter()

    def _map_framework(self, framework: str) -> str:
        """Map writing-hub framework key to outlinefw-compatible key."""
        mapped = self.FRAMEWORK_MAP.get(framework)
        if mapped:
            return mapped
        logger.info("Framework '%s' not in map, using default '%s'", framework, self.DEFAULT_FRAMEWORK)
        return self.DEFAULT_FRAMEWORK

    def generate_outline(
        self,
        project_id: str,
        framework: str = "three_act",
        chapter_count: int = 12,
        quality: str = "standard",
    ):
        if not _OUTLINEFW_AVAILABLE:
            logger.warning("outlinefw not available")
            return _FallbackResult(success=False, error_message="outlinefw not installed")

        ctx = _project_context_from_db(project_id)
        if ctx is None:
            return _FallbackResult(
                success=False,
                error_message="Projektkontext konnte nicht erstellt werden. Bitte Projektbeschreibung ergänzen."
            )

        outlinefw_key = self._map_framework(framework)
        logger.info("generate_outline: framework='%s' -> outlinefw_key='%s'", framework, outlinefw_key)

        try:
            generator = OutlineGenerator(router=self._adapter)
            result = generator.generate(
                framework_key=outlinefw_key,
                context=ctx,
                quality=quality,
            )
            return result
        except Exception as exc:
            logger.exception("OutlineGenerator.generate failed: %s", exc)
            return _FallbackResult(success=False, error_message=str(exc))

    def save_outline(
        self,
        project_id: str,
        nodes: list,
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


class _FallbackResult:
    def __init__(self, success=False, error_message=""):
        self.success = success
        self.nodes = []
        self.error_message = error_message
