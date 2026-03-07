"""
Worlds App — SSoT fuer Weltenbau (ADR-082, ADR-083)

Model-Gruppen:
  1. World               — Welt-Definition (User-owned, projektunabhaengig)
  2. WorldLocation       — Orte innerhalb einer Welt (hierarchisch)
  3. WorldRule           — Regeln/Constraints einer Welt
  4. WorldCharacter      — Charakter auf Welt-Ebene (SSoT)
  5. ProjectWorld        — M2M: World <-> BookProject
  6. ProjectWorldCharacter — M2M: WorldCharacter <-> BookProject mit Projekt-Overrides

weltenfw-Kompatibilitaet: Diese Models implementieren das Weltenbau-SSoT-Pattern
identisch zur iil-weltenfw Spezifikation. Bei Verfuegbarkeit kann weltenfw
als Drop-in genutzt werden.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


# =============================================================================
# 1. World
# =============================================================================


class World(models.Model):
    """
    Projektunabhaengige Weltdefinition.
    Eine Welt gehoert einem User und kann in beliebig vielen
    Projekten verwendet werden via ProjectWorld M2M.
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
    atmosphere = models.TextField(
        blank=True,
        help_text="Stimmung und Atmosphaere der Welt",
    )

    class Language(models.TextChoices):
        DE = "de", "Deutsch"
        EN = "en", "English"
        ES = "es", "Espanol"
        FR = "fr", "Francais"
        IT = "it", "Italiano"
        PT = "pt", "Portugues"

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
            self.slug = (
                f"{base_slug}-{str(self.id)[:8]}" if self.id else base_slug
            )
        super().save(*args, **kwargs)


# =============================================================================
# 2. WorldLocation
# =============================================================================


class WorldLocation(models.Model):
    """Orte innerhalb einer Welt (hierarchisch)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    world = models.ForeignKey(
        "World", on_delete=models.CASCADE, related_name="locations"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    name = models.CharField(max_length=200)

    LOCATION_TYPES = [
        ("continent", "Kontinent"),
        ("country", "Land"),
        ("region", "Region"),
        ("city", "Stadt"),
        ("district", "Stadtteil"),
        ("building", "Gebaeude"),
        ("landmark", "Wahrzeichen"),
        ("natural", "Naturmerkmal"),
    ]
    location_type = models.CharField(
        max_length=20, choices=LOCATION_TYPES, default="city"
    )
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


# =============================================================================
# 3. WorldRule
# =============================================================================


class WorldRule(models.Model):
    """Regeln und Constraints einer Welt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    world = models.ForeignKey(
        "World", on_delete=models.CASCADE, related_name="rules"
    )

    CATEGORY_CHOICES = [
        ("physics", "Physik"),
        ("magic", "Magie"),
        ("social", "Gesellschaft"),
        ("technology", "Technologie"),
        ("biology", "Biologie"),
        ("economy", "Wirtschaft"),
    ]
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="physics"
    )
    rule = models.CharField(max_length=500)
    explanation = models.TextField(blank=True)

    IMPORTANCE_CHOICES = [
        ("absolute", "Absolut - Nie brechen"),
        ("strong", "Stark - Nur mit gutem Grund"),
        ("guideline", "Richtlinie - Flexibel"),
    ]
    importance = models.CharField(
        max_length=20, choices=IMPORTANCE_CHOICES, default="strong"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_world_rules"
        ordering = ["category", "-importance", "rule"]
        verbose_name = "World Rule"
        verbose_name_plural = "World Rules"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.rule[:50]}"


# =============================================================================
# 4. WorldCharacter
# =============================================================================


class WorldCharacter(models.Model):
    """
    Charakter auf Welt-Ebene — projektunabhaengige SSoT (ADR-082).

    Ein Charakter gehoert zu einer Welt und kann in beliebig vielen
    Projekten referenziert werden via ProjectWorldCharacter.

    weltenfw-Kompatibilitaet: Identisch zur iil-weltenfw WorldCharacter-Spezifikation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    world = models.ForeignKey(
        "World", on_delete=models.CASCADE, related_name="characters"
    )

    name = models.CharField(max_length=200)

    class Role(models.TextChoices):
        PROTAGONIST = "protagonist", "Protagonist"
        ANTAGONIST = "antagonist", "Antagonist"
        DEUTERAGONIST = "deuteragonist", "Deuteragonist"
        SUPPORTING = "supporting", "Nebenrolle"
        MINOR = "minor", "Kleinere Rolle"
        MENTOR = "mentor", "Mentor"
        LOVE_INTEREST = "love_interest", "Love Interest"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.SUPPORTING
    )

    description = models.TextField(blank=True)
    background = models.TextField(blank=True, help_text="Hintergrundgeschichte")
    personality = models.TextField(blank=True, help_text="Persoenlichkeitsmerkmale")
    appearance = models.TextField(blank=True, help_text="Physische Beschreibung")
    motivation = models.TextField(blank=True, help_text="Antrieb, Ziele")
    arc = models.TextField(blank=True, help_text="Charakterbogen (generisch)")

    wound = models.TextField(blank=True, help_text="Innere Verletzung/Trauma")
    secret = models.TextField(blank=True, help_text="Verborgenes Geheimnis")
    dark_trait = models.TextField(blank=True, help_text="Dunkle Seite/Schattenseite")

    voice_sample = models.TextField(blank=True, help_text="Beispiel-Dialog")
    speech_patterns = models.TextField(blank=True, help_text="Sprachmuster, Dialekt")

    portrait_image = models.ImageField(
        upload_to="world_character_portraits/", blank=True, null=True
    )

    is_template = models.BooleanField(
        default=False, help_text="Vorlage fuer neue Charaktere"
    )
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


# =============================================================================
# 5. ProjectWorld
# =============================================================================


class ProjectWorld(models.Model):
    """
    M2M: World <-> BookProject mit Projekt-spezifischer Rolle.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="world_links",
    )
    world = models.ForeignKey(
        "World",
        on_delete=models.CASCADE,
        related_name="project_links",
    )

    ROLE_CHOICES = [
        ("primary", "Primaerwelt"),
        ("secondary", "Nebenwelt"),
        ("parallel", "Parallelwelt"),
        ("historical", "Historisch"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="primary")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_worlds"
        unique_together = ["project", "world"]
        ordering = ["project", "role"]
        verbose_name = "Project World"
        verbose_name_plural = "Project Worlds"

    def __str__(self):
        return f"{self.world.name} -> {self.project} ({self.role})"


# =============================================================================
# 6. ProjectWorldCharacter
# =============================================================================


class ProjectWorldCharacter(models.Model):
    """
    M2M: WorldCharacter <-> BookProject mit projekt-spezifischen Anpassungen.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="world_character_links",
    )
    character = models.ForeignKey(
        "WorldCharacter",
        on_delete=models.CASCADE,
        related_name="project_links",
    )

    project_arc = models.TextField(
        blank=True, help_text="Charakterbogen in diesem Buch"
    )
    project_role = models.CharField(
        max_length=20,
        blank=True,
        help_text="Rolle in diesem Buch (kann von World abweichen)",
    )
    first_chapter = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_world_characters"
        unique_together = ["project", "character"]
        ordering = ["project", "character__role", "character__name"]
        verbose_name = "Project World Character"
        verbose_name_plural = "Project World Characters"

    def __str__(self):
        return f"{self.character.name} -> {self.project}"
