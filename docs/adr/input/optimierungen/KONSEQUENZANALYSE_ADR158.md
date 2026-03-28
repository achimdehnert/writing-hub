# Konsequenzanalyse: ADR-158 (neu, Accepted) vs. bestehende Spezifikationen

**Datum:** 2026-03-28  
**Anlass:** Neues ADR-158 (Dialogue Subtext / Opening Image / GenrePromise / QualityDimensions)
ist als **Accepted** eingeliefert worden. Es kollidiert mit drei bereits spezifizierten
Dokumenten und erfordert Renummerierung, App-Konsolidierung und Migrationsneuplanung.

---

## 1. Das Kernproblem: Nummerierungskonflikt

```
KONFLIKT:
    ADR-158 (uploaded, Accepted) → Dialogue Subtext, Image Mirror, GenrePromise, QualityDimension
    ADR-158 (mein Entwurf)       → TextAnalysis, Budget, Pacing, BatchWriteJob

AUFLÖSUNG:
    Uploaded ADR-158 (Accepted) → bleibt ADR-158 ✅
    Mein Entwurf                → wird ADR-161 🔁
```

**Sofortmaßnahme:** `ADR-158-produktions-infrastruktur.md` → umbenennen in
`ADR-161-produktions-infrastruktur.md`.

---

## 2. Direkte Konflikte — müssen aufgelöst werden

---

### Konflikt K1 — `TurningPointTypeLookup` in zwei verschiedenen Apps

**Status: BLOCKING — vor Deployment klären**

```
MEINE SPEC (O1 / Prio-1):
    App:    apps/projects/models_tension.py
    Tabelle: wh_turning_point_type_lookup
    Felder: code, label, description, default_position (Decimal 0.0–1.0),
            outlinefw_beat_name, sort_order

NEUES ADR-158:
    App:    apps/core/models_lookups_drama.py (neue Core-App)
    Tabelle: wh_turning_point_type_lookup  ← GLEICHER TABELLENNAME
    Felder: code, label, description, default_position (SmallInt 0–100),
            mirrors_type_code (Slug), sort_order
```

**Drei Probleme:**

1. **Gleicher `db_table`-Name, zwei verschiedene Django-Apps** → Migration-Crash
2. **`default_position` Typen-Konflikt:** Decimal(0.0–1.0) vs. SmallInteger(0–100)
3. **`mirrors_type_code` fehlt in meiner Spec** → Wichtiges Feature (Opening/Closing-Spiegel)

**Auflösung:**

```python
# ENTSCHEIDUNG: Core-App gewinnt (ADR-158 ist Accepted)
# App:    apps/core/models_lookups_drama.py
# Tabelle: wh_turning_point_type_lookup

# Felder-Vereinigung:
class TurningPointTypeLookup(models.Model):
    code               = models.SlugField(max_length=30, unique=True)
    label              = models.CharField(max_length=100)
    description        = models.TextField(blank=True, default="")

    # ADR-158 nutzt SmallInt (0–100) — konsistenter mit position_percent
    # Meine Spec nutzte Decimal (0.0–1.0) — outlinefw-kompatibel
    # KOMPROMISS: beide Felder, gegenseitig ableitbar
    default_position_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text="Typische Position (0–100%)",
    )
    default_position_normalized = models.DecimalField(
        max_digits=4, decimal_places=3,
        null=True, blank=True,
        help_text="Normiert (0.0–1.0) — für outlinefw-Kompatibilität",
    )

    # ADR-158: Opening/Closing-Spiegel
    mirrors_type_code  = models.SlugField(max_length=30, blank=True, default="")

    # Meine Spec: outlinefw-Mapping
    outlinefw_beat_name = models.CharField(max_length=80, blank=True, default="")

    sort_order         = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "wh_turning_point_type_lookup"
        # app_label explizit setzen:
        # app_label = "core"  ← WICHTIG für Migration-Ownership
```

**Migration-Ownership:** Core-App besitzt die Tabelle.
`apps/projects` referenziert sie als FK ohne eigene Migration.

---

### Konflikt K2 — `GenrePromise` vs. `GenreConventionProfile`: Überschneidung

**Status: KONZEPTUELL — Abgrenzung nötig, kein Migration-Crash**

```
MEIN ADR-160:
    GenreConventionProfile    → Was sind die Regeln dieses Genres?
    (1:1 zu GenreLookup, JSON-Konventionen, regelbasierter Check)

NEUES ADR-158:
    GenrePromiseLookup        → Was verspricht das Genre dem Leser?
    ProjectGenrePromise       → Wie löst DIESES Projekt das Versprechen ein?
```

**Sind das zwei Dinge oder dasselbe?**

Sie sind **verwandt aber verschieden:**

```
GenreConventionProfile (ADR-160):
    → STRUKTURELL: "Hat der Thriller eine Bedrohung bis 10%?"
    → Maschinenprüfbar, checkType-System
    → Binäre Checks (passed/failed)
    → Zuständig: DramaturgicHealthScore

GenrePromiseLookup + ProjectGenrePromise (ADR-158):
    → SEMANTISCH: "Was muss der Leser am Ende fühlen?"
    → LLM-Erinnerung während Generierung
    → Qualitatives Commitment, nicht binär prüfbar
    → Zuständig: LLM-Prompt-Layer (Layer 10)
```

**Auflösung:** Beide Modelle bleiben — sie sind komplementär.
In ADR-160 einen klarstellenden Satz ergänzen:

> *"GenreConventionProfile prüft strukturelle Regeln (Wendepunkt-Positionen,
> Arc-Richtung). GenrePromiseLookup (ADR-158) ist das semantische Gegenstück
> — das emotionale Versprechen, das im LLM-Prompt-Layer verankert wird."*

**Aber:** `GenreConventionProfile.reader_promise` (TextField) in ADR-160
überlappt mit `GenrePromiseLookup.core_promise`. Einer der beiden muss
weichen. **Empfehlung:** `reader_promise` aus `GenreConventionProfile` entfernen
— dieser Inhalt gehört in `GenrePromiseLookup`.

---

### Konflikt K3 — Migrations-Nummernkollision

**Status: BLOCKING — Deployment würde fehlschlagen**

```
MEINE ADR-160 Spec nutzt:
    projects/0012_research_genre_beta

NEUES ADR-158 nutzt:
    projects/0012_dialogue_scene
    projects/0013_turning_point_type_fk
    projects/0014_genre_promise
```

Beide beanspruchen `0012` für unterschiedliche Inhalte.

**Auflösung — neue Migrations-Reihenfolge:**

```
projects/
    0004  dramaturgic_fields           (Prio-1 A)
    0005  narrative_voice              (Prio-1 C)
    0006  theme_motif                  (Prio-1 D)
    0007  tension_architecture         (O1)
    0008  essay_structure              (O3)
    0009  master_timeline              (O4)
    0010  content_type_profile         (O5)
    0011  subplot_arc                  (ADR-157)
    0012  dialogue_scene               (ADR-158 ✅ — neu, Accepted)
    0013  turning_point_type_fk        (ADR-158 ✅)
    0014  genre_promise                (ADR-158 ✅)
    0015  comparable_titles_pitch      (ADR-159)
    0016  research_genre_beta          (ADR-160)
    0017  text_analysis_batch          (ADR-161 — ex ADR-158 mein Entwurf)

worlds/
    0004  character_arc_fields         (Prio-1 B)

series/
    0003  series_arc                   (O2)

core/ (neue App)
    0001  initial                      (Core-App Basis)
    0002  turning_point_type_lookup    (ADR-158 ✅)
    0003  genre_promise_lookup         (ADR-158 ✅)
```

---

### Konflikt K4 — `ProjectTurningPoint.turning_point_type` FK-Target-App-Wechsel

Meine Spec hatte `turning_point_type = FK("projects.TurningPointTypeLookup")`.
ADR-158 setzt es auf `FK("core.TurningPointTypeLookup")`.

**Das ist kein Fehler — aber es bedeutet:**
- Migration `projects/0013_turning_point_type_fk` muss den FK auf `core.TurningPointTypeLookup` zeigen
- Alle bestehenden `ProjectTurningPoint`-Instanzen brauchen kein Update (FK-Feld war NULL)
- Der TurningPointSyncService (aus meiner O1-Spec) muss importpfade anpassen:

```python
# ALT (meine Spec):
from projects.models import TurningPointTypeLookup

# NEU (nach ADR-158):
from core.models_lookups_drama import TurningPointTypeLookup
```

---

## 3. Neue Abhängigkeiten durch ADR-158

### 3.1 Core-App als neue Abhängigkeit

ADR-158 platziert `TurningPointTypeLookup` und `GenrePromiseLookup` in `apps/core`.
**Alle ADRs, die diese Lookups referenzieren, hängen jetzt von `core` ab:**

```
apps/projects → apps/core (TurningPointTypeLookup, GenrePromiseLookup)
apps/series   → apps/core (GenrePromiseLookup — falls SeriesArc ein Genre-Promise hat)
```

Falls `apps/core` noch nicht existiert: Migration `core/0001_initial` muss
vor allen anderen `core`-Migrationen stehen. `INSTALLED_APPS` muss `apps.core` enthalten.

### 3.2 Layer 10 im LLM-Prompt-Stack

ADR-158 führt **Layer 10** (Genre-Versprechen) als neuen globalen System-Prompt-Layer ein.

**Konsequenz für `project_context_service.py`:**

```python
# Bestehende Layer 1–9 bleiben unverändert
# Layer 10 wird IMMER in den System-Prompt eingefügt:

def build_system_prompt(project) -> str:
    layers = [
        _layer_1_narrative_voice(project),
        _layer_2_world_context(project),
        # ... Layer 3–9 ...
        _layer_10_genre_promise(project),   # NEU — ADR-158
    ]
    return "\n\n".join(filter(None, layers))

def _layer_10_genre_promise(project) -> str:
    promise = getattr(project, "genre_promise", None)
    if not promise:
        return ""
    return promise.to_prompt_context()
```

**Achtung:** Layer 10 erhöht den System-Prompt-Token-Count bei jedem
Kapitel-Generierungsaufruf. Bei `llm_reminder`-Texten von 200–300 Zeichen:
ca. 70–100 Tokens zusätzlich pro Call. Bei 20 Kapiteln × 2 Generierungsrunden
= ca. 4.000 zusätzliche Tokens insgesamt — vernachlässigbar.

### 3.3 QualityDimension-Erweiterung: 5 neue Seeds

Die 5 neuen `QualityDimension`-Einträge aus ADR-158 müssen in
`seed_drama_lookups.py` ergänzt werden:

```python
# seed_drama_lookups.py — ergänzen

from authoring.models import QualityDimension

DRAMATIC_QUALITY_DIMENSIONS = [
    dict(code="dramaturgic_tension",      name_de="Dramaturgische Spannung",
         name_en="Dramatic Tension",      weight=1.0, sort_order=10),
    dict(code="emotional_arc_consistency",name_de="Emotions-Arc-Konsistenz",
         name_en="Emotional Arc",         weight=1.0, sort_order=11),
    dict(code="theme_resonance",          name_de="Thematische Resonanz",
         name_en="Theme Resonance",       weight=0.8, sort_order=12),
    dict(code="subtext_quality",          name_de="Subtext-Qualität",
         name_en="Subtext Quality",       weight=0.8, sort_order=13),
    dict(code="genre_promise_consistency",name_de="Genre-Versprechen-Konsistenz",
         name_en="Genre Promise",         weight=0.8, sort_order=14),
]

for d in DRAMATIC_QUALITY_DIMENSIONS:
    QualityDimension.objects.get_or_create(code=d["code"], defaults=d)
```

### 3.4 DramaturgicHealthScore — neue Checks aus ADR-158

`validate_image_mirror()` muss in `compute_dramaturgic_health()` integriert werden:

```python
# In compute_dramaturgic_health() ergänzen:

# --- OPENING/CLOSING IMAGE (Gewicht 2) ---
mirror_ok, mirror_msg = validate_image_mirror(project)
checks.append(HealthCheck(
    label="Opening/Closing Image Spiegel",
    passed=mirror_ok,
    message=mirror_msg or "Opening und Closing Image sind definiert und verknüpft.",
    weight=2,
))

# --- GENRE-VERSPRECHEN (Gewicht 2) ---
genre_promise = getattr(project, "genre_promise", None)
checks.append(HealthCheck(
    label="Genre-Versprechen definiert",
    passed=genre_promise is not None and genre_promise.genre_promise_type is not None,
    message="ProjectGenrePromise fehlt — LLM hat keinen Genre-Constraint.",
    weight=2,
))
if genre_promise and genre_promise.genre_promise_type:
    checks.append(HealthCheck(
        label="Genre-Versprechen eingelöst",
        passed=genre_promise.is_fulfilled,
        message="Genre-Versprechen noch nicht als eingelöst markiert.",
        weight=1,
    ))
```

---

## 4. Auswirkungen auf ADR-157 (in Revision)

ADR-157 Rev.1 (die Revision mit 7 Blocking Issues) muss um folgende
Punkte aus ADR-158 erweitert werden, bevor sie final wird:

| Was | Quelle | Aktion |
|-----|--------|--------|
| Opening/Closing Image Spiegel-Check | ADR-158 Teil B | In `compute_dramaturgic_health()` ergänzen |
| Genre-Versprechen-Check | ADR-158 Teil C | In `compute_dramaturgic_health()` ergänzen |
| `validate_image_mirror()` | ADR-158 Teil B | In `health_service.py` implementieren |

ADR-157 und ADR-158 teilen sich `health_service.py` —
das ist kein Problem, aber die Deployment-Reihenfolge ist zwingend:

```
ADR-157 Rev.1 → ADR-158 → dann erst ADR-159, ADR-160, ADR-161
```

---

## 5. Auswirkungen auf ADR-159 (Publikationsvorbereitung)

Keine direkten Konflikte. Eine Ergänzung ist sinnvoll:

`PitchGeneratorService.generate_expose_de()` sollte das Genre-Versprechen
als Kontext nutzen:

```python
# In generate_expose_de() ergänzen:
genre_promise = getattr(project, "genre_promise", None)
genre_promise_text = (
    genre_promise.genre_promise_type.core_promise
    if genre_promise and genre_promise.genre_promise_type
    else ""
)

# In EXPOSE_DE_USER-Prompt ergänzen:
f"Genre-Versprechen: {genre_promise_text}\n"
```

---

## 6. Auswirkungen auf ADR-160 (Wissens-Infrastruktur)

Wie in K2 beschrieben: `GenreConventionProfile.reader_promise` (TextField)
ist redundant zu `GenrePromiseLookup.core_promise`.

**Konkrete Änderung in ADR-160:**

```python
# GenreConventionProfile — reader_promise ENTFERNEN:
# (vorher)
reader_promise = models.TextField(blank=True, default="", ...)
# (nachher — gestrichen, Feld existiert nicht mehr)

# Stattdessen: Verweis auf GenrePromiseLookup in help_text des conventions-Felds:
conventions = models.JSONField(
    ...,
    help_text="... Das semantische Genre-Versprechen ist in GenrePromiseLookup (ADR-158) definiert.",
)
```

---

## 7. Auswirkungen auf ADR-161 (ex ADR-158 mein Entwurf — Produktions-Infrastruktur)

Keine inhaltlichen Konflikte. Nur Renummerierung und Migration-Nummern anpassen:

```
ADR-158-produktions-infrastruktur.md → ADR-161-produktions-infrastruktur.md
Migration projects/0010_text_analysis → projects/0017_text_analysis_batch
```

---

## 8. Vollständige bereinigte Gesamtübersicht

### ADR-Nummern nach Bereinigung

```
ADR-150  Grundontologie + BookProject-Felder          ✅ Accepted
ADR-151  Makrostruktur + Wendepunkte                  ✅ Accepted
ADR-152  Substrat: Figuren-Arc + NarrativeVoice       ✅ Accepted
ADR-153  Mesostruktur: Kapitel + Szenen               ✅ Accepted
ADR-154  Mikrostruktur: Prosa + Dialog                ✅ Accepted (angenommen)
ADR-155  Spannungsarchitektur                         ✅ Accepted
ADR-156  Thema + Motiv + Zeitstruktur                 ✅ Accepted
ADR-157  Antagonist + B-Story + MVN Health-Score      ⚠️ Rev.1 pending
ADR-158  Dialogue Subtext + Image Mirror +
         GenrePromise + QualityDimension              ✅ Accepted (NEU, uploaded)
ADR-159  Publikationsvorbereitung: Comps + Pitch      📋 Proposed
ADR-160  Wissens-Infrastruktur: Recherche + Beta      📋 Proposed
ADR-161  Produktions-Infrastruktur: TextAnalysis +
         Budget + Pacing + BatchWriteJob              📋 Proposed (ex ADR-158)
```

### Neue Tabellen aus ADR-158

```
wh_turning_point_type_lookup   (Core-App) ← Konsolidiert mit meiner O1-Spec
wh_dialogue_scenes             (Projects)
wh_genre_promise_lookup        (Core-App)
wh_project_genre_promises      (Projects)
```

**Plus:** 5 neue Einträge in `wh_quality_dimensions` (Seed, keine neue Tabelle)

### Bereinigte Migrations-Reihenfolge (vollständig)

```bash
# Core-App zuerst (neue Abhängigkeit durch ADR-158)
python manage.py migrate core    0001_initial
python manage.py migrate core    0002_turning_point_type_lookup
python manage.py migrate core    0003_genre_promise_lookup

# Projects
python manage.py migrate projects 0004_dramaturgic_fields
python manage.py migrate projects 0005_narrative_voice
python manage.py migrate projects 0006_theme_motif
python manage.py migrate projects 0007_tension_architecture
python manage.py migrate projects 0008_essay_structure
python manage.py migrate projects 0009_master_timeline
python manage.py migrate projects 0010_content_type_profile
python manage.py migrate projects 0011_subplot_arc
python manage.py migrate projects 0012_dialogue_scene
python manage.py migrate projects 0013_turning_point_type_fk
python manage.py migrate projects 0014_genre_promise
python manage.py migrate projects 0015_comparable_titles_pitch
python manage.py migrate projects 0016_research_genre_beta
python manage.py migrate projects 0017_text_analysis_batch

# Worlds
python manage.py migrate worlds  0004_character_arc_fields

# Series
python manage.py migrate series  0003_series_arc

# Alles seeden (idempotent)
python manage.py seed_drama_lookups
```

---

## 9. Empfehlung: Sofortmaßnahmen

```
SOFORT (vor nächstem Commit):
  □ ADR-158-produktions-infrastruktur.md umbenennen → ADR-161
  □ ARCHITECTURE_REVIEW.md aktualisieren (ADR-Nummern)
  □ Core-App anlegen falls noch nicht vorhanden

VOR ADR-157 REV.1 MERGE:
  □ validate_image_mirror() in health_service.py ergänzen
  □ Genre-Versprechen-Checks in compute_dramaturgic_health() ergänzen

VOR ADR-158 DEPLOYMENT:
  □ TurningPointTypeLookup-Felder konsolidieren (K1)
  □ reader_promise aus GenreConventionProfile-Plan entfernen (K2)
  □ Migrations-Nummern gemäß Tabelle oben vergeben (K3)
  □ Core-App in INSTALLED_APPS und settings.py

SEED-ERGÄNZUNGEN (nach Migrations):
  □ 12 TurningPointTypeLookup-Einträge
  □ 9 GenrePromiseLookup-Einträge
  □ 5 QualityDimension-Einträge
```

---

*Konsequenzanalyse — kein ADR, kein Zustandsdokument*  
*Anlass: ADR-158 (uploaded, Accepted) kollidiert mit 3 bestehenden Specs*  
*Folge-Dokumente: ADR-157 Rev.1 (Update), ADR-161 (Renummerierung), ARCHITECTURE_REVIEW.md (Update)*
