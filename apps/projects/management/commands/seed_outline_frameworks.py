"""
Management-Command: Seed der Standard-Outline-Frameworks in die DB.

Usage:
    python manage.py seed_outline_frameworks
    python manage.py seed_outline_frameworks --force   # Überschreibt bestehende
"""
from django.core.management.base import BaseCommand

from apps.projects.models import OutlineFramework, OutlineFrameworkBeat

FRAMEWORKS = [
    {
        "key": "three_act",
        "name": "Drei-Akt-Struktur",
        "subtitle": "Klassische dramatische Struktur",
        "icon": "bi-layers",
        "order": 10,
        "beats": [
            ("Akt I: Einführung", 1, 10),
            ("Wendepunkt 1", 10, 25),
            ("Akt II: Konfrontation", 25, 50),
            ("Mittelpunkt", 50, 50),
            ("Wendepunkt 2", 75, 75),
            ("Akt III: Auflösung", 75, 100),
        ],
    },
    {
        "key": "save_the_cat",
        "name": "Save the Cat",
        "subtitle": "15 Beats für emotionale Spannung",
        "icon": "bi-star",
        "order": 20,
        "beats": [
            ("Opening Image", 0, 1),
            ("Theme Stated", 1, 5),
            ("Set-Up", 1, 10),
            ("Catalyst", 10, 10),
            ("Debate", 10, 25),
            ("Break into Two", 25, 25),
            ("B Story", 25, 30),
            ("Fun and Games", 30, 50),
            ("Midpoint", 50, 50),
            ("Bad Guys Close In", 50, 75),
            ("All Is Lost", 75, 75),
            ("Dark Night of the Soul", 75, 80),
            ("Break into Three", 80, 80),
            ("Finale", 80, 99),
            ("Final Image", 99, 100),
        ],
    },
    {
        "key": "heros_journey",
        "name": "Heldenreise",
        "subtitle": "12 Schritte nach Campbell",
        "icon": "bi-compass",
        "order": 30,
        "beats": [
            ("Gewöhnliche Welt", 0, 8),
            ("Ruf zum Abenteuer", 8, 15),
            ("Weigerung", 15, 20),
            ("Mentor", 20, 28),
            ("Überschreiten der Schwelle", 28, 35),
            ("Prüfungen & Verbündete", 35, 50),
            ("Die innerste Höhle", 50, 60),
            ("Die große Prüfung", 60, 70),
            ("Belohnung", 70, 75),
            ("Der Rückweg", 75, 85),
            ("Auferstehung", 85, 95),
            ("Rückkehr mit dem Elixier", 95, 100),
        ],
    },
    {
        "key": "five_act",
        "name": "Fünf-Akt-Struktur",
        "subtitle": "Shakespeares dramatisches Modell",
        "icon": "bi-bar-chart-steps",
        "order": 40,
        "beats": [
            ("Akt I: Exposition", 0, 20),
            ("Akt II: Steigende Handlung", 20, 40),
            ("Akt III: Höhepunkt", 40, 60),
            ("Akt IV: Fallende Handlung", 60, 80),
            ("Akt V: Katastrophe / Auflösung", 80, 100),
        ],
    },
    {
        "key": "dan_harmon",
        "name": "Dan Harmon Story Circle",
        "subtitle": "8 Schritte des Story Circle",
        "icon": "bi-arrow-repeat",
        "order": 50,
        "beats": [
            ("You (Held in Komfortzone)", 0, 12),
            ("Need (Etwas fehlt)", 12, 25),
            ("Go (Unbekannte Zone betreten)", 25, 37),
            ("Search (Anpassung / Suche)", 37, 50),
            ("Find (Was gesucht wurde finden)", 50, 62),
            ("Take (Preis zahlen)", 62, 75),
            ("Return (Zurückkehren)", 75, 87),
            ("Change (Veränderung)", 87, 100),
        ],
    },
    {
        "key": "snowflake",
        "name": "Snowflake Method",
        "subtitle": "Randy Ingermanson: Bottom-up Entwicklung",
        "icon": "bi-snow",
        "order": 60,
        "beats": [
            ("Ein-Satz-Zusammenfassung", 0, 5),
            ("Erweiterung auf einen Absatz", 5, 15),
            ("Charakterentwicklung", 15, 30),
            ("Synopsis eine Seite", 30, 45),
            ("Charakterbiografien", 45, 60),
            ("Vollständige Synopsis", 60, 80),
            ("Szenen-Liste", 80, 100),
        ],
    },
    {
        "key": "seven_point",
        "name": "Seven Point Story Structure",
        "subtitle": "Dan Wells: 7 Punkte für starke Geschichten",
        "icon": "bi-7-circle",
        "order": 70,
        "beats": [
            ("Hook", 0, 5),
            ("Plot Turn 1", 5, 25),
            ("Pinch Point 1", 25, 37),
            ("Midpoint", 37, 50),
            ("Pinch Point 2", 50, 62),
            ("Plot Turn 2", 62, 80),
            ("Resolution", 80, 100),
        ],
    },
    {
        "key": "blank",
        "name": "Leere Kapitel",
        "subtitle": "Freie Struktur ohne vordefinierte Beats",
        "icon": "bi-file-earmark-plus",
        "order": 99,
        "beats": [],
    },
]


class Command(BaseCommand):
    help = "Seed der Standard-Outline-Frameworks in die Datenbank"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Vorhandene Frameworks überschreiben",
        )

    def handle(self, *args, **options):
        force = options["force"]
        created = 0
        updated = 0
        skipped = 0

        for fw_data in FRAMEWORKS:
            key = fw_data["key"]
            beats_data = fw_data.pop("beats")
            fw_data.pop("key")

            fw, was_created = OutlineFramework.objects.get_or_create(
                key=key,
                defaults=fw_data,
            )

            if not was_created and force:
                for field, value in fw_data.items():
                    setattr(fw, field, value)
                fw.save()
                fw.beats.all().delete()
                was_created = True
                updated += 1
            elif not was_created:
                skipped += 1
                fw_data["key"] = key
                fw_data["beats"] = beats_data
                continue
            else:
                created += 1

            for i, (beat_name, pos_start, pos_end) in enumerate(beats_data, 1):
                OutlineFrameworkBeat.objects.create(
                    framework=fw,
                    order=i,
                    name=beat_name,
                    position_start=pos_start,
                    position_end=pos_end,
                )

            fw_data["key"] = key
            fw_data["beats"] = beats_data

        self.stdout.write(
            self.style.SUCCESS(
                f"Frameworks: {created} erstellt, {updated} aktualisiert, {skipped} übersprungen"
            )
        )
