"""
World Builder Service
======================

Generiert Welten via iil-aifw (LLM) und speichert sie in WeltenHub
via iil-weltenfw REST Client.

Packages:
  - iil-aifw:      sync_completion() — LLM-Calls via AIActionType
  - iil-promptfw:  PromptStack — strukturierte Prompts
  - iil-authoringfw: WorldContext — typisiertes Zwischendaten-Schema
  - iil-weltenfw:  get_client().worlds.create() — WeltenHub API
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from apps.core.prompt_utils import render_prompt
from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

logger = logging.getLogger(__name__)


@dataclass
class WorldBuildResult:
    success: bool
    weltenhub_world_id: UUID | None = None
    name: str = ""
    description: str = ""
    geography: str = ""
    culture: str = ""
    magic_system: str = ""
    technology_level: str = ""
    politics: str = ""
    history: str = ""
    inhabitants: str = ""
    error: str = ""


class WorldBuilderService:
    """
    Generiert Welten per LLM (aifw) und persistiert in WeltenHub (weltenfw).

    Verwendung:
        svc = WorldBuilderService()

        # Welt generieren:
        result = svc.generate_world(project_id, genre="Fantasy")

        # In WeltenHub speichern:
        world_id = svc.save_to_weltenhub(result)

        # Projekt verknuepfen:
        svc.link_to_project(project_id, world_id)

    aifw action_codes:
      - world_generate   — vollstaendige Weltgenerierung
      - world_expand     — einzelnen Aspekt vertiefen
      - world_locations  — Orte generieren
    """

    def __init__(self):
        self._router = LLMRouter()
        self._prompt_stack = self._build_prompt_stack()

    def _build_prompt_stack(self):
        """promptfw.PromptStack laden (YAML-Templates aus templates/prompts/)."""
        try:
            import os
            from django.conf import settings
            from promptfw import PromptStack

            templates_dir = getattr(settings, "PROMPT_TEMPLATES_DIR", None)
            if templates_dir and os.path.isdir(templates_dir):
                return PromptStack.from_directory(templates_dir)
            return PromptStack()
        except Exception:
            return None

    def generate_world(
        self,
        project_id: str,
        genre: str = "",
        tone: str = "",
        keywords: list[str] | None = None,
        quality_level: int | None = None,
    ) -> WorldBuildResult:
        """
        Vollstaendige Welt fuer ein Buchprojekt generieren.

        Nutzt authoringfw.WorldContext fuer strukturierten Kontext.
        Nutzt aifw.sync_completion via LLMRouter (action_code=world_generate).
        """
        try:
            from authoringfw import WorldContext
        except ImportError:
            WorldContext = None

        project_title = self._get_project_title(project_id)

        # authoringfw.WorldContext fuer Prompt-Kontext nutzen
        world_ctx_str = ""
        if WorldContext is not None:
            try:
                wc = WorldContext(
                    title=f"Welt fuer '{project_title}'",
                    genre=genre or "unbekannt",
                )
                world_ctx_str = wc.to_context_string()
            except Exception:
                pass

        messages = self._build_world_generation_messages(
            project_title=project_title,
            genre=genre,
            tone=tone,
            keywords=keywords or [],
            world_ctx_str=world_ctx_str,
        )

        try:
            raw = self._router.completion(
                "world_generate",
                messages,
                quality_level=quality_level,
                priority="quality",
            )
            return self._parse_world_response(raw)
        except LLMRoutingError as exc:
            logger.error("WorldBuilderService.generate_world: %s", exc)
            return WorldBuildResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("WorldBuilderService.generate_world unerwarteter Fehler")
            return WorldBuildResult(success=False, error=str(exc))

    def save_to_weltenhub(
        self,
        result: WorldBuildResult,
        is_public: bool = False,
    ) -> UUID | None:
        """
        WorldBuildResult via iil-weltenfw in WeltenHub speichern.

        Gibt die WeltenHub-World-UUID zurueck.
        """
        from weltenfw.django import get_client
        from weltenfw.schema.world import WorldCreateInput

        try:
            client = get_client()
            world = client.worlds.create(
                WorldCreateInput(
                    name=result.name,
                    description=result.description or None,
                    geography=result.geography or None,
                    climate=None,
                    magic_system=result.magic_system or None,
                    technology_level=result.technology_level or None,
                    history=result.history or None,
                    is_public=is_public,
                    notes=(
                        f"Kultur: {result.culture}\nBewohner: {result.inhabitants}"
                        if result.culture or result.inhabitants else None
                    ),
                )
            )
            logger.info("WorldBuilderService: Welt '%s' in WeltenHub erstellt: %s", world.name, world.id)
            return world.id
        except Exception as exc:
            logger.error("WorldBuilderService.save_to_weltenhub: %s", exc)
            return None

    def link_to_project(
        self,
        project_id: str,
        weltenhub_world_id: UUID,
        role: str = "primary",
    ) -> bool:
        """Lokales ProjectWorldLink anlegen."""
        from apps.projects.models import BookProject
        from apps.worlds.models import ProjectWorldLink

        try:
            project = BookProject.objects.get(pk=project_id)
            ProjectWorldLink.objects.get_or_create(
                project=project,
                weltenhub_world_id=weltenhub_world_id,
                defaults={"role": role},
            )
            return True
        except Exception as exc:
            logger.error("WorldBuilderService.link_to_project: %s", exc)
            return False

    def get_project_worlds(
        self, project_id: str
    ) -> list:
        """
        Alle Welten eines Projekts aus WeltenHub laden.
        Gibt Liste von weltenfw.schema.world.WorldSchema zurueck.
        """
        from weltenfw.django import get_client
        from apps.worlds.models import ProjectWorldLink

        links = ProjectWorldLink.objects.filter(project_id=project_id)
        client = get_client()
        worlds = []
        for link in links:
            try:
                world = client.worlds.get(link.weltenhub_world_id)
                worlds.append(world)
            except Exception as exc:
                logger.warning("get_project_worlds: Welt %s nicht gefunden: %s", link.weltenhub_world_id, exc)
        return worlds

    def expand_world_aspect(
        self,
        weltenhub_world_id: UUID,
        aspect: str,
        quality_level: int | None = None,
    ) -> str:
        """
        Einzelnen Welt-Aspekt via LLM vertiefen und in WeltenHub aktualisieren.

        aspect: geography|culture|magic_system|politics|history|inhabitants
        """
        from weltenfw.django import get_client
        from weltenfw.schema.world import WorldUpdateInput

        client = get_client()
        try:
            world = client.worlds.get(weltenhub_world_id)
        except Exception:
            return ""

        messages = render_prompt(
            "worlds/world_expand",
            world_name=world.name,
            world_description=world.description or "",
            aspect=aspect,
        )
        if not messages:
            messages = [
                {"role": "system", "content": f"Du bist ein Weltenbau-Experte fuer '{world.name}'."},
                {"role": "user", "content": f"Vertiefe den Aspekt '{aspect}'."},
            ]

        try:
            content = self._router.completion(
                "world_expand", messages, quality_level=quality_level
            )
            # WeltenHub aktualisieren
            update_data = {aspect: content}
            client.worlds.update(weltenhub_world_id, WorldUpdateInput(**update_data))
            return content
        except Exception as exc:
            logger.error("expand_world_aspect: %s", exc)
            return ""

    def _get_project_title(self, project_id: str) -> str:
        try:
            from apps.projects.models import BookProject
            return BookProject.objects.get(pk=project_id).title
        except Exception:
            return str(project_id)

    @staticmethod
    def _build_world_generation_messages(
        project_title: str,
        genre: str,
        tone: str,
        keywords: list[str],
        world_ctx_str: str,
    ) -> list[dict]:
        messages = render_prompt(
            "worlds/world_generate",
            world_ctx_str=world_ctx_str,
            project_title=project_title,
            genre=genre,
            tone=tone,
            keywords=keywords,
        )
        if not messages:
            messages = [
                {"role": "system", "content": "Du bist ein Weltenbau-Experte. Antworte mit JSON.\n\n" + (world_ctx_str or "")},
                {"role": "user", "content": f"Erstelle eine Welt fuer: '{project_title}'."},
            ]
        return messages

    @staticmethod
    def _parse_world_response(raw: str) -> WorldBuildResult:
        from promptfw.parsing import extract_json
        data = extract_json(raw)
        if data is None:
            logger.warning("_parse_world_response: keine JSON-Antwort")
            return WorldBuildResult(success=False, error="Keine JSON-Antwort vom LLM")
        return WorldBuildResult(
            success=True,
            name=data.get("name", "Unbekannte Welt"),
            description=data.get("description", ""),
            geography=data.get("geography", ""),
            culture=data.get("culture", ""),
            magic_system=data.get("magic_system", ""),
            technology_level=data.get("technology_level", ""),
            politics=data.get("politics", ""),
            history=data.get("history", ""),
            inhabitants=data.get("inhabitants", ""),
        )
