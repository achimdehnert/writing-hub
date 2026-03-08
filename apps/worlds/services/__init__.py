"""
Worlds Services — writing-hub

Nutzt iil-weltenfw als REST-Client gegen WeltenHub.
Nutzt iil-aifw für LLM-Generierung.
Nutzt iil-authoringfw-Schemas für typisierte Zwischen-Daten.

Dokumentation:
  https://pypi.org/project/iil-weltenfw/
  https://pypi.org/project/iil-aifw/
  https://pypi.org/project/iil-authoringfw/
"""

from .character_service import CharacterGenerationResult, WorldCharacterService
from .world_builder_service import WorldBuildResult, WorldBuilderService

__all__ = [
    "CharacterGenerationResult",
    "WorldBuilderService",
    "WorldBuildResult",
    "WorldCharacterService",
]
