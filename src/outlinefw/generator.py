"""
outlinefw.generator — OutlineGenerator

Framework-agnostischer Outline-Generator.
LLM-Calls via iil-aifw (action_code routing).
Kein Django, kein DB.

Usage:
    gen = OutlineGenerator(llm_router)
    result = gen.generate(context, framework="save_the_cat", chapter_count=15)
    result = gen.expand_beat(context, beat_title="Midpoint", sub_count=3)
"""
from __future__ import annotations

import logging
from typing import Protocol

from .frameworks import FRAMEWORKS, get_framework
from .parser import parse_nodes
from .schemas import OutlineNode, OutlineResult, ProjectContext

logger = logging.getLogger(__name__)


class LLMRouter(Protocol):
    """Minimales Interface — kompatibel mit writing-hub LLMRouter."""
    def completion(
        self,
        action_code: str,
        messages: list[dict],
        quality_level: int | None = None,
        priority: str = "balanced",
    ) -> str: ...


class OutlineGenerator:
    """
    Generiert Outlines via LLM.

    Entkoppelt von Django/DB — nimmt einen LLMRouter entgegen,
    der das aifw-Routing kapselt.
    """

    def __init__(self, router: LLMRouter):
        self._router = router

    def generate(
        self,
        context: ProjectContext,
        framework: str = "three_act",
        chapter_count: int = 12,
        quality_level: int | None = None,
    ) -> OutlineResult:
        """
        Vollständige Outline generieren.

        Args:
            context:       Projektkontext (Titel, Genre, Premise, …)
            framework:     Key aus FRAMEWORKS
            chapter_count: Anzahl Kapitel/Beats
            quality_level: aifw quality routing (optional)

        Returns:
            OutlineResult mit nodes oder error
        """
        fw = get_framework(framework)
        beats_str = ", ".join(fw["beats"])
        ctx_block = context.to_prompt_block()

        messages = [
            {
                "role": "system",
                "content": (
                    f"Du bist ein Buchstruktur-Experte. "
                    f"Erstelle eine Outline nach der {fw['name']}-Methode.\n\n"
                    f"{ctx_block}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Erstelle eine Outline mit genau {chapter_count} Kapiteln/Beats "
                    f"nach der {fw['name']}-Struktur ({fw['description']}).\n\n"
                    f"Framework-Beats als Orientierung: {beats_str}\n\n"
                    "Gib ein JSON-Array zurück:\n"
                    '[{"order": 1, "title": "...", "description": "2-3 Sätze", '
                    '"beat_type": "chapter", "beat": "...", "act": "act_1", '
                    '"emotional_arc": "...", "notes": ""}, ...]\n\n'
                    f"Exakt {chapter_count} Einträge. Nur JSON, kein erklärender Text."
                ),
            },
        ]

        try:
            raw = self._router.completion(
                "outline_generate",
                messages,
                quality_level=quality_level,
                priority="quality",
            )
            nodes = parse_nodes(raw)
            if not nodes:
                return OutlineResult(
                    success=False,
                    framework=framework,
                    error="LLM-Antwort enthielt keine gültigen Nodes.",
                )
            return OutlineResult(success=True, nodes=nodes, framework=framework)

        except Exception as exc:
            logger.error("OutlineGenerator.generate Fehler: %s", exc)
            return OutlineResult(success=False, framework=framework, error=str(exc))

    def expand_beat(
        self,
        context: ProjectContext,
        beat_title: str,
        beat_description: str = "",
        sub_count: int = 3,
        quality_level: int | None = None,
    ) -> OutlineResult:
        """Einzelnen Beat in Sub-Kapitel/Szenen aufbrechen."""
        ctx_block = context.to_prompt_block()

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein Buchstruktur-Experte. "
                    "Entwickle einen Outline-Beat in konkrete Szenen aus.\n\n"
                    f"{ctx_block}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Beat: {beat_title}\n"
                    + (f"Beschreibung: {beat_description}\n" if beat_description else "")
                    + f"\nErarbeite {sub_count} konkrete Szenen/Sub-Kapitel.\n"
                    'JSON-Array: [{"order": 1, "title": "...", '
                    '"description": "...", "beat_type": "scene", "beat": "..."}]'
                ),
            },
        ]

        try:
            raw = self._router.completion(
                "outline_beat_expand",
                messages,
                quality_level=quality_level,
            )
            nodes = parse_nodes(raw)
            return OutlineResult(success=True, nodes=nodes)
        except Exception as exc:
            logger.error("OutlineGenerator.expand_beat Fehler: %s", exc)
            return OutlineResult(success=False, error=str(exc))

    @staticmethod
    def context_from_dict(data: dict) -> ProjectContext:
        """Convenience: dict → ProjectContext."""
        return ProjectContext(**{k: v for k, v in data.items() if k in ProjectContext.model_fields})
