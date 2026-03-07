"""
Character Generator Service — Authoring App
=============================================

Wrapper um apps.worlds.services.WorldCharacterService.
Nutzt worlds.models.WorldCharacter als SSoT (ADR-082).

Fuer neue Implementierungen: apps.worlds.services.WorldCharacterService direkt nutzen.
Dieser Service bleibt fuer Rueckwaertskompatibilitaet mit ChapterProductionService.
"""

from apps.worlds.services.character_service import (
    CharacterData,
    CharacterGenerationResult,
    WorldCharacterService,
)

__all__ = [
    "CharacterData",
    "CharacterGenerationResult",
    "WorldCharacterService as CharacterGeneratorService",
]

# Alias fuer Rueckwaertskompatibilitaet
CharacterGeneratorService = WorldCharacterService
