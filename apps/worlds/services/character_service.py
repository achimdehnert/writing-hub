"""
World Character Service
========================

Generiert und verwaltet Charaktere via aifw.
SSoT: apps.worlds.models.WorldCharacter + ProjectWorldCharacter (ADR-082)

Kein direkter LLM-Zugriff — ausschliesslich via LLMRouter (aifw).
"""

import json
import logging
import re
from dataclasses import dataclass, field

from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

logger = logging.getLogger(__name__)


@dataclass
class CharacterData:
    name: str
    role: str = "supporting"
    description: str = ""
    motivation: str = ""
    background: str = ""
    personality: str = ""
    appearance: str = ""
    arc: str = ""
    wound: str = ""
    secret: str = ""
    dark_trait: str = ""
    voice_sample: str = ""
    speech_patterns: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class CharacterGenerationResult:
    success: bool
    characters: list[CharacterData] = field(default_factory=list)
    error: str = ""


# Mapping von LLM-Rollen -> WorldCharacter.Role
_ROLE_MAP = {
    "protagonist": "protagonist",
    "hauptfigur": "protagonist",
    "antagonist": "antagonist",
    "bösewicht": "antagonist",
    "boesewicht": "antagonist",
    "deuteragonist": "deuteragonist",
    "mentor": "mentor",
    "love_interest": "love_interest",
    "liebesinteresse": "love_interest",
    "nebencharakter": "supporting",
    "nebenfigur": "supporting",
    "supporting": "supporting",
    "minor": "minor",
    "kleinere rolle": "minor",
}


def _normalize_role(role: str) -> str:
    """LLM-Rollen auf WorldCharacter.Role normalisieren."""
    return _ROLE_MAP.get(role.lower().strip(), "supporting")


class WorldCharacterService:
    """
    Generiert Charaktere per LLM und speichert sie als WorldCharacter (SSoT ADR-082).

    Charaktere gehoeren zu einer Welt (projektunabhaengige SSoT).
    Projekt-Verknuepfung via ProjectWorldCharacter.

    Verwendung:
        svc = WorldCharacterService()

        # Besetzung generieren:
        result = svc.generate_cast(world_id, project_id, count=5)

        # Charakter vertiefen:
        result = svc.enrich_character(world_id, character_id)

        # Speichern:
        saved = svc.save_characters(world_id, project_id, result.characters)
    """

    ACTION_GENERATE = "character_generate"
    ACTION_ENRICH = "character_generate"  # selber action_code, tiefere Prompts

    def __init__(self):
        self._router = LLMRouter()

    def generate_cast(
        self,
        world_id: str,
        project_id: str,
        count: int = 5,
        requirements: str = "",
        quality_level: int | None = None,
    ) -> CharacterGenerationResult:
        """
        Charakter-Besetzung fuer ein Projekt in einer Welt generieren.

        Args:
            world_id: World UUID (SSoT)
            project_id: BookProject UUID
            count: Anzahl zu generierender Charaktere
            requirements: Optionale Anforderungen
            quality_level: ADR-095
        """
        world_ctx = self._get_world_context(world_id)
        project_ctx = self._get_project_context(project_id)
        existing = self._get_existing_character_names(world_id, project_id)

        schema = [
            {
                "name": "string — Charaktername",
                "role": "protagonist|antagonist|deuteragonist|mentor|love_interest|supporting|minor",
                "description": "string — kurze Beschreibung",
                "motivation": "string — Antrieb und Ziele",
                "background": "string — Hintergrundgeschichte",
                "personality": "string — Persoenlichkeitsmerkmale",
                "appearance": "string — physische Beschreibung",
                "arc": "string — Charakterbogen",
                "wound": "string — innere Verletzung/Trauma",
                "secret": "string — verborgenes Geheimnis",
                "tags": ["string"],
            }
        ]

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein kreativer Charakter-Entwickler. "
                    "Erstelle tiefe, glaubwuerdige Romanfiguren passend zur Welt. "
                    "Antworte ausschliesslich mit einem validen JSON-Array.\n\n"
                    + world_ctx
                    + "\n\n"
                    + project_ctx
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generiere {count} Charaktere fuer dieses Projekt und diese Welt."
                    + (f"\nAnforderungen: {requirements}" if requirements else "")
                    + (f"\nBereits vorhanden (nicht duplizieren): {existing}" if existing else "")
                    + f"\n\nJSON-Array-Schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}"
                ),
            },
        ]

        try:
            raw = self._router.completion(
                self.ACTION_GENERATE,
                messages,
                quality_level=quality_level,
            )
            characters = self._parse_characters(raw)
            return CharacterGenerationResult(success=True, characters=characters)

        except LLMRoutingError as exc:
            logger.error("generate_cast Fehler: %s", exc)
            return CharacterGenerationResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_cast unerwarteter Fehler")
            return CharacterGenerationResult(success=False, error=str(exc))

    def enrich_character(
        self,
        world_id: str,
        character_id: str,
        quality_level: int | None = None,
    ) -> CharacterGenerationResult:
        """
        Bestehenden WorldCharacter mit psychologischer Tiefe anreichern.
        Aktualisiert: wound, secret, dark_trait, voice_sample, speech_patterns, arc.
        """
        from apps.worlds.models import WorldCharacter

        try:
            char = WorldCharacter.objects.select_related("world").get(pk=character_id)
        except WorldCharacter.DoesNotExist:
            return CharacterGenerationResult(
                success=False, error=f"Charakter {character_id} nicht gefunden"
            )

        world_ctx = self._get_world_context(world_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein Experte fuer tiefe Romanfiguren. "
                    "Bereichere den Charakter mit psychologischer Tiefe. "
                    "Antworte mit einem JSON-Objekt.\n\n"
                    + world_ctx
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Charakter: {char.name} ({char.get_role_display()})\n"
                    f"Beschreibung: {char.description}\n"
                    f"Motivation: {char.motivation}\n\n"
                    "Entwickle psychologische Tiefe als JSON:\n"
                    "{\n"
                    '  "wound": "innere Verletzung/Trauma (konkret, praegend)",\n'
                    '  "secret": "verborgenes Geheimnis (plot-relevant)",\n'
                    '  "dark_trait": "dunkle Seite/Schattenseite",\n'
                    '  "arc": "vollstaendiger Charakterbogen (Anfang → Transformation → Ende)",\n'
                    '  "voice_sample": "typischer Dialog-Satz (1-2 Saetze)",\n'
                    '  "speech_patterns": "Sprachmuster und Besonderheiten"\n'
                    "}"
                ),
            },
        ]

        try:
            raw = self._router.completion(
                self.ACTION_ENRICH,
                messages,
                quality_level=quality_level,
                priority="quality",
            )
            data = self._extract_json_object(raw)
            enriched = CharacterData(
                name=char.name,
                role=char.role,
                description=char.description,
                motivation=char.motivation,
                background=char.background,
                personality=char.personality,
                appearance=char.appearance,
                arc=data.get("arc", char.arc),
                wound=data.get("wound", ""),
                secret=data.get("secret", ""),
                dark_trait=data.get("dark_trait", ""),
                voice_sample=data.get("voice_sample", ""),
                speech_patterns=data.get("speech_patterns", ""),
            )
            return CharacterGenerationResult(success=True, characters=[enriched])

        except LLMRoutingError as exc:
            logger.error("enrich_character Fehler: %s", exc)
            return CharacterGenerationResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("enrich_character unerwarteter Fehler")
            return CharacterGenerationResult(success=False, error=str(exc))

    def save_characters(
        self,
        world_id: str,
        project_id: str,
        characters: list[CharacterData],
        project_arc_map: dict[str, str] | None = None,
    ) -> int:
        """
        Charaktere als WorldCharacter (SSoT) + ProjectWorldCharacter speichern.

        Args:
            world_id: World UUID
            project_id: BookProject UUID
            characters: Generierte Charaktere
            project_arc_map: {name: project_arc} optionale projekt-spezifische Boegen

        Returns:
            Anzahl gespeicherter Charaktere
        """
        from apps.worlds.models import World, WorldCharacter
        from apps.projects.models import BookProject

        try:
            from apps.worlds.models import ProjectWorldCharacter
            has_pwc = True
        except ImportError:
            has_pwc = False

        try:
            world = World.objects.get(pk=world_id)
            project = BookProject.objects.get(pk=project_id)
        except Exception as exc:
            logger.error("save_characters: %s", exc)
            return 0

        arc_map = project_arc_map or {}
        saved = 0

        for char_data in characters:
            normalized_role = _normalize_role(char_data.role)

            wc, created = WorldCharacter.objects.update_or_create(
                world=world,
                name=char_data.name,
                defaults={
                    "role": normalized_role,
                    "description": char_data.description,
                    "background": char_data.background,
                    "personality": char_data.personality,
                    "appearance": char_data.appearance,
                    "motivation": char_data.motivation,
                    "arc": char_data.arc,
                    "wound": char_data.wound,
                    "secret": char_data.secret,
                    "dark_trait": char_data.dark_trait,
                    "voice_sample": char_data.voice_sample,
                    "speech_patterns": char_data.speech_patterns,
                    "tags": char_data.tags,
                },
            )

            if has_pwc:
                ProjectWorldCharacter.objects.get_or_create(
                    project=project,
                    character=wc,
                    defaults={
                        "project_arc": arc_map.get(char_data.name, char_data.arc),
                        "project_role": normalized_role,
                    },
                )

            saved += 1
            logger.debug(
                "WorldCharacterService: '%s' %s in Welt '%s'",
                char_data.name,
                "erstellt" if created else "aktualisiert",
                world.name,
            )

        return saved

    def apply_enrichment(
        self, character_id: str, enriched: CharacterData
    ) -> bool:
        """Angereicherte Daten auf WorldCharacter schreiben."""
        from apps.worlds.models import WorldCharacter

        try:
            wc = WorldCharacter.objects.get(pk=character_id)
            for attr in [
                "wound", "secret", "dark_trait",
                "voice_sample", "speech_patterns", "arc",
            ]:
                val = getattr(enriched, attr, "")
                if val:
                    setattr(wc, attr, val)
            wc.save()
            return True
        except Exception as exc:
            logger.error("apply_enrichment Fehler: %s", exc)
            return False

    # --- Context helpers ---

    def _get_world_context(self, world_id: str) -> str:
        """Welt-Kontext als Text-Block."""
        try:
            from apps.worlds.models import World
            world = World.objects.get(pk=world_id)
            lines = [f"## Welt: {world.name}"]
            if world.description:
                lines.append(f"Beschreibung: {world.description[:500]}")
            if world.culture:
                lines.append(f"Kultur: {world.culture[:300]}")
            if world.magic_system:
                lines.append(f"Magie/Technologie: {world.magic_system[:300]}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _get_project_context(self, project_id: str) -> str:
        """Projekt-Kontext als Text-Block."""
        try:
            from apps.projects.models import BookProject
            project = BookProject.objects.get(pk=project_id)
            lines = [f"## Projekt: {project.title}"]
            if project.genre:
                lines.append(f"Genre: {project.genre}")
            if project.description:
                lines.append(f"Beschreibung: {project.description[:300]}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _get_existing_character_names(self, world_id: str, project_id: str) -> list[str]:
        """Namen bereits vorhandener Charaktere."""
        try:
            from apps.worlds.models import WorldCharacter
            return list(
                WorldCharacter.objects.filter(world_id=world_id)
                .values_list("name", flat=True)[:50]
            )
        except Exception:
            return []

    @staticmethod
    def _parse_characters(raw: str) -> list[CharacterData]:
        """JSON-Array aus LLM-Antwort parsen."""
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()

        start_arr = raw.find("[")
        start_obj = raw.find("{")
        if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
            raw = raw[start_arr:]
        elif start_obj != -1:
            raw = "[" + raw[start_obj:] + "]"

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = data.get("characters", [data])
            return [
                CharacterData(
                    name=item.get("name", "Unbekannt"),
                    role=item.get("role", "supporting"),
                    description=item.get("description", ""),
                    motivation=item.get("motivation", ""),
                    background=item.get(
                        "background", item.get("backstory", "")
                    ),
                    personality=item.get("personality", ""),
                    appearance=item.get("appearance", ""),
                    arc=item.get("arc", ""),
                    wound=item.get("wound", ""),
                    secret=item.get("secret", ""),
                    dark_trait=item.get("dark_trait", ""),
                    voice_sample=item.get("voice_sample", ""),
                    speech_patterns=item.get("speech_patterns", ""),
                    tags=item.get("tags", []),
                )
                for item in data
                if isinstance(item, dict) and item.get("name")
            ]
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("_parse_characters JSON-Fehler: %s", exc)
            return []

    @staticmethod
    def _extract_json_object(raw: str) -> dict:
        """JSON-Objekt aus LLM-Antwort extrahieren."""
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
        start = raw.find("{")
        if start != -1:
            raw = raw[start:]
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
