"""
Seed-Command: Befüllt ContentTypeLookup, GenreLookup und AudienceLookup
mit sinnvollen Standardwerten.

Aufruf: python manage.py seed_project_lookups
"""
from django.core.management.base import BaseCommand

from apps.projects.models import AudienceLookup, ContentTypeLookup, GenreLookup

CONTENT_TYPES = [
    ("Roman", "roman"),
    ("Sachbuch", "sachbuch"),
    ("Kurzgeschichte", "kurzgeschichte"),
    ("Drehbuch", "drehbuch"),
    ("Essay", "essay"),
    ("Novelle", "novelle"),
    ("Graphic Novel", "graphic-novel"),
]

GENRES = [
    "Fantasy",
    "Science-Fiction",
    "Thriller",
    "Krimi",
    "Romantik",
    "Horror",
    "Historischer Roman",
    "Literarische Fiktion",
    "Young Adult",
    "Kinderbuch",
    "Autobiografie",
    "Sachbuch",
    "Reisebericht",
    "Humor",
    "Mystery",
]

AUDIENCES = [
    "Erwachsene (18+)",
    "Jugendliche (14–17)",
    "Kinder (8–13)",
    "Kinder (bis 7)",
    "Alle Altersgruppen",
    "Frauen ab 25",
    "Männer ab 25",
    "Business / Fachpublikum",
]


class Command(BaseCommand):
    help = "Seed ContentTypeLookup, GenreLookup, AudienceLookup mit Standardwerten"

    def handle(self, *args, **options):
        created_ct = 0
        for i, (name, slug) in enumerate(CONTENT_TYPES):
            _, created = ContentTypeLookup.objects.get_or_create(
                slug=slug, defaults={"name": name, "order": i}
            )
            if created:
                created_ct += 1

        created_g = 0
        for i, name in enumerate(GENRES):
            _, created = GenreLookup.objects.get_or_create(
                name=name, defaults={"order": i}
            )
            if created:
                created_g += 1

        created_a = 0
        for i, name in enumerate(AUDIENCES):
            _, created = AudienceLookup.objects.get_or_create(
                name=name, defaults={"order": i}
            )
            if created:
                created_a += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Seed abgeschlossen: "
            f"{created_ct} Inhaltstypen, {created_g} Genres, {created_a} Zielgruppen angelegt."
        ))
