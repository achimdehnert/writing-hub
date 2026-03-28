"""
Seed-Command: SeriesArcTypeLookup (ADR-155)

Idempotent — kann beliebig oft ausgeführt werden.
"""
from django.core.management.base import BaseCommand

SERIES_ARC_TYPES = [
    {
        "code": "single_arc",
        "label": "Durchgehender Arc",
        "description": "Eine Figur, ein Arc über alle Bände. Auflösung erst im letzten Band.",
        "sort_order": 10,
    },
    {
        "code": "anthology",
        "label": "Anthologie",
        "description": "Jeder Band eigenständig, lose durch Welt/Figuren verbunden. Kein Serien-Arc.",
        "sort_order": 20,
    },
    {
        "code": "escalating_arc",
        "label": "Eskalierender Arc",
        "description": "Jeder Band erhöht die Einsätze. Figur wird über alle Bände hinweg gebrochen und aufgebaut.",
        "sort_order": 30,
    },
    {
        "code": "dual_arc",
        "label": "Doppel-Arc",
        "description": "Haupt-Serien-Arc + Band-eigener Mini-Arc parallel. Beides muss aufgelöst werden.",
        "sort_order": 40,
    },
]


class Command(BaseCommand):
    help = "Seed SeriesArcTypeLookup (ADR-155) — idempotent"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-update",
            action="store_true",
            help="Vorhandene Einträge überschreiben",
        )

    def handle(self, *args, **options):
        from apps.core.models_lookups_drama import SeriesArcTypeLookup

        force = options["force_update"]
        created = updated = skipped = 0

        for data in SERIES_ARC_TYPES:
            obj, was_created = SeriesArcTypeLookup.objects.get_or_create(
                code=data["code"],
                defaults=data,
            )
            if was_created:
                created += 1
            elif force:
                for k, v in data.items():
                    setattr(obj, k, v)
                obj.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"SeriesArcTypeLookup: {created} erstellt, {updated} aktualisiert, {skipped} übersprungen."
            )
        )
