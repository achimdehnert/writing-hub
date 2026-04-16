"""
Worlds Services — writing-hub

Nutzt iil-weltenfw als REST-Client gegen WeltenHub.
Nutzt iil-aifw für LLM-Generierung.
Nutzt iil-authoringfw-Schemas für typisierte Zwischen-Daten.
Nutzt iil-promptfw für strukturierte Prompt-Templates.

Dokumentation:
  https://pypi.org/project/iil-weltenfw/
  https://pypi.org/project/iil-aifw/
  https://pypi.org/project/iil-authoringfw/
  https://pypi.org/project/iil-promptfw/
"""

from .character_service import CharacterGenerationResult, WorldCharacterService
from .location_service import (
    LocationGenerationResult,
    SceneGenerationResult,
    WorldLocationService,
    WorldSceneService,
)
from .outline_extraction_service import (
    extract_from_outline,
    refine_character_with_llm,
    refine_location_with_llm,
    save_extracted_to_project,
)
from .world_builder_service import WorldBuildResult, WorldBuilderService

__all__ = [
    "CharacterGenerationResult",
    "LocationGenerationResult",
    "SceneGenerationResult",
    "WorldBuilderService",
    "WorldBuildResult",
    "WorldCharacterService",
    "WorldLocationService",
    "WorldSceneService",
    "extract_from_outline",
    "save_extracted_to_project",
    "refine_character_with_llm",
    "refine_location_with_llm",
]
