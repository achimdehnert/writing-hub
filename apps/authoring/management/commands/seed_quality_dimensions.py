"""
Management Command: seed_quality_dimensions

Legt QualityDimension-Lookup-Einträge an.
Idempotent — kann beliebig oft ausgeführt werden.

Ausführen nach erster Migration:
    python manage.py seed_quality_dimensions
"""

from django.core.management.base import BaseCommand

DIMENSIONS = [
    {
        "code": "style",
        "name_de": "Stil",
        "name_en": "Style",
        "description": "Einhaltung des Autorenstils und der Stilrichtlinien.",
        "weight": "1.50",
        "sort_order": 1,
    },
    {
        "code": "genre",
        "name_de": "Genre-Konformität",
        "name_en": "Genre Conformity",
        "description": "Passung zum gewählten Genre (z.B. Fantasy, Thriller).",
        "weight": "1.20",
        "sort_order": 2,
    },
    {
        "code": "scene",
        "name_de": "Szenen-Qualität",
        "name_en": "Scene Quality",
        "description": "Lebendigkeit, Atmosphère und Spannung der Szene.",
        "weight": "1.00",
        "sort_order": 3,
    },
    {
        "code": "serial_logic",
        "name_de": "Serien-Logik",
        "name_en": "Serial Logic",
        "description": "Konsistenz mit vorherigen Kapiteln und Story-Arcs.",
        "weight": "1.30",
        "sort_order": 4,
    },
    {
        "code": "pacing",
        "name_de": "Pacing",
        "name_en": "Pacing",
        "description": "Tempo und Rhythmus des Kapitels.",
        "weight": "0.80",
        "sort_order": 5,
    },
    {
        "code": "dialogue",
        "name_de": "Dialoge",
        "name_en": "Dialogue",
        "description": "Natürlichkeit und Charakterisierung durch Dialoge.",
        "weight": "0.90",
        "sort_order": 6,
    },
]


class Command(BaseCommand):
    help = "Seed QualityDimension Lookup-Daten (idempotent)"

    def handle(self, *args, **options):
        from apps.authoring.models import QualityDimension

        created_count = 0
        updated_count = 0

        for data in DIMENSIONS:
            code = data.pop("code")
            obj, created = QualityDimension.objects.update_or_create(
                code=code,
                defaults=data,
            )
            data["code"] = code
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ Erstellt: {code}"))
            else:
                updated_count += 1
                self.stdout.write(f"  ↩️  Aktualisiert: {code}")

        self.stdout.write(self.style.SUCCESS(f"\nFertig: {created_count} erstellt, {updated_count} aktualisiert."))
