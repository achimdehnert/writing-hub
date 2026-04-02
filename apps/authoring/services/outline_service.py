"""
outline_service.py — Facade für outlinefw.OutlineGenerator

Public API:
    svc = OutlineGeneratorService()
    result = svc.generate_outline(project_id, framework="save_the_cat")
    version_id = svc.save_outline(project_id, result.nodes, name="...", user=user)
"""

import json
import logging
import re
from dataclasses import dataclass

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

    # Non-Fiction Frameworks — werden NICHT über outlinefw generiert
    NONFICTION_FRAMEWORKS = {
        "scientific_essay", "essay", "article", "academic_paper",
        "imrad", "review_article", "thesis", "dissertation",
    }

    # Non-Fiction Content Types (BookProject.content_type)
    NONFICTION_CONTENT_TYPES = {
        "academic", "scientific", "nonfiction",
    }

    # Strukturvorlagen für Non-Fiction Typen
    NONFICTION_STRUCTURES = {
        "scientific_essay": (
            "Typische Struktur: Einleitung (These, Problemstellung) → "
            "Theoretischer Rahmen → Argumentation/Hauptteil (2-4 Abschnitte) → "
            "Diskussion → Fazit/Schluss"
        ),
        "article": (
            "Typische Struktur: Abstract → Einleitung → Methoden (IMRaD) → "
            "Ergebnisse → Diskussion → Schlussfolgerung → Literatur"
        ),
        "imrad": (
            "IMRaD-Struktur: Abstract → Introduction → Methods → "
            "Results → Discussion → Conclusion"
        ),
        "thesis": (
            "Typische Struktur: Abstract → Einleitung → Forschungsstand → "
            "Methodik → Analyse/Ergebnisse → Diskussion → Fazit → Anhang"
        ),
        "essay": (
            "Typische Struktur: Einleitung (These) → "
            "Argumentation (Hauptteil mit 2-4 Abschnitten) → Gegenargumente → Fazit"
        ),
    }

    # Labels für Non-Fiction Typen (für den Prompt)
    NONFICTION_LABELS = {
        "scientific_essay": "wissenschaftlichen Aufsatz",
        "article": "wissenschaftlichen Artikel (IMRaD)",
        "imrad": "IMRaD-Artikel",
        "thesis": "wissenschaftliche Arbeit (Thesis/Dissertation)",
        "essay": "akademischen Essay",
        "academic_paper": "akademisches Paper",
        "review_article": "Review-Artikel",
        "academic": "akademische Arbeit",
        "scientific": "wissenschaftliche Arbeit",
        "nonfiction": "Sachbuch",
    }

    # Mapping von writing-hub Frameworks zu outlinefw-Keys
    # outlinefw unterstützt: three_act, save_the_cat, heros_journey, five_act, dan_harmon
    FRAMEWORK_MAP = {
        # Direkte Mappings (1:1)
        "three_act": "three_act",
        "save_the_cat": "save_the_cat",
        "heros_journey": "heros_journey",
        "five_act": "five_act",
        "dan_harmon": "dan_harmon",
        # Fallback-Mappings für writing-hub spezifische Frameworks
        "scientific_essay": "three_act",  # Wissenschaftlich → 3-Akt (Einleitung, Hauptteil, Schluss)
        "essay": "three_act",
        "article": "three_act",
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

    def _is_nonfiction(self, framework: str, content_type: str = "") -> bool:
        """Prüfe ob Non-Fiction Pfad verwendet werden soll."""
        return (
            framework in self.NONFICTION_FRAMEWORKS
            or content_type in self.NONFICTION_CONTENT_TYPES
        )

    def _get_project_content_type(self, project_id: str) -> str:
        """Lese content_type direkt aus der DB."""
        try:
            from apps.projects.models import BookProject
            project = BookProject.objects.get(pk=project_id)
            return project.content_type or ""
        except Exception:
            return ""

    def _generate_nonfiction_outline(self, project_id: str, framework: str, chapter_count: int) -> _NonfictionResult:
        """Generiere Outline für Non-Fiction mit content-type-spezifischen Prompts."""
        from apps.authoring.services.project_context_service import ProjectContextService
        from apps.core.prompt_utils import render_prompt

        ctx = ProjectContextService().get_context(project_id)
        structure_hint = self.NONFICTION_STRUCTURES.get(framework, "")
        content_type_label = self.NONFICTION_LABELS.get(framework, "wissenschaftlichen Text")

        prompt_msgs = render_prompt(
            "outlines/nonfiction_outline",
            title=ctx.title,
            content_type_label=content_type_label,
            content_type_key=framework,
            description=ctx.description or "",
            chapter_count=chapter_count,
            structure_hint=structure_hint,
        )
        if not prompt_msgs:
            prompt_msgs = [
                {"role": "system", "content": "Du bist ein Experte für wissenschaftliches Schreiben. Antworte NUR mit JSON."},
                {"role": "user", "content": (
                    f"Erstelle eine Gliederung für {content_type_label}: '{ctx.title}'.\n"
                    f"{structure_hint}\n"
                    f"Genau {chapter_count} Abschnitte als JSON-Array mit title, description, section_type."
                )},
            ]

        try:
            raw = self._adapter._router.completion(
                action_code="chapter_outline",
                messages=prompt_msgs,
            )
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if not match:
                return _NonfictionResult(error_message="LLM returned no JSON array")
            items = json.loads(match.group())
            nodes = [
                _SimpleNode(
                    title=item.get("title", f"Abschnitt {i+1}"),
                    description=item.get("description", ""),
                    section_type=item.get("section_type", "chapter"),
                    order=i + 1,
                )
                for i, item in enumerate(items[:50])
            ]
            return _NonfictionResult(nodes=nodes)
        except Exception as exc:
            logger.exception("_generate_nonfiction_outline failed: %s", exc)
            return _NonfictionResult(error_message=str(exc))

    def generate_outline(
        self,
        project_id: str,
        framework: str = "three_act",
        chapter_count: int = 12,
        quality: str = "standard",
    ):
        # Projekttyp aus DB lesen für Content-Type-Erkennung
        content_type = self._get_project_content_type(project_id)

        # Non-Fiction Pfad: bypassed outlinefw komplett
        if self._is_nonfiction(framework, content_type):
            logger.info(
                "Non-Fiction Pfad für framework='%s', content_type='%s'",
                framework, content_type,
            )
            return self._generate_nonfiction_outline(project_id, framework, chapter_count)

        # Fiction Pfad: outlinefw
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


@dataclass
class _SimpleNode:
    """Einfacher Outline-Node für Non-Fiction Generierung."""
    title: str
    description: str = ""
    section_type: str = "chapter"
    order: int = 0

    @property
    def act(self):
        return self.section_type

    @property
    def summary(self):
        return self.description


class _NonfictionResult:
    """Ergebnis-Objekt für Non-Fiction Outline Generierung."""
    def __init__(self, nodes=None, error_message=""):
        self.nodes = nodes or []
        self.success = bool(self.nodes)
        self.error_message = error_message
