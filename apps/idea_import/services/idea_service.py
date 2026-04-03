"""
Idea Generator Service
=======================

Generiert Buchideen und Premises via aifw/promptfw.
action_codes: idea_generate, idea_to_premise

Portiert aus bfagent.writing_hub.services.creative_agent_service.
"""

import json
import logging
from dataclasses import dataclass, field

from apps.core.prompt_utils import render_prompt
from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

logger = logging.getLogger(__name__)


@dataclass
class CharacterSketch:
    name: str
    role: str = "Nebencharakter"
    description: str = ""
    motivation: str = ""


@dataclass
class IdeaResult:
    success: bool
    title: str = ""
    hook: str = ""
    genre: str = ""
    setting: str = ""
    protagonist: str = ""
    conflict: str = ""
    characters: list[CharacterSketch] = field(default_factory=list)
    world_description: str = ""
    error: str = ""


@dataclass
class PremiseResult:
    success: bool
    premise: str = ""
    themes: list[str] = field(default_factory=list)
    unique_selling_points: list[str] = field(default_factory=list)
    protagonist_detail: str = ""
    stakes: str = ""
    error: str = ""


class IdeaGeneratorService:
    """
    Generiert Buchideen und Premises per LLM via aifw.

    Verwendung:
        svc = IdeaGeneratorService()
        ideas = svc.generate_ideas(genre="Fantasy", count=3)
        premise = svc.develop_premise(idea)
    """

    def __init__(self):
        self._router = LLMRouter()

    def generate_ideas(
        self,
        genre: str = "",
        count: int = 3,
        keywords: list[str] | None = None,
        target_audience: str = "",
        quality_level: int | None = None,
    ) -> list[IdeaResult]:
        """
        Buchideen generieren.

        Args:
            genre: Gewuenschtes Genre (z.B. "Fantasy", "Thriller")
            count: Anzahl Ideen
            keywords: Optionale Stichwoerter/Themen
            target_audience: Zielgruppe
            quality_level: ADR-095
        """
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "hook": {"type": "string", "minLength": 20},
                    "genre": {"type": "string"},
                    "setting": {"type": "string"},
                    "protagonist": {"type": "string"},
                    "conflict": {"type": "string"},
                },
                "required": ["title", "hook"],
            },
        }

        messages = render_prompt(
            "idea_import/generate_ideas_service",
            count=count,
            genre=genre,
            keywords=keywords or [],
            target_audience=target_audience,
            schema_json=json.dumps(schema, ensure_ascii=False),
        )
        if not messages:
            messages = [
                {"role": "system", "content": "Du bist ein Buchideen-Entwickler. Antworte mit JSON-Array."},
                {"role": "user", "content": f"Generiere {count} Buchideen."},
            ]

        try:
            raw = self._router.completion(
                "idea_generate",
                messages,
                quality_level=quality_level,
            )
            return self._parse_ideas(raw)

        except LLMRoutingError as exc:
            logger.error("generate_ideas Fehler: %s", exc)
            return [IdeaResult(success=False, error=str(exc))]
        except Exception as exc:
            logger.exception("generate_ideas unerwarteter Fehler")
            return [IdeaResult(success=False, error=str(exc))]

    def develop_premise(
        self,
        idea: IdeaResult,
        quality_level: int | None = None,
    ) -> PremiseResult:
        """
        Idee zu einer vollstaendigen Premise ausarbeiten.

        Args:
            idea: Basis-Idee
            quality_level: ADR-095
        """
        messages = render_prompt(
            "idea_import/develop_premise_service",
            title=idea.title,
            hook=idea.hook,
            genre=idea.genre or "",
            setting=idea.setting or "",
            protagonist=idea.protagonist or "",
            conflict=idea.conflict or "",
        )
        if not messages:
            messages = [
                {"role": "system", "content": "Du bist ein Buchentwickler. Antworte mit JSON."},
                {"role": "user", "content": f"Premise fuer: {idea.title}\n{idea.hook}"},
            ]

        try:
            raw = self._router.completion(
                "idea_to_premise",
                messages,
                quality_level=quality_level,
                priority="quality",
            )
            return self._parse_premise(raw)

        except LLMRoutingError as exc:
            logger.error("develop_premise Fehler: %s", exc)
            return PremiseResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("develop_premise unerwarteter Fehler")
            return PremiseResult(success=False, error=str(exc))

    def generate_from_keywords(
        self,
        keywords: str,
        quality_level: int | None = None,
    ) -> IdeaResult:
        """Einzelne Buchidee aus Freitext/Stichworten generieren."""
        messages = render_prompt(
            "idea_import/generate_single_idea",
            keywords=keywords,
        )
        if not messages:
            messages = [
                {"role": "system", "content": "Du bist ein Buchideen-Entwickler. Antworte mit JSON."},
                {"role": "user", "content": f"Buchidee aus: {keywords}"},
            ]

        try:
            raw = self._router.completion(
                "idea_generate",
                messages,
                quality_level=quality_level,
            )
            ideas = self._parse_ideas(raw)
            return ideas[0] if ideas else IdeaResult(success=False, error="Keine Idee generiert")

        except LLMRoutingError as exc:
            logger.error("generate_from_keywords Fehler: %s", exc)
            return IdeaResult(success=False, error=str(exc))

    @staticmethod
    def _parse_ideas(raw: str) -> list[IdeaResult]:
        from promptfw.parsing import extract_json, extract_json_list
        items = extract_json_list(raw)
        if not items:
            obj = extract_json(raw)
            if obj:
                items = obj.get("ideas") or [obj]
            else:
                return []
        return [
            IdeaResult(
                success=True,
                title=item.get("title", ""),
                hook=item.get("hook", ""),
                genre=item.get("genre", ""),
                setting=item.get("setting", item.get("setting_sketch", "")),
                protagonist=item.get("protagonist", item.get("protagonist_sketch", "")),
                conflict=item.get("conflict", item.get("conflict_sketch", "")),
            )
            for item in items
            if isinstance(item, dict) and item.get("title")
        ]

    @staticmethod
    def _parse_premise(raw: str) -> PremiseResult:
        from promptfw.parsing import extract_json
        data = extract_json(raw)
        if data is None:
            return PremiseResult(success=False, error="Keine JSON-Antwort vom LLM")
        return PremiseResult(
            success=True,
            premise=data.get("premise", ""),
            themes=data.get("themes", []),
            unique_selling_points=data.get("unique_selling_points", []),
            protagonist_detail=data.get("protagonist_detail", ""),
            stakes=data.get("stakes", ""),
        )
