"""
Management Command: setup_aifw_actions

Legt vollständige aifw-Konfiguration an:
  1. LLMProvider (OpenAI)
  2. LLMModel (gpt-4o-mini als Standard)
  3. AIActionType für alle writing-hub Action-Codes

Voraussetzung: OPENAI_API_KEY Umgebungsvariable muss gesetzt sein.

Usage:
    python manage.py setup_aifw_actions
    python manage.py setup_aifw_actions --force   # überschreibt existierende Einträge
    python manage.py setup_aifw_actions --model gpt-4o  # anderes Modell
"""
import logging
import os

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

ACTION_CODES = [
    ("outline.generate",   "Outline generieren (outlinefw)",       4000),
    ("outline_generate",   "Outline generieren (Slug-Fallback)",    4000),
    ("chapter_outline",    "Kapitel-Outline / Node-Verfeinerung",   2000),
    ("chapter_write",      "Kapitel schreiben",                     4000),
    ("chapter_brief",      "Kapitel-Brief generieren",              1000),
    ("chapter_analyze",    "Kapitel-Qualitätsanalyse",              2000),
    ("idea_extraction",    "Ideen-Extraktion aus Dokumenten",       4000),
    ("idea_generate",      "Buchideen generieren",                  2000),
    ("character_generate", "Charaktere generieren",                 2000),
    ("style_check",        "Stil-Check",                            2000),
]


class Command(BaseCommand):
    help = "aifw-Konfiguration anlegen: LLMProvider, LLMModel, AIActionTypes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true",
            help="Bestehende Einträge aktualisieren",
        )
        parser.add_argument(
            "--model", default="gpt-4o-mini",
            help="LLM-Modell-Name (Standard: gpt-4o-mini)",
        )
        parser.add_argument(
            "--provider", default="openai",
            help="Provider-Name (Standard: openai)",
        )

    def handle(self, *args, **options):
        force = options["force"]
        model_name = options["model"]
        provider_name = options["provider"]

        try:
            from aifw.models import AIActionType, LLMModel, LLMProvider
        except ImportError as exc:
            self.stderr.write(self.style.ERROR(f"aifw Import-Fehler: {exc}"))
            return

        api_key_env = "OPENAI_API_KEY" if provider_name == "openai" else "LLM_API_KEY"
        if not os.environ.get(api_key_env):
            self.stdout.write(self.style.WARNING(
                f"Hinweis: {api_key_env} nicht gesetzt. "
                "LLMProvider wird trotzdem angelegt."
            ))

        # 1. LLMProvider
        self.stdout.write(f"\n[1] LLMProvider '{provider_name}' ...")
        provider, created = LLMProvider.objects.get_or_create(
            name=provider_name,
            defaults={
                "display_name": provider_name.capitalize(),
                "api_key_env_var": api_key_env,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Provider erstellt: {provider_name}"))
        elif force:
            provider.api_key_env_var = api_key_env
            provider.is_active = True
            provider.save(update_fields=["api_key_env_var", "is_active"])
            self.stdout.write(self.style.WARNING(f"  ↻ Provider aktualisiert: {provider_name}"))
        else:
            self.stdout.write(f"  — Provider existiert: {provider_name}")

        # 2. LLMModel
        self.stdout.write(f"\n[2] LLMModel '{model_name}' ...")
        model_obj, created = LLMModel.objects.get_or_create(
            provider=provider,
            name=model_name,
            defaults={
                "display_name": model_name,
                "max_tokens": 4096,
                "is_active": True,
                "is_default": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Model erstellt: {model_name}"))
        elif force:
            model_obj.is_active = True
            model_obj.is_default = True
            model_obj.save(update_fields=["is_active", "is_default"])
            self.stdout.write(self.style.WARNING(f"  ↻ Model aktualisiert: {model_name}"))
        else:
            self.stdout.write(f"  — Model existiert: {model_name}")

        # 3. AIActionTypes
        self.stdout.write("\n[3] AIActionTypes ...")
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for code, name, max_tokens in ACTION_CODES:
            try:
                obj, created = AIActionType.objects.get_or_create(
                    code=code,
                    quality_level=None,
                    priority=None,
                    defaults={
                        "name": name,
                        "default_model": model_obj,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "is_active": True,
                    },
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {code}"))
                elif force:
                    obj.name = name
                    obj.default_model = model_obj
                    obj.max_tokens = max_tokens
                    obj.is_active = True
                    obj.save(update_fields=["name", "default_model", "max_tokens", "is_active"])
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"  ↻ {code}"))
                else:
                    if obj.default_model is None:
                        obj.default_model = model_obj
                        obj.is_active = True
                        obj.save(update_fields=["default_model", "is_active"])
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(
                            f"  ↻ {code} (kein Modell — automatisch gesetzt)"
                        ))
                    else:
                        skipped_count += 1
                        self.stdout.write(f"  — {code}")
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  ✗ {code}: {exc}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Fertig: {created_count} erstellt, "
            f"{updated_count} aktualisiert, "
            f"{skipped_count} übersprungen."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Provider: {provider_name} | Model: {model_name}"
        ))
