from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_add_lookup_models_and_series_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="outlinenode",
            name="content",
            field=models.TextField(
                blank=True,
                help_text="Kapitelinhalt (von Autor oder KI geschrieben)",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="word_count",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Anzahl Wörter im content-Feld (automatisch berechnet)",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="content_updated_at",
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Zeitpunkt der letzten Inhalt-Änderung",
            ),
        ),
    ]
