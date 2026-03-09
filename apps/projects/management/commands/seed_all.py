"""
Management Command: seed_all

F\u00fchrt alle Seed-Schritte in der richtigen Reihenfolge aus:
  1. Django Fixtures (Lookups, Quality Dimensions, Gate Decisions)
  2. aifw-Konfiguration (LLMProvider, LLMModel, AIActionTypes)

Idempotent: mehrfach ausf\u00fchrbar, \u00fcberschreibt nichts ohne --force.

Usage:
    python manage.py seed_all
    python manage.py seed_all --force
    python manage.py seed_all --model gpt-4o
    python manage.py seed_all --skip-aifw
    python manage.py seed_all --skip-fixtures
"""
import subprocess
import sys

from django.core.management.base import BaseCommand
from django.core.management import call_command


FIXTURES = [
    "fixtures/initial_lookups.json",
    "fixtures/initial_quality.json",
]


class Command(BaseCommand):
    help = "Alle Stammdaten und aifw-Konfiguration seeden (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Bestehende Eintr\u00e4ge \u00fcberschreiben")
        parser.add_argument("--model", default="gpt-4o-mini", help="LLM-Modell (Standard: gpt-4o-mini)")
        parser.add_argument("--provider", default="openai", help="LLM-Provider (Standard: openai)")
        parser.add_argument("--skip-aifw", action="store_true", help="aifw-Setup \u00fcberspringen")
        parser.add_argument("--skip-fixtures", action="store_true", help="Fixtures \u00fcberspringen")

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== writing-hub seed_all ==="))

        # 1. Fixtures
        if not options["skip_fixtures"]:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[1] Lade Fixtures ..."))
            for fixture in FIXTURES:
                try:
                    call_command("loaddata", fixture, verbosity=0)
                    self.stdout.write(self.style.SUCCESS(f"  \u2713 {fixture}"))
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(f"  ! {fixture}: {exc}"))
        else:
            self.stdout.write("  [1] Fixtures \u00fcbersprungen (--skip-fixtures)")

        # 2. aifw
        if not options["skip_aifw"]:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[2] aifw-Konfiguration ..."))
            try:
                kwargs = {
                    "model": options["model"],
                    "provider": options["provider"],
                }
                if options["force"]:
                    kwargs["force"] = True
                call_command("setup_aifw_actions", **kwargs)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  ! aifw Setup: {exc}"))
        else:
            self.stdout.write("  [2] aifw \u00fcbersprungen (--skip-aifw)")

        self.stdout.write(self.style.SUCCESS("\n=== seed_all abgeschlossen ==="))
