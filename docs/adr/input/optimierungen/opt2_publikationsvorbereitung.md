# OPT2 — Publikationsvorbereitung: Comps, Query Letter, Pitch

> `PublishingProfile` hat ISBN, BISAC, Keywords, Cover — aber was ein
> Verlag wirklich als erstes sieht, fehlt vollständig:
> **Comparable Titles** (Comps) und ein **Query Letter / Exposé**.
>
> Als Verleger: Kein Autor schickt ein nacktes Manuskript. Er schickt
> ein Exposé mit Comps und einem One-Page-Summary. Das ist der erste
> Filter — nicht der Text selbst.

---

## OPT2.1 — Was fehlt in `PublishingProfile`

```
VORHANDEN:
    ISBN, BISAC, keywords, cover_image_url
    dedication, foreword, preface, afterword
    publisher_name, status

FEHLT — für Verlagsanfrage zwingend:
    Comparable Titles (Comps)     → "Wie X, aber Y"
    One-Line-Pitch / Logline      → 1 Satz, der alles sagt
    One-Page-Exposé               → Standard-Verlagsformat DE
    Query Letter                  → Standard-Verlagsformat EN/US
    Target-Verlage-Liste          → Welche Verlage passen?
    Leserprobe-Kapitel            → Erstes Kapitel formatiert
```

---

## OPT2.2 — Model: `ComparableTitle`

```python
# apps/projects/models_publishing.py
"""
Publikations-Erweiterung: Comps, Pitch, QueryLetter.

Verlegerisch ist die Comp-Analyse der wichtigste Indikator dafür,
ob ein Autor seinen Markt versteht. Falsche Comps (zu groß: "wie Harry Potter",
zu alt: Buchtitel von 1990) sind sofortige Ablehnungsgründe.
"""
import uuid
from django.db import models


class ComparableTitle(models.Model):
    """
    Comparable Title (Comp) — vergleichbares veröffentlichtes Werk.

    Verlegerische Regel für gute Comps:
        - Nicht älter als 5 Jahre (Markt-Relevanz)
        - Nicht zu groß (kein Bestseller der 80er als Comp)
        - Gleiche Zielgruppe + ähnliches Genre
        - Begründung: Worin ähnelt, worin unterscheidet das Werk?
    """
    COMP_RELATION = [
        ("similar_theme",    "Ähnliches Thema"),
        ("similar_tone",     "Ähnlicher Ton"),
        ("similar_structure","Ähnliche Struktur"),
        ("same_audience",    "Gleiche Zielgruppe"),
        ("same_subgenre",    "Gleiches Subgenre"),
        ("contrast",         "Kontrast — 'wie X, aber Y'"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="comparable_titles",
    )

    # Buch-Info
    title = models.CharField(max_length=300, verbose_name="Titel")
    author = models.CharField(max_length=200, verbose_name="Autor")
    publisher = models.CharField(max_length=200, blank=True, default="")
    publication_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Erscheinungsjahr",
    )

    # Beziehungs-Analyse
    relation_type = models.CharField(
        max_length=20,
        choices=COMP_RELATION,
        default="similar_theme",
    )
    similarity_note = models.TextField(
        blank=True, default="",
        verbose_name="Worin ähnlich",
        help_text="Was hat dieses Buch mit meinem gemeinsam?",
    )
    difference_note = models.TextField(
        blank=True, default="",
        verbose_name="Worin unterschiedlich",
        help_text="Was macht mein Buch anders/besser? "
                  "Der 'aber'-Teil ist oft wichtiger als der 'wie'-Teil.",
    )

    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wh_comparable_titles"
        ordering = ["project", "sort_order"]
        verbose_name = "Comparable Title"

    def __str__(self):
        return f"{self.author}: {self.title} ({self.publication_year})"

    @property
    def age_warning(self) -> bool:
        """Warnung wenn Comp älter als 5 Jahre."""
        if not self.publication_year:
            return False
        import datetime
        return (datetime.date.today().year - self.publication_year) > 5


class PitchDocument(models.Model):
    """
    Pitch-Dokument — Exposé / Query Letter / One-Pager.

    Typen:
        logline     → 1 Satz: "Ein [Figur] muss [Ziel] erreichen, bevor [Stakes]."
        one_pager   → 1-Seite Zusammenfassung für Agenten (EN)
        expose_de   → Deutsches Verlagsexposé (3–5 Seiten: Inhalt + Figuren + Markt)
        synopsis    → Vollständige Handlungszusammenfassung (mit Ende)
        query       → Query Letter (US/UK Standard)
    """
    PITCH_TYPES = [
        ("logline",   "Logline — 1 Satz"),
        ("one_pager", "One-Pager — 1 Seite EN"),
        ("expose_de", "Exposé — Verlagsstandard DE"),
        ("synopsis",  "Synopsis — vollständige Handlung"),
        ("query",     "Query Letter — US/UK"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="pitch_documents",
    )
    pitch_type = models.CharField(max_length=20, choices=PITCH_TYPES)
    content = models.TextField(verbose_name="Inhalt")
    is_ai_generated = models.BooleanField(default=False)
    ai_agent = models.CharField(max_length=100, blank=True)
    version = models.PositiveSmallIntegerField(default=1)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_pitch_documents"
        ordering = ["project", "pitch_type", "-version"]
        verbose_name = "Pitch-Dokument"

    def __str__(self):
        return f"{self.get_pitch_type_display()} v{self.version} — {self.project.title}"
```

---

## OPT2.3 — Service: `PitchGeneratorService`

```python
# apps/projects/services/pitch_service.py
"""
PitchGeneratorService — generiert Pitch-Dokumente via LLM.

action_codes:
    logline_generate   → 1 Satz nach Save-the-Cat-Formel
    expose_generate    → Deutsches Verlagsexposé
    query_generate     → Query Letter US-Standard
"""
import json
from aifw.service import sync_completion
from projects.models import BookProject, PitchDocument, ComparableTitle


LOGLINE_PROMPT = """
Du schreibst eine professionelle Logline nach der Save-the-Cat-Formel:
"Ein [Figur mit Mangel] muss [äußeres Ziel erreichen], bevor [Stakes] —
aber [Hindernis/Antagonist] stellt sich entgegen."

PROJEKT:
Titel: {title}
Genre: {genre}
Protagonist: {protagonist_want} / {protagonist_need}
Antagonist: {antagonist_logic}
Stakes: {stakes}

Schreibe 1 Satz (max 35 Wörter). Keine Metakommentare.
"""

EXPOSE_DE_PROMPT = """
Du schreibst ein deutsches Verlagsexposé. Format:

1. KURZINHALT (3–4 Sätze, Handlung ohne Ende)
2. FIGUREN (Protagonist + Antagonist, je 2–3 Sätze)
3. THEMA (1 Satz — nie moralisierend)
4. MARKTPOSITIONIERUNG
   - Zielgruppe: {target_audience}
   - Vergleichstitel: {comps_text}
   - Wortanzahl: {word_count}
5. ZUR AUTORIN / ZUM AUTOR (Platzhalter)

ROMAN-BIBEL:
{roman_bible_context}

Ton: professionell, präzise. Kein Werbesprech.
Länge: max 500 Wörter.
"""

QUERY_PROMPT = """
You are writing a query letter for a literary agent (US standard).

FORMAT:
Hook (1 sentence) → Pitch (2-3 sentences) → Comps (2 titles) →
Brief bio → Closing

NOVEL:
Title: {title}
Genre: {genre}
Word Count: {word_count}
Logline: {logline}
Comps: {comps_text}

Write in first person, present tense for the pitch. Max 250 words.
"""


def generate_logline(project: BookProject) -> PitchDocument:
    protagonist = project.projectcharacterlink_set.filter(
        narrative_role="protagonist"
    ).first()
    antagonist = project.projectcharacterlink_set.filter(
        narrative_role="antagonist"
    ).first()

    result = sync_completion(
        action_code="logline_generate",
        messages=[{"role": "user", "content": LOGLINE_PROMPT.format(
            title=project.title,
            genre=project.genre or "",
            protagonist_want=protagonist.want if protagonist else "",
            protagonist_need=protagonist.need if protagonist else "",
            antagonist_logic=antagonist.antagonist_logic if antagonist else "",
            stakes=getattr(project, "inner_story", ""),
        )}],
    )

    if not result.success:
        raise RuntimeError(result.error)

    return _save_pitch(project, "logline", result.content, is_ai=True)


def generate_expose_de(project: BookProject) -> PitchDocument:
    comps = ComparableTitle.objects.filter(project=project).order_by("sort_order")
    comps_text = "; ".join(
        f"{c.author}: {c.title} ({c.publication_year})" for c in comps[:3]
    ) or "Noch keine Comparable Titles definiert"

    # Roman-Bibel-Kontext zusammenstellen
    theme = getattr(project, "theme", None)
    voice = getattr(project, "narrative_voice", None)
    roman_bible = "\n".join(filter(None, [
        f"Äußere Geschichte: {getattr(project, 'outer_story', '')}",
        f"Innere Geschichte: {getattr(project, 'inner_story', '')}",
        f"Thema: {theme.core_question if theme else ''}",
        f"Ton: {voice.tone if voice else ''}",
    ]))

    result = sync_completion(
        action_code="expose_generate",
        messages=[{"role": "user", "content": EXPOSE_DE_PROMPT.format(
            target_audience=project.target_audience or "",
            comps_text=comps_text,
            word_count=f"{project.target_word_count:,}" if project.target_word_count else "?",
            roman_bible_context=roman_bible,
        )}],
    )

    if not result.success:
        raise RuntimeError(result.error)

    return _save_pitch(project, "expose_de", result.content, is_ai=True)


def _save_pitch(project, pitch_type, content, is_ai=False) -> PitchDocument:
    # Vorige Version deaktivieren
    PitchDocument.objects.filter(
        project=project, pitch_type=pitch_type, is_current=True
    ).update(is_current=False)

    last = PitchDocument.objects.filter(
        project=project, pitch_type=pitch_type
    ).order_by("-version").first()
    version = (last.version + 1) if last else 1

    return PitchDocument.objects.create(
        project=project,
        pitch_type=pitch_type,
        content=content,
        is_ai_generated=is_ai,
        ai_agent=pitch_type + "_generate",
        version=version,
        is_current=True,
    )
```

---

## OPT2.4 — Comp-Validierung im Health-Score (Ergänzung zu ADR-157)

```python
# In compute_dramaturgic_health() ergänzen:

comps = project.comparable_titles.all()
checks.append(HealthCheck(
    label="Comparable Titles",
    passed=comps.count() >= 2,
    message="Weniger als 2 Comps — für Verlagsanfrage nicht ausreichend.",
    weight=1,
))
if comps.exists():
    checks.append(HealthCheck(
        label="Comps nicht zu alt",
        passed=not any(c.age_warning for c in comps),
        message="Mindestens ein Comp ist älter als 5 Jahre.",
        weight=1,
    ))
```

---

## OPT2.5 — Migration + URL

```python
# 0011_comparable_titles_pitch.py
# Neue Tabellen: wh_comparable_titles, wh_pitch_documents

# URLs:
path("<uuid:pk>/pitch/", views_publishing.pitch_dashboard, name="pitch_dashboard"),
path("<uuid:pk>/pitch/logline/generate/", views_publishing.generate_logline, name="logline_generate"),
path("<uuid:pk>/pitch/expose/generate/", views_publishing.generate_expose, name="expose_generate"),
```

```bash
# AIActionTypes anlegen:
#   logline_generate
#   expose_generate
#   query_generate
```

---

*writing-hub · OPT2 · Publikationsvorbereitung: Comps, Pitch, Exposé*
*Neue Tabellen: wh_comparable_titles, wh_pitch_documents*
*Verlegerisches Kernprinzip: Kein Manuskript ohne Exposé*
