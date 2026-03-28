"""
Worlds App Models — writing-hub

SSoT ist WeltenHub via iil-weltenfw REST Client.
Lokal werden nur Referenz-Links (UUIDs) gespeichert.
"""
from __future__ import annotations

import uuid

from django.db import models


class ProjectWorldLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einer WeltenHub-Welt (UUID).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="world_links",
    )
    weltenhub_world_id = models.UUIDField(
        db_index=True,
        help_text="UUID der Welt in WeltenHub (via iil-weltenfw)",
    )
    role = models.CharField(
        max_length=20, default="primary",
        choices=[("primary", "Primärwelt"), ("secondary", "Nebenwelt"), ("parallel", "Parallelwelt")],
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_world_links"
        unique_together = ["project", "weltenhub_world_id"]
        ordering = ["project", "role"]
        verbose_name = "Project World Link"
        verbose_name_plural = "Project World Links"

    def __str__(self):
        return f"{self.project} → world:{self.weltenhub_world_id} ({self.role})"

    def get_world(self):
        from weltenfw.django import get_client
        return get_client().worlds.get(self.weltenhub_world_id)


class ProjectCharacterLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einem WeltenHub-Charakter (UUID).

    ADR-157: narrative_role + Antagonisten-Felder ergänzt.
    """

    NARRATIVE_ROLES = [
        ("protagonist",        "Protagonist — Hauptfigur mit Arc"),
        ("antagonist",         "Antagonist — Gegenkraft mit eigener Logik"),
        ("deuteragonist",      "Deuteragonist — zweite Hauptfigur (B-Story)"),
        ("mentor",             "Mentor — gibt Werkzeug/Weisheit"),
        ("ally",               "Verbündeter — Spiegel und Unterstützung"),
        ("love_interest",      "Liebesinteresse — verkörpert das Need"),
        ("trickster",          "Trickster — Humor und Dekonstruktion"),
        ("herald",             "Herold — bringt den Ruf"),
        ("shapeshifter",       "Gestaltenwandler — zweifelt Loyalität an"),
        ("shadow",             "Schatten — was wäre der Protagonist wenn..."),
        ("threshold_guardian", "Schwellenwächter — testet Entschlossenheit"),
        ("supporting",         "Nebenfigur — dramaturgische Funktion"),
    ]

    ANTAGONIST_TYPES = [
        ("person",      "Person / Gruppe"),
        ("system",      "System / Institution / Gesellschaft"),
        ("nature",      "Natur / Umwelt / Schicksal"),
        ("inner_self",  "Inneres Selbst — die eigene dunkle Seite"),
        ("combination", "Kombination mehrerer Typen"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="character_links",
    )
    weltenhub_character_id = models.UUIDField(
        db_index=True,
        help_text="UUID des Charakters in WeltenHub (via iil-weltenfw)",
    )
    project_arc = models.TextField(blank=True, help_text="Projekt-spezifischer Charakterbogen (override)")
    project_role = models.CharField(max_length=50, blank=True, help_text="Rolle in diesem Projekt (override)")
    notes = models.TextField(blank=True)

    # --- ADR-157: Dramaturgische Felder ---
    narrative_role = models.CharField(
        max_length=30,
        choices=NARRATIVE_ROLES,
        default="supporting",
        verbose_name="Narrative Rolle",
        db_index=True,
    )

    # Charakter-Arc (ADR-152)
    want = models.TextField(blank=True, default="", verbose_name="Want (äußeres Ziel)")
    need = models.TextField(blank=True, default="", verbose_name="Need (innere Wahrheit)")
    flaw = models.TextField(blank=True, default="", verbose_name="Flaw (psychologischer Riss)")
    ghost = models.TextField(blank=True, default="", verbose_name="Ghost (prägender Moment)")
    false_belief = models.TextField(blank=True, default="", verbose_name="False Belief")
    true_belief = models.TextField(blank=True, default="", verbose_name="True Belief (Erkenntnis am Ende)")

    # Antagonisten-Felder (ADR-157)
    antagonist_type = models.CharField(
        max_length=20, choices=ANTAGONIST_TYPES,
        blank=True, default="",
        verbose_name="Antagonisten-Typ",
    )
    antagonist_logic = models.TextField(
        blank=True, default="",
        verbose_name="Antagonisten-Logik",
        help_text="Warum glaubt der Antagonist, das Richtige zu tun?",
    )
    mirror_to_protagonist = models.TextField(
        blank=True, default="",
        verbose_name="Spiegel zum Protagonisten",
        help_text="Was zeigt diese Figur, was der Protagonist sein KÖNNTE?",
    )
    shared_trait_with_protagonist = models.TextField(
        blank=True, default="",
        verbose_name="Gemeinsamkeit mit Protagonisten",
    )
    information_advantage = models.TextField(
        blank=True, default="",
        verbose_name="Informationsvorsprung",
        help_text="Nur für externe Antagonisten (person, system, nature).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_project_character_links"
        unique_together = ["project", "weltenhub_character_id"]
        ordering = ["project"]
        verbose_name = "Project Character Link"
        verbose_name_plural = "Project Character Links"

    def __str__(self):
        return f"{self.project} → char:{self.weltenhub_character_id} ({self.narrative_role})"

    def get_character(self):
        from weltenfw.django import get_client
        return get_client().characters.get(self.weltenhub_character_id)

    @property
    def carries_b_story(self) -> bool:
        from projects.models import SubplotArc
        return SubplotArc.objects.filter(
            project=self.project,
            story_label="b_story",
            carried_by_character_id=self.weltenhub_character_id,
        ).exists()


class ProjectLocationLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einem WeltenHub-Ort (UUID).
    SSoT: WeltenHub. Hier nur UUID-Referenz + projektspezifische Notizen.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="location_links",
    )
    weltenhub_location_id = models.UUIDField(
        db_index=True,
        help_text="UUID des Ortes in WeltenHub (via iil-weltenfw)",
    )
    notes = models.TextField(blank=True, help_text="Projekt-spezifische Notizen zum Ort")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_location_links"
        unique_together = ["project", "weltenhub_location_id"]
        ordering = ["project"]
        verbose_name = "Project Location Link"
        verbose_name_plural = "Project Location Links"

    def __str__(self):
        return f"{self.project} → location:{self.weltenhub_location_id}"

    def get_location(self):
        from weltenfw.django import get_client
        return get_client().locations.get(self.weltenhub_location_id)


class ProjectSceneLink(models.Model):
    """
    Verknüpft ein lokales BookProject mit einer WeltenHub-Szene (UUID).
    SSoT: WeltenHub. Hier nur UUID-Referenz + lokaler Kapitel-Bezug.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="scene_links",
    )
    weltenhub_scene_id = models.UUIDField(
        db_index=True,
        help_text="UUID der Szene in WeltenHub (via iil-weltenfw)",
    )
    outline_node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="scene_links",
        help_text="Lokales Kapitel das dieser Szene entspricht",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_scene_links"
        unique_together = ["project", "weltenhub_scene_id"]
        ordering = ["project"]
        verbose_name = "Project Scene Link"
        verbose_name_plural = "Project Scene Links"

    def __str__(self):
        return f"{self.project} → scene:{self.weltenhub_scene_id}"

    def get_scene(self):
        from weltenfw.django import get_client
        return get_client().scenes.get(self.weltenhub_scene_id)
