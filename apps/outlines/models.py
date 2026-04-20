"""
Outlines — Models for DB-backed Prompt Templates + Quality Feedback

Architecture:
  - OutlinePromptTemplate: Versionierte, content-type-aware Prompt-Templates
    - Dispatch: content_type_group × template_key → system_prompt + user_prompt
    - Versioning: version auto-increments, only one is_active per group+key
    - Fallback: .jinja2 files if no DB entry exists
  - OutlineQualityRating: User-Feedback auf KI-generierte Outline-Inhalte
    - Linked to specific template version for prompt-tuning feedback loop

Content-Type Groups:
  fiction    → novel, short_story, screenplay
  academic   → academic, scientific
  nonfiction → nonfiction, essay
"""

from django.conf import settings
from django.db import models

from apps.projects.constants import CONTENT_TYPE_GROUPS
from apps.projects.models import OutlineNode

DEFAULT_GROUP = "fiction"


def get_content_type_group(content_type: str) -> str:
    """Map a BookProject.content_type value to a prompt group."""
    return CONTENT_TYPE_GROUPS.get(content_type, DEFAULT_GROUP)


# ── Prompt Template Model ───────────────────────────────────────────
class OutlinePromptTemplate(models.Model):
    """
    DB-backed, versionierte Prompt-Templates für Outline-Enrichment.

    Dispatch-Key: (content_type_group, template_key)
    Nur ein Template pro Key-Kombination kann is_active=True sein.
    """

    class ContentTypeGroup(models.TextChoices):
        FICTION = "fiction", "Belletristik (Roman, Kurzgeschichte, Drehbuch)"
        ACADEMIC = "academic", "Wissenschaftlich (Paper, Dissertation)"
        NONFICTION = "nonfiction", "Sachtext (Essay, Sachbuch)"

    class TemplateKey(models.TextChoices):
        ENRICH_NODE = "enrich_node", "Einzelnes Kapitel anreichern"
        DETAIL_PASS = "detail_pass", "Detail-Pass (Batch-Generierung)"
        STRUCTURE_PASS = "structure_pass", "Struktur-Pass (Beat/Akt/Wörter)"

    content_type_group = models.CharField(
        max_length=20,
        choices=ContentTypeGroup.choices,
        db_index=True,
    )
    template_key = models.CharField(
        max_length=30,
        choices=TemplateKey.choices,
        db_index=True,
    )
    system_prompt = models.TextField(
        help_text="System-Prompt (Rolle, Regeln, Format). Jinja2-Variablen erlaubt.",
    )
    user_prompt_template = models.TextField(
        help_text=(
            "User-Prompt-Template (Jinja2). Verfügbare Variablen: "
            "context_block, content_type, beat_phase, act, order, title, "
            "target_words, description"
        ),
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(
        default=False,
        help_text="Nur ein Template pro (group, key) darf aktiv sein.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Änderungsnotizen (warum diese Version erstellt wurde).",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_outline_prompt_templates"
        ordering = ["content_type_group", "template_key", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type_group", "template_key", "version"],
                name="unique_prompt_version",
            ),
            models.UniqueConstraint(
                fields=["content_type_group", "template_key"],
                condition=models.Q(is_active=True),
                name="unique_active_prompt",
            ),
        ]
        verbose_name = "Outline Prompt-Template"
        verbose_name_plural = "Outline Prompt-Templates"

    def __str__(self):
        active = " ✓" if self.is_active else ""
        return f"{self.get_content_type_group_display()} / {self.get_template_key_display()} v{self.version}{active}"

    def save(self, *args, **kwargs):
        if not self.version:
            last = (
                OutlinePromptTemplate.objects.filter(
                    content_type_group=self.content_type_group,
                    template_key=self.template_key,
                )
                .order_by("-version")
                .values_list("version", flat=True)
                .first()
            )
            self.version = (last or 0) + 1
        super().save(*args, **kwargs)

    def activate(self):
        """Activate this version and deactivate others for the same key."""
        OutlinePromptTemplate.objects.filter(
            content_type_group=self.content_type_group,
            template_key=self.template_key,
            is_active=True,
        ).update(is_active=False)
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])

    def render_messages(self, **context) -> list[dict]:
        """Render this template with context to messages list."""
        from jinja2 import Template as Jinja2Template

        messages = []
        if self.system_prompt:
            tpl = Jinja2Template(self.system_prompt)
            rendered = tpl.render(**context).strip()
            if rendered:
                messages.append({"role": "system", "content": rendered})
        if self.user_prompt_template:
            tpl = Jinja2Template(self.user_prompt_template)
            rendered = tpl.render(**context).strip()
            if rendered:
                messages.append({"role": "user", "content": rendered})
        return messages


# ── Quality Rating Model ────────────────────────────────────────────
class OutlineQualityRating(models.Model):
    """
    User-Feedback auf KI-generierte Outline-Inhalte.

    Verlinkt mit dem Template-Version die den Inhalt erzeugt hat,
    um Prompt-Tuning-Feedback-Loop zu ermöglichen.
    """

    class Rating(models.IntegerChoices):
        UNUSABLE = 1, "Unbrauchbar"
        POOR = 2, "Schlecht"
        ACCEPTABLE = 3, "Akzeptabel"
        GOOD = 4, "Gut"
        EXCELLENT = 5, "Ausgezeichnet"

    outline_node = models.ForeignKey(
        OutlineNode,
        on_delete=models.CASCADE,
        related_name="quality_ratings",
    )
    prompt_template = models.ForeignKey(
        OutlinePromptTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratings",
        help_text="Template-Version die diesen Inhalt erzeugt hat.",
    )
    rating = models.IntegerField(choices=Rating.choices)
    feedback = models.TextField(
        blank=True,
        default="",
        help_text="Optionaler Freitext: Was war gut/schlecht?",
    )
    generated_content_snapshot = models.TextField(
        blank=True,
        default="",
        help_text="Snapshot des generierten Inhalts zum Zeitpunkt der Bewertung.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_outline_quality_ratings"
        ordering = ["-created_at"]
        verbose_name = "Outline Qualitätsbewertung"
        verbose_name_plural = "Outline Qualitätsbewertungen"

    def __str__(self):
        return f"{self.outline_node.title} — {self.get_rating_display()} ({self.created_at:%Y-%m-%d})"
