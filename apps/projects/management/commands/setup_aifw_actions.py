"""
Management Command: setup_aifw_actions

Legt alle benötigten AIActionType-Einträge für writing-hub an.
Benötigt: aifw installiert, AIActionType-Model verfügbar.

Usage:
    python manage.py setup_aifw_actions
    python manage.py setup_aifw_actions --force  # überschreibt existierende Einträge
"""
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

ACTION_TYPES = [
    {
        "code": "outline.generate",
        "name": "Outline generieren",
        "description": "KI-Outline für Buchprojekte (outlinefw)",
    },
    {
        "code": "outline_generate",
        "name": "Outline generieren (Slug)",
        "description": "Fallback Slug-Variante für outline.generate",
    },
    {
        "code": "chapter_outline",
        "name": "Kapitel-Outline",
        "description": "Einzelne Kapitel-Outlines und Node-Verfeinerung",
    },
    {
        "code": "chapter_write",
        "name": "Kapitel schreiben",
        "description": "Kapitel-Text generieren",
    },
    {
        "code": "idea_extraction",
        "name": "Ideen-Extraktion",
        "description": "Dokument analysieren und Ideen/Charaktere/Welten extrahieren",
    },
]


class Command(BaseCommand):
    help = "Legt AIActionType-Einträge für writing-hub an (ohne Modell-Konfiguration)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Bestehende Einträge aktualisieren",
        )

    def handle(self, *args, **options):
        force = options["force"]

        try:
            from aifw.models import AIActionType
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "aifw nicht installiert oder AIActionType-Model nicht verfügbar."
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for action in ACTION_TYPES:
            code = action["code"]
            try:
                obj, created = AIActionType.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": action["name"],
                        "description": action.get("description", ""),
                    },
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Erstellt: {code}"))
                elif force:
                    obj.name = action["name"]
                    obj.description = action.get("description", "")
                    obj.save(update_fields=["name", "description"])
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"  ↻ Aktualisiert: {code}"))
                else:
                    skipped_count += 1
                    self.stdout.write(f"  — Existiert bereits: {code}")
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  ✗ Fehler bei {code}: {exc}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Fertig: {created_count} erstellt, {updated_count} aktualisiert, {skipped_count} übersprungen."
        ))
        self.stdout.write(self.style.WARNING(
            "WICHTIG: Modell-Konfiguration (LLM Provider, API Key) muss im Django Admin "
            "unter AIActionType für jeden Action-Code eingetragen werden!"
        ))
