# ADR-160: Wissens-Infrastruktur — Recherche, Genre-Konventionen, Beta-Reader

**Status:** Proposed  
**Datum:** 2026-03-28  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-157, ADR-159

---

## Kontext

Drei unabhängige, aber strukturell verwandte Lücken:
Alle drei adressieren **Wissen, das von außen in den Hub fließt** —
von Fakten-Recherche über Genre-Regeln bis zu Testleser-Feedback.

### Lücke 1 — Keine Recherche-Datenbank

Historische Romane, Thriller mit Ermittlungsverfahren, Sci-Fi mit
Physikgrundlagen — alle erfordern verifizierte Fakten. Aktuell
haben Autoren keinen Ort im Hub dafür. Konsequenz: LLM-generierte
Kapitel ohne Fakten-Injection produzieren plausibel klingende,
aber falsche Details.

Ein Recherche-Irrtum (falsche Waffe, falsche historische Jahreszahl,
falsche juristische Prozedur) wird von Verlagen als Zeichen
mangelnder Professionalität gewertet.

### Lücke 2 — Genre-Konventionen nicht maschinenlesbar

Jedes Genre hat implizite Vertrags-Regeln mit dem Leser:
- **Thriller:** Klare Bedrohung bis Seite 15–20 (ca. 10%)
- **Romance:** Meet-Cute im ersten Viertel, Happy End garantiert
- **Krimi:** Fair-Play-Prinzip — alle Hinweise müssen vor Auflösung vorhanden sein
- **Fantasy:** Magisches System mit klaren Regeln bis Ende Akt I

Das writing-hub kann `genre_lookup` setzen — aber nicht validieren,
ob das Genre-Label korrekt ist.

### Lücke 3 — Beta-Leser-Feedback nicht strukturiert

`ChapterReview` (ADR-083) ist für Autor-eigenes oder KI-Review.
Testleser-Feedback folgt anderen Regeln: Der Beta-Leser sieht
den Text ohne dramaturgischen Kontext, reagiert als Leser, nicht
als Strukturanalytiker. Seine Verwirrung ist wichtiger als
sein Stilurteil.

---

## Entscheidung

### Teil A: `ResearchNote` Model

```python
# apps/projects/models_research.py

import uuid
from django.db import models


class ResearchNote(models.Model):
    """
    Recherche-Notiz — verifizierter Fakt, offene Frage oder
    atmosphärisches Detail.

    Verknüpfung mit OutlineNode (M2M): Beim Generieren von Kapitel N
    werden alle relevanten, verifizierten Notizen als Fakten-Kontext
    in den LLM-Prompt injiziert.

    Kategorien:
        fact       → Verifizierter Fakt mit Quelle
        question   → Offene Recherche-Frage (noch unbeantwortet)
        rule       → Weltregeln / Gesetze / Technologie
        atmosphere → Sensorische Details (Gerüche, Klänge, Bilder)
        quote      → Recherchiertes Zitat mit Quelle
    """
    NOTE_TYPES = [
        ("fact",        "Fakt — verifiziert"),
        ("question",    "Offene Frage"),
        ("rule",        "Regel / Gesetz / Technologie"),
        ("atmosphere",  "Atmosphäre / Detail"),
        ("quote",       "Zitat"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="research_notes",
    )
    note_type = models.CharField(
        max_length=20, choices=NOTE_TYPES, default="fact",
    )
    title = models.CharField(max_length=300, verbose_name="Bezeichnung")
    content = models.TextField(verbose_name="Inhalt")
    source = models.CharField(
        max_length=500, blank=True, default="",
        help_text="URL, Buchtitel, Experteninterview — Pflicht für note_type='fact'",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Nur verifizierte Notizen werden in LLM-Prompts injiziert.",
    )
    is_open_question = models.BooleanField(
        default=False,
        help_text="Noch unbeantwortet — wird im Health-Score als offene Frage gezählt.",
    )

    # Kapitel-Verknüpfung
    relevant_nodes = models.ManyToManyField(
        "projects.OutlineNode",
        blank=True,
        related_name="research_notes",
        help_text="Welche Kapitel/Szenen brauchen diese Notiz?",
    )

    # Tagging für Suche und Filterung
    tags = models.JSONField(
        default=list,
        help_text='["Berlin 1989", "Stasi", "Verhörtechnik"]',
    )

    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_research_notes"
        ordering = ["project", "-is_verified", "note_type", "sort_order"]
        verbose_name = "Recherche-Notiz"
        verbose_name_plural = "Recherche-Notizen"

    def __str__(self):
        verified = " ✓" if self.is_verified else " ?"
        return f"[{self.get_note_type_display()}]{verified} {self.title}"

    def to_prompt_context(self) -> str:
        """
        Gibt Notiz als LLM-Prompt-Kontext zurück.
        Nur für is_verified=True aufrufen.
        """
        lines = [
            f"[{self.get_note_type_display().upper()}] {self.title}",
            self.content,
        ]
        if self.source:
            lines.append(f"Quelle: {self.source}")
        return "\n".join(lines)
```

**LLM-Kontext-Erweiterung in `project_context_service.py`:**

```python
# In _build_chapter_context() ergänzen:
research = ResearchNote.objects.filter(
    relevant_nodes=current_node,
    is_verified=True,
).order_by("note_type")

if research.exists():
    context_parts.append(
        "VERIFIZIERTE RECHERCHE FÜR DIESE SZENE:\n"
        + "\n---\n".join(r.to_prompt_context() for r in research[:5])
    )
```

---

### Teil B: `GenreConventionProfile` Model

```python
class GenreConventionProfile(models.Model):
    """
    Genre-Konventions-Profil — maschinenlesbare Vertrags-Regeln.

    1:1 zu GenreLookup. Admin-verwaltbar: neue Genre-Profile
    ohne Code-Deployment.

    conventions JSON-Schema:
    [{
        "label": "Erste Bedrohung",
        "description": "Klare Bedrohung bis 10% des Romans",
        "check_type": "turning_point_exists",
        "check_by_percent": 10,
        "weight": "required|recommended|optional",
        "outlinefw_beat": "inciting_incident"
    }]

    check_types (erweiterbar via Admin):
        turning_point_exists → TurningPoint mit outlinefw_beat <= check_by_percent
        b_story_exists       → SubplotArc vorhanden
        happy_end_required   → arc_direction muss 'positive' sein
        fair_play            → alle ForeshadowingEntries müssen Setup vor 75% haben
    """
    genre_lookup = models.OneToOneField(
        "projects.GenreLookup",
        on_delete=models.CASCADE,
        related_name="convention_profile",
    )
    conventions = models.JSONField(
        default=list,
        help_text="Liste von Konventions-Checks (siehe Schema in Docstring)",
    )
    reader_promise = models.TextField(
        blank=True, default="",
        help_text="Was verspricht dieses Genre dem Leser implizit?",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_genre_convention_profiles"
        verbose_name = "Genre-Konventions-Profil"

    def __str__(self):
        return f"Konventionen: {self.genre_lookup.name}"
```

**Genre-Convention-Service:**

```python
# apps/projects/services/genre_service.py

def check_genre_conventions(project) -> list[dict]:
    """
    Prüft Projekt gegen Genre-Konventionen.
    Gibt Check-Liste zurück — kann in DramaturgicHealthScore integriert werden.
    """
    genre_lookup = getattr(project, "genre_lookup", None)
    if not genre_lookup:
        return []
    profile = getattr(genre_lookup, "convention_profile", None)
    if not profile:
        return []

    results = []
    for conv in profile.conventions:
        passed = _evaluate_convention(project, conv)
        results.append({
            "label": conv.get("label", ""),
            "description": conv.get("description", ""),
            "passed": passed,
            "weight": conv.get("weight", "recommended"),
        })
    return results


def _evaluate_convention(project, conv: dict) -> bool:
    check_type = conv.get("check_type", "")
    if check_type == "turning_point_exists":
        pct = conv.get("check_by_percent", 100)
        beat = conv.get("outlinefw_beat", "")
        return project.turning_points.filter(
            position_percent__lte=pct
        ).exists()
    elif check_type == "b_story_exists":
        return project.subplot_arcs.filter(story_label="b_story").exists()
    elif check_type == "happy_end_required":
        return getattr(project, "arc_direction", "") == "positive"
    elif check_type == "fair_play":
        # Alle ForeshadowingEntries müssen Setup vor 75% haben
        entries = project.foreshadowing_entries.filter(is_planted=True)
        return all(
            e.setup_node and e.setup_node.outlinefw_position and
            float(e.setup_node.outlinefw_position) <= 0.75
            for e in entries
        )
    return True  # unbekannter check_type → nicht blockieren
```

**Seed für Thriller-Konventionen (in Admin oder Management Command):**

```python
THRILLER_CONVENTIONS = [
    {
        "label": "Erste Bedrohung bis 10%",
        "description": "Ein Thriller muss spätestens bei 10% eine klare Bedrohung etabliert haben.",
        "check_type": "turning_point_exists",
        "check_by_percent": 12,
        "weight": "required",
        "outlinefw_beat": "inciting_incident",
    },
    {
        "label": "Kein Happy End erforderlich",
        "description": "Thriller können negativ enden — aber der Protagonist muss aktiv gehandelt haben.",
        "check_type": "none",
        "weight": "optional",
    },
]

ROMANCE_CONVENTIONS = [
    {
        "label": "Happy End erforderlich",
        "description": "Romance-Vertragsregel: positiver Arc ist Genre-Pflicht.",
        "check_type": "happy_end_required",
        "weight": "required",
    },
    {
        "label": "Liebesinteresse als B-Story",
        "description": "Das Liebesinteresse muss eine B-Story tragen.",
        "check_type": "b_story_exists",
        "weight": "required",
    },
]

KRIMI_CONVENTIONS = [
    {
        "label": "Fair-Play-Prinzip",
        "description": "Alle Hinweise müssen vor der Auflösung im Roman platziert sein.",
        "check_type": "fair_play",
        "weight": "required",
    },
]
```

---

### Teil C: Beta-Reader-Modelle

```python
# apps/projects/models_beta.py

class BetaReaderSession(models.Model):
    """
    Beta-Leser-Runde — strukturiertes Testleser-Feedback.

    Unterschied zu ChapterReview:
        ChapterReview → Autor oder KI analysiert Text strukturell
        BetaReaderSession → Externe Person reagiert als Leser

    Der Beta-Leser sieht: Kapitel-Texte (via ManuscriptSnapshot).
    Der Beta-Leser sieht NICHT: Outline, WeltenHub, dramaturgische Metadaten.

    Anonymisierung:
        open      → Autor und Metadaten sichtbar
        anon_meta → Nur Text, keine Metadaten
        anon_full → Vollständig anonym (kein Autor-Name)
    """
    ANON_CHOICES = [
        ("open",      "Offen — alles sichtbar"),
        ("anon_meta", "Text only — keine Metadaten"),
        ("anon_full", "Vollständig anonym"),
    ]
    FEEDBACK_FOCUS = [
        ("general",     "Allgemein"),
        ("pacing",      "Pacing & Tempo"),
        ("character",   "Figuren-Sympathie"),
        ("clarity",     "Verständlichkeit"),
        ("tension",     "Spannungsverlauf"),
        ("ending",      "Schluss / Auflösung"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject", on_delete=models.CASCADE,
        related_name="beta_sessions",
    )
    name = models.CharField(max_length=200, help_text="z.B. 'Beta-Runde 1 — April 2026'")
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

    def __str__(self):
        return f"{self.name} — {self.project.title}"

    @property
    def open_feedback_count(self) -> int:
        return self.feedbacks.filter(is_addressed=False).count()


class BetaReaderFeedback(models.Model):
    """
    Einzelnes Feedback-Item einer Beta-Leser-Session.

    feedback_type unterscheidet Reaktions-Typen:
        confusion    → Leser ist verwirrt (höchste Priorität)
        boredom      → Leser hat Tempo-Problem
        tension_drop → Spannungsabfall erlebt
        highlight    → Positives Feedback
        character_ok → Figur sympathisch
        char_problem → Figur-Problem
        general      → Allgemeines Feedback
    """
    FEEDBACK_TYPES = [
        ("confusion",    "Unklarheit / Verwirrung"),
        ("boredom",      "Langeweile / Tempo zu langsam"),
        ("tension_drop", "Spannungsabfall"),
        ("highlight",    "Besonders gut"),
        ("character_ok", "Figur sympathisch"),
        ("char_problem", "Figur-Problem"),
        ("general",      "Allgemeines Feedback"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        BetaReaderSession, on_delete=models.CASCADE, related_name="feedbacks",
    )
    node = models.ForeignKey(
        "projects.OutlineNode", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="beta_feedbacks",
    )
    feedback_type = models.CharField(
        max_length=20, choices=FEEDBACK_TYPES, default="general",
    )
    text = models.TextField(verbose_name="Feedback-Text")
    text_reference = models.TextField(
        blank=True, default="",
        help_text="Zitierter Textstelle aus dem Manuskript (optional)",
    )
    chapter_order = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Kapitel-Position",
    )
    is_addressed = models.BooleanField(
        default=False,
        help_text="Wurde dieses Feedback berücksichtigt / abgearbeitet?",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_beta_reader_feedbacks"
        ordering = ["session", "chapter_order", "feedback_type"]
        verbose_name = "Beta-Reader-Feedback"

    def __str__(self):
        return f"[{self.get_feedback_type_display()}] {self.text[:60]}"
```

---

### Teil D: Health-Score Integration (ADR-157 Ergänzungen)

```python
# In compute_dramaturgic_health():

# --- OFFENE RECHERCHE-FRAGEN (Gewicht 1) ---
open_questions = project.research_notes.filter(
    is_open_question=True
).count() if hasattr(project, "research_notes") else 0

checks.append(HealthCheck(
    label="Offene Recherche-Fragen",
    passed=open_questions == 0,
    message=f"{open_questions} offene Recherche-Fragen — vor Fertigstellung klären.",
    weight=1,
))

# --- GENRE-KONVENTIONEN (Gewicht 2 für 'required') ---
from projects.services.genre_service import check_genre_conventions
genre_checks = check_genre_conventions(project)
for gc in genre_checks:
    if gc["weight"] == "required":
        checks.append(HealthCheck(
            label=f"Genre-Konvention: {gc['label']}",
            passed=gc["passed"],
            message=gc["description"],
            weight=2,
        ))
```

---

## Begründung

- **`ResearchNote.is_verified` als Injection-Gate:** Nur verifizierte Notizen
  werden in LLM-Prompts injiziert. Unverifizierte Notizen sind Arbeits-Notizen
  für den Autor — sie haben im LLM-Kontext nichts verloren.

- **`ResearchNote` M2M zu `OutlineNode`** (nicht FK auf BookProject):
  Ein Fakt ist oft für mehrere Kapitel relevant. M2M ist die korrekte
  Kardinalität. Der Autor wählt explizit, welche Kapitel die Notiz nutzen.

- **`GenreConventionProfile` Admin-verwaltbar:**
  Genre-Konventionen ändern sich mit dem Markt. Neue Sub-Genres entstehen.
  Kein Code-Deployment für neue Konventions-Profile — Admin reicht.

- **`BetaReaderFeedback.feedback_type = "confusion"` als Priorität:**
  Verwirrung beim Leser ist wichtiger als Stilkritik. Das Typ-System
  priorisiert `confusion` und `boredom` über `general` — im UI
  durch Farb-Codierung sichtbar.

- **Beta-Reader sieht `ManuscriptSnapshot`**, nicht Live-Daten:
  Testleser-Feedback bezieht sich immer auf einen spezifischen
  Manuskript-Stand. ManuscriptSnapshot ist bereits im Stack (ADR-083).

---

## Abgelehnte Alternativen

**ResearchNote ohne M2M (nur FK auf Projekt):**
Zu unspezifisch für LLM-Injection. Ein Projekt mit 50 Notizen
würde alle 50 in jeden Kapitel-Prompt injizieren.

**GenreConventionProfile hardcoded:**
Genre-Märkte sind dynamisch. Admin-Verwaltung ist die
zukunftssicherere Lösung.

**BetaReaderFeedback als ChapterReview-Erweiterung:**
Zu viel Kontamination. Beta-Leser-Feedback ist konzeptionell
getrennt von Autor-Review und KI-Lektorat.

---

## Konsequenzen

- Migration `projects/0012_research_genre_beta` — vier neue Tabellen
  inkl. M2M-Tabelle `wh_research_notes_relevant_nodes`
- `GenreConventionService` in `apps/projects/services/genre_service.py`
- `project_context_service.py`: Research-Injection ergänzen
- Health-Score: offene Fragen + Genre-Checks (ADR-157 Revision)
- Admin: `GenreConventionProfile` mit JSON-Schema-Hilfe für Konventions-Felder
- URLs:
  - `projects/<pk>/research/` → Recherche-Verwaltung
  - `projects/<pk>/beta/` → Beta-Leser-Sessions
  - `projects/<pk>/beta/<session_pk>/feedback/` → Feedback-Eingabe
- Seed: Thriller, Romance, Krimi, Fantasy Konventions-Profile (Management Command)
- AIActionType: kein neuer — Genre-Checks sind regelbasiert

---

**Referenzen:** ADR-083 (ManuscriptSnapshot, ChapterReview),  
ADR-157 (DramaturgicHealthScore — Erweiterungspunkte),  
ADR-159 (Comps — verlegerischer Kontext),  
`docs/adr/input/schritt_06_spannung.md` (Fair-Play-Prinzip)
