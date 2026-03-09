"""
Management Command: check_aifw_config

Diagnostiziert die aktuelle aifw-DB-Konfiguration und zeigt:
  - Alle LLMProvider
  - Alle LLMModel (inkl. defekte mit leerem Namen)
  - Alle AIActionType für writing-hub Action-Codes
  - Ob OPENAI_API_KEY gesetzt ist

Usage:
    python manage.py check_aifw_config
"""
import os

from django.core.management.base import BaseCommand

WRITING_HUB_CODES = [
    "outline.generate", "outline_generate", "chapter_outline",
    "chapter_write", "chapter_brief", "chapter_analyze",
    "idea_extraction", "idea_generate", "character_generate", "style_check",
]


class Command(BaseCommand):
    help = "aifw DB-Konfiguration diagnostizieren."

    def handle(self, *args, **options):
        try:
            from aifw.models import AIActionType, LLMModel, LLMProvider
        except ImportError as exc:
            self.stderr.write(self.style.ERROR(f"aifw Import-Fehler: {exc}"))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== aifw Diagnose ==="))

        # API Key
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            self.stdout.write(self.style.SUCCESS(f"OPENAI_API_KEY: gesetzt ({len(api_key)} Zeichen)"))
        else:
            self.stdout.write(self.style.ERROR("OPENAI_API_KEY: NICHT GESETZT — LLM-Calls werden scheitern!"))

        # Provider
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- LLMProvider ---"))
        providers = LLMProvider.objects.all()
        if not providers:
            self.stdout.write(self.style.ERROR("  Keine Provider in DB!"))
        for p in providers:
            status = "✓" if p.is_active else "✗"
            self.stdout.write(f"  {status} {p.name} | api_key_env={p.api_key_env_var}")

        # Models
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- LLMModel ---"))
        models = LLMModel.objects.select_related("provider").all()
        if not models:
            self.stdout.write(self.style.ERROR("  Keine Models in DB!"))
        for m in models:
            name_ok = bool(m.name.strip())
            status = "✓" if (m.is_active and name_ok) else "✗"
            warn = " ⚠ LEER!" if not name_ok else ""
            self.stdout.write(
                f"  {status} [{m.provider.name}] name='{m.name}'{warn} "
                f"default={m.is_default} active={m.is_active}"
            )

        # ActionTypes
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- AIActionType (writing-hub) ---"))
        missing = []
        for code in WRITING_HUB_CODES:
            rows = AIActionType.objects.filter(
                code=code, quality_level__isnull=True, priority__isnull=True
            ).select_related("default_model__provider")
            if not rows:
                missing.append(code)
                self.stdout.write(self.style.ERROR(f"  ✗ {code}: FEHLT"))
            else:
                for row in rows:
                    model = row.default_model
                    if model and model.name.strip():
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✓ {code}: model='{model.name}' active={row.is_active}"
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"  ✗ {code}: KEIN MODELL (default_model=None oder leer)"
                        ))

        if missing:
            self.stdout.write(self.style.WARNING(
                f"\nFix: python manage.py setup_aifw_actions --force"
            ))
        else:
            self.stdout.write(self.style.SUCCESS("\nAlle Action-Codes konfiguriert."))

        self.stdout.write("")
