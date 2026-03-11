import django.db.models.deletion
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("worlds", "0002_projektlinks"),
        ("projects", "0013_publishingprofile"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectLocationLink",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("project", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="location_links",
                    to="projects.bookproject",
                )),
                ("weltenhub_location_id", models.UUIDField(
                    db_index=True,
                    help_text="UUID des Ortes in WeltenHub (via iil-weltenfw)",
                )),
                ("notes", models.TextField(blank=True, help_text="Projekt-spezifische Notizen zum Ort")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "wh_project_location_links",
                "ordering": ["project"],
                "verbose_name": "Project Location Link",
                "verbose_name_plural": "Project Location Links",
            },
        ),
        migrations.AddConstraint(
            model_name="projectlocationlink",
            constraint=models.UniqueConstraint(
                fields=["project", "weltenhub_location_id"],
                name="unique_project_location",
            ),
        ),
        migrations.CreateModel(
            name="ProjectSceneLink",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("project", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="scene_links",
                    to="projects.bookproject",
                )),
                ("weltenhub_scene_id", models.UUIDField(
                    db_index=True,
                    help_text="UUID der Szene in WeltenHub (via iil-weltenfw)",
                )),
                ("outline_node", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="scene_links",
                    to="projects.outlinenode",
                    help_text="Lokales Kapitel das dieser Szene entspricht",
                )),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "wh_project_scene_links",
                "ordering": ["project"],
                "verbose_name": "Project Scene Link",
                "verbose_name_plural": "Project Scene Links",
            },
        ),
        migrations.AddConstraint(
            model_name="projectscenelink",
            constraint=models.UniqueConstraint(
                fields=["project", "weltenhub_scene_id"],
                name="unique_project_scene",
            ),
        ),
    ]
