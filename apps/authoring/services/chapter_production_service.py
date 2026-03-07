"""
Chapter Production Service
===========================

Pipeline:
  1. Brief    — Kapitel-Brief aus Outline + Kontext
  2. Write    — LLM schreibt Kapitel (via aifw, action_code=chapter_write)
  3. Analyze  — Qualitaetsanalyse (action_code=chapter_analyze)
  4. Gate     — Approve / Review / Revise / Reject
  5. Commit   — Speichern oder Revisions-Loop

Alle LLM-Calls ausschliesslich via LLMRouter (aifw). Kein direkter API-Zugriff.
ADR-095: quality_level aus Projekt-Tier via get_quality_level_for_tier().
"""

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID

from django.db import transaction

from .llm_router import LLMRouter, LLMRoutingError, get_quality_level_for_tier
from .project_context_service import ProjectContextService

logger = logging.getLogger(__name__)


class ProductionStage(str, Enum):
    BRIEF = "brief"
    WRITE = "write"
    ANALYZE = "analyze"
    GATE = "gate"
    REVISE = "revise"
    COMMIT = "commit"


@dataclass
class BriefResult:
    success: bool
    brief: str = ""
    production_goals: list[str] = field(default_factory=list)
    tone_notes: str = ""
    error: str = ""


@dataclass
class WriteResult:
    success: bool
    content: str = ""
    word_count: int = 0
    error: str = ""


@dataclass
class AnalyzeResult:
    success: bool
    overall_score: Decimal = Decimal("0")
    strengths: list[str] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    error: str = ""


@dataclass
class GateResult:
    decision: str = "review"  # approve | review | revise | reject
    allows_commit: bool = False
    reason: str = ""
    required_fixes: list[str] = field(default_factory=list)


@dataclass
class ProductionResult:
    success: bool
    stage: ProductionStage
    chapter_id: UUID | None = None
    brief: BriefResult | None = None
    write: WriteResult | None = None
    analyze: AnalyzeResult | None = None
    gate: GateResult | None = None
    iterations: int = 1
    duration_seconds: float = 0.0
    error: str = ""


class ChapterProductionService:
    """
    Orchestriert die vollstaendige Kapitel-Produktions-Pipeline.

    Verwendung:
        svc = ChapterProductionService(project_id, user)
        result = svc.produce_chapter(chapter_id)

        # Oder einzelne Stages:
        brief = svc.generate_brief(chapter_id)
        write = svc.write_chapter(chapter_id, brief.brief)
        analyze = svc.analyze_chapter(chapter_id, write.content)
        gate = svc.evaluate_gate(analyze)
    """

    def __init__(self, project_id: str, user=None):
        self._project_id = str(project_id)
        self.user = user
        self._router = LLMRouter()
        self._ctx_service = ProjectContextService()
        self._quality_level: int | None = self._resolve_quality_level()

    def _resolve_quality_level(self) -> int | None:
        """Quality-Level aus Projekt-Tier (ADR-095)."""
        try:
            from apps.projects.models import BookProject

            project = BookProject.objects.get(pk=self._project_id)
            tier = getattr(project, "subscription_tier", None)
            if tier:
                return get_quality_level_for_tier(str(tier))
        except Exception:
            pass
        return None

    def _get_context_block(self) -> str:
        """Projekt-Kontext als Text-Block fuer System-Prompt."""
        ctx = self._ctx_service.get_context(self._project_id)
        return ctx.to_prompt_block()

    def generate_brief(self, chapter_id: str) -> BriefResult:
        """Stage 1: Kapitel-Brief aus Outline und Kontext generieren."""
        from apps.projects.models import OutlineNode, OutlineVersion, BookProject

        try:
            project = BookProject.objects.get(pk=self._project_id)
            version = OutlineVersion.objects.filter(
                project=project, is_active=True
            ).order_by("-created_at").first()

            node = None
            if version:
                node = OutlineNode.objects.filter(
                    outline_version=version, pk=chapter_id
                ).first()

            ctx_block = self._get_context_block()
            node_text = ""
            if node:
                node_text = f"\n\n## Kapitel {node.order}: {node.title}\n{node.description}"

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Du bist ein Buchschreib-Assistent. "
                        "Erstelle einen praezisen Schreib-Brief fuer das folgende Kapitel.\n\n"
                        + ctx_block
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Erstelle einen Schreib-Brief fuer das Kapitel:{node_text}\n\n"
                        "Enthalte: Produktionsziele, Ton-Hinweise, "
                        "Charaktermomente und Szenen-Reihung als strukturiertes Briefing."
                    ),
                },
            ]

            content = self._router.completion(
                "chapter_brief",
                messages,
                quality_level=self._quality_level,
            )
            return BriefResult(success=True, brief=content)

        except LLMRoutingError as exc:
            logger.error("generate_brief Fehler: %s", exc)
            return BriefResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("generate_brief unerwarteter Fehler")
            return BriefResult(success=False, error=str(exc))

    def write_chapter(
        self,
        chapter_id: str,
        brief: str,
        target_words: int = 2000,
    ) -> WriteResult:
        """Stage 2: Kapitel schreiben via aifw action_code=chapter_write."""
        ctx_block = self._get_context_block()

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein professioneller Romanautor. "
                    f"Schreibe prosaisch, immersiv und mit ca. {target_words} Woertern.\n\n"
                    + ctx_block
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Schreibe das Kapitel gemaess diesem Brief:\n\n{brief}\n\n"
                    f"Ziellaenge: ca. {target_words} Woerter. "
                    "Schreibe den vollen Kapiteltext — kein Kommentar, keine Erklaerung."
                ),
            },
        ]

        try:
            content = self._router.completion(
                "chapter_write",
                messages,
                quality_level=self._quality_level,
                priority="quality",
            )
            word_count = len(content.split()) if content else 0
            return WriteResult(success=True, content=content, word_count=word_count)

        except LLMRoutingError as exc:
            logger.error("write_chapter Fehler: %s", exc)
            return WriteResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("write_chapter unerwarteter Fehler")
            return WriteResult(success=False, error=str(exc))

    def analyze_chapter(
        self,
        chapter_id: str,
        content: str,
    ) -> AnalyzeResult:
        """Stage 3: Kapitel-Qualitaetsanalyse via aifw action_code=chapter_analyze."""
        ctx_block = self._get_context_block()

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein Lektorats-KI. "
                    "Analysiere das Kapitel nach diesen Dimensionen: "
                    "Stil, Tempo, Charakterkonsistenz, Dialog, Szenenaufbau.\n\n"
                    + ctx_block
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analysiere diesen Kapiteltext und gib ein JSON-Objekt zurueck:\n\n"
                    f"{content[:6000]}\n\n"
                    "Format: {\"overall_score\": 7.5, \"strengths\": [...], "
                    "\"issues\": [{\"dimension\": \"...\", \"description\": \"...\"}]}"
                ),
            },
        ]

        try:
            import json
            import re

            raw = self._router.completion(
                "chapter_analyze",
                messages,
                quality_level=self._quality_level,
            )
            # JSON extrahieren
            match = re.search(r"\{[\s\S]+\}", raw)
            if match:
                data = json.loads(match.group())
                return AnalyzeResult(
                    success=True,
                    overall_score=Decimal(str(data.get("overall_score", 7.0))),
                    strengths=data.get("strengths", []),
                    issues=data.get("issues", []),
                )
            return AnalyzeResult(
                success=True,
                overall_score=Decimal("7.0"),
                strengths=[],
                issues=[],
            )

        except LLMRoutingError as exc:
            logger.error("analyze_chapter Fehler: %s", exc)
            return AnalyzeResult(success=False, error=str(exc))
        except Exception as exc:
            logger.exception("analyze_chapter unerwarteter Fehler")
            return AnalyzeResult(success=False, error=str(exc))

    def evaluate_gate(self, analyze: AnalyzeResult) -> GateResult:
        """Stage 4: Gate-Entscheidung basierend auf Analyse-Score."""
        score = float(analyze.overall_score)
        issues_critical = [
            i for i in analyze.issues if "kritisch" in str(i).lower()
        ]

        if score >= 8.5 and not issues_critical:
            return GateResult(
                decision="approve",
                allows_commit=True,
                reason=f"Score {score:.1f} ≥ 8.5, keine kritischen Issues.",
            )
        elif score >= 7.0:
            return GateResult(
                decision="review",
                allows_commit=False,
                reason=f"Score {score:.1f} — manuelle Pruefung empfohlen.",
            )
        elif score >= 5.0:
            fixes = [i.get("description", "") for i in analyze.issues[:3]]
            return GateResult(
                decision="revise",
                allows_commit=False,
                reason=f"Score {score:.1f} — Revision erforderlich.",
                required_fixes=fixes,
            )
        else:
            return GateResult(
                decision="reject",
                allows_commit=False,
                reason=f"Score {score:.1f} < 5.0 — Kapitel verwerfen.",
            )

    def produce_chapter(
        self,
        chapter_id: str,
        target_words: int = 2000,
        max_iterations: int = 3,
        auto_commit: bool = False,
    ) -> ProductionResult:
        """Vollstaendige Produktions-Pipeline."""
        start = time.time()

        brief_result = self.generate_brief(chapter_id)
        if not brief_result.success:
            return ProductionResult(
                success=False,
                stage=ProductionStage.BRIEF,
                chapter_id=chapter_id,
                brief=brief_result,
                error=brief_result.error,
                duration_seconds=time.time() - start,
            )

        for iteration in range(1, max_iterations + 1):
            write_result = self.write_chapter(
                chapter_id, brief_result.brief, target_words=target_words
            )
            if not write_result.success:
                return ProductionResult(
                    success=False,
                    stage=ProductionStage.WRITE,
                    chapter_id=chapter_id,
                    brief=brief_result,
                    write=write_result,
                    iterations=iteration,
                    error=write_result.error,
                    duration_seconds=time.time() - start,
                )

            analyze_result = self.analyze_chapter(chapter_id, write_result.content)
            gate_result = self.evaluate_gate(analyze_result)

            if gate_result.allows_commit or not gate_result.required_fixes:
                if auto_commit:
                    self._commit_chapter(chapter_id, write_result.content)
                return ProductionResult(
                    success=True,
                    stage=ProductionStage.COMMIT if auto_commit else ProductionStage.GATE,
                    chapter_id=chapter_id,
                    brief=brief_result,
                    write=write_result,
                    analyze=analyze_result,
                    gate=gate_result,
                    iterations=iteration,
                    duration_seconds=time.time() - start,
                )

            if iteration < max_iterations:
                # Brief mit Revision-Hinweisen anreichern
                fixes_text = "\n".join(
                    f"- {f}" for f in gate_result.required_fixes
                )
                brief_result = BriefResult(
                    success=True,
                    brief=(
                        brief_result.brief
                        + f"\n\n## Revisions-Hinweise (Iteration {iteration})\n"
                        + fixes_text
                    ),
                )

        return ProductionResult(
            success=True,
            stage=ProductionStage.GATE,
            chapter_id=chapter_id,
            brief=brief_result,
            write=write_result,
            analyze=analyze_result,
            gate=gate_result,
            iterations=max_iterations,
            duration_seconds=time.time() - start,
        )

    def _commit_chapter(self, chapter_id: str, content: str) -> None:
        """Kapitel-Inhalt in DB speichern."""
        try:
            from apps.projects.models import OutlineNode

            node = OutlineNode.objects.get(pk=chapter_id)
            node.description = content
            node.save(update_fields=["description"])
        except Exception as exc:
            logger.error("_commit_chapter Fehler: %s", exc)


def get_chapter_production_service(
    project_id: str, user=None
) -> ChapterProductionService:
    """Factory fuer ChapterProductionService."""
    return ChapterProductionService(project_id=project_id, user=user)
