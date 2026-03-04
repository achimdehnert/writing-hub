from django.conf import settings
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="World",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="worlds", to=settings.AUTH_USER_MODEL)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(blank=True, max_length=200)),
                ("description", models.TextField(blank=True)),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="worlds/")),
                ("setting_era", models.CharField(blank=True, max_length=200)),
                ("geography", models.TextField(blank=True)),
                ("climate", models.TextField(blank=True)),
                ("inhabitants", models.TextField(blank=True)),
                ("culture", models.TextField(blank=True)),
                ("religion", models.TextField(blank=True)),
                ("technology_level", models.CharField(blank=True, max_length=200)),
                ("magic_system", models.TextField(blank=True)),
                ("politics", models.TextField(blank=True)),
                ("economy", models.TextField(blank=True)),
                ("history", models.TextField(blank=True)),
                ("language", models.CharField(choices=[("de", "🇩🇪 Deutsch"), ("en", "🇬🇧 English"), ("es", "🇪🇸 Español"), ("fr", "🇫🇷 Français"), ("it", "🇮🇹 Italiano"), ("pt", "🇵🇹 Português")], default="de", max_length=5)),
                ("is_public", models.BooleanField(default=False)),
                ("is_template", models.BooleanField(default=False)),
                ("version", models.PositiveIntegerField(default=1)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_worlds", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="WorldLocation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("world", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="locations", to="worlds.world")),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="children", to="worlds.worldlocation")),
                ("name", models.CharField(max_length=200)),
                ("location_type", models.CharField(choices=[("continent", "Kontinent"), ("country", "Land"), ("region", "Region"), ("city", "Stadt"), ("district", "Stadtteil"), ("building", "Gebäude"), ("landmark", "Wahrzeichen"), ("natural", "Naturmerkmal")], default="city", max_length=20)),
                ("description", models.TextField(blank=True)),
                ("significance", models.TextField(blank=True)),
                ("coordinates", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_world_locations", "ordering": ["location_type", "name"]},
        ),
        migrations.CreateModel(
            name="WorldRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("world", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rules", to="worlds.world")),
                ("category", models.CharField(choices=[("physics", "Physik"), ("magic", "Magie"), ("social", "Gesellschaft"), ("technology", "Technologie"), ("biology", "Biologie"), ("economy", "Wirtschaft")], default="physics", max_length=20)),
                ("rule", models.CharField(max_length=500)),
                ("explanation", models.TextField(blank=True)),
                ("importance", models.CharField(choices=[("absolute", "Absolut - Nie brechen"), ("strong", "Stark - Nur mit gutem Grund"), ("guideline", "Richtlinie - Flexibel")], default="strong", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_world_rules", "ordering": ["category", "-importance", "rule"]},
        ),
        migrations.CreateModel(
            name="WorldCharacter",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("world", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="characters", to="worlds.world")),
                ("name", models.CharField(max_length=200)),
                ("role", models.CharField(choices=[("protagonist", "Protagonist"), ("antagonist", "Antagonist"), ("deuteragonist", "Deuteragonist"), ("supporting", "Nebenrolle"), ("minor", "Kleinere Rolle"), ("mentor", "Mentor"), ("love_interest", "Love Interest")], default="supporting", max_length=20)),
                ("description", models.TextField(blank=True)),
                ("background", models.TextField(blank=True)),
                ("personality", models.TextField(blank=True)),
                ("appearance", models.TextField(blank=True)),
                ("motivation", models.TextField(blank=True)),
                ("arc", models.TextField(blank=True)),
                ("wound", models.TextField(blank=True)),
                ("secret", models.TextField(blank=True)),
                ("dark_trait", models.TextField(blank=True)),
                ("voice_sample", models.TextField(blank=True)),
                ("speech_patterns", models.TextField(blank=True)),
                ("portrait_image", models.ImageField(blank=True, null=True, upload_to="world_character_portraits/")),
                ("is_template", models.BooleanField(default=False)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_world_characters", "ordering": ["world", "role", "name"], "unique_together": {("world", "name")}},
        ),
    ]
