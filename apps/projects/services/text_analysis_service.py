"""
TextAnalysisService — ADR-161

Strukturelle Manuskript-Analyse (regelbasiert, kein LLM).
"""
from __future__ import annotations

import json
import re
import statistics

MAX_SNAPSHOTS = 5


def compute_text_analysis(project, check_voice_drift: bool = False, triggered_by: str = "manual"):
    """
    Berechnet strukturellen Analyse-Snapshot.

    check_voice_drift=True → LLM-Call (teuer, nur auf explizite Anfrage).
    Gibt TextAnalysisSnapshot zurück.
    """
    from apps.projects.models import TextAnalysisSnapshot

    version = project.outline_versions.filter(is_active=True).first()
    if not version:
        return TextAnalysisSnapshot.objects.create(
            project=project, triggered_by=triggered_by
        )

    nodes = list(version.nodes.order_by("order"))

    # A — Dead Scenes
    dead = [n for n in nodes if _is_dead_scene(n)]

    # B — Screen Time (Figuren aus pov_character_id)
    screen_time = _compute_screen_time(nodes, project)

    # C — Pacing
    word_counts = [
        {"order": n.order, "word_count": n.word_count, "title": n.title[:40]}
        for n in nodes
        if n.word_count
    ]
    wc_values = [x["word_count"] for x in word_counts]
    variance = statistics.stdev(wc_values) if len(wc_values) > 1 else 0.0
    pacing_issues = _detect_pacing_issues(word_counts)

    # D — Dialogue Ratio
    dialogue_ratios = {
        str(n.order): _estimate_dialogue_ratio(n.content)
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

    if check_voice_drift:
        snap = _check_voice_drift(project, nodes, snap)

    snap.save()
    _enforce_fifo(project)
    return snap


def _is_dead_scene(node) -> bool:
    emotion_start = getattr(node, "emotion_start", None)
    emotion_end = getattr(node, "emotion_end", None)
    if not emotion_start or not emotion_end:
        return False
    return emotion_start.strip().lower() == emotion_end.strip().lower()


def _compute_screen_time(nodes: list, project) -> dict:
    counts: dict[str, dict] = {}
    total = len(nodes)

    role_map = {}
    try:
        for link in project.character_links.all():
            if link.weltenhub_character_id:
                role_map[str(link.weltenhub_character_id)] = link.narrative_role
    except Exception:
        pass

    for n in nodes:
        pov_id = getattr(n, "pov_character_id", None)
        if not pov_id:
            continue
        key = str(pov_id)
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
        counts[key]["percent"] = (
            round(counts[key]["chapters"] / total * 100, 1) if total else 0.0
        )

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
    dialogue_chars = sum(
        len(m.group())
        for m in re.finditer(r'[„»"][^"„»«]*["«»]', content)
    )
    return round(dialogue_chars / total, 2) if total else 0.0


def _check_voice_drift(project, nodes, snap):
    try:
        from aifw.service import sync_completion
    except ImportError:
        return snap

    voice = getattr(project, "narrative_voice", None)
    if not voice or not getattr(voice, "authoringfw_prompt_block", None):
        return snap

    written = [n for n in nodes if n.content and len(n.content) > 300]
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
    from apps.projects.models import TextAnalysisSnapshot
    qs = TextAnalysisSnapshot.objects.filter(project=project).order_by("-computed_at")
    ids_to_delete = list(qs.values_list("id", flat=True)[MAX_SNAPSHOTS:])
    if ids_to_delete:
        TextAnalysisSnapshot.objects.filter(id__in=ids_to_delete).delete()
