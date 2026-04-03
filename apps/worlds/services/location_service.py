"""
World Location & Scene Service
================================

Generiert Orte und Szenen via iil-aifw (LLM) und persistiert in WeltenHub
via iil-weltenfw REST Client.

Packages:
  - iil-aifw:       LLMRouter — action_codes: world_locations, scene_generate
  - iil-promptfw:   render_to_messages() — strukturierte Prompts aus Templates
  - iil-weltenfw:   get_client().locations / .scenes — WeltenHub API
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from apps.core.prompt_utils import render_prompt
from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

logger = logging.getLogger(__name__)


@dataclass
class LocationGenerationResult:
    success: bool
    locations: list[dict] = field(default_factory=list)
    error: str = ""


@dataclass
class SceneGenerationResult:
    success: bool
    scenes: list[dict] = field(default_factory=list)
    error: str = ""


class WorldLocationService:
    """
    Generiert Orte per LLM (aifw) und persistiert in WeltenHub (weltenfw).

    Verwendung:
        svc = WorldLocationService()
        result = svc.generate_locations(world_id, project_id, count=5)
        ids = svc.save_to_weltenhub(world_id, result.locations)
        svc.link_to_project(project_id, ids)

    aifw action_code: world_locations
    """

    def __init__(self):
        self._router = LLMRouter()

    def generate_locations(
        self,
        weltenhub_world_id: UUID,
        project_id: str,
        count: int = 5,
        requirements: str = "",
        quality_level: int | None = None,
    ) -> LocationGenerationResult:
        """
        Orte für eine Welt generieren.
        Nutzt promptfw.render_to_messages() wenn Template vorhanden, sonst Fallback.
        """
        world_ctx = self._get_world_context(weltenhub_world_id)
        project_ctx = self._get_project_context(project_id)

        messages = self._build_location_messages(
            world_ctx=world_ctx,
            project_ctx=project_ctx,
            count=count,
            requirements=requirements,
        )

        try:
            raw = self._router.completion(
                "world_locations", messages, quality_level=quality_level
            )
            locations = self._parse_locations(raw)
            return LocationGenerationResult(success=True, locations=locations)
        except LLMRoutingError as exc:
            logger.error("generate_locations: %s", exc)
            return LocationGenerationResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_locations unerwarteter Fehler")
            return LocationGenerationResult(success=False, error=str(exc))

    def save_to_weltenhub(
        self,
        weltenhub_world_id: UUID,
        locations: list[dict],
    ) -> list[UUID]:
        """
        Generierte Orte via iil-weltenfw in WeltenHub speichern.
        Gibt Liste der erstellten Location-UUIDs zurück.
        """
        from weltenfw.django import get_client
        from weltenfw.schema import LocationCreateInput

        client = get_client()
        created_ids = []
        for loc in locations:
            try:
                obj = client.locations.create(
                    LocationCreateInput(
                        world=weltenhub_world_id,
                        name=loc.get("name", "Unbekannter Ort"),
                        description=loc.get("description") or None,
                        atmosphere=loc.get("atmosphere") or None,
                        significance=loc.get("significance") or None,
                        is_public=False,
                        order=loc.get("order", 0),
                    )
                )
                created_ids.append(obj.id)
                logger.debug("LocationService: Ort '%s' erstellt: %s", obj.name, obj.id)
            except Exception as exc:
                logger.error("save_to_weltenhub location '%s': %s", loc.get("name"), exc)
        return created_ids

    def link_to_project(
        self,
        project_id: str,
        location_ids: list[UUID],
    ) -> int:
        """Orte mit lokalem Projekt via ProjectLocationLink verknüpfen."""
        from apps.projects.models import BookProject
        from apps.worlds.models import ProjectLocationLink
        try:
            project = BookProject.objects.get(pk=project_id)
        except Exception:
            return 0
        count = 0
        for loc_id in location_ids:
            ProjectLocationLink.objects.get_or_create(
                project=project,
                weltenhub_location_id=loc_id,
            )
            count += 1
        return count

    def get_project_locations(self, project_id: str) -> list:
        """
        Alle Orte eines Projekts aus WeltenHub laden.
        Gibt Liste von weltenfw.schema.LocationSchema zurück.
        """
        from apps.worlds.models import ProjectLocationLink
        from weltenfw.django import get_client
        links = ProjectLocationLink.objects.filter(project_id=project_id)
        client = get_client()
        results = []
        for link in links:
            try:
                results.append(client.locations.get(link.weltenhub_location_id))
            except Exception as exc:
                logger.warning("get_project_locations: %s", exc)
        return results

    def get_world_locations(self, weltenhub_world_id: UUID) -> list:
        """
        Alle Orte einer Welt direkt aus WeltenHub laden (gefiltert nach world).
        """
        from weltenfw.django import get_client
        try:
            page = get_client().locations.list(world=str(weltenhub_world_id))
            return list(page.results)
        except Exception as exc:
            logger.warning("get_world_locations: %s", exc)
            return []

    def _get_world_context(self, world_id: UUID) -> str:
        try:
            from weltenfw.django import get_client
            world = get_client().worlds.get(world_id)
            parts = [f"Welt: {world.name}"]
            if world.description:
                parts.append(f"Beschreibung: {world.description}")
            if getattr(world, "geography", None):
                parts.append(f"Geographie: {world.geography}")
            return "\n".join(parts)
        except Exception:
            return ""

    def _get_project_context(self, project_id: str) -> str:
        try:
            from apps.projects.models import BookProject
            p = BookProject.objects.get(pk=project_id)
            return f"Projekt: {p.title}\nGenre: {p.genre}"
        except Exception:
            return ""

    @staticmethod
    def _build_location_messages(
        world_ctx: str,
        project_ctx: str,
        count: int,
        requirements: str,
    ) -> list[dict]:
        """promptfw render_prompt() — raises PromptRenderError on failure."""
        return render_prompt(
            "worlds/location_generate",
            world_ctx=world_ctx,
            project_ctx=project_ctx,
            count=count,
            requirements=requirements,
        )

    @staticmethod
    def _parse_locations(raw: str) -> list[dict]:
        from promptfw.parsing import extract_json, extract_json_list
        data = extract_json_list(raw)
        if not data:
            obj = extract_json(raw)
            data = obj.get("locations", [obj]) if obj else []
        return [item for item in data if isinstance(item, dict) and item.get("name")]


class WorldSceneService:
    """
    Generiert Szenen per LLM (aifw) und persistiert in WeltenHub (weltenfw).

    Szenen brauchen eine WeltenHub Story-UUID (story) als Parent.
    Verwendung:
        svc = WorldSceneService()
        result = svc.generate_scenes(story_id, world_id, project_id, count=3)
        ids = svc.save_to_weltenhub(story_id, result.scenes)
        svc.link_to_project(project_id, ids)

    aifw action_code: scene_generate
    """

    def __init__(self):
        self._router = LLMRouter()

    def generate_scenes(
        self,
        weltenhub_story_id: UUID,
        weltenhub_world_id: UUID,
        project_id: str,
        count: int = 3,
        requirements: str = "",
        quality_level: int | None = None,
    ) -> SceneGenerationResult:
        """Szenen für eine Story generieren."""
        world_ctx = self._get_world_context(weltenhub_world_id)
        project_ctx = self._get_project_context(project_id)

        messages = self._build_scene_messages(
            world_ctx=world_ctx,
            project_ctx=project_ctx,
            count=count,
            requirements=requirements,
        )
        try:
            raw = self._router.completion(
                "scene_generate", messages, quality_level=quality_level
            )
            scenes = self._parse_scenes(raw)
            return SceneGenerationResult(success=True, scenes=scenes)
        except LLMRoutingError as exc:
            logger.error("generate_scenes: %s", exc)
            return SceneGenerationResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_scenes unerwarteter Fehler")
            return SceneGenerationResult(success=False, error=str(exc))

    def save_to_weltenhub(
        self,
        weltenhub_story_id: UUID,
        scenes: list[dict],
    ) -> list[UUID]:
        """Szenen via iil-weltenfw in WeltenHub speichern."""
        from weltenfw.django import get_client
        from weltenfw.schema import SceneCreateInput
        client = get_client()
        created_ids = []
        for i, scene in enumerate(scenes):
            try:
                obj = client.scenes.create(
                    SceneCreateInput(
                        story=weltenhub_story_id,
                        title=scene.get("title", f"Szene {i + 1}"),
                        summary=scene.get("summary") or None,
                        goal=scene.get("goal") or None,
                        disaster=scene.get("disaster") or None,
                        notes=scene.get("notes") or None,
                        order=i,
                    )
                )
                created_ids.append(obj.id)
                logger.debug("SceneService: Szene '%s' erstellt: %s", obj.title, obj.id)
            except Exception as exc:
                logger.error("save_to_weltenhub scene '%s': %s", scene.get("title"), exc)
        return created_ids

    def link_to_project(
        self,
        project_id: str,
        scene_ids: list[UUID],
        node_map: dict[str, str] | None = None,
    ) -> int:
        """Szenen mit lokalem Projekt via ProjectSceneLink verknüpfen."""
        from apps.projects.models import BookProject
        from apps.worlds.models import ProjectSceneLink
        try:
            project = BookProject.objects.get(pk=project_id)
        except Exception:
            return 0
        nm = node_map or {}
        count = 0
        for scene_id in scene_ids:
            ProjectSceneLink.objects.get_or_create(
                project=project,
                weltenhub_scene_id=scene_id,
                defaults={"outline_node_id": nm.get(str(scene_id))},
            )
            count += 1
        return count

    def get_project_scenes(self, project_id: str) -> list:
        """Alle Szenen eines Projekts aus WeltenHub laden."""
        from apps.worlds.models import ProjectSceneLink
        from weltenfw.django import get_client
        links = ProjectSceneLink.objects.filter(project_id=project_id)
        client = get_client()
        results = []
        for link in links:
            try:
                results.append(client.scenes.get(link.weltenhub_scene_id))
            except Exception as exc:
                logger.warning("get_project_scenes: %s", exc)
        return results

    def _get_world_context(self, world_id: UUID) -> str:
        try:
            from weltenfw.django import get_client
            world = get_client().worlds.get(world_id)
            return f"Welt: {world.name}\nBeschreibung: {world.description or ''}"
        except Exception:
            return ""

    def _get_project_context(self, project_id: str) -> str:
        try:
            from apps.projects.models import BookProject
            p = BookProject.objects.get(pk=project_id)
            return f"Projekt: {p.title}\nGenre: {p.genre}"
        except Exception:
            return ""

    @staticmethod
    def _build_scene_messages(
        world_ctx: str,
        project_ctx: str,
        count: int,
        requirements: str,
    ) -> list[dict]:
        """promptfw render_prompt() — raises PromptRenderError on failure."""
        return render_prompt(
            "worlds/scene_generate",
            world_ctx=world_ctx,
            project_ctx=project_ctx,
            count=count,
            requirements=requirements,
        )

    @staticmethod
    def _parse_scenes(raw: str) -> list[dict]:
        from promptfw.parsing import extract_json, extract_json_list
        data = extract_json_list(raw)
        if not data:
            obj = extract_json(raw)
            data = obj.get("scenes", [obj]) if obj else []
        return [item for item in data if isinstance(item, dict) and item.get("title")]
