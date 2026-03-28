"""
DramaDashboardService — ADR-154

Bereitet Chart.js-kompatible Daten für Spannungskurve,
Emotion-Deltas und Wendepunkte auf.
"""
from __future__ import annotations

import json


OUTCOME_COLORS = {
    "yes":     "#22c55e",
    "no":      "#ef4444",
    "yes_but": "#f59e0b",
    "no_and":  "#7f1d1d",
    "":        "#94a3b8",
}


class DramaDashboardService:
    def __init__(self, project):
        self.project = project

    def get_tension_chart_data(self) -> dict:
        """
        Chart.js-kompatibles JSON für die Spannungskurve.
        Nur Nodes der aktiven OutlineVersion.
        """
        from apps.projects.models import OutlineNode

        nodes = list(
            OutlineNode.objects.filter(
                outline_version__project=self.project,
                outline_version__is_active=True,
            ).order_by("order")
        )

        labels = [f"{n.order}. {n.title[:30]}" for n in nodes]
        tension = [n.tension_numeric if n.tension_numeric is not None else None for n in nodes]
        point_colors = [OUTCOME_COLORS.get(n.outcome, "#94a3b8") for n in nodes]

        emotion_deltas = []
        drama_nodes = []
        for n in nodes:
            emotion_deltas.append({
                "label": f"{n.order}. {n.title[:25]}",
                "start": n.emotion_start or None,
                "end":   n.emotion_end or None,
            })
            drama_nodes.append({
                "pk": str(n.pk),
                "order": n.order,
                "title": n.title,
                "tension_numeric": n.tension_numeric,
                "outcome": n.outcome,
                "emotion_start": n.emotion_start,
                "emotion_end": n.emotion_end,
            })

        return {
            "labels": labels,
            "tension": tension,
            "point_colors": point_colors,
            "emotion_deltas": emotion_deltas,
            "drama_nodes": drama_nodes,
            "node_count": len(nodes),
            "has_tension_data": any(t is not None for t in tension),
        }

    def get_turning_points(self) -> list:
        from apps.projects.models import ProjectTurningPoint

        return list(
            ProjectTurningPoint.objects.filter(project=self.project)
            .select_related("turning_point_type", "node")
            .order_by("position_percent")
        )

    def get_health_data(self) -> dict:
        from apps.projects.services.health_service import compute_dramaturgic_health

        try:
            result = compute_dramaturgic_health(self.project)
            return {
                "score": result.score,
                "max_score": result.max_score,
                "percent": result.percent,
                "checks": [
                    {
                        "label": c.label,
                        "passed": c.passed,
                        "message": c.message or "",
                        "weight": c.weight,
                    }
                    for c in result.checks
                ],
            }
        except Exception:
            return {"score": 0, "max_score": 0, "percent": 0, "checks": []}

    def get_chart_json(self) -> str:
        data = self.get_tension_chart_data()
        return json.dumps({
            "labels": data["labels"],
            "datasets": [{
                "label": "Spannung",
                "data": data["tension"],
                "borderColor": "#6366f1",
                "backgroundColor": "rgba(99,102,241,0.08)",
                "tension": 0.4,
                "fill": True,
                "pointBackgroundColor": data["point_colors"],
                "pointRadius": 6,
                "pointHoverRadius": 9,
            }],
        })
