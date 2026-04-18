"""
Seed default ProjectTemplate entries (UC 1.5).
Usage: python manage.py seed_templates
"""
from django.core.management.base import BaseCommand

from apps.projects.models import ProjectTemplate


DEFAULTS = [
    {
        "name": "Roman (3-Akt, 80k)",
        "content_type": "novel",
        "framework_key": "three_act",
        "default_target_words": 80000,
        "default_genre": "Belletristik",
        "chapter_count_hint": 25,
        "description": "Klassischer Roman mit Drei-Akt-Struktur. Ideal für Thriller, Liebesroman, Fantasy.",
    },
    {
        "name": "Krimi / Thriller (Save the Cat, 70k)",
        "content_type": "novel",
        "framework_key": "save_the_cat",
        "default_target_words": 70000,
        "default_genre": "Krimi",
        "chapter_count_hint": 20,
        "description": "Spannungsgetriebener Plot mit 15 Beats nach Save the Cat.",
    },
    {
        "name": "Sachbuch / Ratgeber (200 Seiten)",
        "content_type": "nonfiction",
        "framework_key": "sachbuch",
        "default_target_words": 50000,
        "default_genre": "Sachbuch",
        "chapter_count_hint": 12,
        "description": "Strukturierter Ratgeber mit Einleitung, Hauptteil und Fazit.",
    },
    {
        "name": "Wissenschaftlicher Aufsatz (IMRaD)",
        "content_type": "academic",
        "framework_key": "imrad",
        "default_target_words": 8000,
        "default_genre": "",
        "chapter_count_hint": 5,
        "description": "Introduction, Methods, Results, and Discussion — Standard-Paper.",
    },
    {
        "name": "Essay / Kurztext",
        "content_type": "essay",
        "framework_key": "scientific_essay",
        "default_target_words": 5000,
        "default_genre": "",
        "chapter_count_hint": 5,
        "description": "Argumentativer Essay mit These, Argumentation, Schluss.",
    },
    {
        "name": "Novelle (Heros Journey, 40k)",
        "content_type": "novel",
        "framework_key": "heros_journey",
        "default_target_words": 40000,
        "default_genre": "Fantasy",
        "chapter_count_hint": 15,
        "description": "Kürzere Erzählung mit klassischer Heldenreise.",
    },
]


class Command(BaseCommand):
    help = "Seed default ProjectTemplate entries for UC 1.5"

    def handle(self, *args, **options):
        created = 0
        for tpl_data in DEFAULTS:
            _, was_created = ProjectTemplate.objects.get_or_create(
                name=tpl_data["name"],
                defaults={
                    **tpl_data,
                    "is_system": True,
                    "is_active": True,
                    "owner": None,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"{created} Templates angelegt, {len(DEFAULTS) - created} existierten bereits."
        ))
