"""
Idea Generator Service
=======================

Generiert Buchideen und Premises via aifw/promptfw.
action_codes: idea_generate, idea_to_premise

Portiert aus bfagent.writing_hub.services.creative_agent_service.
"""

import json
import logging
import re
from dataclasses import dataclass, field

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

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein kreativer Buchideen-Entwickler. "
                    "Antworte ausschliesslich mit einem validen JSON-Array."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generiere {count} originelle, packende Buchideen."
                    + (f" Genre: {genre}." if genre else "")
                    + (f" Stichwoerter: {', '.join(keywords)}." if keywords else "")
                    + (f" Zielgruppe: {target_audience}." if target_audience else "")
                    + f"\n\nJSON-Schema: {json.dumps(schema, ensure_ascii=False)}\n"
                    "Jede Idee braucht einen eingaengigen Arbeitstitel und "
                    "einen packenden Hook (1-2 Saetze die das Buch unwiderstehlich machen)."
                ),
            },
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
        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein erfahrener Buchentwickler. "
                    "Entwickle die Idee zu einer vollstaendigen, verkaufbaren Premise aus. "
                    "Antworte mit einem JSON-Objekt."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Buchidee:\nTitel: {idea.title}\nHook: {idea.hook}\n"
                    + (f"Genre: {idea.genre}\n" if idea.genre else "")
                    + (f"Setting: {idea.setting}\n" if idea.setting else "")
                    + (f"Protagonist: {idea.protagonist}\n" if idea.protagonist else "")
                    + (f"Konflikt: {idea.conflict}\n" if idea.conflict else "")
                    + "\nAusarbeiten als JSON-Objekt mit: "
                    "{\"premise\": \"vollstaendige Premise (min 100 Woerter)\", "
                    "\"themes\": [\"...\"], "
                    "\"unique_selling_points\": [\"...\"], "
                    "\"protagonist_detail\": \"...\", "
                    "\"stakes\": \"was steht auf dem Spiel\"}"
                ),
            },
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
        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein kreativer Buchideen-Entwickler. "
                    "Entwickle aus den gegebenen Stichworten eine Buchidee. "
                    "Antworte mit einem JSON-Objekt."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Stichworte/Idee: {keywords}\n\n"
                    "Generiere eine ausgearbeitete Buchidee als JSON: "
                    "{\"title\": \"...\", \"hook\": \"...\", \"genre\": \"...\", "
                    "\"setting\": \"...\", \"protagonist\": \"...\", \"conflict\": \"...\"}"
                ),
            },
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
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()

        # Array oder einzelnes Objekt
        start_arr = raw.find("[")
        start_obj = raw.find("{")
        if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
            raw = raw[start_arr:]
        elif start_obj != -1:
            raw = "[" + raw[start_obj:] + "]"

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                items = data.get("ideas") or [data]
            else:
                items = data
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
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("_parse_ideas JSON-Fehler: %s", exc)
            return []

    @staticmethod
    def _parse_premise(raw: str) -> PremiseResult:
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()

        start = raw.find("{")
        if start != -1:
            raw = raw[start:]

        try:
            data = json.loads(raw)
            return PremiseResult(
                success=True,
                premise=data.get("premise", ""),
                themes=data.get("themes", []),
                unique_selling_points=data.get("unique_selling_points", []),
                protagonist_detail=data.get("protagonist_detail", ""),
                stakes=data.get("stakes", ""),
            )
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("_parse_premise JSON-Fehler: %s", exc)
            return PremiseResult(success=False, error=str(exc))
