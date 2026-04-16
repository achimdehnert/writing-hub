"""
Project Context Service — schreibt akkumulierten Projekt-Kontext
fuer LLM-Prompts zusammen.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from apps.authoring.defaults import (
    CHAR_DESC_MAX_CHARS,
    CHAR_MOTIVATION_MAX_CHARS,
    DEFAULT_CONTENT_TYPE,
    MAX_STYLE_DONT_ITEMS,
    MAX_STYLE_SIGNATURE_MOVES,
    MAX_STYLE_TABOO_ITEMS,
    STYLE_PROMPT_MAX_CHARS,
    VOICE_PATTERN_MAX_CHARS,
    WORLD_DESC_MAX_CHARS,
)

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Vollstaendiger Projekt-Kontext fuer LLM-Prompts."""

    project_id: str = ""
    title: str = ""
    genre: str = ""
    description: str = ""
    content_type: str = DEFAULT_CONTENT_TYPE
    target_audience: str = ""
    target_word_count: int = 0

    premise: str = ""
    themes: list[str] = field(default_factory=list)
    logline: str = ""

    characters: list[dict[str, Any]] = field(default_factory=list)
    worlds: list[dict[str, Any]] = field(default_factory=list)

    outline_nodes: list[dict[str, Any]] = field(default_factory=list)
    chapter_summaries: list[str] = field(default_factory=list)

    author_style: dict[str, Any] = field(default_factory=dict)
    writing_style_prompt: str = ""

    def to_prompt_block(self) -> str:
        """Kontext als kompakter Text-Block fuer LLM-System-Prompt."""
        lines = [f"# Buchprojekt: {self.title}"]
        if self.content_type:
            lines.append(f"Inhaltstyp: {self.content_type}")
        if self.genre:
            lines.append(f"Genre: {self.genre}")
        if self.target_audience:
            lines.append(f"Zielgruppe: {self.target_audience}")
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
                role = ch.get('narrative_role') or ch.get('role', '?')
                desc = ch.get('description', '')[:CHAR_DESC_MAX_CHARS]
                motivation = ch.get('motivation', '')
                line = f"- {ch.get('name', '?')} ({role}): {desc}"
                if motivation:
                    line += f" | Motivation: {motivation[:CHAR_MOTIVATION_MAX_CHARS]}"
                if ch.get('voice_pattern'):
                    line += f" | Stimme: {ch['voice_pattern'][:VOICE_PATTERN_MAX_CHARS]}"
                if ch.get('secret'):
                    line += f" | Geheimnis: {ch['secret'][:VOICE_PATTERN_MAX_CHARS]}"
                if ch.get('want'):
                    line += f" | Will: {ch['want'][:CHAR_MOTIVATION_MAX_CHARS]}"
                if ch.get('need'):
                    line += f" | Braucht: {ch['need'][:CHAR_MOTIVATION_MAX_CHARS]}"
                if ch.get('flaw'):
                    line += f" | Schwaeche: {ch['flaw'][:CHAR_MOTIVATION_MAX_CHARS]}"
                lines.append(line)
        if self.worlds:
            lines.append("\n## Weltenbau")
            for w in self.worlds:
                desc = w.get('description', '')[:WORLD_DESC_MAX_CHARS]
                atmosphere = w.get('atmosphere', '')
                line = f"- {w.get('name', '?')}: {desc}"
                if atmosphere:
                    line += f" | Atmosphaere: {atmosphere[:WORLD_DESC_MAX_CHARS]}"
                lines.append(line)
        if self.writing_style_prompt or self.author_style:
            lines.append("\n## Autorenstil")
            if self.writing_style_prompt:
                lines.append(self.writing_style_prompt[:STYLE_PROMPT_MAX_CHARS])
            if self.author_style.get("name"):
                lines.append(f"Stil-Profil: {self.author_style['name']}")
            if self.author_style.get("signature_moves"):
                lines.append(
                    "Stilmittel: "
                    + ", ".join(self.author_style["signature_moves"][:MAX_STYLE_SIGNATURE_MOVES])
                )
            if self.author_style.get("do_list"):
                lines.append(
                    "DO (empfohlen): "
                    + ", ".join(self.author_style["do_list"][:MAX_STYLE_SIGNATURE_MOVES])
                )
            if self.author_style.get("dont_list"):
                lines.append(
                    "DONT (vermeiden): "
                    + ", ".join(self.author_style["dont_list"][:MAX_STYLE_DONT_ITEMS])
                )
            if self.author_style.get("taboo_list"):
                lines.append(
                    "TABU (niemals verwenden): "
                    + ", ".join(self.author_style["taboo_list"][:MAX_STYLE_TABOO_ITEMS])
                )
        return "\n".join(lines)


class ProjectContextService:
    """Laedt Projekt-Kontext aus der DB fuer LLM-Prompts."""

    def get_context(self, project_id: str) -> ProjectContext:
        """Vollstaendigen Kontext fuer ein Buchprojekt laden."""
        from apps.authoring.models import AuthorStyleDNA
        from apps.projects.models import BookProject, OutlineNode, OutlineVersion
        from apps.worlds.models import ProjectCharacterLink, ProjectWorldLink

        try:
            project = BookProject.objects.get(pk=project_id)
        except BookProject.DoesNotExist:
            logger.warning("ProjectContextService: Projekt %s nicht gefunden", project_id)
            return ProjectContext(project_id=str(project_id))

        genre_name = str(project.genre_lookup) if project.genre_lookup_id else project.genre

        ctx = ProjectContext(
            project_id=str(project.pk),
            title=project.title,
            genre=genre_name,
            description=project.description,
            content_type=project.content_type,
            target_audience=project.target_audience or "",
            target_word_count=project.target_word_count or 0,
        )

        # Charaktere — SSoT ist WeltenHub, lokale Links als Referenz
        try:
            char_links = ProjectCharacterLink.objects.filter(project=project)
            characters = []
            for link in char_links:
                try:
                    from weltenfw.django import get_client
                    char = get_client().characters.get(link.weltenhub_character_id)
                    char_entry = {
                        "name": getattr(char, "name", str(link.weltenhub_character_id)),
                        "role": link.project_role or getattr(char, "role", ""),
                        "narrative_role": link.get_narrative_role_display(),
                        "description": (
                            getattr(char, "description", "")
                            or getattr(char, "backstory", "")
                        ),
                        "motivation": getattr(char, "motivation", ""),
                    }
                    if link.voice_pattern:
                        char_entry["voice_pattern"] = link.voice_pattern
                    if link.secret_what:
                        char_entry["secret"] = link.secret_what
                    if link.want:
                        char_entry["want"] = link.want
                    if link.need:
                        char_entry["need"] = link.need
                    if link.flaw:
                        char_entry["flaw"] = link.flaw
                    characters.append(char_entry)
                except Exception:
                    pass
            ctx.characters = characters
        except Exception:
            pass

        # Welten — SSoT ist WeltenHub, lokale Links als Referenz
        try:
            world_links = ProjectWorldLink.objects.filter(project=project)
            worlds = []
            for link in world_links:
                try:
                    from weltenfw.django import get_client
                    world = get_client().worlds.get(link.weltenhub_world_id)
                    worlds.append({
                        "name": getattr(world, "name", str(link.weltenhub_world_id)),
                        "description": getattr(world, "description", ""),
                        "atmosphere": getattr(world, "atmosphere", ""),
                    })
                except Exception:
                    pass
            ctx.worlds = worlds
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

        # Autor-Stil: WritingStyle vom Projekt (primaer) → AuthorStyleDNA (fallback)
        try:
            ws = project.writing_style
            if ws:
                from apps.authors.services import get_style_prompt_for_writing
                ctx.writing_style_prompt = get_style_prompt_for_writing(ws)
                ctx.author_style = {
                    "name": ws.name,
                    "signature_moves": ws.signature_moves or [],
                    "do_list": ws.do_list or [],
                    "dont_list": ws.dont_list or [],
                    "taboo_list": ws.taboo_list or [],
                }
        except Exception:
            pass

        if not ctx.author_style:
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
