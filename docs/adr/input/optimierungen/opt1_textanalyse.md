# OPT1 — Textanalyse: Rhythmus, Voice Drift, Dead Scenes

> Der bestehende `StyleChecker` ist rein regelbasiert (Regex-Antipattern).
> Das `LektoratIssue`-System prüft einzelne Kapitel isoliert.
> Was fehlt: strukturelle Textanalyse quer über das gesamte Manuskript.

---

## OPT1.1 — Drei ungelöste Probleme

### Problem A: Dead Scenes

`OutlineNode` hat `emotion_start` und `emotion_end` — aber kein System
warnt automatisch, wenn beide gleich sind. Eine Szene ohne emotionalen
Deltawert ist dramaturgisch tot (Romanstruktur-Framework Schritt 4):

> *"Eine Szene, die beim gleichen emotionalen Wert endet wie sie begonnen hat,
> ist dramaturgisch tot."*

Aktuell kann ein Autor 30 Kapitel schreiben, ohne dieses Anti-Pattern
zu sehen.

### Problem B: Voice Drift

Nach 50.000 Wörtern driftet jeder Autor stilistisch. Das `NarrativeVoice`-Model
(ADR-152) definiert den Stil — aber niemand misst, ob Kapitel 18 noch zum
vereinbarten Stil passt. Besonders kritisch bei KI-generierten Kapiteln,
die tendenziell zur Mittelwerts-Prosa tendieren.

### Problem C: Character Screen Time

Welche Figur taucht in wie vielen Kapiteln auf? Ein Antagonist, der in
20 Kapiteln nur 3× vorkommt, ist kein starker Antagonist. Ein Liebesinteresse,
das als B-Story-Träger fungiert, muss regelmäßig präsent sein.
Aktuell keine Möglichkeit, das zu tracken.

---

## OPT1.2 — Model: `TextAnalysisSnapshot`

```python
# apps/projects/models_analysis.py
"""
TextAnalysisSnapshot — strukturelle Manuskript-Analyse.

Nicht-persistierte Berechnungen werden gecacht (max. 1 Snapshot pro Projekt).
Wird bei jedem Lektorat oder auf Anfrage neu berechnet.
"""
import uuid
from django.db import models


class TextAnalysisSnapshot(models.Model):
    """
    Gecachter Analyse-Snapshot des Manuskripts.

    Wird nach jedem Kapitel-Update oder explizit per Button neu berechnet.
    Ersetzt nicht LektoratSession — analysiert Struktur, nicht Text-Inhalt.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.BookProject",
        on_delete=models.CASCADE,
        related_name="analysis_snapshots",
    )

    # Dead Scene Detection
    dead_scene_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Anzahl Szenen/Kapitel mit emotion_start == emotion_end",
    )
    dead_scene_node_ids = models.JSONField(
        default=list,
        help_text="UUIDs der OutlineNodes mit emotionalem Null-Delta",
    )

    # Voice Drift (LLM-basiert)
    voice_drift_detected = models.BooleanField(default=False)
    voice_drift_chapters = models.JSONField(
        default=list,
        help_text="Kapitel-Orders wo Stil-Abweichung detektiert wurde",
    )
    voice_drift_summary = models.TextField(blank=True, default="")

    # Character Screen Time
    character_screen_time = models.JSONField(
        default=dict,
        help_text="{character_id: {chapters: int, percent: float, last_seen: int}}",
    )

    # Pacing
    chapter_word_counts = models.JSONField(
        default=list,
        help_text="[{order: int, word_count: int}] — für Pacing-Kurve",
    )
    pacing_variance = models.FloatField(
        null=True, blank=True,
        help_text="Standardabweichung der Kapitel-Wortanzahlen",
    )

    # Dialogue/Prose Balance pro Kapitel
    dialogue_ratios = models.JSONField(
        default=dict,
        help_text="{chapter_order: float} — Anteil Dialog am Kapiteltext",
    )

    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wh_text_analysis_snapshots"
        ordering = ["-computed_at"]
        get_latest_by = "computed_at"
        verbose_name = "Text-Analyse-Snapshot"
```

---

## OPT1.3 — Service: `TextAnalysisService`

```python
# apps/projects/services/text_analysis_service.py
"""
TextAnalysisService — strukturelle Manuskript-Analyse.

A: Dead Scene Detection   — regelbasiert, kein LLM
B: Character Screen Time  — regelbasiert (OutlineNode.pov_character_id)
C: Pacing Analysis        — regelbasiert (word_count-Verteilung)
D: Voice Drift Detection  — LLM (action: voice_drift_check) — optional/teuer
"""
import re
import statistics
from projects.models import BookProject, OutlineNode, TextAnalysisSnapshot


def compute_text_analysis(project: BookProject, check_voice_drift: bool = False) -> TextAnalysisSnapshot:
    """
    Berechnet vollständigen Analyse-Snapshot.

    check_voice_drift=True ist optional — verursacht LLM-Call.
    Standardmäßig False (regelbasiert reicht für Dead Scenes + Pacing).
    """
    version = project.outline_versions.filter(is_active=True).first()
    if not version:
        return _empty_snapshot(project)

    nodes = list(version.nodes.select_related("outcome", "tension_level").order_by("order"))

    # A — Dead Scenes
    dead = [n for n in nodes if _is_dead_scene(n)]

    # B — Character Screen Time
    screen_time = _compute_screen_time(nodes)

    # C — Pacing
    word_counts = [{"order": n.order, "word_count": n.word_count} for n in nodes if n.word_count]
    variance = statistics.stdev([x["word_count"] for x in word_counts]) if len(word_counts) > 1 else 0

    # D — Dialogue Ratio (einfache Regex-Heuristik)
    dialogue_ratios = {}
    for n in nodes:
        if n.content:
            dialogue_ratios[n.order] = _estimate_dialogue_ratio(n.content)

    snap = TextAnalysisSnapshot(
        project=project,
        dead_scene_count=len(dead),
        dead_scene_node_ids=[str(n.id) for n in dead],
        character_screen_time=screen_time,
        chapter_word_counts=word_counts,
        pacing_variance=variance,
        dialogue_ratios=dialogue_ratios,
    )

    # D — Voice Drift (optional, LLM)
    if check_voice_drift:
        snap = _check_voice_drift(project, nodes, snap)

    snap.save()
    return snap


def _is_dead_scene(node: OutlineNode) -> bool:
    """Szene ist 'tot' wenn emotion_start == emotion_end (beide befüllt)."""
    if not node.emotion_start or not node.emotion_end:
        return False
    return node.emotion_start.strip().lower() == node.emotion_end.strip().lower()


def _compute_screen_time(nodes: list[OutlineNode]) -> dict:
    """Zählt wie oft eine POV-Figur in Nodes vorkommt."""
    counts: dict[str, int] = {}
    last_seen: dict[str, int] = {}
    total = len(nodes)
    for n in nodes:
        if n.pov_character_id:
            key = str(n.pov_character_id)
            counts[key] = counts.get(key, 0) + 1
            last_seen[key] = n.order
    return {
        k: {
            "chapters": v,
            "percent": round(v / total * 100, 1) if total else 0,
            "last_seen": last_seen.get(k, 0),
        }
        for k, v in counts.items()
    }


def _estimate_dialogue_ratio(content: str) -> float:
    """Schätzt Dialoganteil via Anführungszeichen-Heuristik."""
    if not content:
        return 0.0
    total_chars = len(content)
    # Deutsches Anführungszeichen: „..." oder "..."
    dialogue_chars = sum(
        len(m.group())
        for m in re.finditer(r'[„"][^"„"]*[""]', content)
    )
    return round(dialogue_chars / total_chars, 2) if total_chars else 0.0


def _check_voice_drift(project, nodes, snap: TextAnalysisSnapshot) -> TextAnalysisSnapshot:
    """LLM-basierte Voice-Drift-Detection — teuer, nur auf explizite Anfrage."""
    from aifw.service import sync_completion

    voice = getattr(project, "narrative_voice", None)
    if not voice or not voice.authoringfw_prompt_block:
        return snap

    # Nur geschriebene Kapitel prüfen, max. 5 Stichproben
    written = [n for n in nodes if n.content and len(n.content) > 200]
    samples = written[::max(1, len(written) // 5)][:5]

    drifted = []
    for node in samples:
        result = sync_completion(
            action_code="voice_drift_check",
            messages=[{
                "role": "user",
                "content": f"""
ERZÄHLSTIMME-PROFIL:
{voice.authoringfw_prompt_block}

KAPITEL {node.order} (Ausschnitt, erste 300 Wörter):
{node.content[:1200]}

Stimmt dieser Ausschnitt mit dem Erzählstimme-Profil überein?
Antworte als JSON: {{"drift": true/false, "reason": "..."}}
"""
            }]
        )
        if result.success:
            import json
            data = json.loads(result.content)
            if data.get("drift"):
                drifted.append({"order": node.order, "reason": data.get("reason", "")})

    snap.voice_drift_detected = bool(drifted)
    snap.voice_drift_chapters = drifted
    return snap
```

---

## OPT1.4 — Dead Scene Widget im Drama-Dashboard (FE3 ergänzen)

```html
<!-- In templates/projects/drama_dashboard.html ergänzen -->

{% if analysis and analysis.dead_scene_count %}
<div class="card mb-3" style="border-left:3px solid var(--danger);">
    <div class="card-body py-2 px-3">
        <div class="d-flex align-items-center gap-2">
            <i class="bi bi-exclamation-triangle-fill" style="color:var(--danger);"></i>
            <span class="fw-semibold fs-sm">
                {{ analysis.dead_scene_count }} Dead Scene{{ analysis.dead_scene_count|pluralize }}
            </span>
            <span class="text-muted fs-xs">
                — emotion_start == emotion_end
            </span>
        </div>
    </div>
</div>
{% endif %}

<!-- Character Screen Time -->
{% if analysis.character_screen_time %}
<div class="card mb-4">
    <div class="card-header py-2 px-3">
        <span class="fw-semibold fs-sm">
            <i class="bi bi-person-lines-fill me-2 text-primary"></i>Figur-Präsenz
        </span>
    </div>
    <div class="card-body p-2">
        {% for char_id, data in analysis.character_screen_time.items %}
        <div class="d-flex align-items-center gap-2 mb-1">
            <div class="fs-xs text-muted" style="min-width:120px;">{{ char_id|truncatechars:12 }}</div>
            <div class="progress flex-grow-1" style="height:8px;background:var(--bg-hover);">
                <div class="progress-bar"
                     style="width:{{ data.percent }}%;background:var(--primary);"></div>
            </div>
            <div class="fs-xs text-muted">{{ data.chapters }}×</div>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

---

## OPT1.5 — Deployment

```python
# apps/projects/urls_html.py
path("<uuid:pk>/analysis/", views_html.text_analysis_view, name="text_analysis"),
path("<uuid:pk>/analysis/compute/", views_html.compute_analysis, name="compute_analysis"),
```

```bash
python manage.py migrate projects 0010_text_analysis_snapshot
# AIActionType: voice_drift_check (optional)
```

---

*writing-hub · OPT1 · Textanalyse: Dead Scenes, Voice Drift, Screen Time*
*Neue Tabelle: wh_text_analysis_snapshots*
