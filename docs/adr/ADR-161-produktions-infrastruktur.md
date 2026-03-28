# ADR-158: Produktions-Infrastruktur — TextAnalysis, Budget, Pacing, Batch

**Status:** Proposed  
**Datum:** 2026-03-28  
**Kontext:** writing-hub @ achimdehnert/writing-hub  
**Abhängig von:** ADR-150, ADR-151, ADR-157

---

## Kontext

Nach Deployment der dramaturgischen Kern-Modellierung (ADR-150–157) fehlt
die **Produktions-Infrastruktur** — die Werkzeuge, die während des
aktiven Schreibens und der Überarbeitung greifen:

### Lücke 1 — Strukturelle Textanalyse

`StyleChecker` prüft Regex-Antipattern pro Kapitel.
`LektoratIssue` analysiert Kapitel-Inhalt via LLM.
**Niemand prüft die Struktur quer über das gesamte Manuskript:**

- **Dead Scenes:** `emotion_start == emotion_end` — kein emotionaler
  Deltawert, dramaturgisch wertlos (Framework Schritt 4: "Eine Szene,
  die beim gleichen Wert endet, ist dramaturgisch tot.")
- **Character Screen Time:** Antagonist in 3 von 20 Kapiteln ist
  kein starker Antagonist.
- **Voice Drift:** KI-generierte Kapitel tendieren nach 50.000+ Wörtern
  zur Mittelwerts-Prosa — `NarrativeVoice` definiert den Stil, misst
  aber keine Abweichungen.

### Lücke 2 — Kein Wortanzahl-Budget

`BookProject.target_word_count` existiert. `OutlineNode.target_words`
existiert. **Niemand rechnet zusammen:**
- Ob Akt I bereits 60% des Budgets konsumiert
- Ob einzelne Kapitel >20% über/unter Budget liegen
- Wie viele Wörter für die restlichen Kapitel bleiben

### Lücke 3 — Pacing-Anti-Pattern unerkannt

Ein Roman, der seine längsten Kapitel kurz vor dem Climax hat,
arbeitet gegen seine eigene Dramaturgie. Das ist das häufigste
strukturelle Pacing-Problem bei Erstentwürfen — und vollständig
aus `OutlineNode.word_count`-Daten erkennbar.

### Lücke 4 — Keine Batch-Generierung

`ChapterWriteJob` generiert exakt 1 Kapitel. Für 20 Kapitel
einer neuen Outline: 20× Button klicken, 20× auf Celery-Job warten.
Kein sequenzieller Kontext-Transfer zwischen Kapiteln.

---

## Entscheidung

### Teil A: `TextAnalysisSnapshot` Model

```python
# apps/projects/models_analysis.py

import uuid
from django.db import models


class TextAnalysisSnapshot(models.Model):
    """
    Gecachter struktureller Analyse-Snapshot eines Manuskripts.

    Berechnet wird:
        - Dead Scenes (regelbasiert, kein LLM)
        - Character Screen Time (regelbasiert)
        - Pacing-Verteilung (regelbasiert)
        - Dialogue-Ratio-Schätzung (Regex-Heuristik)
        - Voice Drift (optional, LLM — teuer, nur auf Anfrage)

    Nicht-Ziel: Ersatz für LektoratSession.
    Ziel: Strukturelle Signale, die dem Autor helfen, das Manuskript
    zu priorisieren — bevor er ins Lektorat geht.

    Speicher-Strategie: max. 5 Snapshots pro Projekt (FIFO),
    analog zu ManuscriptSnapshot.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="analysis_snapshots",
    )

    # ── Dead Scene Detection ──────────────────────────────────────────────
    dead_scene_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Anzahl Nodes mit emotion_start == emotion_end (beide befüllt)",
    )
    dead_scene_node_ids = models.JSONField(
        default=list,
        help_text="UUIDs der betroffenen OutlineNodes",
    )

    # ── Character Screen Time ─────────────────────────────────────────────
    character_screen_time = models.JSONField(
        default=dict,
        help_text="{character_uuid: {chapters: int, percent: float, last_seen_order: int}}",
    )

    # ── Pacing ────────────────────────────────────────────────────────────
    chapter_word_counts = models.JSONField(
        default=list,
        help_text="[{order: int, word_count: int, title: str}]",
    )
    pacing_variance = models.FloatField(
        null=True, blank=True,
        help_text="Standardabweichung der Kapitel-Wortanzahlen",
    )
    pacing_issues = models.JSONField(
        default=list,
        help_text="[{type: str, severity: str, description: str, chapter_orders: []}]",
    )

    # ── Dialogue Ratio ────────────────────────────────────────────────────
    dialogue_ratios = models.JSONField(
        default=dict,
        help_text="{chapter_order: float} — geschätzter Dialog-Anteil 0.0–1.0",
    )

    # ── Voice Drift (LLM, optional) ───────────────────────────────────────
    voice_drift_checked = models.BooleanField(default=False)
    voice_drift_detected = models.BooleanField(default=False)
    voice_drift_chapters = models.JSONField(
        default=list,
        help_text="[{order: int, reason: str}]",
    )

    # ── Meta ──────────────────────────────────────────────────────────────
    chapters_analyzed = models.PositiveSmallIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)
    triggered_by = models.CharField(
        max_length=20,
        choices=[
            ("manual",   "Manuell ausgelöst"),
            ("lektorat", "Nach Lektorat"),
            ("save",     "Nach Kapitel-Speichern"),
        ],
        default="manual",
    )

    class Meta:
        db_table = "wh_text_analysis_snapshots"
        ordering = ["-computed_at"]
        get_latest_by = "computed_at"
        verbose_name = "Text-Analyse-Snapshot"
        verbose_name_plural = "Text-Analyse-Snapshots"

    def __str__(self):
        return f"Analyse {self.project.title} — {self.computed_at:%Y-%m-%d %H:%M}"

    @property
    def has_issues(self) -> bool:
        return (
            self.dead_scene_count > 0
            or bool(self.pacing_issues)
            or self.voice_drift_detected
        )

    @property
    def antagonist_underrepresented(self) -> bool:
        """
        True wenn der Antagonist in < 25% der Kapitel als POV oder
        erwähnte Figur vorkommt.
        Proxy: character_screen_time enthält antagonist-UUID mit
        percent < 25 und chapters_analyzed > 8.
        """
        if self.chapters_analyzed < 8:
            return False
        for data in self.character_screen_time.values():
            if data.get("role") == "antagonist" and data.get("percent", 100) < 25:
                return True
        return False
```

---

### Teil B: `TextAnalysisService`

```python
# apps/projects/services/text_analysis_service.py

import re
import statistics
import json
import uuid
from projects.models import BookProject, OutlineNode, TextAnalysisSnapshot


# ── Max. Snapshots pro Projekt (FIFO) ────────────────────────────────────
MAX_SNAPSHOTS = 5


def compute_text_analysis(
    project: BookProject,
    check_voice_drift: bool = False,
    triggered_by: str = "manual",
) -> TextAnalysisSnapshot:
    """
    Berechnet strukturellen Analyse-Snapshot.

    check_voice_drift=True → LLM-Call (teuer, nur auf explizite Anfrage).
    """
    version = project.outline_versions.filter(is_active=True).first()
    if not version:
        return TextAnalysisSnapshot.objects.create(project=project)

    nodes = list(
        version.nodes
        .select_related("outcome", "tension_level")
        .order_by("order")
    )

    # A — Dead Scenes
    dead = [n for n in nodes if _is_dead_scene(n)]

    # B — Screen Time (Figuren aus pov_character_id)
    screen_time = _compute_screen_time(nodes, project)

    # C — Pacing
    word_counts = [
        {"order": n.order, "word_count": n.word_count, "title": n.title[:40]}
        for n in nodes if n.word_count
    ]
    wc_values = [x["word_count"] for x in word_counts]
    variance = statistics.stdev(wc_values) if len(wc_values) > 1 else 0.0
    pacing_issues = _detect_pacing_issues(word_counts)

    # D — Dialogue Ratio
    dialogue_ratios = {
        n.order: _estimate_dialogue_ratio(n.content)
        for n in nodes
        if n.content
    }

    snap = TextAnalysisSnapshot(
        project=project,
        dead_scene_count=len(dead),
        dead_scene_node_ids=[str(n.id) for n in dead],
        character_screen_time=screen_time,
        chapter_word_counts=word_counts,
        pacing_variance=variance,
        pacing_issues=pacing_issues,
        dialogue_ratios=dialogue_ratios,
        chapters_analyzed=len(nodes),
        triggered_by=triggered_by,
    )

    # E — Voice Drift (optional)
    if check_voice_drift:
        snap = _check_voice_drift(project, nodes, snap)

    snap.save()
    _enforce_fifo(project)
    return snap


def _is_dead_scene(node: OutlineNode) -> bool:
    if not node.emotion_start or not node.emotion_end:
        return False
    return node.emotion_start.strip().lower() == node.emotion_end.strip().lower()


def _compute_screen_time(nodes: list, project) -> dict:
    """
    Zählt POV-Auftritte pro Figur.
    Reichert mit narrative_role an (falls ProjectCharacterLink existiert).
    """
    counts: dict[str, dict] = {}
    total = len(nodes)

    # Rolle-Lookup aus ProjectCharacterLinks
    role_map = {}
    try:
        for link in project.projectcharacterlink_set.all():
            if link.weltenhub_character_id:
                role_map[str(link.weltenhub_character_id)] = link.narrative_role
    except Exception:
        pass

    for n in nodes:
        if not n.pov_character_id:
            continue
        key = str(n.pov_character_id)
        if key not in counts:
            counts[key] = {
                "chapters": 0,
                "percent": 0.0,
                "last_seen_order": 0,
                "role": role_map.get(key, ""),
            }
        counts[key]["chapters"] += 1
        counts[key]["last_seen_order"] = n.order

    for key in counts:
        counts[key]["percent"] = round(
            counts[key]["chapters"] / total * 100, 1
        ) if total else 0.0

    return counts


def _detect_pacing_issues(word_counts: list) -> list:
    issues = []
    if len(word_counts) < 5:
        return issues

    wc = [(x["order"], x["word_count"]) for x in word_counts]
    total = len(wc)

    # Anti-Pattern 1: Längste Kapitel im letzten Viertel
    last_q_start = int(total * 0.75)
    last_q_orders = {o for o, _ in wc[last_q_start:]}
    top3_orders = {o for o, _ in sorted(wc, key=lambda x: -x[1])[:3]}
    overlap = top3_orders & last_q_orders
    if overlap:
        issues.append({
            "type": "long_climax",
            "severity": "warning",
            "description": (
                "Längste Kapitel im letzten Viertel — kurze Kapitel "
                "vor dem Climax erzeugen mehr Tempo."
            ),
            "chapter_orders": sorted(overlap),
        })

    # Anti-Pattern 2: Monotonie (5+ Kapitel ±10% Länge)
    streak = 0
    streak_start = 0
    for i in range(1, len(wc)):
        _, w_prev = wc[i - 1]
        _, w_curr = wc[i]
        if w_prev > 0 and abs(w_curr - w_prev) / w_prev < 0.10:
            if streak == 0:
                streak_start = i - 1
            streak += 1
        else:
            streak = 0
        if streak >= 4:
            issues.append({
                "type": "monotone_pacing",
                "severity": "info",
                "description": "5+ Kapitel nahezu gleicher Länge — Variation erhöht Lesefluss.",
                "chapter_orders": [wc[j][0] for j in range(streak_start, i + 1)],
            })
            break

    return issues


def _estimate_dialogue_ratio(content: str) -> float:
    if not content:
        return 0.0
    total = len(content)
    # Deutsches Anführungszeichen: „..."/»...«/"..."
    dialogue_chars = sum(
        len(m.group())
        for m in re.finditer(r'[„»"][^"„»«]*["«»]', content)
    )
    return round(dialogue_chars / total, 2) if total else 0.0


def _check_voice_drift(project, nodes, snap: TextAnalysisSnapshot) -> TextAnalysisSnapshot:
    """LLM-basiert — nur auf explizite Anfrage."""
    try:
        from aifw.service import sync_completion
    except ImportError:
        return snap

    voice = getattr(project, "narrative_voice", None)
    if not voice or not voice.authoringfw_prompt_block:
        return snap

    written = [n for n in nodes if n.content and len(n.content) > 300]
    # Stichproben: jedes 5. Kapitel, max. 5
    samples = written[::max(1, len(written) // 5)][:5]

    drifted = []
    for node in samples:
        result = sync_completion(
            action_code="voice_drift_check",
            messages=[{
                "role": "user",
                "content": (
                    f"ERZÄHLSTIMME-PROFIL:\n{voice.authoringfw_prompt_block}\n\n"
                    f"KAPITEL {node.order} (Ausschnitt):\n{node.content[:1200]}\n\n"
                    "Stimmt der Ausschnitt mit dem Profil überein? "
                    'Antworte als JSON: {"drift": true/false, "reason": "..."}'
                ),
            }],
        )
        if result.success:
            try:
                data = json.loads(result.content)
                if data.get("drift"):
                    drifted.append({"order": node.order, "reason": data.get("reason", "")})
            except (json.JSONDecodeError, AttributeError):
                pass

    snap.voice_drift_checked = True
    snap.voice_drift_detected = bool(drifted)
    snap.voice_drift_chapters = drifted
    return snap


def _enforce_fifo(project) -> None:
    """Löscht älteste Snapshots wenn > MAX_SNAPSHOTS."""
    qs = TextAnalysisSnapshot.objects.filter(project=project).order_by("-computed_at")
    ids_to_delete = list(qs.values_list("id", flat=True)[MAX_SNAPSHOTS:])
    if ids_to_delete:
        TextAnalysisSnapshot.objects.filter(id__in=ids_to_delete).delete()
```

---

### Teil C: `BudgetService`

```python
# apps/projects/services/budget_service.py

from dataclasses import dataclass, field
from projects.models import BookProject


@dataclass
class BudgetAllocation:
    target_total: int
    act_budgets: dict        # {"act_1": 22500, ...}
    node_budgets: dict       # {str(node_id): int}
    current_written: int
    remaining_budget: int
    over_budget_nodes: list  # node_ids > 120% Budget
    under_budget_nodes: list # node_ids < 80% Budget (nur wenn geschrieben)
    completion_pct: float
    suggestions: list = field(default_factory=list)


# Standard-Akt-Proportionen (Drei-Akte-Modell)
ACT_PROPORTIONS = {
    "act_1":  0.25,
    "act_2a": 0.25,
    "act_2b": 0.25,
    "act_3":  0.25,
}
TOLERANCE = 0.20  # ±20%


def compute_budget(project: BookProject) -> BudgetAllocation:
    target = project.target_word_count or 90_000
    version = project.outline_versions.filter(is_active=True).first()

    if not version:
        return BudgetAllocation(
            target_total=target, act_budgets={}, node_budgets={},
            current_written=0, remaining_budget=target,
            over_budget_nodes=[], under_budget_nodes=[],
            completion_pct=0.0,
        )

    nodes = list(version.nodes.order_by("order"))
    total_written = sum(n.word_count for n in nodes if n.word_count)

    # Akt-Zuordnung
    act_node_map: dict[str, list] = {k: [] for k in ACT_PROPORTIONS}
    for n in nodes:
        act = (n.act or "act_1").lower().replace(" ", "_")
        if not act.startswith("act_"):
            act = f"act_{act}"
        bucket = act if act in act_node_map else "act_1"
        act_node_map[bucket].append(n)

    act_budgets = {
        act: int(target * prop)
        for act, prop in ACT_PROPORTIONS.items()
    }

    # Budget pro Node
    node_budgets = {}
    for act, act_nodes in act_node_map.items():
        if not act_nodes:
            continue
        per_node = act_budgets[act] // len(act_nodes)
        for n in act_nodes:
            node_budgets[str(n.id)] = per_node

    # Abweichungen
    over_budget, under_budget = [], []
    for n in nodes:
        budget = node_budgets.get(str(n.id), 0)
        if not budget or not n.word_count:
            continue
        ratio = n.word_count / budget
        if ratio > 1 + TOLERANCE:
            over_budget.append(str(n.id))
        elif ratio < 1 - TOLERANCE:
            under_budget.append(str(n.id))

    completion = round(total_written / target * 100, 1) if target else 0.0

    alloc = BudgetAllocation(
        target_total=target,
        act_budgets=act_budgets,
        node_budgets=node_budgets,
        current_written=total_written,
        remaining_budget=target - total_written,
        over_budget_nodes=over_budget,
        under_budget_nodes=under_budget,
        completion_pct=completion,
    )
    alloc.suggestions = _suggest_rebalancing(alloc, nodes)
    return alloc


def _suggest_rebalancing(alloc: BudgetAllocation, nodes) -> list[str]:
    suggestions = []
    if alloc.over_budget_nodes:
        suggestions.append(
            f"{len(alloc.over_budget_nodes)} Kapitel >20% über Budget — "
            "erwäge Szenen zu kürzen oder aufzuteilen."
        )
    remaining_unwritten = sum(
        1 for n in nodes
        if str(n.id) in alloc.node_budgets and not n.word_count
    )
    if alloc.remaining_budget > 0 and remaining_unwritten > 0:
        avg = alloc.remaining_budget // remaining_unwritten
        suggestions.append(
            f"Verbleibendes Budget: {alloc.remaining_budget:,} Wörter "
            f"(Ø {avg:,} für {remaining_unwritten} ungeschriebene Kapitel)."
        )
    return suggestions
```

---

### Teil D: `BatchWriteJob`

```python
# apps/authoring/models_jobs.py — ergänzen

class BatchWriteJob(models.Model):
    """
    Sequenzielle Batch-Generierung mehrerer Kapitel.

    Sicherheit:
        max_chapters=10 — kein blindes Vollmanuskript-Generieren
        Sequenziell (nicht parallel) — jedes Kapitel bekommt
        den Inhalt des vorherigen als Kontext.

    Status-Tracking via HTMX-Polling (alle 3s).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject", on_delete=models.CASCADE,
        related_name="batch_write_jobs",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    node_ids = models.JSONField(
        help_text="Geordnete Liste von OutlineNode-UUIDs (strings)",
    )
    max_chapters = models.PositiveSmallIntegerField(
        default=10,
        help_text="Sicherheits-Limit pro Batch-Job",
    )
    status = models.CharField(
        max_length=10, choices=JobStatus.choices, default=JobStatus.PENDING,
        db_index=True,
    )
    current_index = models.PositiveSmallIntegerField(default=0)
    completed_count = models.PositiveSmallIntegerField(default=0)
    failed_count = models.PositiveSmallIntegerField(default=0)
    error_log = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_batch_write_jobs"
        ordering = ["-created_at"]
        verbose_name = "Batch-Write-Job"

    @property
    def total(self) -> int:
        return min(len(self.node_ids or []), self.max_chapters)

    @property
    def progress_pct(self) -> int:
        return int(self.completed_count / self.total * 100) if self.total else 0

    @property
    def is_running(self) -> bool:
        return self.status == JobStatus.RUNNING
```

```python
# apps/authoring/tasks.py — Celery Task

@shared_task(bind=True, max_retries=2)
def run_batch_write(self, job_id: str):
    from authoring.models_jobs import BatchWriteJob
    from authoring.services.chapter_production_service import write_chapter

    job = BatchWriteJob.objects.get(id=job_id)
    job.status = "running"
    job.save(update_fields=["status"])

    node_ids = (job.node_ids or [])[:job.max_chapters]
    prev_content = ""  # Kontext des vorherigen Kapitels

    for i, node_id in enumerate(node_ids):
        job.current_index = i
        job.save(update_fields=["current_index", "updated_at"])
        try:
            content = write_chapter(
                node_id=node_id,
                project=job.project,
                previous_chapter_content=prev_content[-800:],  # letzten 800 Zeichen
            )
            prev_content = content
            job.completed_count += 1
        except Exception as exc:
            job.failed_count += 1
            job.error_log.append({
                "index": i, "node_id": node_id, "error": str(exc)
            })
        job.save(update_fields=["completed_count", "failed_count", "error_log", "updated_at"])

    job.status = "done" if job.failed_count == 0 else "failed"
    job.save(update_fields=["status", "updated_at"])
```

---

## Begründung

- **TextAnalysisSnapshot als gecachtes Model** (nicht live):
  Dead Scenes und Pacing-Analyse sind rechenintensiv bei 20+ Kapiteln.
  Ein Snapshot wird bei Bedarf neu berechnet — nicht bei jedem Feld-Update.
  Analog zu `ManuscriptSnapshot` (FIFO, max. 5 pro Projekt).

- **Voice Drift opt-in** (`check_voice_drift=False` default):
  LLM-Call pro Kapitel-Sample ist teuer. Regelbasierte Analyse
  (Dead Scenes, Pacing) ist kostenlos und deckt 80% der Fälle.

- **BudgetService als pure Service** (kein Model):
  Budget wird berechnet, nicht persistiert. Ändert sich mit jedem
  `word_count`-Update. Ein Model wäre denormalisiert.

- **BatchWriteJob sequenziell** (nicht parallel):
  Parallelisierung würde Kontext-Kontinuität zerstören.
  Kapitel N+1 soll wissen, wie Kapitel N endet.
  Sicherheits-Limit: `max_chapters=10`.

- **`antagonist_underrepresented` als Property** (nicht Health-Check):
  Character Screen Time ist eine Indikation, kein Blocker.
  Property auf `TextAnalysisSnapshot` — optional im UI anzeigbar.

---

## Abgelehnte Alternativen

**Voice Drift per Celery-Task nach jedem Speichern:** Zu teuer.
Jeden LLM-Call beim Schreiben auslösen würde die UX zerstören.

**BudgetAllocation als Django-Model:** Vollständig denormalisiert.
Jeder `word_count`-Speicher würde eine Budget-Neuberechnung erzwingen.
Service-on-demand ist konsistenter.

**Batch-Generierung parallel:** Verliert den Kapitel-zu-Kapitel-Kontext.
Sequenziell ist das korrekte Modell für narrativen Text.

---

## Konsequenzen

- Migration `projects/0010_text_analysis_snapshot` — neue Tabelle
- Migration `authoring/0003_batch_write_job` — neue Tabelle
- `TextAnalysisService` in `apps/projects/services/`
- `BudgetService` in `apps/projects/services/`
- Celery Task `run_batch_write` in `apps/authoring/tasks.py`
- URL `projects/<pk>/analysis/` + View + Template (Drama-Dashboard FE3 erweitern)
- URL `projects/<pk>/budget/` + View
- URL `authoring/projects/<pk>/batch/` + View
- AIActionType `voice_drift_check` (optional, nur für Voice Drift)
- HTMX-Polling für BatchWriteJob-Fortschritt (FE2)

---

**Referenzen:** ADR-150 (Schritt 4 emotional_arc), ADR-151 (NarrativeVoice),  
ADR-157 (DramaturgicHealthScore), `docs/adr/input/schritt_04_mesostruktur.md`,  
`docs/adr/input/schritt_06_spannung.md` (Pacing-Anti-Pattern)
