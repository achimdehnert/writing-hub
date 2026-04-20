"""
Management Command: seed_genre_promises

Legt GenrePromiseLookup-Einträge an (Genre-Versprechen für LLM Layer 10).
Idempotent: create_or_update via genre_slug.

Usage:
    python manage.py seed_genre_promises
    python manage.py seed_genre_promises --force
"""

from django.core.management.base import BaseCommand

from apps.core.models_lookups_drama import GenrePromiseLookup


GENRE_PROMISES = [
    {
        "genre_slug": "thriller",
        "genre_label": "Thriller",
        "core_promise": (
            "Der Leser erwartet eskalierendes Unwohlsein, eine Bedrohung die real und konkret ist, "
            "und eine tickende Uhr. Spannung entsteht durch Informationsasymmetrie und Kontrolle."
        ),
        "reader_expectation": (
            "Eine Bedrohung tritt bis 10% auf. Der Protagonist ist in echte Gefahr. "
            "Twists sind fair play — nicht aus dem Nichts."
        ),
        "must_haves": [
            "Bedrohung bis Seite/Szene 10%",
            "Clock is ticking (explizit oder implizit)",
            "Informationsasymmetrie: Leser weiß mehr oder weniger als Protagonist",
            "Eskalationskurve — keine Plateaus > 15%",
        ],
        "must_not_haves": [
            "Lange innere Monologe ohne äußere Bedrohung",
            "Twists ohne vorherige Hinweise (Deus-ex-Machina)",
        ],
        "sort_order": 10,
    },
    {
        "genre_slug": "romance",
        "genre_label": "Romance",
        "core_promise": (
            "Der Leser erwartet emotionale Intensität, ein überzeugendes Meet-Cute, "
            "und ein befriedigendes Happy End (HEA oder HFN)."
        ),
        "reader_expectation": (
            "Die Liebesgeschichte ist Hauptstory, nicht Subplot. "
            "Innere Hindernisse (Glaube, Flaw) > äußere Hindernisse. "
            "Obligatorische Szene: Break-up + Reunion."
        ),
        "must_haves": [
            "Meet-Cute oder erstes bedeutungsvolles Aufeinandertreffen",
            "Innerer Konflikt (nicht nur äußere Umstände)",
            "Black Moment / Trennung vor Auflösung",
            "HEA (Happily Ever After) oder HFN (Happy For Now)",
        ],
        "must_not_haves": [
            "Offenes Ende ohne emotionale Auflösung",
            "Protagonist macht keine innere Entwicklung durch",
        ],
        "sort_order": 20,
    },
    {
        "genre_slug": "krimi",
        "genre_label": "Krimi / Kriminalroman",
        "core_promise": (
            "Der Leser erwartet ein faires Rätsel mit lösbaren Hinweisen, "
            "einen kompetenten Ermittler und eine befriedigende Auflösung."
        ),
        "reader_expectation": (
            "Fair Play: alle Hinweise auf den Täter sind im Text. Kein Deus-ex-Machina. Ermittler zeigt Methodik."
        ),
        "must_haves": [
            "Verbrechen (oder Geheimnis) bis Seite/Szene 10%",
            "Fair Play — alle Hinweise sind im Text vorhanden",
            "Ermittler hat eine erkennbare Methodik",
            "Auflösung erklärt alle wesentlichen Fragen",
        ],
        "must_not_haves": [
            "Hinweis der nur dem Autor bekannt war",
            "Täter der nicht zuvor eingeführt wurde (Golden-Rule-Verstoß)",
        ],
        "sort_order": 30,
    },
    {
        "genre_slug": "fantasy",
        "genre_label": "Fantasy",
        "core_promise": (
            "Der Leser erwartet ein kohärentes Weltsystem, Magie mit klaren Kosten, "
            "und eine epische Reise die innere wie äußere Veränderung erzeugt."
        ),
        "reader_expectation": (
            "Die Weltregeln gelten konsistent. Magie hat Preis. "
            "Die Welt fühlt sich bewohnt und lebendig an — nicht nur als Kulisse."
        ),
        "must_haves": [
            "Konsistentes Magiesystem (Kosten + Grenzen definiert)",
            "Welt mit eigener Geschichte und Logik",
            "Innere Reise des Protagonisten spiegelt äußere Welt",
            "Stakes sind klar: Was passiert wenn der Protagonist scheitert?",
        ],
        "must_not_haves": [
            "Magie die Probleme löst ohne Preis (Deus-ex-Machina-Magie)",
            "Weltregeln die sich nach Bedarf ändern",
        ],
        "sort_order": 40,
    },
    {
        "genre_slug": "literarisch",
        "genre_label": "Literarischer Roman",
        "core_promise": (
            "Der Leser erwartet sprachliche Dichte, psychologische Tiefe, "
            "und Ambiguität die zum Nachdenken zwingt — kein einfaches Happy End."
        ),
        "reader_expectation": (
            "Innenwelt > Außenwelt. Sprache ist selbst bedeutungstragend. "
            "Thema wird gezeigt, nicht erklärt. Offene Deutungen sind gewollt."
        ),
        "must_haves": [
            "Sprachliche Präzision — jedes Wort ist gewählt",
            "Psychologische Tiefe der Figuren",
            "Thema wird durch Subtext transportiert, nicht ausgesprochen",
            "Ambiguität am Ende (nicht Unklarheit, sondern bedeutungsvolle Offenheit)",
        ],
        "must_not_haves": [
            "Didaktisches Aussprechen des Themas",
            "Klischee-Auflösungen",
        ],
        "sort_order": 50,
    },
    {
        "genre_slug": "historisch",
        "genre_label": "Historischer Roman",
        "core_promise": (
            "Der Leser erwartet akkurate historische Atmosphäre, "
            "authentische Sprache und Mentalität der Epoche, "
            "und eine Geschichte die nur in dieser Zeit möglich ist."
        ),
        "reader_expectation": (
            "Details sind recherchiert und stimmig. Anachronismen brechen Immersion. "
            "Figuren denken in ihrer Zeit, nicht mit modernen Werten."
        ),
        "must_haves": [
            "Historisch belegte Details (keine Anachronismen)",
            "Mentalität und Weltbild der Epoche (nicht moderne Gedanken)",
            "Geschichte wäre in anderer Epoche nicht möglich",
            "Atmosphäre: Leser fühlt Epoche durch sensorische Details",
        ],
        "must_not_haves": [
            "Anachronistische Sprache oder Werte",
            "Moderne Psychologie in historischen Figuren",
        ],
        "sort_order": 60,
    },
]


class Command(BaseCommand):
    help = "Seed GenrePromiseLookup (Genre-Versprechen für LLM Layer 10). Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Bestehende Einträge aktualisieren")

    def handle(self, *args, **options):
        force = options["force"]
        created = updated = skipped = 0

        for data in GENRE_PROMISES:
            obj, is_new = GenrePromiseLookup.objects.get_or_create(
                genre_slug=data["genre_slug"],
                defaults={
                    "genre_label": data["genre_label"],
                    "core_promise": data["core_promise"],
                    "reader_expectation": data["reader_expectation"],
                    "must_haves": data["must_haves"],
                    "must_not_haves": data["must_not_haves"],
                    "sort_order": data["sort_order"],
                },
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  + {obj.genre_slug}"))
            elif force:
                for field, val in data.items():
                    if field != "genre_slug":
                        setattr(obj, field, val)
                obj.save()
                updated += 1
                self.stdout.write(f"  ~ {obj.genre_slug} (aktualisiert)")
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nGenrePromiseLookup: {created} neu, {updated} aktualisiert, {skipped} übersprungen.")
        )
