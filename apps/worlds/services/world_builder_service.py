"""
World Builder Service
======================

Generiert Weltenbau-Inhalte via aifw (action_code=world_generate, world_expand).
SSoT: apps.worlds.models.World / WorldLocation / WorldRule

Kein direkter LLM-Zugriff — ausschliesslich via LLMRouter (aifw).
"""

import json
import logging
import re
from dataclasses import dataclass, field

from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

logger = logging.getLogger(__name__)


@dataclass
class WorldBuildResult:
    success: bool
    world_id: str = ""
    name: str = ""
    description: str = ""
    geography: str = ""
    culture: str = ""
    magic_system: str = ""
    technology_level: str = ""
    politics: str = ""
    history: str = ""
    inhabitants: str = ""
    rules: list[dict] = field(default_factory=list)
    locations: list[dict] = field(default_factory=list)
    error: str = ""


class WorldBuilderService:
    """
    Generiert und erweitert Welten per LLM via aifw.

    SSoT: apps.worlds.models — World, WorldLocation, WorldRule, WorldCharacter

    Verwendung:
        svc = WorldBuilderService()
        result = svc.generate_world(project_id, genre="Fantasy")
        result = svc.expand_world(world_id, aspect="magic_system")
        svc.save_world(project_id, result, user=request.user)
    """

    # aifw action_codes fuer Weltenbau
    ACTION_GENERATE = "world_generate"
    ACTION_EXPAND = "world_expand"
    ACTION_LOCATIONS = "world_locations"
    ACTION_RULES = "world_rules"

    def __init__(self):
        self._router = LLMRouter()

    def generate_world(
        self,
        project_id: str,
        genre: str = "",
        tone: str = "",
        keywords: list[str] | None = None,
        quality_level: int | None = None,
    ) -> WorldBuildResult:
        """
        Vollstaendige Welt fuer ein Buchprojekt generieren.

        Args:
            project_id: BookProject UUID
            genre: Buchgenre (z.B. "Fantasy", "Science Fiction")
            tone: Ton (z.B. "dark", "hopeful", "gritty")
            keywords: Thematische Stichwoerter
            quality_level: ADR-095 Quality-Level
        """
        # Projekt-Kontext laden
        project_title = self._get_project_title(project_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein kreativer Weltenbau-Experte fuer Romane. "
                    "Erstelle detaillierte, immersive Welten. "
                    "Antworte mit einem JSON-Objekt."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Erstelle eine vollstaendige Welt fuer das Buchprojekt: '{project_title}'.\n"
                    + (f"Genre: {genre}\n" if genre else "")
                    + (f"Ton: {tone}\n" if tone else "")
                    + (f"Themen: {', '.join(keywords)}\n" if keywords else "")
                    + "\nGib ein JSON-Objekt zurueck:\n"
                    "{\n"
                    '  "name": "Weltname",\n'
                    '  "description": "Kernbeschreibung (2-3 Saetze)",\n'
                    '  "geography": "Geografie und Landschaft",\n'
                    '  "culture": "Kulturen und Gesellschaft",\n'
                    '  "magic_system": "Magie/Technologie-System (leer wenn nicht relevant)",\n'
                    '  "technology_level": "Technologiestand",\n'
                    '  "politics": "Politisches System",\n'
                    '  "history": "Wichtige historische Ereignisse",\n'
                    '  "inhabitants": "Bewohner und Voelker",\n'
                    '  "rules": [{"category": "physics|magic|social", "rule": "...", "importance": "absolute|strong|guideline"}],\n'
                    '  "locations": [{"name": "...", "location_type": "city|region|building", "description": "...", "significance": "..."}]\n'
                    "}"
                ),
            },
        ]

        try:
            raw = self._router.completion(
                self.ACTION_GENERATE,
                messages,
                quality_level=quality_level,
                priority="quality",
            )
            return self._parse_world(raw)

        except LLMRoutingError as exc:
            logger.error("generate_world Fehler: %s", exc)
            return WorldBuildResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_world unerwarteter Fehler")
            return WorldBuildResult(success=False, error=str(exc))

    def expand_world(
        self,
        world_id: str,
        aspect: str,
        quality_level: int | None = None,
    ) -> WorldBuildResult:
        """
        Einen Aspekt einer bestehenden Welt vertiefen.

        Args:
            world_id: World UUID
            aspect: Zu vertiefender Aspekt (z.B. "magic_system", "history", "politics")
            quality_level: ADR-095
        """
        from apps.worlds.models import World

        try:
            world = World.objects.get(pk=world_id)
        except World.DoesNotExist:
            return WorldBuildResult(success=False, error=f"Welt {world_id} nicht gefunden")

        aspect_labels = {
            "geography": "Geografie und Landschaft",
            "culture": "Kulturen und Gesellschaft",
            "magic_system": "Magie- oder Technologie-System",
            "politics": "Politisches System und Machstrukturen",
            "history": "Geschichte und wichtige Ereignisse",
            "inhabitants": "Bewohner, Voelker und Rassen",
            "economy": "Wirtschaft und Ressourcen",
            "religion": "Religion und Glaube",
        }
        aspect_label = aspect_labels.get(aspect, aspect)

        current = getattr(world, aspect, "") or ""

        messages = [
            {
                "role": "system",
                "content": (
                    f"Du bist ein Weltenbau-Experte fuer die Welt '{world.name}'. "
                    f"Beschreibung: {world.description[:300]}\n"
                    "Vertiefe den angeforderten Aspekt erheblich."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Vertiefe: {aspect_label}\n\n"
                    + (f"Bisheriger Stand: {current[:500]}\n\n" if current else "")
                    + f"Schreibe 3-5 ausformulierte Absaetze ueber '{aspect_label}' fuer die Welt '{world.name}'. "
                    "Antworte mit reinem Text (kein JSON)."
                ),
            },
        ]

        try:
            content = self._router.completion(
                self.ACTION_EXPAND,
                messages,
                quality_level=quality_level,
            )
            result = WorldBuildResult(success=True, world_id=world_id, name=world.name)
            setattr(result, aspect, content)
            return result

        except LLMRoutingError as exc:
            logger.error("expand_world Fehler: %s", exc)
            return WorldBuildResult(success=False, error=str(exc))

    def generate_locations(
        self,
        world_id: str,
        count: int = 5,
        location_type: str = "city",
        quality_level: int | None = None,
    ) -> list[dict]:
        """
        Orte fuer eine Welt generieren via aifw action_code=world_locations.
        """
        from apps.worlds.models import World

        try:
            world = World.objects.get(pk=world_id)
        except World.DoesNotExist:
            return []

        messages = [
            {
                "role": "system",
                "content": (
                    f"Weltenbau-Experte fuer '{world.name}'. "
                    f"Beschreibung: {world.description[:300]}\n"
                    "Antworte mit JSON-Array."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generiere {count} {location_type}-Orte fuer die Welt '{world.name}'.\n"
                    "JSON-Array: [{\"name\": \"...\", \"location_type\": \""
                    + location_type
                    + "\", \"description\": \"...\", \"significance\": \"...\"}]"
                ),
            },
        ]

        try:
            raw = self._router.completion(
                self.ACTION_LOCATIONS,
                messages,
                quality_level=quality_level,
            )
            raw = re.sub(r"```json\s*|```", "", raw).strip()
            raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
            start = raw.find("[")
            if start != -1:
                raw = raw[start:]
            return json.loads(raw)
        except Exception as exc:
            logger.error("generate_locations Fehler: %s", exc)
            return []

    def save_world(
        self,
        project_id: str,
        result: WorldBuildResult,
        user=None,
        is_primary: bool = True,
    ) -> str | None:
        """
        WorldBuildResult in DB speichern.
        Legt World + WorldLocation/WorldRule + ProjectWorld an.
        Gibt World-UUID zurueck.
        """
        from apps.projects.models import BookProject
        from apps.worlds.models import World, WorldLocation, WorldRule

        # ProjectWorld ist in apps/worlds/models.py definiert
        # Wir versuchen es zu importieren, fallback wenn nicht vorhanden
        try:
            from apps.worlds.models import ProjectWorld
            has_project_world = True
        except ImportError:
            has_project_world = False

        try:
            project = BookProject.objects.get(pk=project_id)
        except BookProject.DoesNotExist:
            logger.error("save_world: Projekt %s nicht gefunden", project_id)
            return None

        owner = user or project.owner

        world, created = World.objects.get_or_create(
            owner=owner,
            name=result.name,
            defaults={
                "description": result.description,
                "geography": result.geography,
                "culture": result.culture,
                "magic_system": result.magic_system,
                "technology_level": result.technology_level,
                "politics": result.politics,
                "history": result.history,
                "inhabitants": result.inhabitants,
            },
        )

        if not created:
            # Felder aktualisieren
            for field_name in [
                "description", "geography", "culture",
                "magic_system", "technology_level", "politics",
                "history", "inhabitants",
            ]:
                val = getattr(result, field_name, "")
                if val:
                    setattr(world, field_name, val)
            world.save()

        # Weltregeln speichern
        for rule_data in result.rules:
            WorldRule.objects.get_or_create(
                world=world,
                rule=rule_data.get("rule", "")[:500],
                defaults={
                    "category": rule_data.get("category", "social"),
                    "importance": rule_data.get("importance", "strong"),
                    "explanation": rule_data.get("explanation", ""),
                },
            )

        # Locations speichern
        for loc_data in result.locations:
            WorldLocation.objects.get_or_create(
                world=world,
                name=loc_data.get("name", ""),
                defaults={
                    "location_type": loc_data.get("location_type", "city"),
                    "description": loc_data.get("description", ""),
                    "significance": loc_data.get("significance", ""),
                },
            )

        # Projekt-Verknuepfung
        if has_project_world:
            ProjectWorld.objects.get_or_create(
                project=project,
                world=world,
                defaults={"role": "primary" if is_primary else "secondary"},
            )

        logger.info(
            "WorldBuilderService: Welt '%s' %s fuer Projekt %s",
            world.name,
            "erstellt" if created else "aktualisiert",
            project_id,
        )
        return str(world.pk)

    def _get_project_title(self, project_id: str) -> str:
        try:
            from apps.projects.models import BookProject
            return BookProject.objects.get(pk=project_id).title
        except Exception:
            return f"Projekt {project_id}"

    @staticmethod
    def _parse_world(raw: str) -> WorldBuildResult:
        """JSON aus LLM-Antwort parsen."""
        raw = re.sub(r"```json\s*|```", "", raw).strip()
        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()

        start = raw.find("{")
        if start != -1:
            raw = raw[start:]

        try:
            data = json.loads(raw)
            return WorldBuildResult(
                success=True,
                name=data.get("name", "Unbekannte Welt"),
                description=data.get("description", ""),
                geography=data.get("geography", ""),
                culture=data.get("culture", ""),
                magic_system=data.get("magic_system", ""),
                technology_level=data.get("technology_level", ""),
                politics=data.get("politics", ""),
                history=data.get("history", ""),
                inhabitants=data.get("inhabitants", ""),
                rules=data.get("rules", []),
                locations=data.get("locations", []),
            )
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("_parse_world JSON-Fehler: %s", exc)
            return WorldBuildResult(success=False, error=str(exc))
