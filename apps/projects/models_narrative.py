"""
Projects App — Narrative Models (ADR-158)

DialogueScene: Subtext-Struktur für Dialog-Szenen.

Hinweis: SubplotArc und ProjectGenrePromise sind in apps/projects/models.py
definiert (Migration 0015). Keine Duplikate hier.
"""

from __future__ import annotations

import uuid

from django.db import models


class DialogueScene(models.Model):
    """
    Subtext-Struktur einer Dialog-Szene (ADR-158).

    Pro OutlineNode kann es 0–N DialogueScenes geben.
    Verhindert On-Nose-Dialog durch strukturierte Subtext-Vorgaben an das LLM.

    Dialog-Outcome-Typen:
        status_quo    → Dialog ändert nichts (selten erlaubt)
        info_shift    → Informationsstand verändert sich
        power_shift   → Machtverhältnis kippt
        relationship  → Beziehung verändert sich
        revelation    → Enthüllung — etwas kommt ans Licht
        decision      → Entscheidung wird herbeigeführt
    """

    DIALOGUE_OUTCOMES = [
        ("status_quo", "Status Quo — nichts ändert sich (Ausnahme!)"),
        ("info_shift", "Info-Shift — Wissensstand verändert sich"),
        ("power_shift", "Power-Shift — Machtverhältnis kippt"),
        ("relationship", "Beziehungs-Shift — Nähe/Distanz verändert"),
        ("revelation", "Enthüllung — etwas kommt ans Licht"),
        ("decision", "Entscheidungs-Katalysator"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(
        "projects.OutlineNode",
        on_delete=models.CASCADE,
        related_name="dialogue_scenes",
        verbose_name="Szene",
    )

    speaker_a_character_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Figur A (WeltenHub UUID)",
    )
    speaker_a_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Figur A (Cache)",
    )
    speaker_b_character_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Figur B (WeltenHub UUID)",
    )
    speaker_b_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Figur B (Cache)",
    )

    goal_a = models.TextField(
        blank=True,
        default="",
        verbose_name="Ziel Figur A im Dialog",
        help_text="Was will Figur A durch dieses Gespräch erreichen?",
    )
    goal_b = models.TextField(
        blank=True,
        default="",
        verbose_name="Ziel Figur B im Dialog",
    )

    subtext_a = models.TextField(
        blank=True,
        default="",
        verbose_name="Subtext Figur A",
        help_text="Was meint Figur A wirklich — darf es aber nicht sagen?",
    )
    subtext_b = models.TextField(
        blank=True,
        default="",
        verbose_name="Subtext Figur B",
    )

    info_asymmetry = models.TextField(
        blank=True,
        default="",
        verbose_name="Informations-Asymmetrie",
        help_text="Was weiß eine Figur, was die andere nicht weiß?",
    )

    dialogue_outcome = models.CharField(
        max_length=20,
        choices=DIALOGUE_OUTCOMES,
        default="info_shift",
        verbose_name="Dialog-Outcome",
    )
    outcome_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Outcome-Beschreibung",
        help_text="Was ändert sich konkret durch diesen Dialog?",
    )

    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_dialogue_scenes"
        ordering = ["node", "sort_order"]
        verbose_name = "Dialog-Subtext"
        verbose_name_plural = "Dialog-Subtexte"

    def __str__(self):
        a = self.speaker_a_name or "?"
        b = self.speaker_b_name or "?"
        return f"Dialog: {a} ↔ {b} [{self.get_dialogue_outcome_display()}]"

    def to_prompt_context(self) -> str:
        """Gibt Subtext-Struktur als LLM-Prompt-Block zurück."""
        lines = [
            f"[DIALOG: {self.speaker_a_name} ↔ {self.speaker_b_name}]",
            f"ZIEL {self.speaker_a_name}: {self.goal_a}",
            f"ZIEL {self.speaker_b_name}: {self.goal_b}",
        ]
        if self.subtext_a:
            lines.append(f"SUBTEXT {self.speaker_a_name}: {self.subtext_a} (darf NICHT direkt gesagt werden)")
        if self.subtext_b:
            lines.append(f"SUBTEXT {self.speaker_b_name}: {self.subtext_b} (darf NICHT direkt gesagt werden)")
        if self.info_asymmetry:
            lines.append(f"INFORMATIONS-ASYMMETRIE: {self.info_asymmetry}")
        lines.append(f"ERWARTETER OUTCOME: {self.get_dialogue_outcome_display()} — {self.outcome_description}")
        return "\n".join(lines)
