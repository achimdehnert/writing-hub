"""
Character Generator Service
============================

Generiert und verwaltet Charaktere via aifw (action_code=character_generate).
Kein direkter LLM-Zugriff.
"""

import json
import logging
import re
from dataclasses import dataclass, field

from .llm_router import LLMRouter, LLMRoutingError
from .project_context_service import ProjectContextService

logger = logging.getLogger(__name__)


@dataclass
class CharacterData:
    name: str
    role: str = "Nebencharakter"
    description: str = ""
    motivation: str = ""
    backstory: str = ""
    arc: str = ""
    traits: list[str] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)


@dataclass
class CharacterGenerationResult:
    success: bool
    characters: list[CharacterData] = field(default_factory=list)
    error: str = ""


class CharacterGeneratorService:
    """
    Generiert Charaktere per LLM via aifw.

    Verwendung:
        svc = CharacterGeneratorService()
        result = svc.generate_cast(project_id, count=5)
        result = svc.enrich_character(project_id, character_id)
    """

    def __init__(self):
        self._router = LLMRouter()
        self._ctx_service = ProjectContextService()

    def generate_cast(
        self,
        project_id: str,
        count: int = 5,
        requirements: str = "",
        quality_level: int | None = None,
    ) -> CharacterGenerationResult:
        """
        Generiert eine vollstaendige Charakter-Besetzung.

        Args:
            project_id: BookProject UUID
            count: Anzahl zu generierender Charaktere
            requirements: Optionale Zusatz-Anforderungen
            quality_level: ADR-095 Quality-Level (None = catch-all)
        """
        ctx = self._ctx_service.get_context(project_id)
        existing_names = [c["name"] for c in ctx.characters]

        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {
                        "type": "string",
                        "enum": ["Protagonist", "Antagonist", "Nebencharakter"],
                    },
                    "description": {"type": "string"},
                    "motivation": {"type": "string"},
                    "backstory": {"type": "string"},
                    "arc": {"type": "string"},
                    "traits": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "role", "description", "motivation"],
            },
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein kreativer Charakter-Entwickler fuer Romane. "
                    "Antworte ausschliesslich mit einem validen JSON-Array.\n\n"
                    + ctx.to_prompt_block()
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generiere {count} Charaktere fuer dieses Buchprojekt. "
                    + (f"Anforderungen: {requirements}\n" if requirements else "")
                    + (f"Bereits vorhandene Charaktere: {existing_names}\n" if existing_names else "")
                    + f"\nGib ein JSON-Array zurueck gemaess diesem Schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}"
                ),
            },
        ]

        try:
            raw = self._router.completion(
                "character_generate",
                messages,
                quality_level=quality_level,
            )
            characters = self._parse_characters(raw)
            return CharacterGenerationResult(success=True, characters=characters)

        except LLMRoutingError as exc:
            logger.error("generate_cast Fehler: %s", exc)
            return CharacterGenerationResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_cast unerwarteter Fehler")
            return CharacterGenerationResult(success=False, error=str(exc))

    def enrich_character(
        self,
        project_id: str,
        character_name: str,
        quality_level: int | None = None,
    ) -> CharacterGenerationResult:
        """Reichert einen bestehenden Charakter mit Tiefe an."""
        ctx = self._ctx_service.get_context(project_id)
        char_data = next(
            (c for c in ctx.characters if c["name"] == character_name), {}
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein Charakter-Experte fuer tiefe, glaubwuerdige Romanfiguren. "
                    "Antworte mit einem JSON-Objekt.\n\n"
                    + ctx.to_prompt_block()
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Vertiefe diesen Charakter erheblich:\n{json.dumps(char_data, ensure_ascii=False)}\n\n"
                    "Fuege hinzu: ausfuehrliche backstory, character arc, "
                    "5-7 konkrete Charakterzuege, Beziehungen zu anderen Figuren.\n"
                    "Gib ein erweitertes JSON-Objekt zurueck."
                ),
            },
        ]

        try:
            raw = self._router.completion(
                "character_generate",
                messages,
                quality_level=quality_level,
            )
            characters = self._parse_characters(raw)
            return CharacterGenerationResult(success=True, characters=characters[:1])

        except LLMRoutingError as exc:
            logger.error("enrich_character Fehler: %s", exc)
            return CharacterGenerationResult(success=False, error=str(exc))

    def save_characters(
        self, project_id: str, characters: list[CharacterData]
    ) -> int:
        """Charaktere in DB speichern. Gibt Anzahl gespeicherter Charaktere zurueck."""
        from apps.worlds.models import Character
        from apps.projects.models import BookProject

        try:
            project = BookProject.objects.get(pk=project_id)
        except Exception:
            return 0

        saved = 0
        for char_data in characters:
            Character.objects.update_or_create(
                project=project,
                name=char_data.name,
                defaults={
                    "role": char_data.role,
                    "description": char_data.description,
                    "motivation": char_data.motivation,
                    "backstory": char_data.backstory,
                    "arc": char_data.arc,
                    "traits": char_data.traits,
                    "is_active": True,
                },
            )
            saved += 1
        return saved

    @staticmethod
    def _parse_characters(raw: str) -> list[CharacterData]:
        """JSON-Array aus LLM-Antwort extrahieren und validieren."""
        # Code-Block entfernen
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        # <think>-Bloecke entfernen (Reasoning Models)
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()

        # Array suchen
        start = raw.find("[")
        if start == -1:
            start = raw.find("{")
            if start != -1:
                raw = "[" + raw[start:] + "]"
        else:
            raw = raw[start:]

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]
            return [
                CharacterData(
                    name=item.get("name", "Unbekannt"),
                    role=item.get("role", "Nebencharakter"),
                    description=item.get("description", ""),
                    motivation=item.get("motivation", ""),
                    backstory=item.get("backstory", ""),
                    arc=item.get("arc", ""),
                    traits=item.get("traits", []),
                    relationships=item.get("relationships", []),
                )
                for item in data
                if isinstance(item, dict) and item.get("name")
            ]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("_parse_characters: JSON-Fehler: %s", exc)
            return []
