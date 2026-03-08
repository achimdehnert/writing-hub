"""
outlinefw — Story Outline Framework
=====================================

Pure-Python, framework-agnostic outline generation.
No Django, no DB in core modules.

Usage:
    from outlinefw import OutlineGenerator, FRAMEWORKS
    from outlinefw.schemas import ProjectContext, OutlineResult
"""

from outlinefw.frameworks import FRAMEWORKS, FrameworkDefinition, get_framework, list_frameworks
from outlinefw.generator import LLMRouter, LLMRouterError, LLMRouterTimeout, OutlineGenerator
from outlinefw.parser import parse_nodes
from outlinefw.schemas import (
    ActPhase,
    BeatDefinition,
    GenerationStatus,
    LLMQuality,
    OutlineGenerationError,
    OutlineNode,
    OutlineResult,
    ParseResult,
    ParseStatus,
    ProjectContext,
    TensionLevel,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "OutlineGenerator",
    "LLMRouter",
    "LLMRouterError",
    "LLMRouterTimeout",
    "parse_nodes",
    "ProjectContext",
    "OutlineNode",
    "OutlineResult",
    "ParseResult",
    "BeatDefinition",
    "FrameworkDefinition",
    "OutlineGenerationError",
    "ActPhase",
    "TensionLevel",
    "LLMQuality",
    "GenerationStatus",
    "ParseStatus",
    "FRAMEWORKS",
    "get_framework",
    "list_frameworks",
]
