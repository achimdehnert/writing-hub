from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_author_style_lookup"),
    ]

    operations = [
        migrations.CreateModel(
            name="OutlineFramework",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("key", models.SlugField(max_length=80, unique=True,
                    help_text="Eindeutiger Schlüssel, z.B. 'save_the_cat'",
                )),
                ("name", models.CharField(max_length=200)),
                ("subtitle", models.CharField(blank=True, max_length=300)),
                ("icon", models.CharField(blank=True, default="bi-list-ol", max_length=60)),
                ("description", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "wh_outline_framework",
                "ordering": ["order", "name"],
                "verbose_name": "Outline-Framework",
                "verbose_name_plural": "Outline-Frameworks",
            },
        ),
        migrations.CreateModel(
            name="OutlineFrameworkBeat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("framework", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="beats",
                    to="projects.outlineframework",
                )),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("position_start", models.PositiveSmallIntegerField(default=0)),
                ("position_end", models.PositiveSmallIntegerField(default=100)),
            ],
            options={
                "db_table": "wh_outline_framework_beat",
                "ordering": ["framework", "order"],
                "verbose_name": "Framework Beat",
                "verbose_name_plural": "Framework Beats",
            },
        ),
        migrations.AlterField(
            model_name="outlineversion",
            name="source",
            field=models.CharField(
                default="manual",
                max_length=80,
                help_text="Framework-Key (OutlineFramework.key) oder 'manual'/'ai'",
            ),
        ),
    ]
