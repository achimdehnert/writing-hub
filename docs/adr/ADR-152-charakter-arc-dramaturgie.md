# ADR-152: Charakter-Arc-Dramaturgie auf ProjectCharacterLink

**Status:** Accepted  
**Datum:** 2026-03-27 (rev. 2026-03-27)  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-151

---

## Kontext

Charaktere leben in WeltenHub (SSoT, ADR-082) — Biographie, Aussehen,
Verwandtschaften sind globale Stammdaten.

Dramaturgie ist jedoch **projekt-spezifisch**: Dieselbe Figur kann in
Projekt A Protagonistin mit positivem Arc sein, in Projekt B Antagonistin
mit negativem Arc. Diese Entscheidungen gehören nicht in WeltenHub.

`ProjectCharacterLink` verbindet lokales Projekt mit WeltenHub-Charakter.
Es fehlen die für LLM-Generierung kritischen Dramaturgie-Felder:

- **want/need** — äußeres Ziel vs. innere Wahrheit (zwei verschiedene Konzepte, s.u.)
- **flaw/ghost** — psychologischer Riss und sein Trauma-Ursprung
- **false_belief/true_belief** — der *epistemische* Entwicklungsbogen (s.u.)
- **voice_description** — figurenspezifische Dialogstimme (≠ NarrativeVoice)
- **CharacterKnowledgeState** (Prio 2) — wer weiß was zu welchem Zeitpunkt

### Begriffsabgrenzung: want/need vs. false_belief/true_belief

Diese vier Felder beschreiben zwei verschiedene Dimensionen der Figur:

| Dimension | Felder | Frage |
|-----------|--------|-------|
| **Motivational** | `want`, `need` | *Was will/braucht die Figur?* |
| **Epistemisch** | `false_belief`, `true_belief` | *Was glaubt die Figur über sich/die Welt?* |

- `want`: Das bewusste, konkrete Ziel ("Ich will den Mörder finden")
- `need`: Was die Figur wirklich braucht ("Sie braucht Vergebung für ihre eigene Schuld")
- `false_belief`: Die falsche *Überzeugung*, die den Arc antreibt ("Ich bin nicht schuldig")
- `true_belief`: Die erkannte Wahrheit am Ende ("Ich trage Mitverantwortung")

`need` ≠ `false_belief`: `need` ist eine Ressource (emotionale Reife, Beziehung, Vergebung).
`false_belief` ist eine kognitive Verzerrung über sich selbst oder die Welt.
Beide sind getrennte Felder, weil ein LLM sie für unterschiedliche Zwecke
nutzt: `need` für Plot-Entscheidungen, `false_belief` für Dialogsubtext und
inneren Monolog.

### Abgrenzung: voice_description vs. NarrativeVoice

`NarrativeVoice` (ADR-151) beschreibt die **Erzählstimme des Projekts** —
POV, Tempus, Distanz, Satzrhythmus. Sie gilt für das gesamte Buch.

`voice_description` auf `ProjectCharacterLink` beschreibt die **Dialogstimme
einer einzelnen Figur** — Wortwahl, Sprachduktus, Eigenheiten in wörtlicher Rede.

**Sonderfall Ich-Erzähler:** Wenn `NarrativeVoice.pov_type = "first"` und die
erzählende Figur == diese Figur, dann ist `voice_description` gleichzeitig
die Erzählstimme. LLM-Prompts müssen diesen Fall explizit behandeln:
```
{% if narrative_voice.pov_type.code == "first" and link.is_narrator %}
Diese Figur IST der Erzähler. voice_description und NarrativeVoice gelten
gleichzeitig — kein stilistischer Widerspruch erlaubt.
{% endif %}
```
Das Feld `is_narrator` (BooleanField) wird auf `ProjectCharacterLink` ergänzt.

### Cross-App FK: `worlds` → `core`

`CharacterArcTypeLookup` liegt in `apps/core` (ADR-151) — kein FK
`worlds → projects`. Die Abhängigkeit ist `worlds → core`, was zirkulärfrei ist.

---

## Entscheidung

### 1. Erweiterung von ProjectCharacterLink (in `apps/worlds/models.py`)

```python
from core.models_lookups_drama import CharacterArcTypeLookup

# --- DRAMATURGISCHE FIGUR-FELDER (ADR-152) ---

# Motivationale Dimension
want = models.TextField(
    blank=True, default="",
    verbose_name="Want (äußeres Ziel)",
    help_text="Was will die Figur bewusst erreichen? Konkretes, aktiv verfolgbares Ziel.",
)
need = models.TextField(
    blank=True, default="",
    verbose_name="Need (innere Ressource)",
    help_text="Was braucht die Figur wirklich? Emotionale Reife, Beziehung, Akzeptanz. "
              "MUSS sich von want unterscheiden — sonst kein Arc.",
)

# Psychologische Tiefe
flaw = models.TextField(
    blank=True, default="",
    verbose_name="Flaw (psychologischer Riss)",
    help_text="Der Charakterfehler — verhindert, dass die Figur ihr need erkennt.",
)
ghost = models.TextField(
    blank=True, default="",
    verbose_name="Ghost (Trauma-Ursprung)",
    help_text="Vergangenes Ereignis, das den flaw erzeugt hat.",
)

# Epistemische Dimension (Entwicklungsbogen der Überzeugungen)
false_belief = models.TextField(
    blank=True, default="",
    verbose_name="False Belief (Überzeugung Anfang)",
    help_text="Falsche kognitive Überzeugung über sich/die Welt zu Beginn. "
              "Erzeugt Dialogsubtext und inneren Monolog. Verschieden von want/need.",
)
true_belief = models.TextField(
    blank=True, default="",
    verbose_name="True Belief (Überzeugung Ende)",
    help_text="Erkannte oder verweigerte Wahrheit am Ende. "
              "Bei negativem Arc: die Wahrheit, die die Figur ablehnt.",
)

# Arc
arc_type = models.ForeignKey(
    CharacterArcTypeLookup,
    null=True, blank=True,
    on_delete=models.SET_NULL,
    verbose_name="Arc-Typ",
)

# Stimme (figurenspezifisch, ≠ NarrativeVoice des Projekts)
voice_description = models.TextField(
    blank=True, default="",
    verbose_name="Dialog-Stimme",
    help_text="Wortwahl, Satzrhythmus, Eigenheiten dieser Figur in wörtlicher Rede. "
              "Gilt auch als Erzählstimme wenn is_narrator=True.",
)
is_narrator = models.BooleanField(
    default=False,
    verbose_name="Ist Erzähler",
    help_text="Bei Ich-Perspektive: diese Figur ist der Erzähler. "
              "voice_description und NarrativeVoice müssen konsistent sein.",
)
```

### 2. CharacterKnowledgeState (Prio 2, `apps/projects/models_narrative.py`)

```python
class CharacterKnowledgeState(models.Model):
    """
    Was weiß eine Figur zu einem bestimmten Szenen-Zeitpunkt?

    Verhindert Info-Leaks: Das LLM prüft vor jedem Dialog, was die
    Figur an diesem Punkt wissen darf.

    Schema für knows / does_not_know (Liste von KnowledgeItem):
        [
          {
            "type": "event",          # event | secret | relationship | world_fact
            "ref_id": "<UUID>",       # OutlineNode.pk, character_id, oder freier Slug
            "label": "Mord an X",     # Menschenlesbarer Bezeichner (für LLM-Prompt)
            "since_chapter": "<UUID>" # OutlineNode.pk ab dem die Figur es weiß
          },
          ...
        ]
    """
    project      = models.ForeignKey("projects.BookProject", on_delete=models.CASCADE)
    character_id = models.UUIDField()
    chapter_ref  = models.ForeignKey("projects.OutlineNode", on_delete=models.CASCADE)
    knows         = models.JSONField(default=list)
    does_not_know = models.JSONField(default=list)

    class Meta:
        db_table        = "wh_character_knowledge_states"
        unique_together = [("project", "character_id", "chapter_ref")]
        verbose_name    = "Wissensstand Figur"
        verbose_name_plural = "Wissensstände Figuren"

    def __str__(self):
        return f"KnowledgeState char={self.character_id} @ {self.chapter_ref}"
```

**KnowledgeItem-Typen:**
- `event` — Plot-Ereignis (referenziert `OutlineNode.pk`)
- `secret` — Geheimnis einer anderen Figur (referenziert `character_id`)
- `relationship` — Beziehungsstatus zu einer anderen Figur
- `world_fact` — Welt-Faktum (freier Slug, z. B. `"magic_system_revealed"`)

### 3. Validierungsregel: want/need-Distinktion

Strategie: **Längen- + Substrings-Heuristik als erste Stufe,
LLM-Aufruf als optionale zweite Stufe** (nur wenn explizit getriggert):

```python
def validate_want_need_distinction(want: str, need: str) -> tuple[bool, str]:
    """
    Stufe 1 — Heuristik (synchron, ohne LLM-Kosten):
      - Leere Felder → Warnung "Felder nicht befüllt"
      - Identische Strings → Fehler "want == need"
      - Hohe Token-Überlappung (>70% gemeinsame Wörter) → Warnung

    Stufe 2 — LLM-Check (asynchron, nur on demand):
      - LLM bewertet ob want und need strukturell different sind
      - Wird im Kreativagenten-Flow als optionaler "Dramaturgie-Check" angeboten

    Returns:
        (is_valid: bool, message: str)
    """
    if not want.strip() or not need.strip():
        return False, "want oder need ist leer — Arc nicht definierbar."
    if want.strip() == need.strip():
        return False, "want == need — kein Arc möglich."
    want_words = set(want.lower().split())
    need_words = set(need.lower().split())
    if len(want_words) > 3 and len(need_words) > 3:
        overlap = len(want_words & need_words) / min(len(want_words), len(need_words))
        if overlap > 0.7:
            return False, f"want und need überlappen zu {overlap:.0%} — möglicherweise kein Arc."
    return True, ""
```

### 4. LLM-Prompt-Integration

```
[FIGUR: {{ character.name }}]
Rolle: {{ link.role }}
{% if link.is_narrator %}[IST ERZÄHLER — voice_description = Erzählstimme]{% endif %}

MOTIVATIONAL:
  Will (Want): {{ link.want }}
  Braucht (Need): {{ link.need }}

PSYCHOLOGISCH:
  Riss (Flaw): {{ link.flaw }}
  Trauma (Ghost): {{ link.ghost }}

EPISTEMISCH:
  Überzeugung Anfang: {{ link.false_belief }}
  Überzeugung Ende: {{ link.true_belief }}

Dialog-Stimme: {{ link.voice_description }}
Arc-Typ: {{ link.arc_type.label }}
```

---

## Begründung

- **want/need/false_belief/true_belief als vier separate Felder:** Die vier
  Konzepte beschreiben zwei orthogonale Dimensionen (motivational + epistemisch).
  Zusammenführen würde LLM-Prompts ambiguieren.
- **`is_narrator`-Flag** löst den Ich-Erzähler-Sonderfall explizit — das LLM
  kann den Konflikt erkennen und auflösen statt ihn zu ignorieren.
- **`CharacterArcTypeLookup` aus `apps/core`** vermeidet zirkuläre
  App-Abhängigkeit `worlds ↔ projects` (vgl. ADR-151).
- **`CharacterKnowledgeState` mit JSON-Schema:** Das Schema ist dokumentiert
  und typed genug für konsistente LLM-Nutzung, aber flexibel genug für
  manuelle Befüllung ohne eigene Migrations-Kosten.
- **validate_want_need: Heuristik-first:** Kein LLM-Aufruf bei jeder Speicherung
  — das wäre zu teuer. Die Heuristik fängt 90% der offensichtlichen Fälle.

---

## Abgelehnte Alternativen

**want/need und false_belief in zwei Felder zusammenführen:** Vermischt
motivationale und epistemische Dimension — LLM-Prompts werden inkonsistent.

**JSONField für alle Arc-Daten:** Keine Typsicherheit, kein Admin-Inline,
keine validate_want_need-Möglichkeit ohne Schema-Kenntnis.

**LLM-Validierung bei jedem Speichern:** Zu teuer (~0,01 € pro Speicherung),
zu langsam für Admin. Heuristik reicht für die häufigen Fehlfälle.

**`is_narrator` als eigenes Modell:** Overkill — ein BooleanField genügt,
da pro Projekt maximal eine Figur Ich-Erzähler sein sollte.

---

## Konsequenzen

- Migration `worlds/0003_character_arc_fields` (ca. 20 min)
- `CharacterArcTypeLookup` aus `apps/core` importieren (ADR-151)
- `is_narrator`-Feld ergänzt — Unique-Constraint "max. 1 Narrator pro Projekt"
  sollte via Clean-Methode gesichert werden
- Admin-Inline für `ProjectCharacterLink` mit Arc-Feldern + Dramaturgic-Check-Button
- LLM-Prompts unterscheiden explizit motivationale und epistemische Dimension
- `validate_want_need_distinction` in `apps/worlds/services/` als Utility

---

**Referenzen:** ADR-082, ADR-150, ADR-151,  
`docs/adr/input/p1b_character_arc_fields.md`,  
`docs/adr/input/schritt_03_substrat.md`,  
`docs/adr/input/gap_analyse_writing_hub.md` (Gap 3)
