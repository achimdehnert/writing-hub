"""
Seed-Command: NarrativeModelLookup + ForeshadowingTypeLookup (ADR-156)

Idempotent — kann beliebig oft ausgeführt werden.
"""
from django.core.management.base import BaseCommand

NARRATIVE_MODELS = [
    {"code": "linear",        "label": "Linear",          "description": "A→B→C→D, Erzählzeit = Story-Zeit", "sort_order": 10},
    {"code": "in_medias_res", "label": "In medias res",   "description": "Beginnt in der Mitte, dann Analepsen", "sort_order": 20},
    {"code": "non_linear",    "label": "Nicht-linear",    "description": "Kapitel-Reihenfolge ≠ Story-Chronologie", "sort_order": 30},
    {"code": "parallel",      "label": "Parallel",        "description": "Mehrere Zeitstränge gleichzeitig", "sort_order": 40},
]

FORESHADOWING_TYPES = [
    {"code": "objekt",      "label": "Objekt",      "description": "Physisches Objekt (Waffe, Brief, Narbe)", "sort_order": 10},
    {"code": "dialog",      "label": "Dialog",      "description": "Gesprochenes Wort mit Doppelbedeutung", "sort_order": 20},
    {"code": "bild",        "label": "Bild/Symbol", "description": "Visuelles Motiv mit späterer Bedeutung", "sort_order": 30},
    {"code": "name",        "label": "Name",        "description": "Name der Figur oder des Ortes enthält Hinweis", "sort_order": 40},
    {"code": "verhalten",   "label": "Verhalten",   "description": "Charakterverhalten, das spätere Entscheidung vorausdeutet", "sort_order": 50},
    {"code": "atmosphaere", "label": "Atmosphäre",  "description": "Stimmung/Setting signalisiert kommendes Ereignis", "sort_order": 60},
]


class Command(BaseCommand):
    help = "Seed NarrativeModelLookup + ForeshadowingTypeLookup (ADR-156) — idempotent"

    def add_arguments(self, parser):
        parser.add_argument("--force-update", action="store_true")

    def handle(self, *args, **options):
        from apps.projects.models_timeline import (
            ForeshadowingTypeLookup,
            NarrativeModelLookup,
        )

        force = options["force_update"]
        stats = {"NarrativeModel": [0, 0, 0], "ForeshadowingType": [0, 0, 0]}

        for data in NARRATIVE_MODELS:
            obj, created = NarrativeModelLookup.objects.get_or_create(
                code=data["code"], defaults=data
            )
            if created:
                stats["NarrativeModel"][0] += 1
            elif force:
                for k, v in data.items():
                    setattr(obj, k, v)
                obj.save()
                stats["NarrativeModel"][1] += 1
            else:
                stats["NarrativeModel"][2] += 1

        for data in FORESHADOWING_TYPES:
            obj, created = ForeshadowingTypeLookup.objects.get_or_create(
                code=data["code"], defaults=data
            )
            if created:
                stats["ForeshadowingType"][0] += 1
            elif force:
                for k, v in data.items():
                    setattr(obj, k, v)
                obj.save()
                stats["ForeshadowingType"][1] += 1
            else:
                stats["ForeshadowingType"][2] += 1

        for name, (c, u, s) in stats.items():
            self.stdout.write(
                self.style.SUCCESS(
                    f"{name}: {c} erstellt, {u} aktualisiert, {s} übersprungen."
                )
            )
