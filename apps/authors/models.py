"""
Authors App — Autor-Profile und Schreibstile

Struktur:
  Author (1 User → N Authors)
  WritingStyle (1 Author → N Styles, mit DO/DONT/Taboo Style Lab Feldern)
  WritingStyleSample (1 Style → N Beispieltexte)
"""
import uuid

from django.conf import settings
from django.db import models


class Author(models.Model):
    """Autor-Profil (kann Pen-Name oder realer Name sein)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authors",
    )
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_authors"
        ordering = ["name"]
        verbose_name = "Autor"
        verbose_name_plural = "Autoren"

    def __str__(self):
        return self.name

    @property
    def style_count(self):
        return self.writing_styles.count()


class WritingStyle(models.Model):
    """Schreibstil eines Autors — Style Lab Builder mit DO/DONT/Taboo."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Entwurf"
        ANALYZING = "analyzing", "Analyse läuft"
        READY = "ready", "Bereit"
        ERROR = "error", "Fehler"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="writing_styles",
    )
    name = models.CharField(
        max_length=200,
        help_text="z.B. 'Thriller-Stil', 'Romantisch', 'Sachlich'",
    )
    description = models.TextField(
        blank=True,
        help_text="Kurzbeschreibung des Stils",
    )
    source_text = models.TextField(
        blank=True,
        help_text="Originaltext der hochgeladen und analysiert wurde",
    )
    style_profile = models.TextField(
        blank=True,
        help_text="LLM-generiertes Stil-Profil",
    )
    style_prompt = models.TextField(
        blank=True,
        help_text="Kondensierter Prompt-Baustein für LLM-Generierung",
    )
    # Style Lab Builder Felder (bfagent-kompatibel)
    do_list = models.JSONField(
        default=list,
        help_text="Erlaubte/empfohlene Stilmittel (Style Lab DO-Liste)",
    )
    dont_list = models.JSONField(
        default=list,
        help_text="Verbotene Stilmittel (Style Lab DONT-Liste)",
    )
    taboo_list = models.JSONField(
        default=list,
        help_text="Tabu-Wörter (niemals verwenden)",
    )
    signature_moves = models.JSONField(
        default=list,
        help_text="Charakteristische Stilmittel dieses Autors",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    error_message = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_writing_styles"
        ordering = ["author", "name"]
        verbose_name = "Schreibstil"
        verbose_name_plural = "Schreibstile"

    def __str__(self):
        return f"{self.author.name} — {self.name}"

    @property
    def sample_count(self):
        return self.samples.count()

    @property
    def has_style_lab_data(self):
        return bool(self.do_list or self.dont_list or self.taboo_list or self.signature_moves)


class WritingStyleSample(models.Model):
    """Beispieltext in einem bestimmten Schreibstil für eine Situation."""

    SITUATIONS = [
        ("action", "Actionszene"),
        ("dialogue", "Dialog"),
        ("description", "Ortsbeschreibung"),
        ("emotion", "Emotionale Szene"),
        ("intro", "Kapiteleinstieg"),
        ("outro", "Kapitelende / Cliffhanger"),
        ("inner", "Innerer Monolog"),
        ("exposition", "Exposition"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    style = models.ForeignKey(
        WritingStyle,
        on_delete=models.CASCADE,
        related_name="samples",
    )
    situation = models.CharField(max_length=30, choices=SITUATIONS)
    text = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_writing_style_samples"
        ordering = ["style", "situation"]
        verbose_name = "Stil-Beispieltext"
        verbose_name_plural = "Stil-Beispieltexte"

    def __str__(self):
        return f"{self.style} — {self.get_situation_display()}"
