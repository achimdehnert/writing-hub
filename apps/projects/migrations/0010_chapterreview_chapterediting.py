import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0009_bookproject_writing_styles_m2m"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChapterReview",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("node", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="reviews",
                    to="projects.outlinenode",
                    verbose_name="Kapitel",
                )),
                ("created_by", models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ("reviewer", models.CharField(max_length=200, default="Autor", verbose_name="Reviewer")),
                ("feedback_type", models.CharField(
                    max_length=20,
                    choices=[("positive", "Positiv"), ("suggestion", "Vorschlag"), ("issue", "Problem"), ("question", "Frage")],
                    default="suggestion",
                )),
                ("feedback", models.TextField(verbose_name="Feedback")),
                ("text_reference", models.TextField(blank=True, verbose_name="Textreferenz")),
                ("is_resolved", models.BooleanField(default=False)),
                ("is_ai_generated", models.BooleanField(default=False)),
                ("ai_agent", models.CharField(max_length=100, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_chapter_reviews", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ChapterEditing",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("node", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="editings",
                    to="projects.outlinenode",
                    verbose_name="Kapitel",
                )),
                ("created_by", models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ("suggestion_type", models.CharField(
                    max_length=30,
                    choices=[
                        ("style", "Stil"), ("clarity", "Kl\u00e4rung"),
                        ("consistency", "Konsistenz"), ("grammar", "Grammatik"),
                        ("pacing", "Pacing"), ("character", "Charakter"),
                    ],
                    default="style",
                )),
                ("original_text", models.TextField(blank=True)),
                ("suggestion", models.TextField(verbose_name="Vorschlag")),
                ("explanation", models.TextField(blank=True)),
                ("is_accepted", models.BooleanField(null=True, blank=True)),
                ("is_ai_generated", models.BooleanField(default=True)),
                ("ai_agent", models.CharField(max_length=100, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_chapter_editings", "ordering": ["-created_at"]},
        ),
    ]
