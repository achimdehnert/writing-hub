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
        db_index=True, null=True, blank=True,
        help_text="UUID der Welt in WeltenHub (leer = nur lokal)",
    )
    name = models.CharField(
        max_length=200, default="", blank=True,
        verbose_name="Name (lokal)",
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
        label = self.name or str(self.weltenhub_world_id or "Unbenannte Welt")
        return f"{self.project} → {label}"

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

    CHARACTER_STATUS = [
        ("alive",   "Lebt"),
        ("dead",    "Tot"),
        ("missing", "Vermisst"),
        ("unknown", "Unbekannt"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="character_links",
    )
    weltenhub_character_id = models.UUIDField(
        db_index=True, null=True, blank=True,
        help_text="UUID des Charakters in WeltenHub (leer = nur lokal)",
    )
    name = models.CharField(
        max_length=200, default="", blank=True,
        verbose_name="Name (lokal)",
        help_text="Lokaler Cache / Fallback wenn WeltenHub nicht erreichbar",
    )
    description = models.TextField(
        blank=True, default="",
        verbose_name="Beschreibung (lokal)",
    )
    personality = models.TextField(
        blank=True, default="",
        verbose_name="Persönlichkeit (lokal)",
    )
    backstory = models.TextField(
        blank=True, default="",
        verbose_name="Hintergrundgeschichte (lokal)",
    )
    is_protagonist = models.BooleanField(
        default=False,
        verbose_name="Protagonist",
    )
    source = models.CharField(
        max_length=20, default="manual", blank=True,
        choices=[("manual", "Manuell"), ("outline", "Aus Outline"), ("llm", "Per LLM generiert"), ("weltenhub", "WeltenHub")],
        verbose_name="Quelle",
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

    # Stimme / Sprechmuster (Speed-Matters-Erweiterung)
    voice_pattern = models.TextField(
        blank=True, default="",
        verbose_name="Stimme / Sprechmuster",
        help_text="Wie redet die Figur? Kurzsätze, Füllwörter, Dialekt, Schweigen als Mittel.",
    )

    # Geheimnis (strukturiert: Was, vor wem, warum)
    secret_what = models.TextField(
        blank=True, default="",
        verbose_name="Geheimnis — Was",
        help_text="Was verbirgt die Figur?",
    )
    secret_from_whom = models.CharField(
        max_length=200,
        blank=True, default="",
        verbose_name="Geheimnis — Vor wem",
    )
    secret_why = models.TextField(
        blank=True, default="",
        verbose_name="Geheimnis — Warum",
    )

    # Plot-Status
    character_status = models.CharField(
        max_length=20, choices=CHARACTER_STATUS,
        default="alive",
        verbose_name="Status im Plot",
    )
    first_appearance = models.CharField(
        max_length=100,
        blank=True, default="",
        verbose_name="Erster Auftritt",
        help_text="Kapitel oder Szene, in der die Figur erstmals erscheint.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_project_character_links"
        ordering = ["project"]
        verbose_name = "Project Character Link"
        verbose_name_plural = "Project Character Links"

    def __str__(self):
        label = self.name or str(self.weltenhub_character_id or "Unbenannt")[:12]
        return f"{self.project} → {label} ({self.get_narrative_role_display()})"

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


class CharacterRelationship(models.Model):
    """
    Beziehung zwischen zwei Charakteren innerhalb eines Projekts.

    Phase 2: bidirektionale Darstellung (A→B auch als B←A sichtbar),
    aber gespeichert als gerichtete Kante from → to.
    """

    RELATIONSHIP_TYPES = [
        ("knows",       "Kennt"),
        ("friend",      "Freundschaft"),
        ("love",        "Liebesbeziehung"),
        ("family",      "Familie / Verwandtschaft"),
        ("rival",       "Rivalität"),
        ("enemy",       "Feindschaft"),
        ("mentor",      "Mentor → Schüler"),
        ("protects",    "Beschützt"),
        ("distrusts",   "Misstraut"),
        ("depends_on",  "Abhängig von"),
        ("betrayed_by", "Verraten von"),
        ("secret_from", "Verbirgt Geheimnis vor"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="character_relationships",
    )
    from_character = models.ForeignKey(
        ProjectCharacterLink,
        on_delete=models.CASCADE,
        related_name="relationships_from",
        verbose_name="Von",
    )
    to_character = models.ForeignKey(
        ProjectCharacterLink,
        on_delete=models.CASCADE,
        related_name="relationships_to",
        verbose_name="Zu",
    )
    relationship_type = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_TYPES,
        verbose_name="Beziehungstyp",
    )
    description = models.TextField(
        blank=True, default="",
        verbose_name="Beschreibung",
        help_text="Freitext: Was macht diese Beziehung besonders?",
    )
    since_chapter = models.CharField(
        max_length=100,
        blank=True, default="",
        verbose_name="Seit Kapitel/Szene",
        help_text="Ab welchem Punkt existiert diese Beziehung?",
    )
    intensity = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="Intensität (1-5)",
        help_text="1=oberflächlich, 5=existenziell",
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name="Öffentlich bekannt?",
        help_text="Wissen andere Figuren von dieser Beziehung?",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_character_relationships"
        unique_together = ["project", "from_character", "to_character", "relationship_type"]
        ordering = ["project", "-intensity"]
        verbose_name = "Character Relationship"
        verbose_name_plural = "Character Relationships"

    def __str__(self):
        return f"{self.from_character} —[{self.get_relationship_type_display()}]→ {self.to_character}"


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
        db_index=True, null=True, blank=True,
        help_text="UUID des Ortes in WeltenHub (leer = nur lokal)",
    )
    name = models.CharField(
        max_length=200, default="", blank=True,
        verbose_name="Name (lokal)",
    )
    description = models.TextField(
        blank=True, default="",
        verbose_name="Beschreibung (lokal)",
    )
    atmosphere = models.TextField(
        blank=True, default="",
        verbose_name="Atmosphäre",
    )
    significance = models.TextField(
        blank=True, default="",
        verbose_name="Bedeutung für die Geschichte",
    )
    source = models.CharField(
        max_length=20, default="manual", blank=True,
        choices=[("manual", "Manuell"), ("outline", "Aus Outline"), ("llm", "Per LLM generiert"), ("weltenhub", "WeltenHub")],
        verbose_name="Quelle",
    )
    notes = models.TextField(blank=True, help_text="Projekt-spezifische Notizen zum Ort")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_project_location_links"
        ordering = ["project"]
        verbose_name = "Project Location Link"
        verbose_name_plural = "Project Location Links"

    def __str__(self):
        label = self.name or str(self.weltenhub_location_id or "Unbenannter Ort")
        return f"{self.project} → {label}"

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
