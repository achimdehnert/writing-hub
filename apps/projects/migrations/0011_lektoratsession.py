import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0010_chapterreview_chapterediting"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LektoratSession",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("project", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="lektorat_sessions",
                    to="projects.bookproject",
                )),
                ("created_by", models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ("name", models.CharField(max_length=200, default="Lektorat")),
                ("status", models.CharField(
                    max_length=20,
                    choices=[("pending", "Ausstehend"), ("running", "Wird gepr\u00fcft"), ("done", "Abgeschlossen"), ("error", "Fehler")],
                    default="pending",
                )),
                ("chapter_count", models.PositiveIntegerField(default=0)),
                ("issues_found", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(null=True, blank=True)),
                ("summary", models.TextField(blank=True)),
            ],
            options={"db_table": "wh_lektorat_sessions", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="LektoratIssue",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("session", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="issues",
                    to="projects.lektoratsession",
                )),
                ("node", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="lektorat_issues",
                    to="projects.outlinenode",
                )),
                ("issue_type", models.CharField(
                    max_length=30,
                    choices=[
                        ("consistency", "Konsistenz"),
                        ("logic", "Logik"),
                        ("style", "Stil"),
                        ("character", "Charakter"),
                        ("timeline", "Zeitlinie"),
                        ("pacing", "Pacing"),
                    ],
                    default="consistency",
                )),
                ("severity", models.CharField(
                    max_length=10,
                    choices=[("info", "Info"), ("warning", "Warnung"), ("error", "Fehler")],
                    default="warning",
                )),
                ("description", models.TextField()),
                ("suggestion", models.TextField(blank=True)),
                ("is_resolved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_lektorat_issues", "ordering": ["session", "node__order"]},
        ),
    ]
