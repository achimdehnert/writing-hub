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
    """

    def __init__(self):
        self._router = LLMRouter()

    def completion(self, messages, action_code="outline.generate", **kwargs):
        for code in [action_code, "outline.generate", "outline_generate", "chapter_outline"]:
            try:
                return self._router.completion(messages=messages, action_code=code, **kwargs)
            except Exception as exc:
                last_exc = exc
                logger.debug("LLM fallback from %s: %s", code, exc)
        raise last_exc


def _build_project_context(ctx):
    """
    Versucht outlinefw.ProjectContext aus dem lokalen ProjectContext zu bauen.
    Füllt alle Pflichtfelder mit Fallback-Werten wenn nicht vorhanden.
    Probiert verschiedene Signaturen um verschiedene outlinefw-Versionen zu unterstützen.
    """
    if ProjectContext is None:
        return None

    title = ctx.title or "Unbekanntes Projekt"
    genre = ctx.genre or ctx.content_type or "Allgemein"  # Fallback für leeres Genre
    description = ctx.description or ""

    # Logline aus description ableiten wenn nicht vorhanden
    logline = ctx.logline if ctx.logline else (description[:200] if description else title)

    # Protagonist aus characters ableiten
    protagonist = ""
    if ctx.characters:
        first = ctx.characters[0]
        protagonist = first.get("name", "") or first.get("role", "") or ""
    if not protagonist:
        protagonist = "Protagonist"

    # Setting aus worlds ableiten
    setting = ""
    if ctx.worlds:
        setting = ctx.worlds[0].get("name", "") or ctx.worlds[0].get("description", "")[:100]
    if not setting:
        setting = description[:100] if description else genre

    # Versuche verschiedene Signaturen (outlinefw kann unterschiedliche Versionen haben)
    attempts = [
        # Vollständig mit allen bekannten Feldern
        lambda: ProjectContext(
            title=title,
            genre=genre,
            description=description,
            logline=logline,
            protagonist=protagonist,
            setting=setting,
        ),
        # Ohne optionale Felder
        lambda: ProjectContext(
            title=title,
            genre=genre,
            description=description,
            logline=logline,
            protagonist=protagonist,
            setting=setting,
            themes=[],
            characters=[],
        ),
        # Minimale Signatur
        lambda: ProjectContext(
            title=title,
            logline=logline,
            protagonist=protagonist,
            setting=setting,
        ),
        # Nur title + description als letzter Fallback
        lambda: ProjectContext(
            title=title,
            description=description,
        ),
    ]

    for attempt in attempts:
        try:
            return attempt()
        except Exception as exc:
            logger.debug("ProjectContext attempt failed: %s", exc)
            continue

    logger.error("Alle ProjectContext-Signaturen fehlgeschlagen für Projekt %s", ctx.title)
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

    def __init__(self) -> None:
        self._adapter = _OutlineLLMRouterAdapter()

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

        try:
            generator = OutlineGenerator(router=self._adapter)
            result = generator.generate(
                context=ctx,
                framework=framework,
                chapter_count=chapter_count,
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
