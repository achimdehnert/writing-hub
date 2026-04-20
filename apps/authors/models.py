"""
Authors App — Autor-Profile und Schreibstile

Struktur:
  GenreProfile (genre-spezifische Situationstypen-Konfiguration)
  SituationType (1 GenreProfile → N SituationTypes)
  Author (1 User → N Authors)
  WritingStyle (1 Author → N Styles, 1 GenreProfile)
  WritingStyleSample (1 Style → N Beispieltexte, 1 SituationType)
"""

import uuid

from django.conf import settings
from django.db import models


class GenreProfile(models.Model):
    """Genre mit eigener Situationstypen-Konfiguration."""

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    name_short = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "wh_genre_profiles"
        ordering = ["sort_order", "name"]
        verbose_name = "Genre-Profil"
        verbose_name_plural = "Genre-Profile"

    def __str__(self):
        return self.name

    @property
    def situation_count(self):
        return self.situation_types.filter(is_active=True).count()


class SituationType(models.Model):
    """Ein Situationstyp innerhalb eines GenreProfiles."""

    genre_profile = models.ForeignKey(
        GenreProfile,
        on_delete=models.CASCADE,
        related_name="situation_types",
    )
    slug = models.SlugField(max_length=80)
    label = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    llm_prompt_hint = models.TextField(
        blank=True,
        help_text="Zusaetzliche Analysekriterien fuer LLM-Prompts",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "wh_situation_types"
        ordering = ["sort_order"]
        unique_together = [("genre_profile", "slug")]
        verbose_name = "Situationstyp"
        verbose_name_plural = "Situationstypen"

    def __str__(self):
        return f"{self.genre_profile.name_short} — {self.label}"


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
    genre_profile = models.ForeignKey(
        GenreProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="writing_styles",
        help_text="Genre bestimmt die verfuegbaren Situationstypen",
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

    # Akademische / fachspezifische Felder
    class CitationStyle(models.TextChoices):
        APA = "apa", "APA 7th"
        IEEE = "ieee", "IEEE"
        ACM = "acm", "ACM"
        HARVARD = "harvard", "Harvard"
        CHICAGO = "chicago", "Chicago"
        DIN_ISO = "din_iso", "DIN ISO 690"
        CUSTOM = "custom", "Benutzerdefiniert"

    class FormalityLevel(models.TextChoices):
        HIGH = "high", "Hoch-akademisch"
        SEMI = "semi", "Semi-formal"
        POPULAR = "popular", "Populaerwissenschaftlich"

    citation_style = models.CharField(
        max_length=20,
        choices=CitationStyle.choices,
        blank=True,
        help_text="Zitationsstil (APA, IEEE, ACM, ...)",
    )
    language = models.CharField(
        max_length=10,
        blank=True,
        help_text="Sprache: de, en, de-en (Mixed)",
    )
    target_audience = models.CharField(
        max_length=120,
        blank=True,
        help_text="Zielgruppe: Fachpublikum, Studenten, Management, ...",
    )
    formality_level = models.CharField(
        max_length=20,
        choices=FormalityLevel.choices,
        blank=True,
        help_text="Formalitaetsgrad des Stils",
    )
    domain = models.CharField(
        max_length=200,
        blank=True,
        help_text="Fachgebiet: Wirtschaftsinformatik, KI, BWL, ...",
    )
    publication_format = models.CharField(
        max_length=200,
        blank=True,
        help_text="Typisches Format: Conference Paper, Journal, Dissertation, ...",
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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
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
    situation = models.CharField(
        max_length=30,
        choices=SITUATIONS,
        help_text="Legacy-Feld, wird durch situation_type ersetzt",
    )
    situation_type = models.ForeignKey(
        SituationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="samples",
        help_text="Genre-spezifischer Situationstyp (ersetzt situation CharField)",
    )
    text = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_writing_style_samples"
        ordering = ["style", "situation"]
        verbose_name = "Stil-Beispieltext"
        verbose_name_plural = "Stil-Beispieltexte"

    def __str__(self):
        if self.situation_type:
            return f"{self.style} — {self.situation_type.label}"
        return f"{self.style} — {self.get_situation_display()}"

    @property
    def effective_label(self):
        """Label aus SituationType oder Fallback auf legacy CharField."""
        if self.situation_type:
            return self.situation_type.label
        return self.get_situation_display()
