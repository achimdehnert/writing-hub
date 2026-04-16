"""
Data migration: Populate genre profiles + situation types from fixture,
then link existing WritingStyle/WritingStyleSample to fiction-thriller.
"""
from django.db import migrations


# Mapping legacy WritingStyleSample.situation values → SituationType slugs
LEGACY_SLUG_MAP = {
    "action": "action",
    "dialogue": "dialogue",
    "description": "setting",
    "emotion": "emotional",
    "intro": "chapter-open",
    "outro": "chapter-close",
    "inner": "inner-monologue",
    "exposition": "exposition",
}


def populate_genres_and_link(apps, schema_editor):
    GenreProfile = apps.get_model("authors", "GenreProfile")
    SituationType = apps.get_model("authors", "SituationType")
    WritingStyle = apps.get_model("authors", "WritingStyle")
    WritingStyleSample = apps.get_model("authors", "WritingStyleSample")

    # Create fiction-thriller genre (the default)
    thriller, _ = GenreProfile.objects.get_or_create(
        slug="fiction-thriller",
        defaults={
            "name": "Belletristik / Thriller",
            "name_short": "Thriller",
            "description": "Spannungsliteratur, Psychothriller, Crime Fiction",
            "icon": "\U0001F52A",
            "sort_order": 10,
            "is_active": True,
        },
    )

    # Create the 8 thriller situation types
    thriller_types = [
        ("action", "Actionszene", 10),
        ("dialogue", "Dialog", 20),
        ("setting", "Ortsbeschreibung", 30),
        ("emotional", "Emotionale Szene", 40),
        ("chapter-open", "Kapiteleinstieg", 50),
        ("chapter-close", "Kapitelende / Cliffhanger", 60),
        ("inner-monologue", "Innerer Monolog", 70),
        ("exposition", "Exposition", 80),
    ]
    slug_to_type = {}
    for slug, label, order in thriller_types:
        st, _ = SituationType.objects.get_or_create(
            genre_profile=thriller,
            slug=slug,
            defaults={
                "label": label,
                "sort_order": order,
                "is_active": True,
            },
        )
        slug_to_type[slug] = st

    # Link all existing WritingStyles to fiction-thriller
    WritingStyle.objects.filter(genre_profile__isnull=True).update(
        genre_profile=thriller
    )

    # Link existing WritingStyleSamples to their SituationTypes
    for legacy_key, new_slug in LEGACY_SLUG_MAP.items():
        st = slug_to_type.get(new_slug)
        if st:
            WritingStyleSample.objects.filter(
                situation=legacy_key,
                situation_type__isnull=True,
            ).update(situation_type=st)


def reverse_populate(apps, schema_editor):
    WritingStyle = apps.get_model("authors", "WritingStyle")
    WritingStyleSample = apps.get_model("authors", "WritingStyleSample")
    WritingStyle.objects.all().update(genre_profile=None)
    WritingStyleSample.objects.all().update(situation_type=None)


class Migration(migrations.Migration):

    dependencies = [
        ("authors", "0004_genre_situation_types"),
    ]

    operations = [
        migrations.RunPython(populate_genres_and_link, reverse_populate),
    ]
