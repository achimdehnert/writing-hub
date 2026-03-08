"""
outlinefw.schemas — Pydantic models (pure Python, no Django)
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class OutlineNode(BaseModel):
    """Ein einzelner Beat/Kapitel in einer Outline."""
    order: int = 0
    title: str
    description: str = ""
    beat_type: str = "chapter"  # chapter | scene | beat | act | part
    beat: str = ""              # Framework-Beat-Name z.B. "Midpoint"
    act: str = ""               # act_1 | act_2a | act_2b | act_3
    notes: str = ""
    emotional_arc: str = ""
    tension_level: str = ""     # low | medium | high | peak
    target_words: int = 0


class OutlineResult(BaseModel):
    """Ergebnis einer Outline-Generierung."""
    success: bool
    nodes: list[OutlineNode] = Field(default_factory=list)
    framework: str = "three_act"
    error: str = ""


class ProjectContext(BaseModel):
    """Projektkontext für LLM-Prompts (framework-agnostic)."""
    title: str = ""
    genre: str = ""
    description: str = ""
    premise: str = ""
    logline: str = ""
    themes: str = ""
    target_audience: str = ""
    target_word_count: int = 0
    characters: list[dict] = Field(default_factory=list)
    worlds: list[dict] = Field(default_factory=list)

    def to_prompt_block(self) -> str:
        """Kompakten Kontextblock für LLM-System-Prompt bauen."""
        parts = []
        if self.title:
            parts.append(f"**Titel:** {self.title}")
        if self.genre:
            parts.append(f"**Genre:** {self.genre}")
        if self.description:
            parts.append(f"**Beschreibung:** {self.description}")
        if self.premise:
            parts.append(f"**Premise:** {self.premise}")
        if self.logline:
            parts.append(f"**Logline:** {self.logline}")
        if self.themes:
            parts.append(f"**Themen:** {self.themes}")
        if self.target_audience:
            parts.append(f"**Zielgruppe:** {self.target_audience}")
        if self.target_word_count:
            parts.append(f"**Ziel-Wörter:** {self.target_word_count:,}")
        if self.characters:
            char_lines = ["**Charaktere:**"]
            for c in self.characters[:5]:
                name = c.get("name", "?")
                role = c.get("role", "supporting")
                desc = c.get("description", "")[:100]
                char_lines.append(f"- {name} ({role}): {desc}")
            parts.append("\n".join(char_lines))
        if self.worlds:
            world_lines = ["**Welten/Settings:**"]
            for w in self.worlds[:3]:
                name = w.get("name", "?")
                desc = w.get("description", "")[:100]
                world_lines.append(f"- {name}: {desc}")
            parts.append("\n".join(world_lines))
        return "\n\n".join(parts) if parts else "(kein Kontext)"
