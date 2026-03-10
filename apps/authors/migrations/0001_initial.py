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
            name="Author",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("owner", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="authors",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("name", models.CharField(max_length=200)),
                ("bio", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_authors", "ordering": ["name"],
                     "verbose_name": "Autor", "verbose_name_plural": "Autoren"},
        ),
        migrations.CreateModel(
            name="WritingStyle",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("author", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="writing_styles",
                    to="authors.author",
                )),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("source_text", models.TextField(blank=True)),
                ("style_profile", models.TextField(blank=True)),
                ("style_prompt", models.TextField(blank=True)),
                ("status", models.CharField(
                    choices=[("draft", "Entwurf"), ("analyzing", "Analyse läuft"),
                             ("ready", "Bereit"), ("error", "Fehler")],
                    default="draft", max_length=20,
                )),
                ("error_message", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_writing_styles", "ordering": ["author", "name"],
                     "verbose_name": "Schreibstil", "verbose_name_plural": "Schreibstile"},
        ),
        migrations.CreateModel(
            name="WritingStyleSample",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("style", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="samples",
                    to="authors.writingstyle",
                )),
                ("situation", models.CharField(
                    choices=[
                        ("action", "Actionszene"), ("dialogue", "Dialog"),
                        ("description", "Ortsbeschreibung"), ("emotion", "Emotionale Szene"),
                        ("intro", "Kapiteleinstieg"), ("outro", "Kapitelende / Cliffhanger"),
                        ("inner", "Innerer Monolog"), ("exposition", "Exposition"),
                    ],
                    max_length=30,
                )),
                ("text", models.TextField()),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "wh_writing_style_samples", "ordering": ["style", "situation"],
                     "verbose_name": "Stil-Beispieltext", "verbose_name_plural": "Stil-Beispieltexte"},
        ),
    ]
