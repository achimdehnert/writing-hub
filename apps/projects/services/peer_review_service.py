"""
PeerReviewService — Multi-Agent wissenschaftliches Peer Review.

Orchestriert 4 spezialisierte Review-Agenten:
  1. Methodik-Prüfer (methodology)
  2. Argumentations-Prüfer (argumentation)
  3. Quellen-Prüfer (sources)
  4. Struktur-Prüfer (structure)

Erzeugt anschließend ein Gesamtgutachten (Editor-in-Chief).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from django.utils import timezone

logger = logging.getLogger(__name__)

PEER_REVIEW_AGENTS = [
    {
        "key": "methodology",
        "name": "Methodik-Prüfer",
        "icon": "bi-clipboard-data",
        "description": "Prüft Forschungsdesign, Validität, Reliabilität und Reproduzierbarkeit",
        "prompt_template": "projects/peer_review_methodology",
    },
    {
        "key": "argumentation",
        "name": "Argumentations-Prüfer",
        "icon": "bi-diagram-3",
        "description": "Prüft Logik, Evidenz, Kausalität und Bias",
        "prompt_template": "projects/peer_review_argumentation",
    },
    {
        "key": "sources",
        "name": "Quellen-Prüfer",
        "icon": "bi-journal-bookmark",
        "description": "Prüft Quellenabdeckung, Aktualität und Zitierethik",
        "prompt_template": "projects/peer_review_sources",
    },
    {
        "key": "structure",
        "name": "Struktur-Prüfer",
        "icon": "bi-list-nested",
        "description": "Prüft Gliederung, Kohärenz und akademische Konventionen",
        "prompt_template": "projects/peer_review_structure",
    },
]

VALID_FINDING_TYPES = {"strength", "weakness", "suggestion", "concern"}
VALID_SEVERITIES = {"minor", "major", "critical"}

# Content types that support peer review
SCIENTIFIC_CONTENT_TYPES = {"scientific", "academic", "essay"}


def is_peer_review_eligible(project) -> bool:
    """Check if a project supports scientific peer review."""
    return project.content_type in SCIENTIFIC_CONTENT_TYPES


def run_peer_review(
    project,
    user,
    agents: list[str] | None = None,
) -> str:
    """
    Run a full scientific peer review on a project.

    Args:
        project: BookProject instance
        user: requesting user
        agents: optional subset of agent keys to run

    Returns:
        PeerReviewSession UUID as string
    """
    from apps.projects.models import (
        OutlineVersion,
        PeerReviewSession,
    )

    active_agents = PEER_REVIEW_AGENTS
    if agents:
        active_agents = [a for a in PEER_REVIEW_AGENTS if a["key"] in agents]
    if not active_agents:
        active_agents = PEER_REVIEW_AGENTS

    version = (
        OutlineVersion.objects.filter(project=project, is_active=True)
        .order_by("-created_at")
        .first()
    )
    if not version:
        logger.warning("No active outline for project %s", project.pk)
        return ""

    chapters = list(version.nodes.order_by("order"))
    if not chapters:
        logger.warning("No chapters for project %s", project.pk)
        return ""

    session = PeerReviewSession.objects.create(
        project=project,
        created_by=user,
        status="running",
        chapter_count=len(chapters),
        agents_used=[a["key"] for a in active_agents],
    )

    try:
        total_findings = _run_agents(session, project, chapters, active_agents)
        _generate_verdict(session, project, chapters, total_findings)

        session.status = "done"
        session.finding_count = total_findings
        session.finished_at = timezone.now()
        session.save(update_fields=[
            "status", "finding_count", "finished_at",
            "verdict", "summary", "strengths", "main_issues",
            "recommendations", "scores",
        ])
    except Exception as exc:
        logger.exception("PeerReview error for project %s: %s", project.pk, exc)
        session.status = "error"
        session.summary = str(exc)[:500]
        session.save(update_fields=["status", "summary"])

    return str(session.pk)


def _run_agents(session, project, chapters, agents) -> int:
    """Run each agent on each chapter. Returns total finding count."""
    from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
    from apps.core.prompt_utils import render_prompt
    from apps.projects.models import PeerReviewFinding

    router = LLMRouter()
    total = 0
    section_titles = " → ".join(ch.title for ch in chapters)
    content_type_label = project.get_content_type_display()

    for agent in agents:
        for node in chapters:
            if not node.content or not node.content.strip():
                continue

            template_ctx = {
                "order": node.order,
                "title": node.title,
                "content": node.content,
                "project_title": project.title,
                "content_type": content_type_label,
                "section_titles": section_titles,
            }

            prompt_msgs = render_prompt(agent["prompt_template"], **template_ctx)
            if not prompt_msgs:
                prompt_msgs = _fallback_prompt(agent, node, project)

            try:
                raw = router.completion(
                    action_code="peer_review",
                    messages=prompt_msgs,
                )
                findings = _parse_findings(raw)
                for f in findings[:10]:
                    finding_type = f.get("type", "suggestion")
                    if finding_type not in VALID_FINDING_TYPES:
                        finding_type = "suggestion"
                    severity = f.get("severity", "minor")
                    if severity not in VALID_SEVERITIES:
                        severity = "minor"

                    PeerReviewFinding.objects.create(
                        session=session,
                        node=node,
                        agent=agent["key"],
                        finding_type=finding_type,
                        category=f.get("category", "")[:50],
                        severity=severity,
                        feedback=f.get("feedback", "")[:2000],
                        text_reference=f.get("text_ref", "")[:500],
                    )
                    total += 1

            except LLMRoutingError as exc:
                logger.warning(
                    "PeerReview LLM error agent=%s node=%s: %s",
                    agent["key"], node.pk, exc,
                )
            except Exception as exc:
                logger.warning(
                    "PeerReview agent=%s node=%s error: %s",
                    agent["key"], node.pk, exc,
                )

    return total


def _generate_verdict(session, project, chapters, total_findings: int):
    """Generate overall verdict using Editor-in-Chief prompt."""
    from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError
    from apps.core.prompt_utils import render_prompt
    from apps.projects.models import PeerReviewFinding

    findings = PeerReviewFinding.objects.filter(session=session).select_related("node")

    section_summaries = []
    for ch in chapters:
        ch_findings = [f for f in findings if str(f.node_id) == str(ch.pk)]
        if ch_findings:
            summary_parts = [f"### {ch.title}"]
            for f in ch_findings[:5]:
                summary_parts.append(
                    f"- [{f.get_agent_display()}] ({f.severity}) {f.feedback[:150]}"
                )
            section_summaries.append("\n".join(summary_parts))

    finding_summary_parts = []
    for sev in ("critical", "major", "minor"):
        sev_findings = [f for f in findings if f.severity == sev]
        if sev_findings:
            finding_summary_parts.append(
                f"**{sev.upper()}**: {len(sev_findings)} Findings"
            )
            for f in sev_findings[:3]:
                finding_summary_parts.append(f"  - {f.feedback[:100]}")

    prompt_msgs = render_prompt(
        "projects/peer_review_summary",
        project_title=project.title,
        content_type=project.get_content_type_display(),
        section_summaries="\n\n".join(section_summaries) or "Keine Abschnitte analysiert.",
        finding_summary="\n".join(finding_summary_parts) or f"{total_findings} Findings insgesamt.",
    )

    if not prompt_msgs:
        return

    try:
        router = LLMRouter()
        raw = router.completion(
            action_code="peer_review_verdict",
            messages=prompt_msgs,
        )
        verdict_data = _parse_verdict(raw)
        if verdict_data:
            valid_verdicts = {"accept", "minor_revisions", "major_revisions", "reject"}
            session.verdict = verdict_data.get("verdict", "major_revisions")
            if session.verdict not in valid_verdicts:
                session.verdict = "major_revisions"
            session.summary = verdict_data.get("summary", "")[:500]
            session.strengths = verdict_data.get("strengths", [])[:10]
            session.main_issues = verdict_data.get("main_issues", [])[:10]
            session.recommendations = verdict_data.get("recommendations", [])[:10]
            session.scores = verdict_data.get("scores", {})
    except (LLMRoutingError, Exception) as exc:
        logger.warning("PeerReview verdict generation error: %s", exc)
        session.verdict = ""
        session.summary = f"Gutachten konnte nicht erstellt werden: {exc}"


def _parse_findings(raw: str) -> list[dict[str, Any]]:
    """Parse JSON array of findings from LLM response."""
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group())
        if isinstance(items, list):
            return [i for i in items if isinstance(i, dict) and i.get("feedback")]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _parse_verdict(raw: str) -> dict[str, Any] | None:
    """Parse JSON verdict object from LLM response."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _fallback_prompt(agent: dict, node, project) -> list[dict[str, str]]:
    """Generate fallback prompt if template rendering fails."""
    role_map = {
        "methodology": "Methodik-Prüfer für Forschungsdesign und Validität",
        "argumentation": "Argumentationsprüfer für Logik und Evidenz",
        "sources": "Quellenprüfer für Zitierpraxis und Literaturabdeckung",
        "structure": "Strukturprüfer für Gliederung und akademische Konventionen",
    }
    role = role_map.get(agent["key"], "wissenschaftlicher Reviewer")
    return [
        {
            "role": "system",
            "content": (
                f"Du bist ein erfahrener {role}.\n"
                "Antworte als JSON-Array: "
                '[{"type": "strength|weakness|suggestion|concern", '
                '"category": "...", "severity": "minor|major|critical", '
                '"feedback": "...", "text_ref": "..."}]'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Projekt: {project.title}\n"
                f"Abschnitt {node.order}: {node.title}\n\n"
                f"{(node.content or '')[:8000]}"
            ),
        },
    ]
