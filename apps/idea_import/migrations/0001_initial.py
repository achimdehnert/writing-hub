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
            name="IdeaImportDraft",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="idea_import_drafts", to="projects.bookproject", verbose_name="Buchprojekt")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="idea_import_drafts", to=settings.AUTH_USER_MODEL, verbose_name="Erstellt von")),
                ("source_filename", models.CharField(blank=True, max_length=255, verbose_name="Quelldatei")),
                ("source_format", models.CharField(blank=True, max_length=10, verbose_name="Quellformat")),
                ("source_text", models.TextField(blank=True, verbose_name="Normalisierter Quelltext")),
                ("extracted_data", models.JSONField(verbose_name="Extrahierte Daten")),
                ("extraction_model", models.CharField(blank=True, max_length=100, verbose_name="Verwendetes LLM")),
                ("status", models.CharField(choices=[("pending_review", "Wartet auf Review"), ("committed", "Vollst\u00e4ndig committed"), ("partial", "Teilweise committed"), ("discarded", "Verworfen")], db_index=True, default="pending_review", max_length=20, verbose_name="Status")),
                ("committed_sections", models.JSONField(default=list, verbose_name="Committete Sektionen")),
                ("commit_notes", models.TextField(blank=True, verbose_name="Commit-Notizen")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")),
                ("committed_at", models.DateTimeField(blank=True, null=True, verbose_name="Committed am")),
            ],
            options={"db_table": "wh_idea_import_drafts", "ordering": ["-created_at"], "verbose_name": "Ideen-Import-Entwurf", "verbose_name_plural": "Ideen-Import-Entw\u00fcrfe"},
        ),
    ]
