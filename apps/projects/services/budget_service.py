"""
BudgetService — ADR-161

Berechnet Wortanzahl-Budget pro Akt und Kapitel.
Pure Service — kein Model, kein LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ACT_PROPORTIONS = {
    "act_1": 0.25,
    "act_2a": 0.25,
    "act_2b": 0.25,
    "act_3": 0.25,
}
TOLERANCE = 0.20


@dataclass
class BudgetAllocation:
    target_total: int
    act_budgets: dict
    node_budgets: dict
    current_written: int
    remaining_budget: int
    over_budget_nodes: list
    under_budget_nodes: list
    completion_pct: float
    suggestions: list = field(default_factory=list)


def compute_budget(project) -> BudgetAllocation:
    """
    Berechnet Budget-Allokation für ein Projekt.

    Akt-Zuordnung über OutlineNode.act (defensiv via getattr).
    Standardmäßig 25% pro Akt (Drei-Akte-Modell).
    """
    target = project.target_word_count or 90_000
    version = project.outline_versions.filter(is_active=True).first()

    if not version:
        return BudgetAllocation(
            target_total=target,
            act_budgets={},
            node_budgets={},
            current_written=0,
            remaining_budget=target,
            over_budget_nodes=[],
            under_budget_nodes=[],
            completion_pct=0.0,
        )

    nodes = list(version.nodes.order_by("order"))
    total_written = sum(n.word_count for n in nodes if n.word_count)

    act_node_map: dict[str, list] = {k: [] for k in ACT_PROPORTIONS}
    for n in nodes:
        raw_act = getattr(n, "act", None) or "act_1"
        act = raw_act.lower().replace(" ", "_")
        if not act.startswith("act_"):
            act = f"act_{act}"
        bucket = act if act in act_node_map else "act_1"
        act_node_map[bucket].append(n)

    act_budgets = {act: int(target * prop) for act, prop in ACT_PROPORTIONS.items()}

    node_budgets = {}
    for act, act_nodes in act_node_map.items():
        if not act_nodes:
            continue
        per_node = act_budgets[act] // len(act_nodes)
        for n in act_nodes:
            node_budgets[str(n.id)] = per_node

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
            f"{len(alloc.over_budget_nodes)} Kapitel >20% über Budget — erwäge Szenen zu kürzen oder aufzuteilen."
        )
    remaining_unwritten = sum(1 for n in nodes if str(n.id) in alloc.node_budgets and not n.word_count)
    if alloc.remaining_budget > 0 and remaining_unwritten > 0:
        avg = alloc.remaining_budget // remaining_unwritten
        suggestions.append(
            f"Verbleibendes Budget: {alloc.remaining_budget:,} Wörter "
            f"(Ø {avg:,} für {remaining_unwritten} ungeschriebene Kapitel)."
        )
    return suggestions
