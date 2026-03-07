"""
Outline Generator Service
==========================

Generiert Buchoutlines via aifw (action_code=outline_generate, outline_beat_expand).
Kein direkter LLM-Zugriff.
"""

import json
import logging
import re
from dataclasses import dataclass, field

from .llm_router import LLMRouter, LLMRoutingError
from .project_context_service import ProjectContextService

logger = logging.getLogger(__name__)


@dataclass
class OutlineNode:
    title: str
    description: str = ""
    beat_type: str = "chapter"
    order: int = 0
    notes: str = ""


@dataclass
class OutlineGenerationResult:
    success: bool
    nodes: list[OutlineNode] = field(default_factory=list)
    framework: str = "three_act"
    error: str = ""


FRAMEWORKS = {
    "three_act": {
        "name": "Drei-Akt-Struktur",
        "description": "Klassisch: Setup, Konfrontation, Aufloesung",
        "beats": ["Setup", "Inciting Incident", "Rising Action", "Midpoint",
                  "Crisis", "Climax", "Resolution"],
    },
    "save_the_cat": {
        "name": "Save the Cat",
        "description": "Blake Snyder's 15-Beat Sheet",
        "beats": ["Opening Image", "Theme Stated", "Set-Up", "Catalyst",
                  "Debate", "Break into Two", "B Story", "Fun and Games",
                  "Midpoint", "Bad Guys Close In", "All Is Lost",
                  "Dark Night of the Soul", "Break into Three",
                  "Finale", "Final Image"],
    },
    "heros_journey": {
        "name": "Heldenreise",
        "description": "Joseph Campbell's Monomyth",
        "beats": ["Gewoehnliche Welt", "Ruf des Abenteuers", "Weigerung",
                  "Mentor", "Schwellenueberschreitung", "Tests und Gefaehrten",
                  "Naehe zur tiefsten Hoehle", "Bewaehrungsprobe",
                  "Belohnung", "Rueckkehr", "Auferstehung", "Rueckkehr mit dem Elixier"],
    },
    "five_act": {
        "name": "Fuenf-Akt-Struktur",
        "description": "Shakespeareanische Struktur",
        "beats": ["Exposition", "Steigende Handlung", "Hoehepunkt",
                  "Fallende Handlung", "Katastrophe/Aufloesung"],
    },
}


class OutlineGeneratorService:
    """
    Generiert Buchoutlines per LLM via aifw.

    Verwendung:
        svc = OutlineGeneratorService()
        result = svc.generate_outline(project_id, framework="save_the_cat")
        result = svc.expand_beat(project_id, beat_title="Midpoint", chapter_count=3)
    """

    def __init__(self):
        self._router = LLMRouter()
        self._ctx_service = ProjectContextService()

    def generate_outline(
        self,
        project_id: str,
        framework: str = "three_act",
        chapter_count: int = 20,
        quality_level: int | None = None,
    ) -> OutlineGenerationResult:
        """
        Vollstaendige Outline generieren.

        Args:
            project_id: BookProject UUID
            framework: "three_act"|"save_the_cat"|"heros_journey"|"five_act"
            chapter_count: Anzahl Kapitel/Beats
            quality_level: ADR-095
        """
        ctx = self._ctx_service.get_context(project_id)
        fw = FRAMEWORKS.get(framework, FRAMEWORKS["three_act"])

        messages = [
            {
                "role": "system",
                "content": (
                    f"Du bist ein Buchstruktur-Experte. "
                    f"Erstelle eine Outline nach der {fw['name']}-Methode.\n\n"
                    + ctx.to_prompt_block()
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Erstelle eine Outline mit ca. {chapter_count} Kapiteln/Beats "
                    f"nach der {fw['name']}-Struktur ({fw['description']}).\n\n"
                    f"Framework-Beats als Orientierung: {', '.join(fw['beats'])}\n\n"
                    "Gib ein JSON-Array zurueck:\n"
                    '[{"order": 1, "title": "...", "description": "...", '
                    '"beat_type": "chapter", "notes": "..."}, ...]\n\n'
                    f"Exakt {chapter_count} Eintraege."
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
            nodes = self._parse_nodes(raw)
            return OutlineGenerationResult(
                success=True, nodes=nodes, framework=framework
            )

        except LLMRoutingError as exc:
            logger.error("generate_outline Fehler: %s", exc)
            return OutlineGenerationResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_outline unerwarteter Fehler")
            return OutlineGenerationResult(success=False, error=str(exc))

    def expand_beat(
        self,
        project_id: str,
        beat_title: str,
        beat_description: str = "",
        sub_chapter_count: int = 3,
        quality_level: int | None = None,
    ) -> OutlineGenerationResult:
        """Einen Beat in Sub-Kapitel aufbrechen."""
        ctx = self._ctx_service.get_context(project_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein Buchstruktur-Experte. "
                    "Entwickle einen Outline-Beat in Szenen/Sub-Kapitel aus.\n\n"
                    + ctx.to_prompt_block()
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Beat: {beat_title}\n"
                    + (f"Beschreibung: {beat_description}\n" if beat_description else "")
                    + f"\nErarbeite {sub_chapter_count} konkrete Szenen/Sub-Kapitel. "
                    "JSON-Array: [{\"order\": 1, \"title\": \"...\", "
                    "\"description\": \"...\", \"beat_type\": \"scene\"}]"
                ),
            },
        ]

        try:
            raw = self._router.completion(
                "outline_beat_expand",
                messages,
                quality_level=quality_level,
            )
            nodes = self._parse_nodes(raw)
            return OutlineGenerationResult(success=True, nodes=nodes)

        except LLMRoutingError as exc:
            logger.error("expand_beat Fehler: %s", exc)
            return OutlineGenerationResult(success=False, error=str(exc))

    def save_outline(
        self,
        project_id: str,
        nodes: list[OutlineNode],
        name: str = "KI-generiert",
        user=None,
    ) -> str | None:
        """Outline in DB speichern. Gibt OutlineVersion-ID zurueck."""
        from apps.projects.models import BookProject
        from apps.projects.models import OutlineVersion
        from apps.projects.models import OutlineNode as DBOutlineNode

        try:
            project = BookProject.objects.get(pk=project_id)

            # Alte aktive Versionen deaktivieren
            OutlineVersion.objects.filter(project=project, is_active=True).update(
                is_active=False
            )

            version = OutlineVersion.objects.create(
                project=project,
                name=name,
                source="ai_generated",
                is_active=True,
                created_by=user,
            )

            DBOutlineNode.objects.bulk_create(
                [
                    DBOutlineNode(
                        outline_version=version,
                        title=node.title,
                        description=node.description,
                        beat_type=node.beat_type,
                        order=node.order or (i + 1),
                        notes=node.notes,
                    )
                    for i, node in enumerate(nodes)
                ]
            )
            return str(version.pk)

        except Exception as exc:
            logger.error("save_outline Fehler: %s", exc)
            return None

    @staticmethod
    def _parse_nodes(raw: str) -> list[OutlineNode]:
        """JSON-Array aus LLM-Antwort parsen."""
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()

        start = raw.find("[")
        if start != -1:
            raw = raw[start:]

        try:
            data = json.loads(raw)
            return [
                OutlineNode(
                    title=item.get("title", f"Kapitel {i + 1}"),
                    description=item.get("description", ""),
                    beat_type=item.get("beat_type", "chapter"),
                    order=item.get("order", i + 1),
                    notes=item.get("notes", ""),
                )
                for i, item in enumerate(data)
                if isinstance(item, dict)
            ]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("_parse_nodes JSON-Fehler: %s", exc)
            return []
