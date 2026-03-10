import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authors", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="writingstyle",
            name="do_list",
            field=models.JSONField(default=list, help_text="Erlaubte/empfohlene Stilmittel"),
        ),
        migrations.AddField(
            model_name="writingstyle",
            name="dont_list",
            field=models.JSONField(default=list, help_text="Verbotene Stilmittel"),
        ),
        migrations.AddField(
            model_name="writingstyle",
            name="taboo_list",
            field=models.JSONField(default=list, help_text="Tabu-Wörter"),
        ),
        migrations.AddField(
            model_name="writingstyle",
            name="signature_moves",
            field=models.JSONField(default=list, help_text="Charakteristische Stilmittel"),
        ),
    ]
