"""
Core App — Dramaturgische Lookup-Tabellen (ADR-158)

TurningPointTypeLookup: Semantische Wendepunkt-Typen (konsolidiert K1-Fix).
GenrePromiseLookup:     Genre-Versprechen für LLM-Layer 10.

app_label = "core" — beide Tabellen werden app-übergreifend referenziert.
"""
from __future__ import annotations

from django.db import models


class TurningPointTypeLookup(models.Model):
    """
    Lookup: Semantische Typen von Wendepunkten.

    K1-Fix: beide Positions-Felder für maximale Kompatibilität:
        default_position_percent  (0–100) — konsistent mit position_start/end im Stack
        default_position_normalized (0.0–1.0) — für outlinefw-Kompatibilität

    Seed-Daten (Management Command: seed_turning_point_types):
        opening_image     |  1% | Status Quo VOR der Veränderung
        inciting_incident | 10% | Das auslösende Ereignis
        debate            | 12% | Figur zögert
        break_into_2      | 25% | Kein Zurück
        b_story_begins    | 37% | Thematischer Spiegel beginnt
        midpoint          | 50% | Scheinsieg / Scheinniederlage
        bad_guys_close    | 62% | Alles wird schlimmer
        all_is_lost       | 75% | Tiefpunkt
        dark_night        | 78% | Figur gibt (fast) auf
        break_into_3      | 87% | Neue Erkenntnis
        climax            | 98% | Finale Konfrontation
        closing_image     |100% | Neue Normalwelt — spiegelt Opening
    """

    code = models.SlugField(max_length=30, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    default_position_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text="Typische Position im Roman (0–100%)",
    )
    default_position_normalized = models.DecimalField(
        max_digits=4, decimal_places=3,
        null=True, blank=True,
        help_text="Normiert (0.0–1.0) — für outlinefw-Kompatibilität",
    )
    outlinefw_beat_name = models.CharField(
        max_length=80, blank=True, default="",
        help_text="Mapping auf outlinefw BeatDefinition-Name (falls vorhanden)",
    )
    mirrors_type_code = models.SlugField(
        max_length=30, blank=True, default="",
        help_text="Code des gespiegelten Typs (z.B. closing_image → opening_image)",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        app_label = "core"
        db_table = "wh_turning_point_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Wendepunkt-Typ"
        verbose_name_plural = "Wendepunkt-Typen"

    def __str__(self):
        return f"{self.code} — {self.label} ({self.default_position_percent}%)"

    def save(self, *args, **kwargs):
        if self.default_position_percent and self.default_position_normalized is None:
            from decimal import Decimal
            self.default_position_normalized = Decimal(
                str(round(self.default_position_percent / 100, 3))
            )
        super().save(*args, **kwargs)


class GenrePromiseLookup(models.Model):
    """
    Genre-Versprechen — was dieses Genre dem Leser verspricht.

    LLM Layer 10: Genre-Promise wird in den Prompt injiziert um
    sicherzustellen, dass KI-generierter Text die Genre-Erwartungen erfüllt.

    Seed-Daten (Management Command: seed_genre_promises):
        thriller    → Eskalation, Bedrohung, Clock is ticking
        romance     → Emotionale Intensität, Happy End, Meet-Cute
        krimi       → Fair-Play, Rätsel, Auflösung
        fantasy     → Wunderbares System, Kosten der Magie, Weltregeln
        literarisch → Sprachdichte, Ambiguität, Innenwelt > Außenwelt
    """

    genre_slug = models.SlugField(max_length=50, unique=True)
    genre_label = models.CharField(max_length=100)

    core_promise = models.TextField(
        verbose_name="Kern-Versprechen",
        help_text="Was verspricht dieses Genre dem Leser implizit? (1–3 Sätze)",
    )
    reader_expectation = models.TextField(
        blank=True, default="",
        verbose_name="Leser-Erwartung",
        help_text="Was erwartet der Leser konkret? (für LLM-Prompt)",
    )
    must_haves = models.JSONField(
        default=list,
        help_text='["Bedrohung bis 10%", "Clock is ticking", ...]',
    )
    must_not_haves = models.JSONField(
        default=list,
        help_text='["Happy End nicht verpflichtend", ...]',
    )

    llm_prompt_block = models.TextField(
        blank=True, default="",
        verbose_name="LLM-Prompt-Block (Layer 10)",
        help_text="Fertiger Prompt-Block für Genre-Context-Injection.",
    )

    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "wh_genre_promise_lookup"
        ordering = ["sort_order", "genre_label"]
        verbose_name = "Genre-Versprechen"
        verbose_name_plural = "Genre-Versprechen"

    def __str__(self):
        return f"{self.genre_label}: {self.core_promise[:60]}"

    def to_prompt_context(self) -> str:
        """Gibt fertigen LLM-Prompt-Block zurück (Layer 10)."""
        if self.llm_prompt_block:
            return self.llm_prompt_block
        lines = [
            f"GENRE-VERSPRECHEN ({self.genre_label.upper()}):",
            self.core_promise,
        ]
        if self.reader_expectation:
            lines.append(f"Leser-Erwartung: {self.reader_expectation}")
        if self.must_haves:
            lines.append("Pflicht-Elemente: " + ", ".join(self.must_haves))
        return "\n".join(lines)


class SeriesArcTypeLookup(models.Model):
    """
    Lookup: Serien-Arc-Typen (ADR-155).

    Seed-Werte:
        single_arc     | Durchgehender Arc  | Eine Figur, ein Arc über alle Bände
        anthology      | Anthologie         | Jeder Band eigenständig, lose verbunden
        escalating_arc | Eskalierender Arc  | Jeder Band erhöht die Einsätze
        dual_arc       | Doppel-Arc         | Haupt-Arc + Band-eigener Arc parallel
    """

    code = models.SlugField(max_length=30, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        app_label = "core"
        db_table = "wh_series_arc_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Serien-Arc-Typ"
        verbose_name_plural = "Serien-Arc-Typen"

    def __str__(self):
        return self.label
