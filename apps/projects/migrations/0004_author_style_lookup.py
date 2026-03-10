import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_outlinenode_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="contenttypelookup",
            name="icon",
            field=models.CharField(
                blank=True, default="", max_length=50,
                help_text="Bootstrap-Icon-Klasse, z.B. 'bi-book'",
            ),
        ),
        migrations.AddField(
            model_name="contenttypelookup",
            name="subtitle",
            field=models.CharField(
                blank=True, default="", max_length=200,
                help_text="Kurzbeschreibung unter dem Namen",
            ),
        ),
        migrations.AddField(
            model_name="contenttypelookup",
            name="workflow_hint",
            field=models.CharField(
                blank=True, default="", max_length=300,
                help_text="Workflow-Schritte z.B. 'Konzept → Struktur → Schreiben'",
            ),
        ),
        migrations.CreateModel(
            name="AuthorStyleLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, unique=True,
                    help_text="Name des Autors / Stils")),
                ("description", models.TextField(blank=True)),
                ("style_prompt", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Autor / Schreibstil",
                "verbose_name_plural": "Autoren / Schreibstile",
                "db_table": "wh_author_style_lookup",
                "ordering": ["order", "name"],
            },
        ),
        migrations.AddField(
            model_name="bookproject",
            name="author_style",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="projects.authorstylelookup",
                verbose_name="Autor / Schreibstil",
            ),
        ),
    ]
