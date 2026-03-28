# OPT4 — Produktionsplanung: Budget, Pacing, Batch-Generierung

> Drei technische Lücken, die den Schreibprozess ineffizient machen:
> Kein Wortanzahl-Budget pro Akt. Keine Erkennung von Pacing-Problemen.
> Keine Möglichkeit, mehrere Kapitel in einem Zug zu generieren.

---

## OPT4.1 — Wortanzahl-Budget-Management

### Problem

`BookProject.target_word_count` existiert. `OutlineNode.target_words` existiert.
Aber: Niemand rechnet zusammen, ob die geplanten Node-Wortanzahlen
das Projekt-Ziel ergeben. Kein Warnsystem wenn Akt I 60% des Budgets
konsumiert. Kein Rebalancing-Vorschlag.

```python
# apps/projects/services/budget_service.py
"""
WordCountBudgetService — plant und überwacht Wortanzahl-Budget.

Verlegerisch: Ein Roman mit 90.000 Wörtern braucht:
    Akt I  (25%): ~22.500 Wörter
    Akt II (50%): ~45.000 Wörter
    Akt III(25%): ~22.500 Wörter

Kapitel-Budgets sollten innerhalb ±20% des Akt-Budgets liegen.
"""
from dataclasses import dataclass


@dataclass
class BudgetAllocation:
    target_total: int
    act_budgets: dict[str, int]        # {"act_1": 22500, ...}
    node_budgets: dict[str, int]       # {node_id: target_words}
    current_written: int
    remaining_budget: int
    over_budget_nodes: list[str]       # node_ids die Budget überschreiten
    under_budget_nodes: list[str]      # node_ids die stark unter Budget sind
    completion_pct: float


def compute_budget(project) -> BudgetAllocation:
    """
    Berechnet Wortanzahl-Budget und aktuellen Stand.
    Gibt Empfehlungen zurück wenn Budget-Abweichungen > 20%.
    """
    target = project.target_word_count or 90000
    version = project.outline_versions.filter(is_active=True).first()
    if not version:
        return BudgetAllocation(
            target_total=target, act_budgets={}, node_budgets={},
            current_written=0, remaining_budget=target,
            over_budget_nodes=[], under_budget_nodes=[], completion_pct=0.0
        )

    nodes = list(version.nodes.order_by("order"))
    total_written = sum(n.word_count for n in nodes)

    # Akt-Budgets aus outlinefw-Positionen ableiten
    act_budgets = {
        "act_1":   int(target * 0.25),
        "act_2a":  int(target * 0.25),
        "act_2b":  int(target * 0.25),
        "act_3":   int(target * 0.25),
    }

    # Budget pro Node = akt_budget / akt_kapitel_anzahl
    act_node_map: dict[str, list] = {"act_1": [], "act_2a": [], "act_2b": [], "act_3": []}
    for n in nodes:
        act = n.act or "act_1"
        # Normalisierung: "1" → "act_1"
        if not act.startswith("act_"):
            act = f"act_{act}"
        act_node_map.setdefault(act, []).append(n)

    node_budgets = {}
    for act_key, act_nodes in act_node_map.items():
        if not act_nodes:
            continue
        per_node = act_budgets.get(act_key, target // 4) // len(act_nodes)
        for n in act_nodes:
            node_budgets[str(n.id)] = per_node

    # Abweichungen
    TOLERANCE = 0.2  # ±20%
    over_budget = []
    under_budget = []
    for n in nodes:
        budget = node_budgets.get(str(n.id), 0)
        if not budget or not n.word_count:
            continue
        ratio = n.word_count / budget
        if ratio > (1 + TOLERANCE):
            over_budget.append(str(n.id))
        elif n.word_count > 0 and ratio < (1 - TOLERANCE):
            under_budget.append(str(n.id))

    return BudgetAllocation(
        target_total=target,
        act_budgets=act_budgets,
        node_budgets=node_budgets,
        current_written=total_written,
        remaining_budget=target - total_written,
        over_budget_nodes=over_budget,
        under_budget_nodes=under_budget,
        completion_pct=round(total_written / target * 100, 1),
    )


def suggest_rebalancing(allocation: BudgetAllocation) -> list[str]:
    """Gibt konkrete Rebalancing-Empfehlungen als Strings zurück."""
    suggestions = []
    if allocation.over_budget_nodes:
        suggestions.append(
            f"{len(allocation.over_budget_nodes)} Kapitel sind >20% über Budget — "
            f"erwäge Szenen zu kürzen oder in neue Kapitel aufzuteilen."
        )
    remaining_chapters = len([
        nid for nid, b in allocation.node_budgets.items()
        if nid not in allocation.over_budget_nodes
    ])
    if allocation.remaining_budget > 0 and remaining_chapters > 0:
        avg_remaining = allocation.remaining_budget // max(remaining_chapters, 1)
        suggestions.append(
            f"Verbleibendes Budget: {allocation.remaining_budget:,} Wörter "
            f"({avg_remaining:,} pro verbleibenden Kapitel)."
        )
    return suggestions
```

---

## OPT4.2 — Pacing-Kurve: Kurze Kapitel vor Climax (Feature)

**Verlegerisches Prinzip:** Starke Romane verkürzen die Kapitel-Länge
kurz vor dem Climax — das erzeugt physisch das Gefühl von beschleunigtem
Puls. Ein Roman, der kurz vor dem Climax die längsten Kapitel hat, arbeitet
gegen seine eigene Dramaturgie.

```python
# In TextAnalysisService ergänzen:

def detect_pacing_issues(nodes: list) -> list[dict]:
    """
    Detektiert strukturelle Pacing-Probleme:
    - Längste Kapitel kurz vor Climax (Anti-Pattern)
    - Klumpen gleichlanger Kapitel (Monotonie)
    - Zu kurze Kapitel am Anfang (Setup unterfinanziert)
    """
    issues = []
    if len(nodes) < 5:
        return issues

    word_counts = [(n.order, n.word_count) for n in nodes if n.word_count]
    if not word_counts:
        return issues

    avg = sum(w for _, w in word_counts) / len(word_counts)

    # Anti-Pattern: Längste 3 Kapitel im letzten Viertel?
    last_quarter_start = int(len(word_counts) * 0.75)
    last_quarter = word_counts[last_quarter_start:]
    all_sorted = sorted(word_counts, key=lambda x: -x[1])
    top3_orders = {o for o, _ in all_sorted[:3]}
    last_quarter_orders = {o for o, _ in last_quarter}

    if top3_orders & last_quarter_orders:
        issues.append({
            "type": "long_climax",
            "severity": "warning",
            "description": "Längste Kapitel befinden sich im letzten Viertel — "
                           "kurze Kapitel vor dem Climax erzeugen mehr Tempo.",
            "chapter_orders": list(top3_orders & last_quarter_orders),
        })

    # Monotonie: 5+ Kapitel in ±10% Bereich
    monotone_streak = 0
    for i in range(len(word_counts) - 1):
        _, w1 = word_counts[i]
        _, w2 = word_counts[i + 1]
        if abs(w1 - w2) / max(w1, 1) < 0.1:
            monotone_streak += 1
        else:
            monotone_streak = 0
        if monotone_streak >= 4:
            issues.append({
                "type": "monotone_pacing",
                "severity": "info",
                "description": f"5+ Kapitel gleicher Länge in Folge — "
                               f"Varianz erhöht den Lesefluss.",
                "chapter_orders": [word_counts[j][0] for j in range(i-3, i+2)],
            })
            break

    return issues
```

---

## OPT4.3 — Batch-Generierung (`BatchWriteJob`)

### Problem

`ChapterWriteJob` generiert immer genau ein Kapitel. Für einen Autor,
der 20 Kapitel einer Outline hat und diese in einem Zug KI-generieren
will, gibt es keine Möglichkeit. Er muss 20× Button klicken und
20× auf Celery-Job warten.

```python
# apps/authoring/models_jobs.py — ergänzen

class BatchWriteJob(models.Model):
    """
    Batch-Generierung mehrerer Kapitel in Folge.

    Verarbeitet Kapitel der Reihe nach (nicht parallel) —
    jedes Kapitel bekommt den Kontext der vorherigen als Input.

    Sicherung: max_chapters=10 — nicht das ganze Manuskript blind generieren.
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
        help_text="Geordnete Liste von OutlineNode-UUIDs",
    )
    max_chapters = models.PositiveSmallIntegerField(
        default=10,
        help_text="Sicherheits-Limit: max. Kapitel pro Batch-Job",
    )
    status = models.CharField(
        max_length=10, choices=JobStatus.choices, default=JobStatus.PENDING,
    )
    current_index = models.PositiveSmallIntegerField(
        default=0, help_text="Welches Kapitel wird gerade generiert?",
    )
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
    def progress_pct(self) -> int:
        total = len(self.node_ids or [])
        return int(self.completed_count / total * 100) if total else 0

    @property
    def is_running(self) -> bool:
        return self.status == JobStatus.RUNNING
```

```python
# apps/authoring/tasks.py — Celery Task

@shared_task(bind=True, max_retries=3)
def run_batch_write(self, job_id: str):
    """
    Verarbeitet BatchWriteJob Kapitel für Kapitel.
    Nach jedem Kapitel: kurze Pause + Snapshot des vorherigen Inhalts
    als Kontext für das nächste.
    """
    from authoring.models_jobs import BatchWriteJob
    job = BatchWriteJob.objects.get(id=job_id)
    job.status = "running"
    job.save(update_fields=["status"])

    node_ids = job.node_ids[:job.max_chapters]

    for i, node_id in enumerate(node_ids):
        job.current_index = i
        job.save(update_fields=["current_index", "updated_at"])
        try:
            _generate_single_chapter(node_id, job.project)
            job.completed_count += 1
        except Exception as e:
            job.failed_count += 1
            job.error_log.append({"index": i, "node_id": node_id, "error": str(e)})
        job.save(update_fields=["completed_count", "failed_count", "error_log", "updated_at"])

    job.status = "done" if job.failed_count == 0 else "failed"
    job.save(update_fields=["status", "updated_at"])
```

---

## OPT4.4 — HTMX-Fortschrittsbalken für Batch-Job

```html
<!-- templates/authoring/_batch_progress.html -->
<div id="batch-progress"
     hx-get="{% url 'authoring:batch_status' job.id %}"
     hx-trigger="every 3s [{{ job.is_running }}]"
     hx-swap="outerHTML">

    <div class="card p-3">
        <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="fw-semibold fs-sm">
                <span class="spinner-border spinner-border-sm text-primary me-2"
                      {% if not job.is_running %}style="display:none"{% endif %}></span>
                Batch-Generierung — {{ job.completed_count }}/{{ job.node_ids|length }} Kapitel
            </span>
            <span class="fs-xs text-muted">{{ job.progress_pct }}%</span>
        </div>
        <div class="progress" style="height:6px;background:var(--bg-hover);">
            <div class="progress-bar"
                 style="width:{{ job.progress_pct }}%;background:var(--primary);
                        transition:width .3s;"></div>
        </div>
        {% if job.failed_count %}
        <div class="mt-2 fs-xs" style="color:var(--danger);">
            {{ job.failed_count }} Fehler aufgetreten
        </div>
        {% endif %}
    </div>
</div>
```

---

## OPT4.5 — Deployment

```bash
# Keine neue Migration für BudgetService (nur Service)
# Migration für BatchWriteJob:
python manage.py migrate authoring 0003_batch_write_job

# Celery Task registrieren
# URL: /projects/<pk>/budget/ (Budget-Dashboard)
# URL: /authoring/projects/<pk>/batch/ (Batch-Generierung starten)
```

---

*writing-hub · OPT4 · Produktionsplanung: Budget, Pacing, Batch*
*Verlegerisches Kernprinzip: Kurze Kapitel vor dem Climax sind kein Zufall*
