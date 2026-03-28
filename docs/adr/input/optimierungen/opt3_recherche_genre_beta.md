# OPT3 — Recherche, Genre-Konventionen & Beta-Reader

> Drei strukturell unverbundene Lücken, die gemeinsam adressiert werden:
> Recherche-Notes fehlen vollständig. Genre-Konventionen sind nicht
> maschinenlesbar. Feedback von Dritten hat kein Modell.

---

## OPT3.1 — Recherche-Notes (`ResearchNote`)

### Problem
Ein historischer Roman, ein Thriller mit Polizeiverfahren, ein Sci-Fi-Roman
mit Physik — alle brauchen Recherche. Aktuell hat der Hub keinen Ort dafür.
Recherche-Notizen landen in Notizbüchern, Notion oder nirgendwo.
Konsequenz: LLM-generierte Kapitel haben keine Möglichkeit, auf geprüfte
Fakten zuzugreifen.

```python
# apps/projects/models_research.py

class ResearchNote(models.Model):
    """
    Recherche-Notiz — verifizierter Fakt oder offene Frage.

    Typen:
        fact       → Verifizierbarer Fakt (mit Quelle)
        question   → Offene Recherche-Frage
        rule       → Weltregeln / technische Regeln (für Sci-Fi, Fantasy)
        atmosphere → Atmosphärische Details (Gerüche, Klänge, Bilder)
        quote      → Recherchiertes Zitat

    Verknüpfung mit OutlineNode: LLM kann beim Schreiben von Kapitel N
    alle relevanten Notizen für diese Szene als Kontext erhalten.
    """
    RESEARCH_TYPES = [
        ("fact",        "Fakt — verifiziert"),
        ("question",    "Offene Frage"),
        ("rule",        "Regel / Gesetz / Technologie"),
        ("atmosphere",  "Atmosphäre / Detail"),
        ("quote",       "Zitat"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.BookProject", on_delete=models.CASCADE,
                                related_name="research_notes")
    note_type = models.CharField(max_length=20, choices=RESEARCH_TYPES, default="fact")
    title = models.CharField(max_length=300)
    content = models.TextField()
    source = models.CharField(max_length=500, blank=True, default="",
                              help_text="URL, Buch, Gespräch mit Experten")
    is_verified = models.BooleanField(default=False)
    is_open_question = models.BooleanField(default=False,
                                           help_text="Noch nicht beantwortet")

    # Verknüpfung mit Kapiteln / Szenen
    relevant_nodes = models.ManyToManyField(
        "projects.OutlineNode",
        blank=True,
        related_name="research_notes",
        help_text="In welchen Kapiteln/Szenen ist diese Notiz relevant?",
    )

    # Tags für Suche
    tags = models.JSONField(default=list, help_text='["Berlin 1989", "Stasi", "Verhörtechniken"]')

    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_research_notes"
        ordering = ["project", "-is_verified", "note_type", "sort_order"]
        verbose_name = "Recherche-Notiz"

    def to_prompt_context(self) -> str:
        """Für LLM-Injection bei Kapitel-Generierung."""
        lines = [f"[{self.get_note_type_display().upper()}] {self.title}",
                 self.content]
        if self.source:
            lines.append(f"Quelle: {self.source}")
        return "\n".join(lines)
```

**LLM-Kontext-Erweiterung:** `project_context_service.py` ergänzen:
```python
# Beim Aufbau des Kapitel-Schreib-Kontexts:
research = ResearchNote.objects.filter(
    relevant_nodes=current_node, is_verified=True
)
if research.exists():
    context_parts.append("RECHERCHE FÜR DIESE SZENE:\n" +
                         "\n---\n".join(r.to_prompt_context() for r in research[:5]))
```

---

## OPT3.2 — Genre-Konventions-Checkliste (`GenreConventionCheck`)

### Problem
Jedes Genre hat implizite Vertragsregeln mit dem Leser:
- Thriller: Eine Leiche (oder Bedrohung) bis Seite 15–20
- Romance: Meet-Cute in den ersten 10%, Happy End garantiert
- Krimi: Fair-Play — alle Hinweise müssen vor der Auflösung da sein
- Fantasy: Magisches System mit klaren Regeln bis Ende Akt I
- Literary Fiction: Kein Happy End nötig — aber emotionale Wahrhaftigkeit

Verlage prüfen das. Ein "Thriller" ohne Bedrohung in den ersten 50 Seiten
ist kein Thriller — sondern ein falsches Genre-Label.

```python
class GenreConventionProfile(models.Model):
    """
    Genre-Konventions-Profil — maschinenlesbare Erwartungen.

    Wird mit genre_lookup verknüpft.
    Admin-verwaltbar: neue Genres ohne Code-Änderung.
    """
    genre_lookup = models.OneToOneField(
        "projects.GenreLookup",
        on_delete=models.CASCADE,
        related_name="convention_profile",
    )
    conventions = models.JSONField(
        default=list,
        help_text="""
Liste von Genre-Konventionen. Format:
[{
    "label": "Erste Bedrohung",
    "description": "Eine klare Bedrohung muss in den ersten 10% erscheinen",
    "check_by_percent": 10,
    "weight": "required|recommended|optional",
    "check_field": "turning_points__turning_point_type__code",
    "check_value": "inciting_incident"
}]
"""
    )
    reader_promise = models.TextField(
        blank=True, default="",
        help_text="Was verspricht dieses Genre dem Leser implizit? "
                  "(z.B. 'Ein Thriller verspricht: Auflösung der Bedrohung')",
    )

    class Meta:
        db_table = "wh_genre_convention_profiles"
        verbose_name = "Genre-Konventions-Profil"
```

**Service:**
```python
def check_genre_conventions(project: BookProject) -> list[dict]:
    """Prüft Projekt gegen Genre-Konventionen. Gibt Check-Liste zurück."""
    profile = getattr(
        getattr(project, "genre_lookup", None), "convention_profile", None
    )
    if not profile:
        return []

    results = []
    for conv in profile.conventions:
        # Prüfung: Gibt es einen TurningPoint innerhalb der geforderten Prozentzahl?
        if "check_by_percent" in conv:
            tp_exists = project.turning_points.filter(
                position_percent__lte=conv["check_by_percent"]
            ).exists()
            results.append({
                "label": conv["label"],
                "passed": tp_exists,
                "weight": conv.get("weight", "recommended"),
                "description": conv["description"],
            })
    return results
```

---

## OPT3.3 — Beta-Reader-Feedback (`BetaReaderSession`)

### Problem
`ChapterReview` ist für Autor-eigenes Review oder KI-Review gedacht.
Es gibt kein Modell für externes Feedback (Testleser, Lektorat, Verlag).
Der Unterschied ist wichtig: Ein Beta-Leser sieht den Text ohne Kontext,
hat andere Fragen (Spannung? Figur sympathisch? Verständlich?) und seine
Antworten haben andere Gewichtung.

```python
class BetaReaderSession(models.Model):
    """
    Beta-Leser-Runde — externes Feedback zu einem Manuskript-Stand.

    Ein Beta-Leser sieht: Kapitel-Texte (optional anonym).
    Er sieht NICHT: Outline, WeltenHub-Daten, dramaturgische Metadaten.

    Anonymisierungs-Optionen:
        anon_full   → Autor-Name verborgen
        anon_meta   → Nur Text, keine Metadaten
        open        → Alles sichtbar
    """
    ANON_CHOICES = [
        ("open",      "Offen"),
        ("anon_meta", "Text only"),
        ("anon_full", "Vollständig anonym"),
    ]

    FEEDBACK_FOCUS = [
        ("general",     "Allgemein"),
        ("pacing",      "Pacing & Tempo"),
        ("character",   "Figuren-Sympathie"),
        ("clarity",     "Verständlichkeit"),
        ("tension",     "Spannung"),
        ("ending",      "Schluss / Auflösung"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.BookProject", on_delete=models.CASCADE,
                                related_name="beta_sessions")
    name = models.CharField(max_length=200, help_text="Bezeichnung der Runde")
    anonymization = models.CharField(max_length=20, choices=ANON_CHOICES, default="anon_meta")
    feedback_focus = models.CharField(max_length=20, choices=FEEDBACK_FOCUS, default="general")
    manuscript_snapshot = models.ForeignKey(
        "projects.ManuscriptSnapshot",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="beta_sessions",
        help_text="Welcher Manuskript-Stand wurde geteilt?",
    )
    reader_name = models.CharField(max_length=200, blank=True, default="")
    reader_note = models.TextField(blank=True, default="")
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "wh_beta_reader_sessions"
        ordering = ["-created_at"]
        verbose_name = "Beta-Leser-Session"


class BetaReaderFeedback(models.Model):
    """Einzelnes Feedback-Item einer Beta-Leser-Session."""
    FEEDBACK_TYPES = [
        ("confusion",    "Unklarheit / Verwirrung"),
        ("boredom",      "Langeweile / Tempo zu langsam"),
        ("tension_drop", "Spannungsabfall"),
        ("character_ok", "Figur sympathisch"),
        ("char_problem", "Figur-Problem"),
        ("highlight",    "Besonders gut"),
        ("general",      "Allgemeines Feedback"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(BetaReaderSession, on_delete=models.CASCADE,
                                related_name="feedbacks")
    node = models.ForeignKey("projects.OutlineNode", on_delete=models.SET_NULL,
                             null=True, blank=True, related_name="beta_feedbacks")
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default="general")
    text = models.TextField()
    text_reference = models.TextField(blank=True, default="")
    chapter_order = models.PositiveSmallIntegerField(null=True, blank=True)
    is_addressed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_beta_reader_feedbacks"
        ordering = ["session", "chapter_order", "feedback_type"]
        verbose_name = "Beta-Reader-Feedback"
```

---

## OPT3.4 — Integration in DramaturgicHealthScore

```python
# Ergänzungen in compute_dramaturgic_health():

# Genre-Konventionen
genre_checks = check_genre_conventions(project)
for gc in genre_checks:
    if gc["weight"] == "required":
        checks.append(HealthCheck(
            label=f"Genre: {gc['label']}",
            passed=gc["passed"],
            message=gc["description"],
            weight=2,
        ))

# Offene Recherche-Fragen
open_questions = project.research_notes.filter(is_open_question=True).count()
checks.append(HealthCheck(
    label="Offene Recherche-Fragen",
    passed=open_questions == 0,
    message=f"{open_questions} offene Recherche-Fragen — vor Fertigstellung klären.",
    weight=1,
))
```

---

## OPT3.5 — Tabellen-Übersicht OPT3

```bash
# Neue Tabellen:
wh_research_notes
wh_genre_convention_profiles
wh_beta_reader_sessions
wh_beta_reader_feedbacks

# Migration: 0012_research_genre_beta
# Seed: GenreConventionProfile für Thriller, Romance, Krimi (Admin)
```

---

*writing-hub · OPT3 · Recherche, Genre-Konventionen, Beta-Reader*
*Verlegerischer Kern: Genre-Konventionen sind Verträge mit dem Leser*
