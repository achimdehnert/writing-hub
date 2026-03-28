"""
Management Command: seed_all

Führt alle Seed-Schritte in der richtigen Reihenfolge aus:
  1. Django Fixtures (Lookups, Quality Dimensions)
  2. Project Lookups (ContentType, Genre, Audience)
  3. Outline Frameworks (Drei-Akt, Save the Cat, etc.)
  4. aifw-Konfiguration (LLMProvider, LLMModel, AIActionTypes)

Idempotent: mehrfach ausführbar, überschreibt nichts ohne --force.

Usage:
    python manage.py seed_all
    python manage.py seed_all --force
    python manage.py seed_all --skip-aifw
    python manage.py seed_all --skip-fixtures
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


FIXTURES = [
    "fixtures/initial_lookups.json",
    "fixtures/initial_quality.json",
]


class Command(BaseCommand):
    help = "Alle Stammdaten und aifw-Konfiguration seeden (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Bestehende Einträge überschreiben")
        parser.add_argument("--model", default="gpt-4o-mini", help="LLM-Modell (Standard: gpt-4o-mini)")
        parser.add_argument("--provider", default="openai", help="LLM-Provider (Standard: openai)")
        parser.add_argument("--skip-aifw", action="store_true", help="aifw-Setup überspringen")
        parser.add_argument("--skip-fixtures", action="store_true", help="Fixtures überspringen")

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== writing-hub seed_all ==="))
        force = options["force"]

        # 1. Fixtures
        if not options["skip_fixtures"]:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[1] Lade Fixtures ..."))
            for fixture in FIXTURES:
                try:
                    call_command("loaddata", fixture, verbosity=0)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {fixture}"))
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(f"  ! {fixture}: {exc}"))
        else:
            self.stdout.write("  [1] Fixtures übersprungen (--skip-fixtures)")

        # 2. Project Lookups (ContentType, Genre, Audience)
        self.stdout.write(self.style.MIGRATE_HEADING("\n[2] Project Lookups ..."))
        try:
            kwargs = {}
            if force:
                kwargs["force"] = True
            call_command("seed_project_lookups", **kwargs)
            self.stdout.write(self.style.SUCCESS("  ✓ Project Lookups"))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  ! seed_project_lookups: {exc}"))

        # 3. Outline Frameworks
        self.stdout.write(self.style.MIGRATE_HEADING("\n[3] Outline Frameworks ..."))
        try:
            kwargs = {}
            if force:
                kwargs["force"] = True
            call_command("seed_outline_frameworks", **kwargs)
            self.stdout.write(self.style.SUCCESS("  ✓ Outline Frameworks"))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  ! seed_outline_frameworks: {exc}"))

        # 4. Core Lookups (TurningPointTypes + GenrePromises)
        self.stdout.write(self.style.MIGRATE_HEADING("\n[4] Core Dramaturgik-Lookups ..."))
        for cmd in ["seed_turning_point_types", "seed_genre_promises"]:
            try:
                kwargs = {}
                if force:
                    kwargs["force"] = True
                call_command(cmd, **kwargs)
                self.stdout.write(self.style.SUCCESS(f"  ✓ {cmd}"))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  ! {cmd}: {exc}"))

        # 5. aifw
        if not options["skip_aifw"]:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[4] aifw-Konfiguration ..."))
            try:
                kwargs = {
                    "model": options["model"],
                    "provider": options["provider"],
                }
                if force:
                    kwargs["force"] = True
                call_command("setup_aifw_actions", **kwargs)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  ! aifw Setup: {exc}"))
        else:
            self.stdout.write("  [4] aifw übersprungen (--skip-aifw)")

        self.stdout.write(self.style.SUCCESS("\n=== seed_all abgeschlossen ==="))
