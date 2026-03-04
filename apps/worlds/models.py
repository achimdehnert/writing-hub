"""
Worlds App — SSoT für Weltenbau (ADR-082, ADR-083)

Extrahiert aus bfagent/apps/writing_hub/models_world.py.
Modelle: World, WorldLocation, WorldRule, WorldCharacter, ProjectWorld, ProjectWorldCharacter
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class World(models.Model):
    """
    Projektunabhängige Weltdefinition.

    Eine Welt gehört einem User und kann in beliebig vielen Projekten
    verwendet werden über die ProjectWorld M2M-Beziehung.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="worlds",
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="worlds/", blank=True, null=True)

    setting_era = models.CharField(max_length=200, blank=True)
    geography = models.TextField(blank=True)
    climate = models.TextField(blank=True)
    inhabitants = models.TextField(blank=True)
    culture = models.TextField(blank=True)
    religion = models.TextField(blank=True)
    technology_level = models.CharField(max_length=200, blank=True)
    magic_system = models.TextField(blank=True)
    politics = models.TextField(blank=True)
    economy = models.TextField(blank=True)
    history = models.TextField(blank=True)

    class Language(models.TextChoices):
        DE = "de", "🇩🇪 Deutsch"
        EN = "en", "🇬🇧 English"
        ES = "es", "🇪🇸 Español"
        FR = "fr", "🇫🇷 Français"
        IT = "it", "🇮🇹 Italiano"
        PT = "pt", "🇵🇹 Português"

    language = models.CharField(
        max_length=5,
        choices=Language.choices,
        default=Language.DE,
    )

    is_public = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    tags = models.JSONField(blank=True, default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_worlds"
        ordering = ["name"]
        verbose_name = "World"
        verbose_name_plural = "Worlds"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{str(self.id)[:8]}" if self.id else base_slug
        super().save(*args, **kwargs)


class WorldLocation(models.Model):
    """
    Orte innerhalb einer Welt (hierarchisch).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    world = models.ForeignKey("World", on_delete=models.CASCADE, related_name="locations")
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )

    name = models.CharField(max_length=200)

    LOCATION_TYPES = [
        ("continent", "Kontinent"),
        ("country", "Land"),
        ("region", "Region"),
        ("city", "Stadt"),
        ("district", "Stadtteil"),
        ("building", "Gebäude"),
        ("landmark", "Wahrzeichen"),
        ("natural", "Naturmerkmal"),
    ]
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default="city")
    description = models.TextField(blank=True)
    significance = models.TextField(blank=True)
    coordinates = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_world_locations"
        ordering = ["location_type", "name"]
        verbose_name = "World Location"
        verbose_name_plural = "World Locations"

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"


class WorldRule(models.Model):
    """
    Regeln und Constraints einer Welt.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    world = models.ForeignKey("World", on_delete=models.CASCADE, related_name="rules")

    CATEGORY_CHOICES = [
        ("physics", "Physik"),
        ("magic", "Magie"),
        ("social", "Gesellschaft"),
        ("technology", "Technologie"),
        ("biology", "Biologie"),
        ("economy", "Wirtschaft"),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="physics")
    rule = models.CharField(max_length=500)
    explanation = models.TextField(blank=True)

    IMPORTANCE_CHOICES = [
        ("absolute", "Absolut - Nie brechen"),
        ("strong", "Stark - Nur mit gutem Grund"),
        ("guideline", "Richtlinie - Flexibel"),
    ]
    importance = models.CharField(max_length=20, choices=IMPORTANCE_CHOICES, default="strong")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_world_rules"
        ordering = ["category", "-importance", "rule"]
        verbose_name = "World Rule"
        verbose_name_plural = "World Rules"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.rule[:50]}"


class WorldCharacter(models.Model):
    """
    Charakter auf Welt-Ebene — projektunabhängige SSoT (ADR-082).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    world = models.ForeignKey("World", on_delete=models.CASCADE, related_name="characters")

    name = models.CharField(max_length=200)

    class Role(models.TextChoices):
        PROTAGONIST = "protagonist", "Protagonist"
        ANTAGONIST = "antagonist", "Antagonist"
        DEUTERAGONIST = "deuteragonist", "Deuteragonist"
        SUPPORTING = "supporting", "Nebenrolle"
        MINOR = "minor", "Kleinere Rolle"
        MENTOR = "mentor", "Mentor"
        LOVE_INTEREST = "love_interest", "Love Interest"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SUPPORTING)

    description = models.TextField(blank=True)
    background = models.TextField(blank=True)
    personality = models.TextField(blank=True)
    appearance = models.TextField(blank=True)
    motivation = models.TextField(blank=True)
    arc = models.TextField(blank=True)

    wound = models.TextField(blank=True)
    secret = models.TextField(blank=True)
    dark_trait = models.TextField(blank=True)

    voice_sample = models.TextField(blank=True)
    speech_patterns = models.TextField(blank=True)

    portrait_image = models.ImageField(
        upload_to="world_character_portraits/", blank=True, null=True
    )

    is_template = models.BooleanField(default=False)
    tags = models.JSONField(blank=True, default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_world_characters"
        ordering = ["world", "role", "name"]
        unique_together = ["world", "name"]
        verbose_name = "World Character"
        verbose_name_plural = "World Characters"

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) — {self.world.name}"
