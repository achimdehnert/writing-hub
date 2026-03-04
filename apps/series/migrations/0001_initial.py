import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BookSeries",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="book_series", to=settings.AUTH_USER_MODEL)),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField(blank=True)),
                ("genre", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_book_series", "ordering": ["title"]},
        ),
        migrations.CreateModel(
            name="SeriesVolume",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("series", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="volumes", to="series.bookseries")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="series_volumes", to="projects.bookproject")),
                ("volume_number", models.PositiveIntegerField(default=1)),
                ("subtitle", models.CharField(blank=True, max_length=300)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "wh_series_volumes", "ordering": ["series", "volume_number"], "unique_together": {("series", "volume_number")}},
        ),
    ]
