"""
Management Command: seed_turning_point_types

Legt TurningPointTypeLookup-Einträge an (Drei-Akte / Save-the-Cat).
Idempotent: create_or_update via code-Feld.

Usage:
    python manage.py seed_turning_point_types
    python manage.py seed_turning_point_types --force
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.core.models_lookups_drama import TurningPointTypeLookup


TURNING_POINTS = [
    {
        "code": "opening_image",
        "label": "Opening Image",
        "description": "Erste Szene — Status Quo VOR der Veränderung. Spiegelt Closing Image.",
        "default_position_percent": 1,
        "outlinefw_beat_name": "Opening Image",
        "mirrors_type_code": "closing_image",
        "sort_order": 10,
    },
    {
        "code": "inciting_incident",
        "label": "Inciting Incident",
        "description": "Das auslösende Ereignis — bringt den Protagonisten aus der Balance.",
        "default_position_percent": 10,
        "outlinefw_beat_name": "Catalyst",
        "mirrors_type_code": "",
        "sort_order": 20,
    },
    {
        "code": "debate",
        "label": "Debate",
        "description": "Figur zögert — will sie sich wirklich verändern?",
        "default_position_percent": 12,
        "outlinefw_beat_name": "Debate",
        "mirrors_type_code": "",
        "sort_order": 30,
    },
    {
        "code": "break_into_2",
        "label": "Break into Act II",
        "description": "Kein Zurück — Protagonist tritt bewusst in neue Welt ein.",
        "default_position_percent": 25,
        "outlinefw_beat_name": "Break Into Two",
        "mirrors_type_code": "break_into_3",
        "sort_order": 40,
    },
    {
        "code": "b_story_begins",
        "label": "B-Story Start",
        "description": "Thematischer Spiegel beginnt — Liebesinteresse/Mentor tritt auf.",
        "default_position_percent": 37,
        "outlinefw_beat_name": "B Story",
        "mirrors_type_code": "",
        "sort_order": 50,
    },
    {
        "code": "midpoint",
        "label": "Midpoint",
        "description": "Scheinsieg oder Scheinniederlage — Einsatz steigt.",
        "default_position_percent": 50,
        "outlinefw_beat_name": "Midpoint",
        "mirrors_type_code": "",
        "sort_order": 60,
    },
    {
        "code": "bad_guys_close",
        "label": "Bad Guys Close In",
        "description": "Alles wird schlimmer — innere und äußere Dämonen schließen ein.",
        "default_position_percent": 62,
        "outlinefw_beat_name": "Bad Guys Close In",
        "mirrors_type_code": "",
        "sort_order": 70,
    },
    {
        "code": "all_is_lost",
        "label": "All Is Lost",
        "description": "Tiefpunkt — das Gegenteil des Midpoints, oft Tod/Verlust.",
        "default_position_percent": 75,
        "outlinefw_beat_name": "All Is Lost",
        "mirrors_type_code": "",
        "sort_order": 80,
    },
    {
        "code": "dark_night",
        "label": "Dark Night of the Soul",
        "description": "Figur gibt (fast) auf — Moment vor der Erkenntnis.",
        "default_position_percent": 78,
        "outlinefw_beat_name": "Dark Night of the Soul",
        "mirrors_type_code": "",
        "sort_order": 90,
    },
    {
        "code": "break_into_3",
        "label": "Break into Act III",
        "description": "Neue Erkenntnis — A-Story + B-Story verbinden sich zur Lösung.",
        "default_position_percent": 87,
        "outlinefw_beat_name": "Break Into Three",
        "mirrors_type_code": "break_into_2",
        "sort_order": 100,
    },
    {
        "code": "climax",
        "label": "Climax",
        "description": "Finale Konfrontation — Protagonist wendet die neue Wahrheit an.",
        "default_position_percent": 98,
        "outlinefw_beat_name": "Finale",
        "mirrors_type_code": "",
        "sort_order": 110,
    },
    {
        "code": "closing_image",
        "label": "Closing Image",
        "description": "Neue Normalwelt — spiegelt Opening Image, zeigt die Veränderung.",
        "default_position_percent": 100,
        "outlinefw_beat_name": "Final Image",
        "mirrors_type_code": "opening_image",
        "sort_order": 120,
    },
]


class Command(BaseCommand):
    help = "Seed TurningPointTypeLookup (Drei-Akte / Save-the-Cat). Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Bestehende Einträge aktualisieren")

    def handle(self, *args, **options):
        force = options["force"]
        created = updated = skipped = 0

        for data in TURNING_POINTS:
            percent = data["default_position_percent"]
            normalized = Decimal(str(round(percent / 100, 3)))

            obj, is_new = TurningPointTypeLookup.objects.get_or_create(
                code=data["code"],
                defaults={
                    "label": data["label"],
                    "description": data["description"],
                    "default_position_percent": percent,
                    "default_position_normalized": normalized,
                    "outlinefw_beat_name": data["outlinefw_beat_name"],
                    "mirrors_type_code": data["mirrors_type_code"],
                    "sort_order": data["sort_order"],
                },
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  + {obj.code} ({percent}%)"))
            elif force:
                obj.label = data["label"]
                obj.description = data["description"]
                obj.default_position_percent = percent
                obj.default_position_normalized = normalized
                obj.outlinefw_beat_name = data["outlinefw_beat_name"]
                obj.mirrors_type_code = data["mirrors_type_code"]
                obj.sort_order = data["sort_order"]
                obj.save()
                updated += 1
                self.stdout.write(f"  ~ {obj.code} (aktualisiert)")
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTurningPointTypeLookup: {created} neu, {updated} aktualisiert, {skipped} übersprungen."
            )
        )
