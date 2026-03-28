# Prio-1 · Schritt B — `ProjectCharacterLink` Arc-Felder

> **Ziel:** `ProjectCharacterLink` bekommt die dramaturgischen Figur-Felder
> (want/need/flaw/ghost/arc) als lokale Felder — WeltenHub bleibt SSoT für
> Biographie/Aussehen, writing-hub besitzt die Dramaturgiedaten.
> Kompatibel mit `authoringfw.CharacterProfile`.

---

## B.1 — Neuer Lookup: `CharacterArcTypeLookup`

In `apps/projects/models_lookups_drama.py` ergänzen:

```python
class CharacterArcTypeLookup(models.Model):
    """
    Lookup: Charakter-Arc-Typen.
    Kompatibel mit outlinefw und dem Romanstruktur-Framework Schritt 3.

    Seed-Werte:
        positive | Positiver Arc   | Figur überwindet falschen Glauben
        negative | Negativer Arc   | Figur scheitert, verweigert Wahrheit (Tragödie)
        flat     | Flacher Arc     | Figur verändert die Welt statt sich selbst
    """
    code = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_character_arc_type_lookup"
        ordering = ["sort_order"]
        verbose_name = "Charakter-Arc-Typ"
        verbose_name_plural = "Charakter-Arc-Typen"

    def __str__(self):
        return f"{self.code} — {self.label}"
```

---

## B.2 — `ProjectCharacterLink` erweitern (in `apps/worlds/models.py`)

Füge die folgenden Felder in die bestehende `ProjectCharacterLink`-Klasse ein:

```python
# --- DRAMATURGISCHE FIGUR-FELDER (Romanstruktur-Framework Schritt 3) ---

# Das want/need-Paar — kritischste Unterscheidung
want = models.TextField(
    blank=True, default="",
    verbose_name="Want (äußeres Ziel)",
    help_text="Was will die Figur bewusst erreichen? Konkretes, aktiv verfolgbares Ziel.",
)
need = models.TextField(
    blank=True, default="",
    verbose_name="Need (innere Wahrheit)",
    help_text="Was braucht die Figur wirklich, ohne es zu wissen? "
              "Muss sich von want unterscheiden — sonst kein Arc.",
)

# Der psychologische Riss
flaw = models.TextField(
    blank=True, default="",
    verbose_name="Flaw (psychologischer Fehler)",
    help_text="Der Riss in der Figur, der sie an der Erfüllung des need hindert.",
)

# Traumatischer Ursprung
ghost = models.TextField(
    blank=True, default="",
    verbose_name="Ghost (Trauma-Ursprung)",
    help_text="Das Erlebnis aus der Vergangenheit, das den flaw erklärt. "
              "Ghost → Flaw ist eine kausale Kette.",
)

# Überzeugungsbogen
false_belief = models.TextField(
    blank=True, default="",
    verbose_name="Falsche Überzeugung (Anfang)",
    help_text="Was glaubt die Figur fälschlicherweise am Anfang? "
              "Wird durch den Arc in Frage gestellt.",
)
true_belief = models.TextField(
    blank=True, default="",
    verbose_name="Wahre Erkenntnis (Ende)",
    help_text="Was versteht die Figur am Ende? Muss durch Ereignisse gezeigt, "
              "nie ausgesprochen werden.",
)

# Arc-Typ (DB-getrieben)
arc_type = models.ForeignKey(
    "projects.CharacterArcTypeLookup",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="character_links",
    verbose_name="Arc-Typ",
)

# Figur-Stimme für Mikrostruktur
voice_description = models.TextField(
    blank=True, default="",
    verbose_name="Stimme / Sprechstil",
    help_text="Wie klingt diese Figur? Kurze Beschreibung für LLM-Prompts. "
              "Wird in authoringfw.CharacterProfile.arc injiziert.",
)

# authoringfw-Mapping
authoringfw_role = models.CharField(
    max_length=30, blank=True, default="",
    verbose_name="authoringfw Role",
    help_text="Mapping zu authoringfw.CharacterProfile.role "
              "(z.B. 'protagonist', 'antagonist', 'mentor')",
)
```

---

## B.3 — Migration: `apps/worlds/migrations/0004_character_arc_fields.py`

```python
"""
Migration 0004: Dramaturgische Arc-Felder für ProjectCharacterLink
                + CharacterArcTypeLookup.

Neue Tabelle:
    wh_character_arc_type_lookup

Neue Felder auf wh_project_character_links:
    want, need, flaw, ghost,
    false_belief, true_belief,
    arc_type_id, voice_description, authoringfw_role
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("worlds", "0003_location_scene_links"),   # ← letzte worlds-Migration
        ("projects", "0004_dramaturgic_fields"),    # CharacterArcTypeLookup liegt in projects
    ]

    operations = [
        # ── 1. CharacterArcTypeLookup (in projects-App, aber referenziert hier) ──
        # Lookup wurde in projects/migration 0004 angelegt — nur FK hier nötig.

        # ── 2. Felder auf ProjectCharacterLink ───────────────────────────────
        migrations.AddField(
            model_name="projectcharacterlink",
            name="want",
            field=models.TextField(blank=True, default="", verbose_name="Want (äußeres Ziel)"),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="need",
            field=models.TextField(blank=True, default="", verbose_name="Need (innere Wahrheit)"),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="flaw",
            field=models.TextField(blank=True, default="", verbose_name="Flaw (psychologischer Fehler)"),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="ghost",
            field=models.TextField(blank=True, default="", verbose_name="Ghost (Trauma-Ursprung)"),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="false_belief",
            field=models.TextField(blank=True, default="", verbose_name="Falsche Überzeugung (Anfang)"),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="true_belief",
            field=models.TextField(blank=True, default="", verbose_name="Wahre Erkenntnis (Ende)"),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="arc_type",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="character_links",
                to="projects.characterarctypelookup",
                verbose_name="Arc-Typ",
            ),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="voice_description",
            field=models.TextField(blank=True, default="", verbose_name="Stimme / Sprechstil"),
        ),
        migrations.AddField(
            model_name="projectcharacterlink",
            name="authoringfw_role",
            field=models.CharField(blank=True, default="", max_length=30, verbose_name="authoringfw Role"),
        ),
    ]
```

---

## B.4 — Seed: `CharacterArcTypeLookup` ergänzen in `seed_drama_lookups.py`

```python
# In seed_drama_lookups.py ergänzen:
from projects.models import CharacterArcTypeLookup

CHARACTER_ARC_TYPES = [
    dict(code="positive", label="Positiver Arc", sort_order=1,
         description="Figur überwindet falsche Überzeugung und wächst."),
    dict(code="negative", label="Negativer Arc (Tragödie)", sort_order=2,
         description="Figur verweigert die wahre Erkenntnis und scheitert."),
    dict(code="flat",     label="Flacher Arc", sort_order=3,
         description="Figur hat bereits die Wahrheit und verändert die Welt statt sich selbst."),
]

# In handle():
self._seed(CharacterArcTypeLookup, CHARACTER_ARC_TYPES, "CharacterArcTypeLookup")
```

---

## B.5 — Service: `apps/worlds/services/character_arc_service.py`

```python
"""
CharacterArcService — füllt want/need/flaw/ghost per LLM.

Nutzt:
    iil-aifw   → LLMRouter.completion (action: 'character_arc_generate')
    iil-promptfw → PromptStack.render_to_messages()
    iil-authoringfw → CharacterProfile als Zwischen-Schema
"""
import json

from aifw.service import sync_completion
from authoringfw import CharacterProfile

from worlds.models import ProjectCharacterLink


PROMPT_SYSTEM = """
Du bist ein erfahrener Dramaturg. Du entwickelst die dramaturgische Tiefe einer Figur.
Antworte ausschließlich als valides JSON ohne Markdown-Fencing.
"""

PROMPT_USER = """
Entwickle die dramaturgischen Kernfelder für diese Figur:

NAME: {name}
ROLLE: {role}
BESCHREIBUNG: {description}
ROMAN-GENRE: {genre}
ROMAN-THEMA: {theme}

Erstelle:
{{
  "want": "Äußeres, bewusstes Ziel — konkret, aktiv verfolgbar",
  "need": "Innere Wahrheit — MUSS sich von want unterscheiden",
  "flaw": "Psychologischer Riss — der Kern-Fehler",
  "ghost": "Trauma-Ursprung — erklärt den flaw kausal",
  "false_belief": "Was glaubt die Figur fälschlicherweise am Anfang?",
  "true_belief": "Was versteht sie am Ende? (nie ausgesprochen, nur gezeigt)",
  "voice_description": "Wie klingt sie? Satzlänge, Wortwahl, 2-3 Sätze",
  "authoringfw_role": "protagonist | antagonist | mentor | ally | trickster"
}}

KRITISCH: want ≠ need. Ghost erklärt Flaw kausal.
"""


def generate_character_arc(
    link: ProjectCharacterLink,
    character_name: str,
    character_description: str,
    genre: str = "",
    theme: str = "",
) -> ProjectCharacterLink:
    """
    Generiert dramaturgische Arc-Felder für einen ProjectCharacterLink via LLM.
    Gibt den (gespeicherten) Link zurück.
    """
    prompt = PROMPT_USER.format(
        name=character_name,
        role=link.authoringfw_role or "unbekannt",
        description=character_description,
        genre=genre,
        theme=theme,
    )

    result = sync_completion(
        action_code="character_arc_generate",
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    if not result.success:
        raise RuntimeError(f"LLM-Fehler: {result.error}")

    data = json.loads(result.content)

    # Validierung via authoringfw.CharacterProfile
    profile = CharacterProfile(
        name=character_name,
        role=data.get("authoringfw_role", ""),
        arc=f"{data.get('false_belief', '')} → {data.get('true_belief', '')}",
        description=data.get("voice_description", ""),
    )

    # In DB schreiben
    link.want = data.get("want", "")
    link.need = data.get("need", "")
    link.flaw = data.get("flaw", "")
    link.ghost = data.get("ghost", "")
    link.false_belief = data.get("false_belief", "")
    link.true_belief = data.get("true_belief", "")
    link.voice_description = data.get("voice_description", "")
    link.authoringfw_role = profile.role or data.get("authoringfw_role", "")
    link.save(update_fields=[
        "want", "need", "flaw", "ghost",
        "false_belief", "true_belief",
        "voice_description", "authoringfw_role",
    ])

    return link
```

---

## B.6 — Admin-Ergänzung: `apps/worlds/admin.py`

```python
from django.contrib import admin
from .models import ProjectCharacterLink

# Bestehenden Admin erweitern (falls vorhanden):
class ProjectCharacterLinkAdmin(admin.ModelAdmin):
    list_display = [
        "project", "weltenhub_character_id", "arc_type",
        "authoringfw_role", "want_short"
    ]
    readonly_fields = ["weltenhub_character_id"]
    fieldsets = [
        ("Referenz", {"fields": ["project", "weltenhub_character_id", "role"]}),
        ("Dramaturgie", {"fields": [
            "arc_type", "authoringfw_role",
            "want", "need", "flaw", "ghost",
            "false_belief", "true_belief",
            "voice_description",
        ]}),
        ("Meta", {"fields": ["notes"]}),
    ]

    @admin.display(description="Want")
    def want_short(self, obj):
        return obj.want[:60] + "..." if len(obj.want) > 60 else obj.want

admin.site.register(ProjectCharacterLink, ProjectCharacterLinkAdmin)
```

---

## B.7 — Deployment-Reihenfolge

```bash
# Voraussetzung: Schritt A bereits deployed

# 1. Migration
python manage.py migrate worlds 0004_character_arc_fields

# 2. Seed (ergänzt CharacterArcTypeLookup)
python manage.py seed_drama_lookups

# 3. AIActionType in Admin anlegen:
#    code: character_arc_generate
#    model: z.B. claude-sonnet-4-5 (oder gemäß DB-Konfiguration)

# 4. Verify
python manage.py shell -c "
from projects.models import CharacterArcTypeLookup
from worlds.models import ProjectCharacterLink
print('ArcTypes:', CharacterArcTypeLookup.objects.count())
link = ProjectCharacterLink.objects.first()
print('Link has want field:', hasattr(link, 'want'))
"
```

---

*writing-hub · Prio-1 Schritt B von 4 · ProjectCharacterLink Arc-Felder*
*Packages: iil-aifw 0.9.0 · iil-authoringfw 0.8.0*
