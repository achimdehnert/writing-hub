import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0006_outline_framework"),
        ("authors", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bookproject",
            name="author_style",
        ),
        migrations.AddField(
            model_name="bookproject",
            name="writing_style",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="authors.writingstyle",
                verbose_name="Schreibstil",
            ),
        ),
    ]
