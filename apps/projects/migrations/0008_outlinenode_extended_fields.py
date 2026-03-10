from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0007_bookproject_writing_style"),
    ]

    operations = [
        migrations.AddField(
            model_name="outlinenode",
            name="beat_phase",
            field=models.CharField(
                blank=True, max_length=100, default="",
                help_text="Beat/Phase des Frameworks, z.B. 'Opening Image'",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="act",
            field=models.CharField(
                blank=True, max_length=100, default="",
                help_text="Akt/Teil, z.B. 'Akt 1 - Setup'",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="target_words",
            field=models.PositiveIntegerField(
                null=True, blank=True,
                help_text="Ziel-Wortanzahl für dieses Kapitel",
            ),
        ),
        migrations.AddField(
            model_name="outlinenode",
            name="emotional_arc",
            field=models.CharField(
                blank=True, max_length=300, default="",
                help_text="Emotionaler Bogen des Kapitels",
            ),
        ),
        migrations.AddField(
            model_name="outlineversion",
            name="version_label",
            field=models.CharField(
                blank=True, max_length=200, default="",
                help_text="Optionales Label für diese Version",
            ),
        ),
    ]
