import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
        ("series", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentTypeLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=50, unique=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Inhaltstyp",
                "verbose_name_plural": "Inhaltstypen",
                "db_table": "wh_content_type_lookup",
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="GenreLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Genre",
                "verbose_name_plural": "Genres",
                "db_table": "wh_genre_lookup",
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="AudienceLookup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, unique=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Zielgruppe",
                "verbose_name_plural": "Zielgruppen",
                "db_table": "wh_audience_lookup",
                "ordering": ["order", "name"],
            },
        ),
        migrations.AddField(
            model_name="bookproject",
            name="series",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="series.bookseries",
                verbose_name="Serie",
                help_text="Buchserie zu der dieses Projekt gehört (optional)",
            ),
        ),
        migrations.AddField(
            model_name="bookproject",
            name="content_type_lookup",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="projects.contenttypelookup",
                verbose_name="Inhaltstyp",
            ),
        ),
        migrations.AddField(
            model_name="bookproject",
            name="genre_lookup",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="projects.genrelookup",
                verbose_name="Genre",
            ),
        ),
        migrations.AddField(
            model_name="bookproject",
            name="audience_lookup",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="projects.audiencelookup",
                verbose_name="Zielgruppe",
            ),
        ),
    ]
