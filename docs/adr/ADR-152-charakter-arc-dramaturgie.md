# ADR-152: Charakter-Arc-Dramaturgie auf ProjectCharacterLink

**Status:** Accepted  
**Datum:** 2026-03-27  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150

---

## Kontext

Charaktere leben in WeltenHub (SSoT, ADR-082) — Biographie, Aussehen,
Verwandtschaften sind globale Stammdaten.

Dramaturgie ist jedoch **projekt-spezifisch**: Dieselbe Figur kann in
Projekt A Protagonistin mit positivem Arc sein, in Projekt B Antagonistin
mit negativem Arc. Diese Entscheidungen gehören nicht in WeltenHub.

`ProjectCharacterLink` verbindet lokales Projekt mit WeltenHub-Charakter.
Es fehlen die für LLM-Generierung kritischen Dramaturgie-Felder:

- **want/need** — das wichtigste Paar: äußeres Ziel vs. innere Wahrheit.
  Wenn `want == need`, gibt es keinen Arc — das LLM muss das prüfen können.
- **flaw/ghost** — psychologischer Riss und sein Trauma-Ursprung
- **false_belief/true_belief** — Entwicklungsbogen von Anfang zu Ende
- **voice_description** — wie klingt diese Figur in Dialogen?
- **CharacterKnowledgeState** (Prio 2) — wer weiß was zu welchem Zeitpunkt

---

## Entscheidung

### 1. Erweiterung von ProjectCharacterLink (in `apps/worlds/models.py`)

```python
# --- DRAMATURGISCHE FIGUR-FELDER (ADR-152) ---

# Want/Need — kritischstes Paar im Romanstruktur-Framework Schritt 3
want = models.TextField(
    blank=True, default="",
    verbose_name="Want (äußeres Ziel)",
    help_text="Was will die Figur bewusst erreichen? Konkretes, aktiv verfolgbares Ziel.",
)
need = models.TextField(
    blank=True, default="",
    verbose_name="Need (innere Wahrheit)",
    help_text="Was braucht die Figur wirklich, ohne es zu wissen? "
              "MUSS sich von want unterscheiden — sonst kein Arc.",
)

# Psychologische Tiefe
flaw = models.TextField(
    blank=True, default="",
    verbose_name="Flaw (Fehler)",
    help_text="Psychologischer Riss — verhindert, dass die Figur ihr need erkennt.",
)
ghost = models.TextField(
    blank=True, default="",
    verbose_name="Ghost (Trauma)",
    help_text="Vergangenes Ereignis, das den flaw erzeugt hat.",
)

# Entwicklungsbogen
false_belief = models.TextField(
    blank=True, default="",
    verbose_name="False Belief (Anfang)",
    help_text="Falsche Überzeugung zu Beginn des Romans.",
)
true_belief = models.TextField(
    blank=True, default="",
    verbose_name="True Belief (Ende)",
    help_text="Erkannte Wahrheit am Ende (oder verweigerte Wahrheit bei negativem Arc).",
)

# Arc-Typ (DB-Lookup aus ADR-151)
arc_type = models.ForeignKey(
    "projects.CharacterArcTypeLookup",
    null=True, blank=True,
    on_delete=models.SET_NULL,
    verbose_name="Arc-Typ",
)

# Stimme
voice_description = models.TextField(
    blank=True, default="",
    verbose_name="Stimme / Sprachprofil",
    help_text="Wie klingt diese Figur? Wortwahl, Rhythmus, Eigenheiten im Dialog.",
)
```

### 2. CharacterKnowledgeState (Prio 2, neue Datei: `apps/projects/models_narrative.py`)

```python
class CharacterKnowledgeState(models.Model):
    """
    Was weiß eine Figur zu einem bestimmten Kapitel-Zeitpunkt?

    Kritisch für Dialog-Generierung: Das LLM prüft vor jedem Dialog,
    was die Figur in dieser Szene wissen darf.
    Verhindert den häufigsten LLM-Fehler: Figuren, die Dinge "wissen",
    die sie noch nicht wissen dürfen (Info-Leak).
    """
    project      = models.ForeignKey("projects.BookProject", on_delete=models.CASCADE)
    character_id = models.UUIDField()    # WeltenHub-Referenz
    chapter_ref  = models.ForeignKey("projects.OutlineNode", on_delete=models.CASCADE)
    knows         = models.JSONField(default=list)
    does_not_know = models.JSONField(default=list)

    class Meta:
        db_table       = "wh_character_knowledge_states"
        unique_together = [("project", "character_id", "chapter_ref")]
        verbose_name = "Wissensstand Figur"
        verbose_name_plural = "Wissensstände Figuren"
```

### 3. LLM-Prompt-Integration

Die neuen Felder werden in `iil-promptfw`-Templates als Kontext-Block eingefügt:

```
[FIGUR: {{ character.name }}]
Rolle: {{ link.role }}
Will (Want): {{ link.want }}
Braucht (Need): {{ link.need }}
Psychologischer Riss: {{ link.flaw }}
Trauma-Ursprung: {{ link.ghost }}
Aktuelle Überzeugung: {{ link.false_belief }}
Stimme: {{ link.voice_description }}
Arc-Typ: {{ link.arc_type.label }}
```

### 4. Validierungsregel

Ein LLM-Service soll `want` und `need` vergleichen und warnen, wenn sie
semantisch identisch sind (kein Arc möglich):

```python
def validate_want_need_distinction(want: str, need: str) -> bool:
    """
    Gibt False zurück, wenn want und need zu ähnlich sind.
    Wird im Admin und im Kreativagenten-Flow angezeigt.
    """
```

---

## Begründung

- **want/need-Trennung** ist nach Robert McKee / John Truby das wichtigste
  dramaturgische Prinzip. Ohne es generiert das LLM Figuren ohne Arc —
  Figuren, die ihr Ziel wollen und brauchen, entwickeln sich nicht.
- **Lokale Speicherung auf ProjectCharacterLink** ist korrekt: WeltenHub
  speichert universale Figuren-Daten, writing-hub die projekt-spezifische
  Dramaturgie. Keine Duplizierung, klare Verantwortlichkeit (ADR-082).
- **CharacterKnowledgeState** ist der technische Schutz gegen den häufigsten
  LLM-Fehler: Figuren, die Dinge „wissen", die sie noch nicht wissen dürfen.
  Ohne dieses Modell kann kein Dialog-Generator konsistente Szenen erzeugen.
- **arc_type als FK auf Lookup** statt CharField: Admin-verwaltbar,
  kompatibel mit `iil-outlinefw` CharacterArc-Typen.

---

## Abgelehnte Alternativen

**Dramaturgie-Felder direkt in WeltenHub:** Verstößt gegen SSoT-Prinzip —
WeltenHub ist universaler Daten-Store, nicht Roman-Projekt-spezifisch.

**JSONField für alle Arc-Daten:** Keine Typsicherheit, kein
iil-authoringfw.CharacterProfile-Mapping, keine Admin-Verwaltung,
keine sinnvolle Validierung der want/need-Trennung.

**Alles in WritingStyle:** WritingStyle ist Autoren-bezogen, nicht
projekt-/charakter-bezogen. Falsche Granularität.

---

## Konsequenzen

- Migration `worlds/0003_character_arc_fields` (ca. 20 min)
- `CharacterArcTypeLookup` liegt in `apps/projects/models_lookups_drama.py` (ADR-151)
- Admin-Inline für `ProjectCharacterLink` mit Arc-Feldern erweitern
- LLM-Prompts für Charakter-/Dialog-Generierung erhalten want/need/flaw/ghost-Kontext
- `authoringfw.CharacterProfile` wird via Mapping befüllt
- Validierungswarnung im Kreativagenten-Flow wenn `want ≈ need`

---

**Referenzen:** ADR-082, ADR-150, ADR-151,  
`docs/adr/input/p1b_character_arc_fields.md`,  
`docs/adr/input/schritt_03_substrat.md`,  
`docs/adr/input/gap_analyse_writing_hub.md` (Gap 3)
