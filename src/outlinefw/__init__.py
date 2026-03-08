"""
outlinefw — Story Outline Framework (MVP)
==========================================

Pure-Python, framework-agnostic outline generation.
No Django, no DB — only Pydantic schemas + LLM generation logic.

Usage:
    from outlinefw import OutlineGenerator, FRAMEWORKS
    from outlinefw.schemas import OutlineNode, OutlineResult

Later: extracted to iil-outlinefw PyPI package.
"""

from .frameworks import FRAMEWORKS, get_framework
from .generator import OutlineGenerator
from .parser import parse_nodes
from .schemas import OutlineNode, OutlineResult, ProjectContext

__all__ = [
    "FRAMEWORKS",
    "get_framework",
    "OutlineGenerator",
    "parse_nodes",
    "OutlineNode",
    "OutlineResult",
    "ProjectContext",
]
