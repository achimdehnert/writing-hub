import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0011_lektoratsession"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ManuscriptSnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="snapshots",
                    to="projects.bookproject",
                )),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ("name", models.CharField(max_length=200)),
                ("notes", models.TextField(blank=True)),
                ("chapter_count", models.PositiveIntegerField(default=0)),
                ("word_count", models.PositiveIntegerField(default=0)),
                ("data", models.JSONField(default=dict, help_text="Serialisierter Stand aller Kapitel")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "wh_manuscript_snapshots",
                "ordering": ["-created_at"],
                "verbose_name": "Manuskript-Snapshot",
                "verbose_name_plural": "Manuskript-Snapshots",
            },
        ),
    ]
