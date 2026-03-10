import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("idea_import", "0001_initial"),
        ("projects", "0013_publishingprofile"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. CreativeSession without selected_idea FK first
        migrations.CreateModel(
            name="CreativeSession",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="creative_sessions", to=settings.AUTH_USER_MODEL)),
                ("title", models.CharField(max_length=200)),
                ("inspiration", models.TextField(blank=True)),
                ("genre", models.CharField(blank=True, max_length=100)),
                ("style_dna_hint", models.TextField(blank=True)),
                ("phase", models.CharField(
                    choices=[("brainstorming", "Brainstorming"), ("refining", "Verfeinern"), ("premise", "Premise"), ("done", "Abgeschlossen")],
                    default="brainstorming", max_length=20,
                )),
                ("premise", models.TextField(blank=True)),
                ("created_project", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="creative_sessions",
                    to="projects.bookproject",
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "wh_creative_sessions",
                "ordering": ["-updated_at"],
                "verbose_name": "Kreativ-Session",
                "verbose_name_plural": "Kreativ-Sessions",
            },
        ),
        # 2. BookIdea (depends on CreativeSession)
        migrations.CreateModel(
            name="BookIdea",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("session", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ideas",
                    to="idea_import.creativesession",
                )),
                ("title", models.CharField(max_length=300)),
                ("logline", models.TextField()),
                ("hook", models.TextField(blank=True)),
                ("genre", models.CharField(blank=True, max_length=100)),
                ("themes", models.JSONField(default=list)),
                ("rating", models.SmallIntegerField(
                    choices=[(0, "Nicht bewertet"), (1, "\u2665 Schwach"), (2, "\u2665\u2665 Ok"), (3, "\u2665\u2665\u2665 Gut"), (4, "\u2665\u2665\u2665\u2665 Toll")],
                    default=0,
                )),
                ("is_refined", models.BooleanField(default=False)),
                ("refined_logline", models.TextField(blank=True)),
                ("premise", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "wh_book_ideas",
                "ordering": ["session", "order"],
                "verbose_name": "Buchidee",
                "verbose_name_plural": "Buchideen",
            },
        ),
        # 3. Add selected_idea FK to CreativeSession (after BookIdea exists)
        migrations.AddField(
            model_name="creativesession",
            name="selected_idea",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="selected_for_sessions",
                to="idea_import.bookidea",
            ),
        ),
    ]
