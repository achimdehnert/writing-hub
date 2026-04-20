"""
Seed-Command: Befüllt ContentTypeLookup, GenreLookup und AudienceLookup
mit sinnvollen Standardwerten.

Aufruf: python manage.py seed_project_lookups
"""

from django.core.management.base import BaseCommand

from apps.projects.constants import DEFAULT_AUDIENCES, DEFAULT_CONTENT_TYPES, DEFAULT_GENRES
from apps.projects.models import AudienceLookup, ContentTypeLookup, GenreLookup


class Command(BaseCommand):
    help = "Seed ContentTypeLookup, GenreLookup, AudienceLookup mit Standardwerten"

    def handle(self, *args, **options):
        created_ct = 0
        for i, ct in enumerate(DEFAULT_CONTENT_TYPES):
            _, created = ContentTypeLookup.objects.get_or_create(
                slug=ct["slug"],
                defaults={
                    "name": ct["name"],
                    "order": i,
                    "icon": ct["icon"],
                    "subtitle": ct["subtitle"],
                },
            )
            if created:
                created_ct += 1

        created_g = 0
        for i, name in enumerate(DEFAULT_GENRES):
            _, created = GenreLookup.objects.get_or_create(name=name, defaults={"order": i})
            if created:
                created_g += 1

        created_a = 0
        for i, name in enumerate(DEFAULT_AUDIENCES):
            _, created = AudienceLookup.objects.get_or_create(name=name, defaults={"order": i})
            if created:
                created_a += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Seed abgeschlossen: "
                f"{created_ct} Inhaltstypen, {created_g} Genres, {created_a} Zielgruppen angelegt."
            )
        )
