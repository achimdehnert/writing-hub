"""
Project Context Service — schreibt akkumulierten Projekt-Kontext
fuer LLM-Prompts zusammen.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Vollstaendiger Projekt-Kontext fuer LLM-Prompts."""

    project_id: str = ""
    title: str = ""
    genre: str = ""
    description: str = ""
    content_type: str = "novel"
    target_word_count: int = 0

    premise: str = ""
    themes: list[str] = field(default_factory=list)
    logline: str = ""

    characters: list[dict[str, Any]] = field(default_factory=list)
    worlds: list[dict[str, Any]] = field(default_factory=list)

    outline_nodes: list[dict[str, Any]] = field(default_factory=list)
    chapter_summaries: list[str] = field(default_factory=list)

    author_style: dict[str, Any] = field(default_factory=dict)

    def to_prompt_block(self) -> str:
        """Kontext als kompakter Text-Block fuer LLM-System-Prompt."""
        lines = [f"# Buchprojekt: {self.title}"]
        if self.genre:
            lines.append(f"Genre: {self.genre}")
        if self.description:
            lines.append(f"Beschreibung: {self.description}")
        if self.premise:
            lines.append(f"Premise: {self.premise}")
        if self.logline:
            lines.append(f"Logline: {self.logline}")
        if self.themes:
            lines.append(f"Themen: {', '.join(self.themes)}")
        if self.characters:
            lines.append("\n## Charaktere")
            for ch in self.characters:
                lines.append(
                    f"- {ch.get('name', '?')} ({ch.get('role', '?')}): "
                    f"{ch.get('description', '')[:200]}"
                )
        if self.worlds:
            lines.append("\n## Weltenbau")
            for w in self.worlds:
                lines.append(
                    f"- {w.get('name', '?')}: {w.get('description', '')[:200]}"
                )
        if self.author_style:
            lines.append("\n## Autorenstil")
            if self.author_style.get("signature_moves"):
                lines.append(
                    "Stilmittel: "
                    + ", ".join(self.author_style["signature_moves"][:5])
                )
            if self.author_style.get("dont_list"):
                lines.append(
                    "Vermeiden: "
                    + ", ".join(self.author_style["dont_list"][:5])
                )
        return "\n".join(lines)


class ProjectContextService:
    """Laedt Projekt-Kontext aus der DB fuer LLM-Prompts."""

    def get_context(self, project_id: str) -> ProjectContext:
        """Vollstaendigen Kontext fuer ein Buchprojekt laden."""
        from apps.projects.models import BookProject, OutlineNode, OutlineVersion
        from apps.worlds.models import World, Character
        from apps.authoring.models import AuthorStyleDNA

        try:
            project = BookProject.objects.get(pk=project_id)
        except BookProject.DoesNotExist:
            logger.warning("ProjectContextService: Projekt %s nicht gefunden", project_id)
            return ProjectContext(project_id=str(project_id))

        ctx = ProjectContext(
            project_id=str(project.pk),
            title=project.title,
            genre=project.genre,
            description=project.description,
            content_type=project.content_type,
            target_word_count=project.target_word_count or 0,
        )

        # Charaktere
        try:
            characters = Character.objects.filter(
                project=project, is_active=True
            ).order_by("role", "name")
            ctx.characters = [
                {
                    "name": c.name,
                    "role": c.role,
                    "description": c.description,
                    "motivation": c.motivation,
                }
                for c in characters
            ]
        except Exception:
            pass

        # Welten
        try:
            worlds = World.objects.filter(project=project, is_active=True)
            ctx.worlds = [
                {
                    "name": w.name,
                    "description": w.description,
                    "atmosphere": w.atmosphere,
                }
                for w in worlds
            ]
        except Exception:
            pass

        # Aktive Outline
        try:
            version = OutlineVersion.objects.filter(
                project=project, is_active=True
            ).order_by("-created_at").first()
            if version:
                nodes = OutlineNode.objects.filter(
                    outline_version=version
                ).order_by("order")
                ctx.outline_nodes = [
                    {
                        "order": n.order,
                        "title": n.title,
                        "description": n.description,
                        "beat_type": n.beat_type,
                    }
                    for n in nodes
                ]
        except Exception:
            pass

        # Autor-Stil (primaeres Profil)
        try:
            style_dna = AuthorStyleDNA.objects.filter(
                author=project.owner, is_primary=True
            ).first()
            if style_dna:
                ctx.author_style = {
                    "name": style_dna.name,
                    "signature_moves": style_dna.signature_moves,
                    "do_list": style_dna.do_list,
                    "dont_list": style_dna.dont_list,
                    "taboo_list": style_dna.taboo_list,
                }
        except Exception:
            pass

        return ctx
