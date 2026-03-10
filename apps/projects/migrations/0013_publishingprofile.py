import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0012_manuscriptsnapshot"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PublishingProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="publishing_profile",
                    to="projects.bookproject",
                )),
                ("isbn", models.CharField(max_length=20, blank=True)),
                ("asin", models.CharField(max_length=20, blank=True)),
                ("publisher_name", models.CharField(max_length=200, blank=True, default="Selbstverlag")),
                ("imprint", models.CharField(max_length=200, blank=True)),
                ("copyright_year", models.CharField(max_length=4, blank=True)),
                ("copyright_holder", models.CharField(max_length=200, blank=True)),
                ("language", models.CharField(max_length=10, blank=True, default="de")),
                ("age_rating", models.CharField(max_length=30, blank=True, default="0")),
                ("bisac_category", models.CharField(max_length=200, blank=True)),
                ("keywords", models.TextField(blank=True, help_text="Komma-getrennt, max. 7")),
                ("first_published", models.DateField(null=True, blank=True)),
                ("this_edition", models.DateField(null=True, blank=True)),
                ("status", models.CharField(
                    max_length=20,
                    choices=[
                        ("draft", "Entwurf"),
                        ("review", "In Review"),
                        ("ready", "Druckfertig"),
                        ("published", "Ver\u00f6ffentlicht"),
                    ],
                    default="draft",
                )),
                ("cover_image_url", models.URLField(blank=True)),
                ("cover_notes", models.TextField(blank=True)),
                ("dedication", models.TextField(blank=True)),
                ("foreword", models.TextField(blank=True)),
                ("preface", models.TextField(blank=True)),
                ("afterword", models.TextField(blank=True)),
                ("acknowledgements", models.TextField(blank=True)),
                ("about_author", models.TextField(blank=True)),
                ("bibliography", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "wh_publishing_profiles",
                "verbose_name": "Publishing Profile",
                "verbose_name_plural": "Publishing Profiles",
            },
        ),
    ]
