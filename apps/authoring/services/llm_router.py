"""
LLM Router — aifw-basiertes Routing (ADR-095).

Alle LLM-Calls ausschliesslich via aifw.sync_completion / aifw.completion.
Kein direkter Zugriff auf openai/anthropic/litellm.

AIActionType wird im Django Admin konfiguriert — kein Code-Change noetig.
"""

import logging
from typing import Any

from aifw import sync_completion

logger = logging.getLogger(__name__)

_TIER_QUALITY_MAP = {
    "free": 1,
    "basic": 3,
    "standard": 5,
    "premium": 8,
    "enterprise": 10,
}


class LLMRoutingError(Exception):
    """Kein passendes LLM fuer diesen Action-Code konfiguriert."""


def get_quality_level_for_tier(tier: str) -> int | None:
    """Tenant-Tier → quality_level (ADR-095). None = catch-all."""
    return _TIER_QUALITY_MAP.get(tier.lower()) if tier else None


class LLMRouter:
    """
    Einheitlicher LLM-Router via aifw.

    Alle action_codes werden im Django Admin unter AIActionType konfiguriert.
    Writing-Hub Action-Codes:
      - chapter_write          — Kapitel schreiben
      - chapter_brief          — Kapitel-Brief generieren
      - chapter_analyze        — Kapitel-Qualitaetsanalyse
      - character_generate     — Charaktere generieren
      - outline_generate       — Outline generieren
      - outline_beat_expand    — Beat ausarbeiten
      - idea_generate          — Buchideen generieren
      - idea_to_premise        — Idee zu Premise ausarbeiten
      - style_check            — Stil-Check
    """

    def completion(
        self,
        action_code: str,
        messages: list[dict[str, Any]],
        quality_level: int | None = None,
        priority: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Synchroner LLM-Call via aifw.

        Args:
            action_code: AIActionType.code (z.B. "chapter_write")
            messages: OpenAI-Format [{"role": "user", "content": "..."}]
            quality_level: 1-10, None = catch-all (ADR-097)
            priority: "quality"|"balanced"|"fast"|None

        Returns:
            Antwort-String

        Raises:
            LLMRoutingError: kein AIActionType konfiguriert oder aifw-Fehler
        """
        from aifw.exceptions import ConfigurationError

        try:
            result = sync_completion(
                action_code=action_code,
                messages=messages,
                quality_level=quality_level,
                priority=priority,
                **kwargs,
            )
        except ConfigurationError as exc:
            raise LLMRoutingError(
                f"aifw Konfigurationsfehler fuer '{action_code}': {exc}"
            ) from exc

        if result.success:
            logger.debug(
                "LLMRouter: action=%s model=%s ql=%s",
                action_code,
                result.model,
                quality_level,
            )
            return result.content

        raise LLMRoutingError(
            f"aifw completion fehlgeschlagen fuer '{action_code}': {result.error}"
        )

    async def async_completion(
        self,
        action_code: str,
        messages: list[dict[str, Any]],
        quality_level: int | None = None,
        priority: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Async LLM-Call via aifw."""
        from aifw import completion as aifw_completion
        from aifw.exceptions import ConfigurationError

        try:
            result = await aifw_completion(
                action_code=action_code,
                messages=messages,
                quality_level=quality_level,
                priority=priority,
                **kwargs,
            )
        except ConfigurationError as exc:
            raise LLMRoutingError(
                f"aifw Konfigurationsfehler fuer '{action_code}': {exc}"
            ) from exc

        if result.success:
            return result.content

        raise LLMRoutingError(
            f"aifw async completion fehlgeschlagen fuer '{action_code}': {result.error}"
        )

    def get_quality_level_for_tier(self, tier: str) -> int | None:
        """Tier-Name → quality_level. None = catch-all."""
        try:
            return get_quality_level_for_tier(tier)
        except Exception:
            return None
