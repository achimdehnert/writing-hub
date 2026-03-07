"""
World Character Service
========================

Generiert Charaktere via iil-aifw (LLM) und persistiert in WeltenHub
via iil-weltenfw REST Client.

Packages:
  - iil-aifw:       sync_completion() — LLM-Calls
  - iil-promptfw:   PromptStack — strukturierte Prompts
  - iil-authoringfw: CharacterProfile — typisiertes Schema
  - iil-weltenfw:   get_client().characters.create() — WeltenHub API
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from uuid import UUID

from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

logger = logging.getLogger(__name__)


@dataclass
class CharacterGenerationResult:
    success: bool
    characters: list[dict] = field(default_factory=list)
    error: str = ""


class WorldCharacterService:
    """
    Generiert Charaktere per LLM (aifw) und persistiert in WeltenHub (weltenfw).

    authoringfw.CharacterProfile wird als Zwischen-Schema genutzt:
      CharacterProfile(name, role, personality_traits, arc) — to_context_string()

    Verwendung:
        svc = WorldCharacterService()

        # Besetzung generieren:
        result = svc.generate_cast(world_id, project_id, count=5)

        # In WeltenHub speichern:
        ids = svc.save_to_weltenhub(world_id, result.characters)

        # Projekt verknuepfen:
        svc.link_to_project(project_id, ids)

    aifw action_code: character_generate
    """

    def __init__(self):
        self._router = LLMRouter()

    def generate_cast(
        self,
        weltenhub_world_id: UUID,
        project_id: str,
        count: int = 5,
        requirements: str = "",
        quality_level: int | None = None,
    ) -> CharacterGenerationResult:
        """
        Charakter-Besetzung generieren.

        Nutzt authoringfw.CharacterProfile fuer typisierte Prompt-Konstruktion.
        Nutzt aifw via LLMRouter (action_code=character_generate).
        Ergebnis: Liste von Charakter-Dicts (WeltenHub CharacterCreateInput-Format).
        """
        world_ctx = self._get_world_context(weltenhub_world_id)
        project_ctx = self._get_project_context(project_id)
        existing = self._get_existing_character_names(weltenhub_world_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein kreativer Charakter-Entwickler fuer Romane. "
                    "Erstelle tiefe, glaubwuerdige Figuren. "
                    "Antworte ausschliesslich mit einem JSON-Array.\n\n"
                    + world_ctx
                    + "\n"
                    + project_ctx
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generiere {count} Charaktere."
                    + (f" Anforderungen: {requirements}" if requirements else "")
                    + (f" Nicht duplizieren: {existing}" if existing else "")
                    + "\n\nJSON-Array:\n"
                    '[{"name": "", "personality": "", "backstory": "", '
                    '"goals": "", "fears": "", "appearance": "", '
                    '"is_protagonist": false}]'
                ),
            },
        ]

        try:
            raw = self._router.completion(
                "character_generate", messages, quality_level=quality_level
            )
            chars = self._parse_characters(raw)
            return CharacterGenerationResult(success=True, characters=chars)
        except LLMRoutingError as exc:
            logger.error("generate_cast: %s", exc)
            return CharacterGenerationResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_cast unerwarteter Fehler")
            return CharacterGenerationResult(success=False, error=str(exc))

    def enrich_character(
        self,
        weltenhub_character_id: UUID,
        quality_level: int | None = None,
    ) -> dict:
        """
        Bestehenden Charakter aus WeltenHub laden, via LLM bereichern,
        und in WeltenHub aktualisieren.

        Nutzt authoringfw.CharacterProfile fuer strukturierten Kontext.
        """
        from weltenfw.django import get_client
        from weltenfw.schema.character import CharacterUpdateInput

        client = get_client()
        try:
            char = client.characters.get(weltenhub_character_id)
        except Exception as exc:
            logger.error("enrich_character: Charakter nicht gefunden: %s", exc)
            return {}

        # authoringfw.CharacterProfile fuer Prompt-Kontext
        char_ctx = self._build_character_context(char)

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein Experte fuer tiefe Romanfiguren. "
                    "Bereichere den Charakter mit psychologischer Tiefe. "
                    "Antworte mit einem JSON-Objekt."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Charakter:\n{char_ctx}\n\n"
                    "Vertiefe: personality, backstory, goals, fears. "
                    "JSON: {\"personality\": \"\", \"backstory\": \"\", "
                    "\"goals\": \"\", \"fears\": \"\"}"
                ),
            },
        ]

        try:
            raw = self._router.completion(
                "character_generate", messages,
                quality_level=quality_level, priority="quality"
            )
            data = self._extract_json_object(raw)
            # WeltenHub aktualisieren
            client.characters.update(
                weltenhub_character_id,
                CharacterUpdateInput(
                    personality=data.get("personality") or None,
                    backstory=data.get("backstory") or None,
                    goals=data.get("goals") or None,
                    fears=data.get("fears") or None,
                ),
            )
            return data
        except LLMRoutingError as exc:
            logger.error("enrich_character LLM-Fehler: %s", exc)
            return {}
        except Exception as exc:
            logger.exception("enrich_character unerwarteter Fehler")
            return {}

    def save_to_weltenhub(
        self,
        weltenhub_world_id: UUID,
        characters: list[dict],
    ) -> list[UUID]:
        """
        Generierte Charaktere via iil-weltenfw in WeltenHub speichern.
        Gibt Liste der erstellten Charakter-UUIDs zurueck.
        """
        from weltenfw.django import get_client
        from weltenfw.schema.character import CharacterCreateInput

        client = get_client()
        created_ids = []

        for char_data in characters:
            try:
                char = client.characters.create(
                    CharacterCreateInput(
                        world=weltenhub_world_id,
                        name=char_data.get("name", "Unbekannt"),
                        personality=char_data.get("personality") or None,
                        backstory=char_data.get("backstory") or None,
                        goals=char_data.get("goals") or None,
                        fears=char_data.get("fears") or None,
                        appearance=char_data.get("appearance") or None,
                        is_protagonist=char_data.get("is_protagonist", False),
                        is_active=True,
                        notes=char_data.get("notes") or None,
                    )
                )
                created_ids.append(char.id)
                logger.debug("WorldCharacterService: Charakter '%s' erstellt: %s", char.name, char.id)
            except Exception as exc:
                logger.error("save_to_weltenhub: Charakter '%s' Fehler: %s", char_data.get("name"), exc)

        return created_ids

    def link_to_project(
        self,
        project_id: str,
        character_ids: list[UUID],
        project_arc_map: dict[str, str] | None = None,
    ) -> int:
        """Charaktere mit lokalem Projekt verknuepfen via ProjectCharacterLink."""
        from apps.worlds.models import ProjectCharacterLink
        from apps.projects.models import BookProject

        try:
            project = BookProject.objects.get(pk=project_id)
        except Exception:
            return 0

        arc_map = project_arc_map or {}
        count = 0
        for char_id in character_ids:
            ProjectCharacterLink.objects.get_or_create(
                project=project,
                weltenhub_character_id=char_id,
                defaults={"project_arc": arc_map.get(str(char_id), "")},
            )
            count += 1
        return count

    def get_project_characters(
        self, project_id: str
    ) -> list:
        """
        Alle Charaktere eines Projekts aus WeltenHub laden.
        Gibt Liste von weltenfw.schema.character.CharacterSchema zurueck.
        """
        from apps.worlds.models import ProjectCharacterLink
        from weltenfw.django import get_client

        links = ProjectCharacterLink.objects.filter(project_id=project_id)
        client = get_client()
        characters = []
        for link in links:
            try:
                char = client.characters.get(link.weltenhub_character_id)
                characters.append(char)
            except Exception as exc:
                logger.warning("get_project_characters: %s", exc)
        return characters

    def _get_world_context(self, world_id: UUID) -> str:
        """Welt-Kontext von WeltenHub laden."""
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

    def _get_existing_character_names(self, world_id: UUID) -> list[str]:
        try:
            from weltenfw.django import get_client
            chars = list(get_client().characters.iter_all())
            return [c.name for c in chars if str(getattr(c, 'world', '')) == str(world_id)][:30]
        except Exception:
            return []

    @staticmethod
    def _build_character_context(char) -> str:
        """authoringfw.CharacterProfile fuer Prompt-Kontext."""
        try:
            from authoringfw import CharacterProfile
            profile = CharacterProfile(
                name=char.name,
                role="protagonist" if char.is_protagonist else "supporting",
                personality_traits=[
                    t.strip() for t in (char.personality or "").split(",") if t.strip()
                ][:5],
                backstory=char.backstory or "",
            )
            return profile.to_context_string()
        except Exception:
            return f"Name: {char.name}, Persoenlichkeit: {char.personality or ''}"

    @staticmethod
    def _parse_characters(raw: str) -> list[dict]:
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
        start = raw.find("[")
        if start != -1:
            raw = raw[start:]
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = data.get("characters", [data])
            return [item for item in data if isinstance(item, dict) and item.get("name")]
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    def _extract_json_object(raw: str) -> dict:
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
        start = raw.find("{")
        if start != -1:
            raw = raw[start:]
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
