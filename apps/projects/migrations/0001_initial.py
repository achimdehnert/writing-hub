import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BookProject",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="book_projects", to=settings.AUTH_USER_MODEL)),
                ("bfagent_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField(blank=True)),
                ("content_type", models.CharField(choices=[("novel", "Roman"), ("nonfiction", "Sachbuch"), ("short_story", "Kurzgeschichte"), ("screenplay", "Drehbuch"), ("essay", "Essay")], default="novel", max_length=20)),
                ("genre", models.CharField(blank=True, max_length=100)),
                ("target_audience", models.CharField(blank=True, max_length=200)),
                ("target_word_count", models.PositiveIntegerField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_book_projects", "ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="OutlineVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outline_versions", to="projects.bookproject")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("name", models.CharField(max_length=200)),
                ("source", models.CharField(default="manual", max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_outline_versions", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OutlineNode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("outline_version", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nodes", to="projects.outlineversion")),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField(blank=True)),
                ("beat_type", models.CharField(choices=[("chapter", "Kapitel"), ("scene", "Szene"), ("beat", "Beat"), ("act", "Akt"), ("part", "Teil")], default="chapter", max_length=20)),
                ("order", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "wh_outline_nodes", "ordering": ["outline_version", "order"]},
        ),
    ]
