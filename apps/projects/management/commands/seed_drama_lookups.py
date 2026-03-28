"""
Management Command: seed_drama_lookups (ADR-158)

Idempotent Seed für:
  1. TurningPointTypeLookup (12 Drei-Akte-Typen)
  2. GenrePromiseLookup     (9 Genre-Versprechen)
  3. QualityDimension       (5 dramaturgische Dimensionen)

Usage:
    python manage.py seed_drama_lookups
    python manage.py seed_drama_lookups --force
"""
from django.core.management.base import BaseCommand


TURNING_POINT_TYPES = [
    dict(
        code="opening_image",
        label="Opening Image",
        description="Erste Szene — zeigt den Status Quo VOR der Veränderung.",
        default_position_percent=1,
        mirrors_type_code="closing_image",
        sort_order=1,
    ),
    dict(
        code="inciting_incident",
        label="Inciting Incident",
        description="Das auslösende Ereignis — die Welt ändert sich.",
        default_position_percent=10,
        sort_order=2,
    ),
    dict(
        code="debate",
        label="Debate",
        description="Figur zögert — soll sie die neue Welt betreten?",
        default_position_percent=12,
        sort_order=3,
    ),
    dict(
        code="break_into_2",
        label="Break into Act II",
        description="Kein Zurück — Figur betritt die neue Welt.",
        default_position_percent=25,
        sort_order=4,
    ),
    dict(
        code="b_story_begins",
        label="B-Story beginnt",
        description="Thematischer Spiegel beginnt — typisch Liebesinteresse/Mentor.",
        default_position_percent=37,
        sort_order=5,
    ),
    dict(
        code="midpoint",
        label="Midpoint",
        description="Scheinsieg / Scheinniederlage — Stakes steigen.",
        default_position_percent=50,
        sort_order=6,
    ),
    dict(
        code="bad_guys_close",
        label="Bad Guys Close In",
        description="Alles wird schlimmer — äußerer und innerer Druck steigt.",
        default_position_percent=62,
        sort_order=7,
    ),
    dict(
        code="all_is_lost",
        label="All Is Lost",
        description="Tiefpunkt — das Gegenteil des Midpoints.",
        default_position_percent=75,
        sort_order=8,
    ),
    dict(
        code="dark_night",
        label="Dark Night of the Soul",
        description="Figur gibt (fast) auf — Reflexion vor dem Finale.",
        default_position_percent=78,
        sort_order=9,
    ),
    dict(
        code="break_into_3",
        label="Break into Act III",
        description="Neue Erkenntnis — A-Story und B-Story verbinden sich.",
        default_position_percent=87,
        sort_order=10,
    ),
    dict(
        code="climax",
        label="Climax",
        description="Finale Konfrontation — der Kern des Romans.",
        default_position_percent=98,
        sort_order=11,
    ),
    dict(
        code="closing_image",
        label="Closing Image",
        description="Letzte Szene — neue Normalwelt, spiegelt Opening Image.",
        default_position_percent=100,
        mirrors_type_code="opening_image",
        sort_order=12,
    ),
]

GENRE_PROMISES = [
    dict(
        genre_slug="thriller",
        genre_label="Thriller",
        core_promise=(
            "Eskalation bis zur letzten Seite. Alle Geheimnisse aufgelöst. "
            "Spannung nie unter dem Eröffnungslevel."
        ),
        reader_expectation=(
            "Clock is ticking. Protagonist in echtem Danger. "
            "Antagonist einen Schritt voraus."
        ),
        must_haves=["Bedrohung ab Seite 1", "Clock is ticking", "Alle Fäden aufgelöst"],
        must_not_haves=["Deus Ex Machina", "Erklärungen statt Handlung"],
        sort_order=1,
    ),
    dict(
        genre_slug="romance",
        genre_label="Romance",
        core_promise=(
            "Emotionale Intensität. HEA (Happily Ever After) oder HFN "
            "(Happy For Now) — PFLICHT, keine Ausnahmen."
        ),
        reader_expectation="Meet-Cute. Obstacles. Black Moment. Reunion.",
        must_haves=["HEA oder HFN", "Emotionaler Schwarzpunkt", "Chemie ab Seite 1"],
        must_not_haves=["Offenes Ende", "Tod des Love Interest"],
        sort_order=2,
    ),
    dict(
        genre_slug="literary",
        genre_label="Literarisch",
        core_promise=(
            "Thematische Tiefe und Stilqualität. Sprache ist das Erlebnis. "
            "Innenwelt über Außenwelt."
        ),
        reader_expectation="Ambiguität erlaubt. Langsame Entfaltung. Sprachliche Dichte.",
        must_haves=["Stilistische Kohärenz", "Thematische Resonanz"],
        must_not_haves=["Klischierte Auflösung", "On-Nose-Dialog"],
        sort_order=3,
    ),
    dict(
        genre_slug="fantasy",
        genre_label="Fantasy",
        core_promise=(
            "Weltenkonsistenz. Magie-System-Integrität. "
            "Die Regeln der Welt gelten auch für den Protagonisten."
        ),
        reader_expectation="Immersives Worldbuilding. Konsequentes Magie-System.",
        must_haves=["Konsistente Weltregeln", "Kosten der Magie"],
        must_not_haves=["Regelbruch ohne Konsequenz", "Info-Dump > 2 Seiten"],
        sort_order=4,
    ),
    dict(
        genre_slug="scifi",
        genre_label="Science-Fiction",
        core_promise=(
            "Wissenschaftliche oder technische Prämisse, konsequent durchgedacht. "
            "Worldbuilding mit innerer Logik."
        ),
        reader_expectation="Sense of Wonder. Technologische Kohärenz.",
        must_haves=["Konsistente Technik-/Wissenschaftsregeln", "Worldbuilding-Tiefe"],
        must_not_haves=["Technologie als Deus Ex Machina"],
        sort_order=5,
    ),
    dict(
        genre_slug="mystery",
        genre_label="Krimi / Mystery",
        core_promise=(
            "Fair-Play-Prinzip: alle Hinweise lagen offen. "
            "Täter identifiziert. Alle relevanten Fragen beantwortet."
        ),
        reader_expectation="Rätsel. Clues. Roter Hering. Befriedigende Auflösung.",
        must_haves=["Fair-Play-Clues", "Täter-Identifikation", "Alle Fäden aufgelöst"],
        must_not_haves=["Versteckte Clues", "Zufällige Auflösung"],
        sort_order=6,
    ),
    dict(
        genre_slug="horror",
        genre_label="Horror",
        core_promise=(
            "Bedrohung realisiert sich oder bleibt unheimlich — aber nie harmlos. "
            "Kosten sind real."
        ),
        reader_expectation="Angst. Unbehagen. Konsequenzen.",
        must_haves=["Reale Bedrohung", "Kosten für den Protagonisten"],
        must_not_haves=["Alles war nur ein Traum"],
        sort_order=7,
    ),
    dict(
        genre_slug="historical",
        genre_label="Historisch",
        core_promise=(
            "Historische Authentizität im Detail. "
            "Figuren denken und handeln ihrer Zeit entsprechend."
        ),
        reader_expectation="Immersion. Historische Details ohne Info-Dump.",
        must_haves=["Historische Korrektheit", "Zeitgemäße Figurenpsychologie"],
        must_not_haves=["Moderne Denkweise in historischer Figur"],
        sort_order=8,
    ),
    dict(
        genre_slug="ya",
        genre_label="Young Adult",
        core_promise=(
            "Coming-of-Age-Transformation. Protagonistin im Teenager-Alter. "
            "Zugänglicher Stil ohne Vereinfachung."
        ),
        reader_expectation="Identifikation. Erste Male. Emanzipation.",
        must_haves=["Protagonist im Teenager-Alter", "Coming-of-Age-Arc"],
        must_not_haves=["Erwachsenen-Protagonist als Hauptfigur"],
        sort_order=9,
    ),
]

DRAMATIC_QUALITY_DIMENSIONS = [
    dict(
        code="dramaturgic_tension",
        label="Dramaturgische Spannung",
        description=(
            "Ist das Spannungsniveau dieser Szene konsistent mit der "
            "Spannungskurve (tension_numeric)? "
            "Zu flach = Leser verliert Interesse. "
            "Zu hoch ohne Eskalation = Wirkung verpufft."
        ),
        weight=3,
    ),
    dict(
        code="emotional_arc_consistency",
        label="Emotions-Arc-Konsistenz",
        description=(
            "Stimmt das Emotions-Delta (emotion_start → emotion_end) mit "
            "dem Figuren-Arc überein? "
            "Eine Figur darf nicht 'falsch' fühlen."
        ),
        weight=3,
    ),
    dict(
        code="theme_resonance",
        label="Thematische Resonanz",
        description=(
            "Zahlt diese Szene auf das Thema ein? "
            "Jede Szene sollte das Thema berühren — direkt oder durch Kontrast."
        ),
        weight=2,
    ),
    dict(
        code="subtext_quality",
        label="Subtext-Qualität",
        description=(
            "Sprechen Figuren im Dialog ON-NOSE (sagen direkt was sie meinen) "
            "oder mit Subtext? "
            "On-Nose-Dialog ist das häufigste LLM-Schwächezeichen."
        ),
        weight=2,
    ),
    dict(
        code="genre_promise_consistency",
        label="Genre-Versprechen-Konsistenz",
        description=(
            "Hält diese Szene das Genre-Versprechen? "
            "Ein Thriller muss auch in ruhigen Szenen latente Bedrohung erzeugen."
        ),
        weight=2,
    ),
]


class Command(BaseCommand):
    help = "TurningPointTypeLookup, GenrePromiseLookup + QualityDimension seeden (ADR-158)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Bestehende Einträge überschreiben",
        )

    def handle(self, *args, **options):
        force = options["force"]
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== seed_drama_lookups (ADR-158) ==="))

        self._seed_turning_point_types(force)
        self._seed_genre_promises(force)
        self._seed_quality_dimensions(force)

        self.stdout.write(self.style.SUCCESS("\nFertig."))

    def _seed_turning_point_types(self, force: bool) -> None:
        from apps.core.models_lookups_drama import TurningPointTypeLookup
        from decimal import Decimal

        self.stdout.write("\n[1] TurningPointTypeLookup ...")
        created = updated = skipped = 0

        for item in TURNING_POINT_TYPES:
            item.setdefault("mirrors_type_code", "")
            item.setdefault("description", "")
            item.setdefault("outlinefw_beat_name", "")
            normalized = Decimal(str(round(item["default_position_percent"] / 100, 3)))
            obj, was_created = TurningPointTypeLookup.objects.get_or_create(
                code=item["code"],
                defaults={
                    "label": item["label"],
                    "description": item["description"],
                    "default_position_percent": item["default_position_percent"],
                    "default_position_normalized": normalized,
                    "mirrors_type_code": item["mirrors_type_code"],
                    "outlinefw_beat_name": item.get("outlinefw_beat_name", ""),
                    "sort_order": item["sort_order"],
                },
            )
            if was_created:
                created += 1
            elif force:
                for k, v in item.items():
                    if k != "code":
                        setattr(obj, k, v)
                obj.default_position_normalized = normalized
                obj.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            f"   Erstellt: {created}  Aktualisiert: {updated}  Übersprungen: {skipped}"
        )

    def _seed_genre_promises(self, force: bool) -> None:
        from apps.core.models_lookups_drama import GenrePromiseLookup

        self.stdout.write("\n[2] GenrePromiseLookup ...")
        created = updated = skipped = 0

        for item in GENRE_PROMISES:
            obj, was_created = GenrePromiseLookup.objects.get_or_create(
                genre_slug=item["genre_slug"],
                defaults={
                    "genre_label": item["genre_label"],
                    "core_promise": item["core_promise"],
                    "reader_expectation": item.get("reader_expectation", ""),
                    "must_haves": item.get("must_haves", []),
                    "must_not_haves": item.get("must_not_haves", []),
                    "sort_order": item.get("sort_order", 0),
                },
            )
            if was_created:
                created += 1
            elif force:
                for k, v in item.items():
                    if k != "genre_slug":
                        setattr(obj, k, v)
                obj.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            f"   Erstellt: {created}  Aktualisiert: {updated}  Übersprungen: {skipped}"
        )

    def _seed_quality_dimensions(self, force: bool) -> None:
        try:
            from apps.core.models import QualityDimension
        except ImportError:
            self.stdout.write(self.style.WARNING(
                "\n[3] QualityDimension — Modell nicht gefunden, übersprungen."
            ))
            return

        self.stdout.write("\n[3] QualityDimension (dramaturgisch) ...")
        created = updated = skipped = 0

        for item in DRAMATIC_QUALITY_DIMENSIONS:
            obj, was_created = QualityDimension.objects.get_or_create(
                code=item["code"],
                defaults={
                    "label": item["label"],
                    "description": item["description"],
                    "weight": item.get("weight", 1),
                },
            )
            if was_created:
                created += 1
            elif force:
                obj.label = item["label"]
                obj.description = item["description"]
                obj.weight = item.get("weight", 1)
                obj.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            f"   Erstellt: {created}  Aktualisiert: {updated}  Übersprungen: {skipped}"
        )
