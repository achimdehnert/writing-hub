"""
Migration: Ersetze alte World/WorldCharacter ORM-Models
durch ProjectWorldLink + ProjectCharacterLink (weltenfw-Referenzen).
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("worlds", "0001_initial"),
        ("projects", "0001_initial"),
    ]

    operations = [
        # Alte Tabellen entfernen
        migrations.DeleteModel(name="WorldCharacter"),
        migrations.DeleteModel(name="WorldLocation"),
        migrations.DeleteModel(name="WorldRule"),
        migrations.DeleteModel(name="World"),

        # Neue Link-Tabellen anlegen
        migrations.CreateModel(
            name="ProjectWorldLink",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="world_links",
                        to="projects.bookproject",
                    ),
                ),
                (
                    "weltenhub_world_id",
                    models.UUIDField(
                        db_index=True,
                        help_text="UUID der Welt in WeltenHub (via iil-weltenfw)",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("primary", "Primärwelt"),
                            ("secondary", "Nebenwelt"),
                            ("parallel", "Parallelwelt"),
                        ],
                        default="primary",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "wh_project_world_links",
                "ordering": ["project", "role"],
                "verbose_name": "Project World Link",
                "verbose_name_plural": "Project World Links",
            },
        ),
        migrations.AddConstraint(
            model_name="ProjectWorldLink",
            constraint=models.UniqueConstraint(
                fields=["project", "weltenhub_world_id"],
                name="unique_project_world",
            ),
        ),
        migrations.CreateModel(
            name="ProjectCharacterLink",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="character_links",
                        to="projects.bookproject",
                    ),
                ),
                (
                    "weltenhub_character_id",
                    models.UUIDField(
                        db_index=True,
                        help_text="UUID des Charakters in WeltenHub (via iil-weltenfw)",
                    ),
                ),
                (
                    "project_arc",
                    models.TextField(
                        blank=True,
                        help_text="Projekt-spezifischer Charakterbogen (override)",
                    ),
                ),
                (
                    "project_role",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        help_text="Rolle in diesem Projekt (override)",
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "wh_project_character_links",
                "ordering": ["project"],
                "verbose_name": "Project Character Link",
                "verbose_name_plural": "Project Character Links",
            },
        ),
        migrations.AddConstraint(
            model_name="ProjectCharacterLink",
            constraint=models.UniqueConstraint(
                fields=["project", "weltenhub_character_id"],
                name="unique_project_character",
            ),
        ),
    ]
