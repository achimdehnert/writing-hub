# ADR-159: Publikationsvorbereitung — Comps, Pitch, Exposé

```yaml
status: Proposed
datum: 2026-03-28
kontext: writing-hub @ achimdehnert/writing-hub
abhaengig_von: [ADR-083, ADR-150, ADR-151, ADR-157-Rev1, ADR-158]
implementation_status: none
```

**Status:** Proposed  
**Datum:** 2026-03-28  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-083, ADR-150, ADR-151, ADR-157-Rev1, ADR-158  
**Deployment-Voraussetzung:** ADR-157 Rev.1 muss deployed sein (`narrative_role`-Feld auf `ProjectCharacterLink` wird in `_get_character()` vorausgesetzt)

---

## Kontext

`PublishingProfile` (ADR-083) enthält ISBN, BISAC, Keywords und Cover.
Das sind Metadaten **nach** der Annahme. Was fehlt, ist alles **vor** der Annahme:
das Transmissions-Format zwischen Manuskript und Verlag.

Kein Verlag liest ein kaltes Manuskript. Der erste Filter ist immer:

```
1. Logline       — 1 Satz: Worum geht es? Warum jetzt?
2. Comps         — 2–3 vergleichbare Titel: Wo liegt das Buch im Markt?
3. Exposé / Synopsis — Was passiert? (mit Ende)
4. Query Letter  — Das formale Anschreiben (EN/US)
```

Verlegerische Realität: 90% der Ablehnungen passieren auf Comp- und
Logline-Ebene — nicht weil das Manuskript schlecht ist, sondern weil
Autoren ihren Markt nicht kommunizieren können.

### Fehler, die dieser ADR verhindert

**Falsche Comps (häufigster Fehler):**
- Zu alt: "wie Das Parfum" → Verlag: "1985 ist kein Comp"
- Zu groß: "wie Harry Potter" → Verlag: "Kein Erstautor schreibt wie Rowling"
- Falsche Kategorie: Literaturnobelpreis als Comp für einen Genre-Roman

**Schwache Logline:**
- Plot-Summary statt dramatischer Kern
- Fehlendes Stakes-Element

**Kein Exposé:**
Der Hub ermöglicht heute den Abschluss des Manuskripts —
aber nicht das Einreichen bei Verlagen.

---

## Entscheidung

### Teil A: `ComparableTitle` Model

```python
# apps/projects/models_publishing.py — erweitern

import uuid
import datetime
from django.db import models


class ComparableTitle(models.Model):
    """
    Comparable Title (Comp) — ein vergleichbares, veröffentlichtes Werk.

    Verlegerische Regeln für gute Comps:
        - Erschienen in den letzten 5 Jahren (Markt-Relevanz)
        - Kein Mega-Bestseller (Harry Potter, Hunger Games)
        - Gleiches Genre + Zielgruppe
        - Begründung: Worin ähnlich, worin unterschiedlich

    Der "aber"-Teil ist oft wichtiger als der "wie"-Teil:
    "Wie [Comp A], aber mit [einzigartiger Differenzierung]"
    ist stärker als reiner Ähnlichkeits-Vergleich.
    """
    COMP_RELATION = [
        ("similar_theme",     "Ähnliches Thema"),
        ("similar_tone",      "Ähnlicher Ton"),
        ("similar_structure", "Ähnliche Struktur"),
        ("same_audience",     "Gleiche Zielgruppe"),
        ("same_subgenre",     "Gleiches Subgenre"),
        ("contrast",          "Kontrast — 'wie X, aber Y'"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="comparable_titles",
    )

    title = models.CharField(max_length=300, verbose_name="Buchtitel")
    author = models.CharField(max_length=200, verbose_name="Autor")
    publisher = models.CharField(max_length=200, blank=True, default="")
    publication_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Erscheinungsjahr",
        help_text="Für Validierung: Comps sollten < 5 Jahre alt sein.",
    )

    relation_type = models.CharField(
        max_length=20, choices=COMP_RELATION, default="similar_theme",
        verbose_name="Beziehungstyp",
    )
    similarity_note = models.TextField(
        blank=True, default="",
        verbose_name="Worin ähnlich",
        help_text="Was hat dieses Buch mit meinem Manuskript gemeinsam?",
    )
    difference_note = models.TextField(
        blank=True, default="",
        verbose_name="Worin anders",
        help_text="Was macht mein Buch einzigartig gegenüber diesem Comp?",
    )

    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_comparable_titles"
        ordering = ["project", "sort_order"]
        verbose_name = "Comparable Title"
        verbose_name_plural = "Comparable Titles"

    def __str__(self):
        year = f" ({self.publication_year})" if self.publication_year else ""
        return f"{self.author}: {self.title}{year}"

    @property
    def age_warning(self) -> bool:
        """True wenn Comp älter als 5 Jahre — verlegerisch zu alt."""
        if not self.publication_year:
            return False
        return (datetime.date.today().year - self.publication_year) > 5

    def to_comp_string(self) -> str:
        """
        Gibt Comp als formatierten String für Pitch-Dokumente zurück.
        Format: "Autor: Titel (Jahr) — [Beziehungstyp]"
        """
        year = f" ({self.publication_year})" if self.publication_year else ""
        rel = self.get_relation_type_display()
        result = f"{self.author}: {self.title}{year} [{rel}]"
        if self.difference_note:
            result += f" — {self.difference_note[:100]}"
        return result
```

---

### Teil B: `PitchDocument` Model

```python
class PitchDocument(models.Model):
    """
    Pitch-Dokument — Logline, Exposé, Synopsis oder Query Letter.

    Typen:
        logline    → 1 Satz nach Save-the-Cat-Formel (max. 35 Wörter)
        one_pager  → 1-Seite EN (für Agenten-Anfragen)
        expose_de  → Deutsches Verlagsexposé (3–5 Seiten)
        synopsis   → Vollständige Handlung mit Ende (1–3 Seiten)
        query      → Query Letter US/UK-Standard

    Versionierung: Jede Neu-Generierung inkrementiert version.
    `is_current=True` markiert die aktive Version pro Typ.
    """
    PITCH_TYPES = [
        ("logline",   "Logline — 1 Satz"),
        ("one_pager", "One-Pager — EN"),
        ("expose_de", "Exposé — DE Verlagsstandard"),
        ("synopsis",  "Synopsis — vollständige Handlung"),
        ("query",     "Query Letter — US/UK"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="pitch_documents",
    )
    pitch_type = models.CharField(
        max_length=20, choices=PITCH_TYPES, db_index=True,
    )
    content = models.TextField(verbose_name="Inhalt")
    word_count = models.PositiveIntegerField(default=0)

    is_ai_generated = models.BooleanField(default=False)
    ai_agent = models.CharField(max_length=100, blank=True, default="")
    is_current = models.BooleanField(
        default=True, db_index=True,
        help_text="Aktive Version dieses Typs (nur eine gleichzeitig).",
    )
    version = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_pitch_documents"
        ordering = ["project", "pitch_type", "-version"]
        verbose_name = "Pitch-Dokument"

    def __str__(self):
        return f"{self.get_pitch_type_display()} v{self.version} — {self.project.title}"

    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)
```

---

### Teil C: `PitchGeneratorService`

```python
# apps/projects/services/pitch_service.py

import json
from aifw.service import sync_completion
from projects.models import BookProject, PitchDocument, ComparableTitle


# ── Prompt-Templates ─────────────────────────────────────────────────────

LOGLINE_SYSTEM = """
Du schreibst professionelle Loglines für Verlagsanfragen.
Format (Save-the-Cat): "Ein [Figur mit Mangel/Eigenschaft] muss
[äußeres Ziel erreichen], bevor [Stakes/Konsequenz] — aber
[Antagonist/Hindernis] stellt sich entgegen."
Max. 35 Wörter. Keine Metakommentare. Kein Spoiler des Endes.
"""

EXPOSE_DE_SYSTEM = """
Du schreibst deutschsprachige Verlagsexposés im Branchenstandard.
Ton: professionell, präzise, kein Werbesprech.
Kein "In diesem fesselnden Roman..." — Fakten, keine Adjektive.
"""

EXPOSE_DE_USER = """
Schreibe ein deutsches Verlagsexposé für diesen Roman.

STRUKTUR (exakt):
1. KURZINHALT (3–4 Sätze, Handlung ohne Ausgang)
2. FIGUREN (Protagonist 2–3 Sätze, Antagonist 1–2 Sätze)
3. THEMA (1 Satz — nie moralisierend, als Frage formulierbar)
4. MARKT
   Zielgruppe: {target_audience}
   Vergleichstitel: {comps}
   Umfang: ca. {word_count} Wörter
5. ZUR AUTORIN / ZUM AUTOR
   [Platzhalter — hier Kurzbiografie einfügen]

ROMAN-BIBEL:
Titel: {title}
Genre: {genre}
Äußere Geschichte: {outer_story}
Innere Geschichte: {inner_story}
Thema: {theme}
Protagonist: {protagonist}
Antagonist: {antagonist}

Länge: max. 500 Wörter. Keine Wertungen.
"""

QUERY_SYSTEM = """
You write query letters for US/UK literary agents.
Standard format: Hook → Pitch → Comps → Bio → Closing.
Present tense for the pitch. Max 250 words. No adjective inflation.
"""

QUERY_USER = """
Write a query letter for this novel.

Title: {title}
Genre: {genre}
Word Count: {word_count}
Logline: {logline}
Comp 1: {comp1}
Comp 2: {comp2}

Bio placeholder: [Author bio here]

Hook: Start with the most compelling narrative moment or question.
Pitch: 2-3 sentences in present tense, include protagonist + stakes.
Comps: "For fans of [comp1] and [comp2]..."
"""


# ── Service-Funktionen ───────────────────────────────────────────────────

def generate_logline(project: BookProject) -> PitchDocument:
    protagonist = _get_character(project, "protagonist")
    antagonist = _get_character(project, "antagonist")
    theme = getattr(project, "theme", None)

    user_prompt = (
        f"Titel: {project.title}\n"
        f"Genre: {project.genre or ''}\n"
        f"Protagonist Want: {protagonist.want if protagonist else ''}\n"
        f"Protagonist Need: {protagonist.need if protagonist else ''}\n"
        f"Protagonist Flaw: {protagonist.flaw if protagonist else ''}\n"
        f"Antagonist Logik: {antagonist.antagonist_logic if antagonist else ''}\n"
        f"Innere Geschichte: {getattr(project, 'inner_story', '')}\n"
        f"Thema: {theme.core_question if theme else ''}\n"
    )

    result = sync_completion(
        action_code="logline_generate",
        messages=[
            {"role": "system", "content": LOGLINE_SYSTEM},
            {"role": "user",   "content": user_prompt},
        ],
    )
    if not result.success:
        raise RuntimeError(f"Logline-Generierung fehlgeschlagen: {result.error}")

    return _save_pitch(project, "logline", result.content.strip(), is_ai=True)


def generate_expose_de(project: BookProject) -> PitchDocument:
    comps = ComparableTitle.objects.filter(project=project).order_by("sort_order")[:3]
    comps_text = "; ".join(c.to_comp_string() for c in comps) or "—"

    protagonist = _get_character(project, "protagonist")
    antagonist  = _get_character(project, "antagonist")
    theme = getattr(project, "theme", None)

    logline_doc = PitchDocument.objects.filter(
        project=project, pitch_type="logline", is_current=True
    ).first()

    user_prompt = EXPOSE_DE_USER.format(
        title=project.title,
        genre=project.genre or (project.genre_lookup.name if project.genre_lookup else ""),
        target_audience=project.target_audience or "Erwachsene Leser",
        comps=comps_text,
        word_count=f"{project.target_word_count:,}" if project.target_word_count else "?",
        outer_story=getattr(project, "outer_story", ""),
        inner_story=getattr(project, "inner_story", ""),
        theme=theme.core_question if theme else "",
        protagonist=(
            f"{protagonist.want} / {protagonist.need}"
            if protagonist else "—"
        ),
        antagonist=(
            antagonist.antagonist_logic   # Rev.1-Fix C1: war fälschlich protagonist.antagonist_logic
            if antagonist else "—"
        ),
    )

    result = sync_completion(
        action_code="expose_generate",
        messages=[
            {"role": "system", "content": EXPOSE_DE_SYSTEM},
            {"role": "user",   "content": user_prompt},
        ],
    )
    if not result.success:
        raise RuntimeError(f"Exposé-Generierung fehlgeschlagen: {result.error}")

    return _save_pitch(project, "expose_de", result.content.strip(), is_ai=True)


def generate_query(project: BookProject) -> PitchDocument:
    comps = ComparableTitle.objects.filter(project=project).order_by("sort_order")[:2]
    logline_doc = PitchDocument.objects.filter(
        project=project, pitch_type="logline", is_current=True
    ).first()

    user_prompt = QUERY_USER.format(
        title=project.title,
        genre=project.genre or "",
        word_count=f"{project.target_word_count:,}" if project.target_word_count else "?",
        logline=logline_doc.content if logline_doc else "",
        comp1=comps[0].to_comp_string() if len(comps) > 0 else "—",
        comp2=comps[1].to_comp_string() if len(comps) > 1 else "—",
    )

    result = sync_completion(
        action_code="query_generate",
        messages=[
            {"role": "system", "content": QUERY_SYSTEM},
            {"role": "user",   "content": user_prompt},
        ],
    )
    if not result.success:
        raise RuntimeError(f"Query-Generierung fehlgeschlagen: {result.error}")

    return _save_pitch(project, "query", result.content.strip(), is_ai=True)


# ── Hilfsfunktionen ──────────────────────────────────────────────────────

def _get_character(project, role: str):
    try:
        return project.projectcharacterlink_set.filter(
            narrative_role=role
        ).first()
    except Exception:
        return None


def _save_pitch(
    project: BookProject,
    pitch_type: str,
    content: str,
    is_ai: bool = False,
) -> PitchDocument:
    """Deaktiviert Vorgänger-Version, speichert neue."""
    PitchDocument.objects.filter(
        project=project, pitch_type=pitch_type, is_current=True
    ).update(is_current=False)

    last = PitchDocument.objects.filter(
        project=project, pitch_type=pitch_type
    ).order_by("-version").first()

    return PitchDocument.objects.create(
        project=project,
        pitch_type=pitch_type,
        content=content,
        is_ai_generated=is_ai,
        ai_agent=f"{pitch_type}_generate",
        version=(last.version + 1) if last else 1,
        is_current=True,
    )
```

---

### Teil D: Health-Score Integration (ADR-157 Ergänzung)

```python
# In compute_dramaturgic_health() ergänzen (apps/projects/services/health_service.py):

# --- COMPS (Gewicht 1) ---
comp_count = project.comparable_titles.count()
checks.append(HealthCheck(
    label="Comparable Titles",
    passed=comp_count >= 2,
    message="Weniger als 2 Comps — für Verlagsanfrage unzureichend.",
    weight=1,
))
if comp_count > 0:
    comps = project.comparable_titles.all()
    checks.append(HealthCheck(
        label="Comps aktuell (< 5 Jahre)",
        passed=not any(c.age_warning for c in comps),
        message="Mindestens ein Comp ist älter als 5 Jahre — verlegerisch problematisch.",
        weight=1,
    ))
```

---

### Teil E: URLs

```python
# apps/projects/urls_html.py
path("<uuid:pk>/pitch/",
     views_publishing.pitch_dashboard, name="pitch_dashboard"),
path("<uuid:pk>/pitch/logline/generate/",
     views_publishing.generate_logline_view, name="logline_generate"),
path("<uuid:pk>/pitch/expose/generate/",
     views_publishing.generate_expose_view, name="expose_generate"),
path("<uuid:pk>/pitch/query/generate/",
     views_publishing.generate_query_view, name="query_generate"),
```

---

## Begründung

- **`ComparableTitle` als eigenes Model** (nicht JSON-Feld auf PublishingProfile):
  Comps brauchen individuelle Validierung (`age_warning`), Sortierung,
  und werden in mehreren Pitch-Typen referenziert. JSON-Feld wäre
  nicht querybar.

- **`PitchDocument` mit Versionierung**: Ein Exposé wird mehrfach
  überarbeitet. Die Versionshistorie ist wertvoller Feedback-Track
  — zu welchem Zeitpunkt hatte der Autor welche Formulierung?

- **Exposé VOR Synopsis** als Standard: Das deutsche Verlagsexposé
  (ohne Ende) ist häufiger gefragt als die amerikanische Synopsis
  (mit Ende). Separate Typen für beide.

- **`logline_generate` als Voraussetzung für `expose_generate`**:
  Der Service prüft ob eine aktuelle Logline existiert und injiziert
  sie ins Exposé. Logline-first ist verlegerisch richtig —
  wer seinen Roman nicht in 1 Satz erklären kann, kennt ihn
  selbst nicht vollständig.

---

## Abgelehnte Alternativen

**Pitch-Felder direkt auf PublishingProfile:** Zu viele verschiedene
Pitch-Typen, jeder mit eigener Versionsgeschichte. Ein Feld `expose_text`
wäre unkontrolliert überschreibbar.

**Comps als JSONField:** Nicht querybar. `age_warning` nicht
als Django-Property implementierbar. Health-Score-Integration
würde rohe JSON-Iteration erfordern.

---

## Konsequenzen

- Migration `projects/0015_comparable_titles_pitch` — zwei neue Tabellen (Reihenfolge gemäß KONSEQUENZANALYSE_ADR158)
- `PitchGeneratorService` in `apps/projects/services/pitch_service.py`
- AIActionTypes anlegen via Seed-Management-Command oder Admin:
  `logline_generate`, `expose_generate`, `query_generate`
  ```bash
  python manage.py seed_ai_action_types  # falls Management Command vorhanden
  # alternativ: Django Admin → AI-Action-Types manuell anlegen
  ```
- URL `projects/<pk>/pitch/` mit Tabs: Logline / Comps / Exposé / Query
- `pitch_dashboard`-View mit Context: alle aktuellen PitchDocuments + Comps
- Health-Score: Comp-Checks ergänzen (ADR-157 Revision)
- Sidebar: Publishing → "Pitch-Paket" als Unter-Navigation
- **Out of scope (v2):** Leserprobe-Kapitel als eigener Pitch-Typ, Rate-Limit auf Generierungs-Views

---

**Referenzen:** ADR-083 (PublishingProfile), ADR-150 (roman_kern),  
ADR-157 (DramaturgicHealthScore — Comp-Integration),  
`docs/adr/input/schritt_02_makrostruktur.md` (Logline-Kontext)
