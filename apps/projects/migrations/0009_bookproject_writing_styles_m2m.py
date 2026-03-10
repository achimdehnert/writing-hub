import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0008_outlinenode_extended_fields"),
        ("authors", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookproject",
            name="writing_styles",
            field=models.ManyToManyField(
                blank=True,
                related_name="projects_m2m",
                to="authors.writingstyle",
                verbose_name="Schreibstile (mehrere möglich)",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="writing_style",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="outline_nodes",
                to="authors.writingstyle",
                verbose_name="Schreibstil für dieses Kapitel",
            ),
        ),
    ]
